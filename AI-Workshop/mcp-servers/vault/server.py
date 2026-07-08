#!/usr/bin/env python3
"""Vault MCP server — queryable navigation for the Context vault.

Replaces loading whole files into context with targeted lookups. Each tool
returns only what matches, so per-task overhead stops growing as the vault
grows.

Tools (read-only unless noted):
  Navigation / selection
    - find_skill(query)            → best-matching skills (BM25 over SKILL.md)
    - resolve_agent(task)          → best-matching sub-agents (BM25 over AGENT.md)
  Orientation
    - get_open_work()              → open items from open-work.md
    - get_session_brief()          → one-call startup bundle (session, work, prefs, caps)
  Content
    - search_notes(query)          → BM25 over note bodies, returns path + snippet
  Link graph (BFS over [[wikilinks]])
    - get_links(note, ...)         → neighbours by link distance
    - find_broken_links()          → links pointing at nothing
    - find_orphans()               → notes nothing links to
  Structure / resolution
    - resolve_note(name)           → a [[wikilink]] / bare name -> real path(s)
    - vault_tree(path, depth)      → compact folder/file layout
    - list_by_status(status)       → notes by validated `status` frontmatter field
  Maintenance
    - vault_health(fix)            → one-call maintenance report (links, orphans,
                                     maps, lint, archive candidates); fix=true also
                                     applies the deterministic safe fixes (writes)
  Session close
    - wrap_session(...)            → writes the handoff note, applies open-work
                                     changes, archives history notes (writes)

A single mtime-cached index backs every tool below find_skill/resolve_agent, so
a query reparses only the files that changed since the last call. The index
honours Context/.vaultignore (so the Starter mirror and test trees do not
double every note).

ZERO DEPENDENCIES: implements the MCP stdio protocol (newline-delimited
JSON-RPC 2.0) with the Python standard library only. Runs under any system
python3 (>=3.7) with no venv and no pip install.

Vault root resolves to VAULT_PATH if set, else the repo root three levels above
this file (AI-Workshop/mcp-servers/vault/server.py -> vault root).
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from collections import Counter, deque
from fnmatch import fnmatch
from pathlib import Path

VAULT = Path(os.environ.get("VAULT_PATH", str(Path(__file__).resolve().parents[3])))

# Fixed status vocabulary. The server validates against this, so the field
# cannot drift into synonyms (#wip vs #in-progress) the way free tags would.
STATUS_VOCAB = ["idea", "active", "blocked", "needs-eval", "done"]

# Basenames / subtrees that are entry points by nature — excluded from the
# orphan report so it surfaces only notes that probably *should* be linked.
_ORPHAN_EXEMPT_NAMES = {
    "main", "claude", "readme", "memory", "open-work",
    "vault_map", "skill_map", "agent_map", "systems_map",
    "human", "onboarding",
}
_ORPHAN_EXEMPT_DIRS = ("Context/History", "Context/Diagnostics", "Context/Memory")

# --------------------------------------------------------------------------- #
# Text utilities + BM25 ranking
# --------------------------------------------------------------------------- #
_WORD = re.compile(r"[a-z0-9]+")


def _tok(text):
    return _WORD.findall((text or "").lower())


def _bm25_rank(query, docs, k1=1.5, b=0.75):
    """Rank docs by BM25 relevance to query.

    docs: list of (id, payload, tokens). Returns [(id, payload, score)] sorted
    by score descending, keeping only positive scores.
    """
    q = set(_tok(query))
    n = len(docs)
    if not q or n == 0:
        return []
    df = Counter()
    for _id, _payload, toks in docs:
        for t in set(toks):
            df[t] += 1
    avgdl = sum(len(toks) for _, _, toks in docs) / n
    idf = {t: math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) for t in q if df.get(t)}
    ranked = []
    for id_, payload, toks in docs:
        tf = Counter(toks)
        dl = len(toks) or 1
        score = 0.0
        for t in q:
            f = tf.get(t, 0)
            if f and t in idf:
                score += idf[t] * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        if score > 0:
            ranked.append((id_, payload, round(score, 3)))
    ranked.sort(key=lambda r: -r[2])
    return ranked


# --------------------------------------------------------------------------- #
# .vaultignore  (so scans/index skip tests, the Starter mirror, generated dirs)
# --------------------------------------------------------------------------- #
_DEFAULT_IGNORE = [".git/", ".obsidian/", ".trash/"]


def _load_ignore():
    patterns = list(_DEFAULT_IGNORE)
    p = VAULT / "Context" / ".vaultignore"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def _ignored(rel, patterns):
    """True if a vault-relative path (file or dir) matches an ignore pattern."""
    rel = rel.replace(os.sep, "/").strip("/")
    if not rel:
        return False
    parts = rel.split("/")
    for pat in patterns:
        p = pat.strip()
        if not p:
            continue
        if p.startswith("**/"):
            name = p[3:].rstrip("/")
            if name and name in parts:
                return True
        elif any(ch in p for ch in "*?["):
            glob = p.rstrip("/")
            if any(fnmatch(part, glob) for part in parts):
                return True
        else:
            pref = p.rstrip("/")
            if rel == pref or rel.startswith(pref + "/"):
                return True
    return False


def _iter_files(patterns):
    """Yield (abs_path, rel_path) for every non-ignored file, pruning ignored dirs."""
    root = str(VAULT)
    for dirpath, dirnames, filenames in os.walk(root):
        reldir = os.path.relpath(dirpath, root)
        reldir = "" if reldir == "." else reldir
        dirnames[:] = [
            d for d in dirnames
            if not _ignored((reldir + "/" + d) if reldir else d, patterns)
        ]
        for fn in filenames:
            rel = (reldir + "/" + fn) if reldir else fn
            rel = rel.replace(os.sep, "/")
            if _ignored(rel, patterns):
                continue
            yield os.path.join(dirpath, fn), rel


# --------------------------------------------------------------------------- #
# Frontmatter + wikilink parsing
# --------------------------------------------------------------------------- #
_FM_LINE = re.compile(r"(?m)^([A-Za-z][\w-]*):\s*(.*)$")
_LINK = re.compile(r"\[\[([^\]]+)\]\]")
_H1 = re.compile(r"(?m)^#\s+(.+?)\s*$")


def _parse_frontmatter(md):
    """Return (frontmatter_dict, body). Simple line-based YAML for `key: value`."""
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            block = md[3:end]
            body = md[end + 4:]
            fm = {}
            for m in _FM_LINE.finditer(block):
                fm[m.group(1).strip().lower()] = m.group(2).strip().strip("'\"")
            return fm, body
    return {}, md


def _norm_key(target):
    """Normalize a wikilink target / note name to its lookup keys.

    Returns (basename_key, fullpath_key) lowercased, alias/heading/.md stripped,
    or (None, None) for template placeholders or heading-only links.
    """
    t = target.strip()
    if t.startswith("[[") and t.endswith("]]"):
        t = t[2:-2]
    t = t.split("|")[0].split("#")[0].strip()
    if not t or "{" in t:
        return None, None
    if t.lower().endswith(".md"):
        t = t[:-3]
    full = t.strip().lower()
    base = full.split("/")[-1]
    return base, full


# --------------------------------------------------------------------------- #
# Cached vault index
# --------------------------------------------------------------------------- #
_FENCE = re.compile(r"```.*?```", re.S)
_INLINE_CODE = re.compile(r"`[^`]*`")


def _strip_code(md):
    """Drop fenced and inline code so example [[links]] in docs aren't counted."""
    return _INLINE_CODE.sub(" ", _FENCE.sub(" ", md))


# rel -> (mtime, note_dict). Reparses only files whose mtime changed.
_NOTE_CACHE = {}


def _build_index():
    """Return the live index, reparsing only changed markdown files.

    Index dict:
      notes        : list of note dicts {rel, title, frontmatter, body, links[], mtime}
      by_key       : note lookup key (basename + relpath-without-ext) -> [rel]
      file_keys    : set of every file's basename + relpath (lower) for link checks
    """
    patterns = _load_ignore()
    notes = []
    file_keys = set()
    seen = set()
    for abs_path, rel in _iter_files(patterns):
        low = rel.lower()
        file_keys.add(low)
        file_keys.add(low.split("/")[-1])
        if not rel.endswith(".md"):
            continue
        seen.add(rel)
        try:
            mtime = os.path.getmtime(abs_path)
        except OSError:
            continue
        cached = _NOTE_CACHE.get(rel)
        if cached and cached[0] == mtime:
            notes.append(cached[1])
            continue
        try:
            md = Path(abs_path).read_text(encoding="utf-8")
        except OSError:
            continue
        fm, body = _parse_frontmatter(md)
        title_m = _H1.search(md)
        links = []
        for raw in _LINK.findall(_strip_code(md)):
            base, _full = _norm_key(raw)
            if base:
                links.append(raw.split("|")[0].split("#")[0].strip())
        note = {
            "rel": rel,
            "title": title_m.group(1).strip() if title_m else rel.rsplit("/", 1)[-1][:-3],
            "frontmatter": fm,
            "body": body,
            "links": links,
            "mtime": mtime,
        }
        _NOTE_CACHE[rel] = (mtime, note)
        notes.append(note)

    # Drop cache entries for deleted files.
    for stale in [r for r in _NOTE_CACHE if r not in seen]:
        _NOTE_CACHE.pop(stale, None)

    # Ignored-but-linkable trees: excluded from notes/orphans (not canonical
    # vault content) but valid link targets, so links into them aren't flagged
    # broken. .claude skills are first-class (registered in skill_map).
    for p in VAULT.glob(".claude/skills/*/SKILL.md"):
        file_keys.add(p.parent.name.lower())
    for p in (VAULT / "Workshop-Human").rglob("*.md"):
        file_keys.add(p.name.lower())
        file_keys.add(p.stem.lower())

    by_key = {}
    for note in notes:
        rel = note["rel"]
        without_ext = rel[:-3].lower()
        fname = without_ext.split("/")[-1]
        keys = {without_ext}
        # Skills/agents are folder-named (file is AGENT.md/SKILL.md), and the
        # vault links them as [[folder-name]] — so key by the containing folder.
        if fname in ("agent", "skill", "index", "readme") and "/" in without_ext:
            keys.add(without_ext.split("/")[-2])
        else:
            keys.add(fname)
        for k in keys:
            by_key.setdefault(k, []).append(rel)
    return {"notes": notes, "by_key": by_key, "file_keys": file_keys}


def _resolve_to_rel(name, index):
    """Resolve a wikilink/name to matching note rel path(s)."""
    base, full = _norm_key(name)
    if base is None:
        return []
    hits = index["by_key"].get(full) or index["by_key"].get(base) or []
    # de-dupe, preserve order
    out = []
    for r in hits:
        if r not in out:
            out.append(r)
    return out


def _adjacency(index):
    """Build outbound/inbound adjacency maps keyed by rel path."""
    out = {n["rel"]: set() for n in index["notes"]}
    inb = {n["rel"]: set() for n in index["notes"]}
    for note in index["notes"]:
        src = note["rel"]
        for raw in note["links"]:
            for tgt in _resolve_to_rel(raw, index):
                if tgt != src:
                    out[src].add(tgt)
                    inb.setdefault(tgt, set()).add(src)
    return out, inb


# --------------------------------------------------------------------------- #
# Loaders for skill/agent/open-work (specific structure, kept lightweight)
# --------------------------------------------------------------------------- #
def _load_skills():
    out = []
    for p in sorted((VAULT / "Context" / "Skills").glob("*/SKILL.md")):
        try:
            md = p.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, _ = _parse_frontmatter(md)
        out.append({
            "name": fm.get("name") or p.parent.name,
            "path": str(p.relative_to(VAULT)),
            "description": fm.get("description") or "",
        })
    return out


def _load_agents():
    out = []
    for p in sorted((VAULT / "Context" / "Agents").glob("*/AGENT.md")):
        try:
            md = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m = re.search(r"(?ms)^##\s+Purpose\s*\n(.+?)(?=\n##\s|\Z)", md)
        purpose = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        out.append({"name": p.parent.name, "path": str(p.relative_to(VAULT)), "purpose": purpose})
    return out


def _load_open_work():
    p = VAULT / "Context" / "History" / "open-work.md"
    if not p.exists():
        return []
    md = p.read_text(encoding="utf-8")
    m = re.search(r"(?ms)^##\s+Open\s*\n(.+?)(?=^##\s+Done|\Z)", md)
    body = m.group(1) if m else md
    items = []
    for blk in re.split(r"(?m)^###\s+", body):
        blk = blk.strip()
        if not blk:
            continue
        head, _, rest = blk.partition("\n")
        summary = re.sub(r"\s+", " ", rest).strip()
        summary = re.sub(r"\s*-{3,}\s*$", "", summary).strip()  # drop trailing --- rule
        items.append({"title": head.strip(), "summary": summary[:600]})
    return items


# --------------------------------------------------------------------------- #
# Core logic — existing tools
# --------------------------------------------------------------------------- #
def find_skill_core(query, limit=3):
    skills = _load_skills()
    docs = [(s["name"], s, _tok(s["name"] + " " + s["name"] + " " + s["description"])) for s in skills]
    ranked = _bm25_rank(query, docs)[: max(1, int(limit))]
    return {"query": query, "matches": [
        {"name": p["name"], "path": p["path"], "description": p["description"], "score": sc}
        for _, p, sc in ranked]}


def get_open_work_core():
    return {"open_work": _load_open_work()}


def resolve_agent_core(task, limit=3):
    agents = _load_agents()
    docs = [(a["name"], a, _tok(a["name"] + " " + a["purpose"])) for a in agents]
    ranked = _bm25_rank(task, docs)[: max(1, int(limit))]
    return {"task": task, "matches": [
        {"name": p["name"], "path": p["path"], "purpose": p["purpose"][:300], "score": sc}
        for _, p, sc in ranked]}


# --------------------------------------------------------------------------- #
# Core logic — new tools
# --------------------------------------------------------------------------- #
def _snippet(body, query, width=200):
    toks = set(_tok(query))
    for line in body.splitlines():
        low = line.lower()
        if any(t in low for t in toks):
            s = line.strip()
            return (s[:width] + "…") if len(s) > width else s
    s = " ".join(body.split())
    return (s[:width] + "…") if len(s) > width else s


def search_notes_core(query, limit=5, scope=None):
    index = _build_index()
    notes = index["notes"]
    if scope:
        sc = scope.strip("/").lower()
        notes = [n for n in notes if n["rel"].lower().startswith(sc + "/") or n["rel"].lower().startswith(sc)]
    docs = [(n["rel"], n, _tok(n["title"] + " " + n["body"])) for n in notes]
    ranked = _bm25_rank(query, docs)[: max(1, int(limit))]
    return {"query": query, "scope": scope, "matches": [
        {"path": n["rel"], "title": n["title"], "score": sc, "snippet": _snippet(n["body"], query)}
        for _, n, sc in ranked]}


def _latest_session_file():
    hist = VAULT / "Context" / "History"
    if not hist.exists():
        return None
    cands = []
    for p in hist.glob("*.md"):
        if p.name == "open-work.md":
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
        date = m.group(1) if m else ""
        try:
            mtime = p.stat().st_mtime
        except OSError:
            mtime = 0
        cands.append((date, mtime, p))
    if not cands:
        return None
    # Date first, then mtime — so same-date sessions order by actual recency.
    cands.sort(key=lambda c: (c[0], c[1]))
    return cands[-1][2]


def _load_preferences():
    p = VAULT / "Context" / "Memory" / "MEMORY.md"
    if not p.exists():
        return []
    prefs = []
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*[-*]\s*\[([^\]]+)\]\(([^)]+)\)\s*[—-]+\s*(.+)$", line)
        if m:
            prefs.append({"label": m.group(1).strip(), "note": m.group(2).strip(),
                          "summary": m.group(3).strip()})
    return prefs


def get_session_brief_core():
    f = _latest_session_file()
    last = None
    if f:
        md = f.read_text(encoding="utf-8")
        h1 = _H1.search(md)
        title = h1.group(1).strip() if h1 else f.stem
        if "—" in title:
            title = title.split("—")[-1].strip()
        dm = re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
        last = {"date": dm.group(1) if dm else "", "file": str(f.relative_to(VAULT)),
                "topic": title}
    skills = _load_skills()
    agents = _load_agents()
    return {
        "last_session": last,
        "open_work": _load_open_work(),
        "preferences": _load_preferences(),
        "capabilities": {
            "skills": sorted(s["name"] for s in skills),
            "agents": sorted(a["name"] for a in agents),
        },
    }


def get_links_core(note, direction="both", depth=1):
    index = _build_index()
    starts = _resolve_to_rel(note, index)
    if not starts:
        return {"error": "No note matches %r. Try resolve_note first." % note, "matches": []}
    start = starts[0]
    out, inb = _adjacency(index)
    depth = max(1, int(depth))
    seen = {start: 0}
    q = deque([(start, 0)])
    while q:
        cur, d = q.popleft()
        if d >= depth:
            continue
        nbrs = set()
        if direction in ("outbound", "both"):
            nbrs |= out.get(cur, set())
        if direction in ("inbound", "both"):
            nbrs |= inb.get(cur, set())
        for nb in nbrs:
            if nb not in seen:
                seen[nb] = d + 1
                q.append((nb, d + 1))
    results = sorted(((d, r) for r, d in seen.items() if r != start), key=lambda x: (x[0], x[1]))
    return {
        "note": start,
        "direction": direction,
        "depth": depth,
        "ambiguous": starts[1:] if len(starts) > 1 else [],
        "neighbours": [{"path": r, "distance": d} for d, r in results[:100]],
    }


def find_broken_links_core():
    index = _build_index()
    note_keys = set(index["by_key"].keys())
    file_keys = index["file_keys"]
    broken = []
    for note in index["notes"]:
        for raw in note["links"]:
            base, full = _norm_key(raw)
            if base is None:
                continue
            if full in note_keys or base in note_keys:
                continue
            tl = raw.split("|")[0].split("#")[0].strip().lower()
            if tl in file_keys or tl.split("/")[-1] in file_keys:
                continue
            broken.append({"source": note["rel"], "target": raw.split("|")[0].strip()})
    return {"count": len(broken), "broken_links": broken[:200]}


def find_orphans_core():
    index = _build_index()
    _out, inb = _adjacency(index)
    orphans, exempt = [], 0
    for note in index["notes"]:
        rel = note["rel"]
        if inb.get(rel):
            continue
        base = rel[:-3].split("/")[-1].lower()
        if base in _ORPHAN_EXEMPT_NAMES or any(rel.startswith(d + "/") for d in _ORPHAN_EXEMPT_DIRS):
            exempt += 1
            continue
        orphans.append({"path": rel, "title": note["title"]})
    return {"count": len(orphans), "exempt": exempt, "orphans": sorted(orphans, key=lambda o: o["path"])}


def resolve_note_core(name):
    index = _build_index()
    matches = _resolve_to_rel(name, index)
    return {"name": name, "matches": matches, "ambiguous": len(matches) > 1, "found": bool(matches)}


def vault_tree_core(path=".", depth=2):
    patterns = _load_ignore()
    base = (VAULT / path).resolve()
    depth = max(1, int(depth))
    try:
        base.relative_to(VAULT)
    except ValueError:
        return {"error": "path escapes the vault"}
    lines = []
    root = str(base)
    for dirpath, dirnames, filenames in os.walk(root):
        rel_from_vault = os.path.relpath(dirpath, str(VAULT))
        rel_from_vault = "" if rel_from_vault == "." else rel_from_vault
        dirnames[:] = sorted(
            d for d in dirnames
            if not _ignored((rel_from_vault + "/" + d) if rel_from_vault else d, patterns)
        )
        rel_from_base = os.path.relpath(dirpath, root)
        level = 0 if rel_from_base == "." else rel_from_base.count(os.sep) + 1
        if level > depth:
            dirnames[:] = []
            continue
        md = sum(1 for f in filenames if f.endswith(".md"))
        name = os.path.basename(dirpath) if rel_from_base != "." else (path.strip("/") or ".")
        lines.append("%s%s/  (%d md)" % ("  " * level, name, md))
    return {"root": path, "depth": depth, "tree": lines[:300]}


def list_by_status_core(status=None):
    index = _build_index()
    if status is not None:
        s = str(status).strip().lower()
        if s not in STATUS_VOCAB:
            return {"error": "Unknown status %r. Valid: %s" % (status, ", ".join(STATUS_VOCAB))}
        hits = [{"path": n["rel"], "title": n["title"]}
                for n in index["notes"] if n["frontmatter"].get("status", "").lower() == s]
        return {"status": s, "count": len(hits), "notes": hits}
    grouped = {}
    for n in index["notes"]:
        st = n["frontmatter"].get("status", "").lower()
        if st:
            grouped.setdefault(st, []).append(n["rel"])
    return {"vocabulary": STATUS_VOCAB, "by_status": {k: sorted(v) for k, v in sorted(grouped.items())}}


# --------------------------------------------------------------------------- #
# Core logic — vault_health (deterministic maintenance report; fix=True also
# applies the safe subset: unambiguous link/map repoints and mechanical lint)
# --------------------------------------------------------------------------- #
_PATH_REF = re.compile(r"(?:`|\[\[)([^`\[\]|\n]+\.md)(?:`|\]\]|\|)")


def _extract_md_paths(text):
    """Explicit .md path references in backticks or [[wikilinks]] — real paths
    only, so placeholders (<name>, {var}, globs) are skipped."""
    out = set()
    for m in _PATH_REF.finditer(text):
        p = m.group(1).strip()
        if "/" in p and not any(ch in p for ch in "<>{}*"):
            out.add(p)
    return out


def _dir_names(max_depth=3):
    """Set of directory names in the vault up to max_depth. Ignored dirs are
    recorded (they exist on disk) but not descended into."""
    patterns = _load_ignore()
    names = set()
    root = str(VAULT)
    for dirpath, dirnames, _files in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        rel = "" if rel == "." else rel.replace(os.sep, "/")
        depth = 0 if not rel else rel.count("/") + 1
        visible = [d for d in dirnames if not d.startswith(".")]
        names.update(visible)
        dirnames[:] = [
            d for d in visible
            if not _ignored((rel + "/" + d) if rel else d, patterns)
        ]
        if depth >= max_depth:
            dirnames[:] = []
    return names


def _check_maps():
    """Verify map files and entry points: listed paths exist on disk, real
    skills/agents/systems are listed, vault_map's diagram matches the tree."""
    missing_paths = []   # listed in a map/entry point but not on disk
    unlisted = []        # exists on disk but missing from its map

    def listed_paths_exist(rel):
        p = VAULT / rel
        if not p.exists():
            return ""
        text = p.read_text(encoding="utf-8")
        for ref in sorted(_extract_md_paths(text)):
            if not (VAULT / ref).exists():
                missing_paths.append({"map": rel, "path": ref})
        return text

    skill_text = listed_paths_exist("Context/Maps/skill_map.md")
    agent_text = listed_paths_exist("Context/Maps/agent_map.md")
    systems_text = listed_paths_exist("Context/Maps/systems_map.md")
    listed_paths_exist("main.md")
    listed_paths_exist("CLAUDE.md")

    for pat, text, map_rel in (
        ("Context/Skills/*/SKILL.md", skill_text, "skill_map.md"),
        (".claude/skills/*/SKILL.md", skill_text, "skill_map.md"),
        ("Context/Agents/*/AGENT.md", agent_text, "agent_map.md"),
        ("Context/Systems/*.md", systems_text, "systems_map.md"),
    ):
        for p in sorted(VAULT.glob(pat)):
            rel = str(p.relative_to(VAULT))
            # HUMAN.md files are folder documentation, not registrable entries.
            if "/Archive/" in rel or p.name == "HUMAN.md":
                continue
            if text and rel not in text:
                unlisted.append({"map": map_rel, "path": rel})

    # vault_map structure diagram vs the real tree, both directions.
    vault_map_drift = []
    vm = VAULT / "Context/Maps/vault_map.md"
    if vm.exists():
        text = vm.read_text(encoding="utf-8")
        fence = re.search(r"```(.*?)```", text, re.S)
        on_disk = _dir_names()
        if fence:
            drawn = set(re.findall(r"([A-Za-z][\w.-]*)/", fence.group(1))) - {"YourVault"}
            for name in sorted(drawn - on_disk):
                vault_map_drift.append({"issue": "listed folder not on disk", "folder": name})
        top_level = {d.name for d in VAULT.iterdir()
                     if d.is_dir() and not d.name.startswith(".")
                     and not _ignored(d.name, _load_ignore())}
        for name in sorted(top_level):
            if name not in text:
                vault_map_drift.append({"issue": "top-level folder not in vault_map", "folder": name})

    return {"missing_paths": missing_paths, "unlisted": unlisted,
            "vault_map_drift": vault_map_drift}


# Folders whose notes follow a shared structured format — the cosmetic
# heading-spacing check applies only here, not to personal/free-form notes.
_STRUCTURED_DIRS = ("Context/Skills/", "Context/Systems/", "Context/Agents/",
                    "Context/Maps/", "Context/Guide/", "Start_Here/")


def _lint_notes():
    """Deterministic format checks with file+line. Detection only."""
    findings = []
    folder_h2s = {}
    patterns = _load_ignore()
    for abs_path, rel in _iter_files(patterns):
        if not rel.endswith(".md"):
            continue
        try:
            lines = Path(abs_path).read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        structured = rel.startswith(_STRUCTURED_DIRS) and "/Archive/" not in rel
        in_fence = False
        h2s = set()
        for i, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            # Inline code often holds syntax *examples* — never lint inside it.
            bare = _INLINE_CODE.sub(" ", line)
            if re.search(r"\[\[[^\[\]|]+\]\|", bare):
                findings.append({"file": rel, "line": i,
                                 "issue": "broken wikilink brackets ([[x]|y] -> [[x|y]])"})
            if re.match(r"^#{1,6}\s+#{1,6}(\s|$)", bare):
                findings.append({"file": rel, "line": i, "issue": "duplicate heading markers"})
            m = re.match(r"^(#{2,})\s", line)
            if m:
                if len(m.group(1)) == 2:
                    h2s.add(line.lstrip("#").strip())
                nxt = lines[i] if i < len(lines) else ""
                if structured and nxt.strip() and not nxt.startswith("#") and nxt.strip() != "---":
                    findings.append({"file": rel, "line": i,
                                     "issue": "missing blank line after heading"})
        folder = rel.rsplit("/", 1)[0] if "/" in rel else "."
        folder_h2s.setdefault(folder, []).append((rel, h2s))

    # Sibling check: in folders of 4+ notes, flag files missing an H2 that
    # 75%+ of their siblings have. History and Archive folders are exempt.
    sibling_flags = []
    for folder, files in folder_h2s.items():
        if len(files) < 4 or "Archive" in folder or folder.startswith("Context/History"):
            continue
        counts = Counter(h for _rel, hs in files for h in hs)
        common = [h for h, c in counts.items() if c >= max(3, math.ceil(0.75 * len(files)))]
        for rel, hs in files:
            missing = sorted(h for h in common if h not in hs)
            if missing:
                sibling_flags.append({"file": rel, "missing_headers": missing})

    return {"findings": findings[:100], "sibling_flags": sibling_flags[:50]}


def _archive_candidates():
    """History notes no longer referenced (by filename or date) in the Open
    section of open-work.md — candidates to move to Archive/, never auto-moved."""
    open_text = ""
    p = VAULT / "Context/History/open-work.md"
    if p.exists():
        md = p.read_text(encoding="utf-8")
        m = re.search(r"(?ms)^##\s+Open\s*\n(.+?)(?=^##\s+Done|\Z)", md)
        open_text = (m.group(1) if m else md).lower()
    latest = _latest_session_file()
    cands = []
    for f in sorted((VAULT / "Context/History").glob("*.md")):
        if f.name in ("open-work.md", "log.md") or (latest and f == latest):
            continue
        dm = re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
        date = dm.group(1) if dm else ""
        if f.name.lower() not in open_text and not (date and date in open_text):
            cands.append("Context/History/" + f.name)
    return {"count": len(cands), "candidates": cands}


def _health_report():
    broken = find_broken_links_core()
    orphans = find_orphans_core()
    maps = _check_maps()
    lint = _lint_notes()
    archive = _archive_candidates()
    counts = {
        "broken_links": broken["count"],
        "orphans": orphans["count"],
        "map_issues": len(maps["missing_paths"]) + len(maps["unlisted"]) + len(maps["vault_map_drift"]),
        "lint_findings": len(lint["findings"]) + len(lint["sibling_flags"]),
        "archive_candidates": archive["count"],
    }
    return {
        "clean": not any(counts.values()),
        "counts": counts,
        "broken_links": broken["broken_links"],
        "orphans": orphans["orphans"],
        "map_check": maps,
        "lint": lint,
        "archive_candidates": archive["candidates"],
    }


_FOLDER_NAMED = ("agent", "skill", "index", "readme")


def _display_target(rel):
    """Canonical wikilink text for a note path: the full path for folder-named
    files (Obsidian resolves by basename, so AGENT/SKILL need the path),
    otherwise the file stem (real case)."""
    stem = rel.rsplit("/", 1)[-1]
    if stem.lower().endswith(".md"):
        stem = stem[:-3]
    if stem.lower() in _FOLDER_NAMED and "/" in rel:
        return rel
    return stem


def _fix_broken_links(broken):
    """Repoint broken wikilinks whose target squash-matches exactly one note
    (case/punctuation drift, or a folder-named file whose folder moved).
    Anything else is skipped."""
    index = _build_index()

    def squash(s):
        return re.sub(r"[^a-z0-9]", "", s.lower())

    smap = {}
    for key, rels in index["by_key"].items():
        smap.setdefault(squash(key), set()).update(rels)
    fixed, skipped = [], []
    for b in broken:
        base, _full = _norm_key(b["target"])
        # AGENT/SKILL-style targets: the folder is the identity, not the
        # basename — and the basename disambiguates (wrap-up the skill vs
        # wrap-up the archived agent).
        want_base = None
        if base in _FOLDER_NAMED and "/" in b["target"]:
            want_base = base + ".md"
            base = b["target"].split("/")[-2]
        rels = smap.get(squash(base or ""), set())
        if want_base:
            rels = {r for r in rels if r.rsplit("/", 1)[-1].lower() == want_base}
        if len(rels) != 1:
            skipped.append({"kind": "broken_link", "file": b["source"],
                            "target": b["target"],
                            "reason": "%d candidate notes" % len(rels)})
            continue
        new = _display_target(next(iter(rels)))
        src = VAULT / b["source"]
        try:
            text = src.read_text(encoding="utf-8")
        except OSError:
            continue
        pat = re.compile(r"\[\[\s*" + re.escape(b["target"]) + r"\s*(?=[#|\]])")
        new_text = pat.sub("[[" + new, text)
        if new_text != text:
            src.write_text(new_text, encoding="utf-8")
            fixed.append({"kind": "broken_link", "file": b["source"],
                          "old": b["target"], "new": new})
    return fixed, skipped


def _fix_map_paths(missing):
    """Repoint map rows whose listed .md path no longer exists. Candidates are
    on-disk files with the same basename that the map does not already list —
    for folder-named files (SKILL.md/AGENT.md) that is the renamed folder, for
    plain notes a move that kept the filename. Only a unique candidate is
    applied; anything else is skipped for the caller."""
    all_rels = [rel for _a, rel in _iter_files(_load_ignore())]
    fixed, skipped = [], []
    for item in missing:
        ref = item["path"]
        base = ref.rsplit("/", 1)[-1]
        map_file = VAULT / item["map"]
        try:
            text = map_file.read_text(encoding="utf-8")
        except OSError:
            continue
        cands = [r for r in all_rels
                 if r.rsplit("/", 1)[-1] == base and r != ref and r not in text
                 and "/Archive/" not in r]
        if len(cands) != 1:
            skipped.append({"kind": "map_path", "file": item["map"], "path": ref,
                            "reason": "%d on-disk candidates" % len(cands)})
            continue
        if ref in text:
            map_file.write_text(text.replace(ref, cands[0]), encoding="utf-8")
            fixed.append({"kind": "map_path", "file": item["map"],
                          "old": ref, "new": cands[0]})
    return fixed, skipped


def _fix_lint(findings):
    """Apply the three mechanical lint fixes in place, bottom-up per file so
    reported line numbers stay valid while editing."""
    fixed, skipped = [], []
    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)
    for rel, items in by_file.items():
        p = VAULT / rel
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        changed = False
        for f in sorted(items, key=lambda x: -x["line"]):
            i = f["line"] - 1
            issue = f["issue"]
            if i >= len(lines):
                continue
            if issue.startswith("missing blank line"):
                lines.insert(i + 1, "")
            elif issue.startswith("broken wikilink brackets"):
                new = re.sub(r"\[\[([^\[\]|]+)\]\|([^\[\]]+)\]\]?", r"[[\1|\2]]", lines[i])
                if new == lines[i]:
                    continue
                lines[i] = new
            elif issue.startswith("duplicate heading markers"):
                new = re.sub(r"^(#{1,6})\s+#{1,6}\s*", r"\1 ", lines[i])
                if new == lines[i]:
                    continue
                lines[i] = new
            else:
                skipped.append({"kind": "lint", "file": rel, "line": f["line"],
                                "issue": issue, "reason": "no mechanical fix"})
                continue
            changed = True
            fixed.append({"kind": "lint", "file": rel, "line": f["line"], "issue": issue})
        if changed:
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fixed, skipped


def vault_health_core(fix=False):
    report = _health_report()
    if not fix:
        return report
    fixed, skipped = [], []
    for f, s in (_fix_broken_links(report["broken_links"]),
                 _fix_map_paths(report["map_check"]["missing_paths"]),
                 _fix_lint(report["lint"]["findings"])):
        fixed += f
        skipped += s
    report = _health_report()  # fresh pass: the report now shows only what remains
    report["fixes_applied"] = fixed
    report["fix_skipped"] = skipped
    return report


# --------------------------------------------------------------------------- #
# Core logic — wrap_session (session-close mechanics: handoff file, open-work
# reconciliation, history archiving; the caller composes all prose)
# --------------------------------------------------------------------------- #
_ITEM_SPLIT = re.compile(r"(?m)^(?=### )")
_PRIORITY_TAG = re.compile(r"\s*\[(?:NOW|NEXT|BLOCKED[^\]]*)\]")


def wrap_session_core(session_date, session_slug, handoff,
                      open_work_changes=None, current_focus=None, archive=None):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(session_date)):
        return {"error": "session_date must be YYYY-MM-DD"}
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", str(session_slug)):
        return {"error": "session_slug must be kebab-case (lowercase, hyphens)"}
    errors, applied, archived = [], [], []

    hist = VAULT / "Context" / "History"
    hpath = hist / ("%s-%s.md" % (session_date, session_slug))
    overwrote = hpath.exists()
    hpath.write_text(str(handoff).rstrip() + "\n", encoding="utf-8")

    ow = hist / "open-work.md"
    if (open_work_changes or current_focus) and not ow.exists():
        errors.append("open-work.md not found")
    elif open_work_changes or current_focus:
        text = ow.read_text(encoding="utf-8")
        m = re.search(r"(?ms)^## Open\s*\n(.*?)(^## Done\s*\n)", text)
        if not m:
            errors.append("open-work.md: '## Open' ... '## Done' sections not found")
        else:
            header = text[:m.start(1)]
            done_head, done_body = m.group(2), text[m.end(2):]
            chunks = [c for c in _ITEM_SPLIT.split(m.group(1)) if c.strip()]
            preamble = ""
            if chunks and not chunks[0].startswith("### "):
                preamble = chunks.pop(0)
            items = []
            for c in chunks:
                first, _, rest = c.partition("\n")
                items.append([first.rstrip(), rest.strip()])

            def find(key):
                kl = (key or "").lower()
                return [i for i, it in enumerate(items) if kl and kl in it[0].lower()]

            for ch in (open_work_changes or []):
                act = str(ch.get("action", "")).lower()
                if act == "add":
                    if not ch.get("title"):
                        errors.append("add: missing title")
                        continue
                    item = ["### " + ch["title"], str(ch.get("body", "")).strip()]
                    items.insert(0, item) if ch.get("position") == "top" else items.append(item)
                    applied.append("add: " + ch["title"])
                elif act in ("edit", "close", "remove"):
                    hits = find(ch.get("match"))
                    if len(hits) != 1:
                        errors.append("%s: match %r hit %d items" % (act, ch.get("match"), len(hits)))
                        continue
                    i = hits[0]
                    if act == "edit":
                        if ch.get("title"):
                            items[i][0] = "### " + ch["title"]
                        if ch.get("body") is not None:
                            items[i][1] = str(ch["body"]).strip()
                    elif act == "close":
                        heading, body = items.pop(i)
                        heading = _PRIORITY_TAG.sub("", heading).rstrip()
                        done_body = "%s\n%s\n\n%s" % (
                            heading, str(ch.get("summary") or body).strip(), done_body)
                    else:
                        items.pop(i)
                    applied.append("%s: %s" % (act, ch.get("match")))
                else:
                    errors.append("unknown action %r" % ch.get("action"))

            if current_focus:
                new_header = re.sub(r"(?m)^Current focus:.*$",
                                    "Current focus: " + str(current_focus).strip(),
                                    header, count=1)
                if new_header == header:
                    errors.append("'Current focus:' line not found in open-work.md header")
                header = new_header

            open_body = "".join("%s\n\n%s" % (h, b + "\n\n" if b else "") for h, b in items)
            if preamble.strip():
                open_body = preamble.rstrip() + "\n\n" + open_body
            ow.write_text(header + open_body + done_head + done_body, encoding="utf-8")

    for rel in (archive or []):
        rel = str(rel).strip()
        name = rel.rsplit("/", 1)[-1]
        if (not rel.startswith("Context/History/") or "/Archive/" in rel
                or name in ("open-work.md", "log.md")):
            errors.append("archive: refusing %r" % rel)
            continue
        src = VAULT / rel
        if not src.exists():
            errors.append("archive: not found %r" % rel)
            continue
        dst = VAULT / "Context" / "History" / "Archive"
        dst.mkdir(parents=True, exist_ok=True)
        src.rename(dst / name)
        archived.append(rel)

    return {"handoff": str(hpath.relative_to(VAULT)), "overwrote": overwrote,
            "open_work_applied": applied, "archived": archived, "errors": errors}


# --------------------------------------------------------------------------- #
# Tool registry (name, description, JSON schema, handler, annotations)
# --------------------------------------------------------------------------- #
_RO = {"readOnlyHint": True, "openWorldHint": False}


def _tool_specs():
    return [
        {"name": "find_skill",
         "description": "Find the vault skill(s) best suited to a task. Ranked matches "
                        "(name, path, description, score). Use instead of reading skill_map.md.",
         "inputSchema": {"type": "object", "properties": {
             "query": {"type": "string", "description": "What you want to do."},
             "limit": {"type": "integer", "description": "Max matches (default 3).", "default": 3}},
             "required": ["query"]},
         "annotations": _RO, "handler": find_skill_core},

        {"name": "resolve_agent",
         "description": "Find the sub-agent(s) best suited to a task. Ranked matches "
                        "(name, path, purpose, score). Use instead of reading agent_map.md.",
         "inputSchema": {"type": "object", "properties": {
             "task": {"type": "string", "description": "The task to delegate."},
             "limit": {"type": "integer", "description": "Max matches (default 3).", "default": 3}},
             "required": ["task"]},
         "annotations": _RO, "handler": resolve_agent_core},

        {"name": "get_open_work",
         "description": "Return current open work items (the Open section of open-work.md). "
                        "Use instead of reading the whole file.",
         "inputSchema": {"type": "object", "properties": {}, "required": []},
         "annotations": _RO, "handler": lambda: get_open_work_core()},

        {"name": "get_session_brief",
         "description": "One-call startup bundle: latest session (date + topic), open "
                        "work, working-style preferences, and skill/agent capability lists. "
                        "Use at session start instead of reading history, open-work, memory, "
                        "and the maps separately.",
         "inputSchema": {"type": "object", "properties": {}, "required": []},
         "annotations": _RO, "handler": lambda: get_session_brief_core()},

        {"name": "search_notes",
         "description": "Full-text search over note bodies (BM25). Returns ranked path + title "
                        "+ matching snippet, not whole files. Optional `scope` limits to a "
                        "folder prefix (e.g. 'Context' or 'Projects').",
         "inputSchema": {"type": "object", "properties": {
             "query": {"type": "string", "description": "Words to search for."},
             "limit": {"type": "integer", "description": "Max matches (default 5).", "default": 5},
             "scope": {"type": "string", "description": "Optional folder prefix to restrict the search."}},
             "required": ["query"]},
         "annotations": _RO, "handler": search_notes_core},

        {"name": "get_links",
         "description": "Walk the wikilink graph from a note (BFS). direction = "
                        "outbound | inbound | both; depth limits hops. Returns neighbours with "
                        "their link distance. Use for 'what links here' and related notes.",
         "inputSchema": {"type": "object", "properties": {
             "note": {"type": "string", "description": "Note name or [[wikilink]] to start from."},
             "direction": {"type": "string", "enum": ["outbound", "inbound", "both"],
                           "description": "Link direction (default both).", "default": "both"},
             "depth": {"type": "integer", "description": "Max hops (default 1).", "default": 1}},
             "required": ["note"]},
         "annotations": _RO, "handler": get_links_core},

        {"name": "find_broken_links",
         "description": "List [[wikilinks]] that resolve to no existing note or file. "
                        "Returns {source, target} pairs. Honors .vaultignore.",
         "inputSchema": {"type": "object", "properties": {}, "required": []},
         "annotations": _RO, "handler": lambda: find_broken_links_core()},

        {"name": "find_orphans",
         "description": "List notes with no inbound links (excluding natural entry points like "
                        "main.md, maps, history, and memory). Candidates that may need linking.",
         "inputSchema": {"type": "object", "properties": {}, "required": []},
         "annotations": _RO, "handler": lambda: find_orphans_core()},

        {"name": "resolve_note",
         "description": "Resolve a [[wikilink]] or bare note name to its real vault path(s). "
                        "Flags ambiguity when more than one note matches.",
         "inputSchema": {"type": "object", "properties": {
             "name": {"type": "string", "description": "Note name or [[wikilink]]."}},
             "required": ["name"]},
         "annotations": _RO, "handler": resolve_note_core},

        {"name": "vault_tree",
         "description": "Compact folder/file layout under a path (md-file counts per folder), "
                        "honoring .vaultignore. Use instead of repeated directory listings.",
         "inputSchema": {"type": "object", "properties": {
             "path": {"type": "string", "description": "Folder to start from (default vault root).", "default": "."},
             "depth": {"type": "integer", "description": "Max folder depth (default 2).", "default": 2}},
             "required": []},
         "annotations": _RO, "handler": vault_tree_core},

        {"name": "list_by_status",
         "description": "List notes by their `status` frontmatter field. With no argument, "
                        "groups all set statuses. Valid values: " + ", ".join(STATUS_VOCAB) + ".",
         "inputSchema": {"type": "object", "properties": {
             "status": {"type": "string", "enum": STATUS_VOCAB,
                        "description": "Status to filter by; omit to group all."}},
             "required": []},
         "annotations": _RO, "handler": list_by_status_core},

        {"name": "vault_health",
         "description": "One-call maintenance report: broken links, orphans, map/entry-point "
                        "verification, format lint (with file+line), and archive-candidate "
                        "history notes. With fix=true it also applies the deterministic safe "
                        "fixes (unambiguous link and map-path repoints, mechanical lint) and "
                        "reports what it fixed, skipped, and what remains for the caller. "
                        "Use for vault maintenance instead of scanning files.",
         "inputSchema": {"type": "object", "properties": {
             "fix": {"type": "boolean", "default": False,
                     "description": "Apply the safe fixes, not just report them."}},
             "required": []},
         "annotations": {"readOnlyHint": False, "openWorldHint": False},
         "handler": vault_health_core},

        {"name": "wrap_session",
         "description": "Session-close mechanics in one call: writes the handoff note to "
                        "Context/History/<date>-<slug>.md verbatim, applies structured "
                        "open-work.md changes (add/edit/close/remove items, update the "
                        "'Current focus:' line), and moves named history notes to Archive/. "
                        "The caller composes all prose; this tool only applies it.",
         "inputSchema": {"type": "object", "properties": {
             "session_date": {"type": "string", "description": "YYYY-MM-DD."},
             "session_slug": {"type": "string",
                              "description": "Kebab-case label for the handoff filename."},
             "handoff": {"type": "string",
                         "description": "Full markdown content of the handoff note, "
                                        "written verbatim (include the H1)."},
             "open_work_changes": {"type": "array", "items": {"type": "object", "properties": {
                 "action": {"type": "string", "enum": ["add", "edit", "close", "remove"]},
                 "match": {"type": "string",
                           "description": "Heading substring (edit/close/remove); must hit "
                                          "exactly one Open item."},
                 "title": {"type": "string",
                           "description": "Heading text without '### ', including the "
                                          "[NOW]/[NEXT]/[BLOCKED] tag (add, or retitle on edit)."},
                 "body": {"type": "string", "description": "Item body markdown (add/edit)."},
                 "summary": {"type": "string",
                             "description": "Done-entry body when closing (defaults to the "
                                            "item's current body)."},
                 "position": {"type": "string", "enum": ["top", "bottom"],
                              "description": "Where to insert an added item (default bottom)."}},
                 "required": ["action"]},
                 "description": "Changes to the Open section of open-work.md."},
             "current_focus": {"type": "string",
                               "description": "Replacement text for the 'Current focus:' "
                                              "line (label added automatically)."},
             "archive": {"type": "array", "items": {"type": "string"},
                         "description": "Vault-relative Context/History/ notes to move "
                                        "to Archive/."}},
             "required": ["session_date", "session_slug", "handoff"]},
         "annotations": {"readOnlyHint": False, "openWorldHint": False},
         "handler": wrap_session_core},
    ]


# --------------------------------------------------------------------------- #
# Minimal MCP stdio server (JSON-RPC 2.0 over newline-delimited stdin/stdout)
# --------------------------------------------------------------------------- #
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "vault", "version": "2.1.0"}

# --------------------------------------------------------------------------- #
# Rule injection: give clients that don't load CLAUDE.md themselves (Claude
# Desktop) the same rule text Claude Code and Claudian already get. Gated behind
# VAULT_MCP_INJECT_RULES=1 so Code/Claudian, which load CLAUDE.md natively, don't
# receive the rules twice. Set the flag only in the Desktop client config.
# --------------------------------------------------------------------------- #
_IMPORT_RE = re.compile(r"^\s*@(\S+)\s*$")


def _expand_imports(path, seen, depth=0):
    """Inline @imports exactly as Claude Code expands CLAUDE.md, so Desktop gets
    byte-for-byte the same rule chain Code sees. Cycle- and depth-guarded; a
    missing or unreadable file resolves to empty rather than raising."""
    path = Path(path).resolve()
    if depth > 10 or str(path) in seen:
        return ""
    seen.add(str(path))
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    lines = []
    for line in text.splitlines():
        m = _IMPORT_RE.match(line)
        if not m:
            lines.append(line)
            continue
        target = m.group(1)
        for cand in ((VAULT / target), (path.parent / target)):
            if cand.exists():
                lines.append(_expand_imports(cand, seen, depth + 1))
                break
    return "\n".join(lines)


def _load_instructions():
    """Full expanded CLAUDE.md chain, or None when the flag is off / file gone."""
    if os.environ.get("VAULT_MCP_INJECT_RULES") != "1":
        return None
    entry = VAULT / "CLAUDE.md"
    if not entry.exists():
        return None
    text = _expand_imports(entry, set()).strip()
    return text or None


def _send(obj):
    try:
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()
    except BrokenPipeError:
        raise SystemExit(0)


def _serve_stdio():
    specs = _tool_specs()
    handlers = {t["name"]: t["handler"] for t in specs}
    public_tools = [{k: t[k] for k in ("name", "description", "inputSchema", "annotations")} for t in specs]

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue

        mid = msg.get("id")
        method = msg.get("method")
        params = msg.get("params") or {}

        if mid is None:
            continue

        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
                "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO}
            instr = _load_instructions()
            if instr:
                result["instructions"] = instr
            _send({"jsonrpc": "2.0", "id": mid, "result": result})
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": mid, "result": {"tools": public_tools}})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            fn = handlers.get(name)
            if fn is None:
                _send({"jsonrpc": "2.0", "id": mid,
                       "error": {"code": -32602, "message": "Unknown tool: %s" % name}})
                continue
            try:
                result = fn(**args)
                _send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                    "structuredContent": result, "isError": False}})
            except Exception as exc:  # noqa: BLE001 — report any tool error to the client
                _send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": "Error: %s" % exc}], "isError": True}})
        elif method == "ping":
            _send({"jsonrpc": "2.0", "id": mid, "result": {}})
        else:
            _send({"jsonrpc": "2.0", "id": mid,
                   "error": {"code": -32601, "message": "Method not found: %s" % method}})


if __name__ == "__main__":
    try:
        _serve_stdio()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
