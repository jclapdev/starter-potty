#!/usr/bin/env python3
"""
PostToolUse hook — runs after Write/Edit on .md files in the vault.

Two kinds of check:
  1. Language tells (BLOCKING) — em-dashes, banned words, negative parallelism,
     clickbait teasers / curiosity gaps.
     Exits 2 so the write is handed back for a fix instead of standing.
  2. Broken outgoing wikilinks (ADVISORY) — printed, exits 0 on their own.

If any blocking issue is found the hook exits 2; otherwise 0.

Language checks run on prose only: fenced code blocks, inline code, and
blockquote lines are stripped first, so example tells inside code or quoted
source don't trip it. Files that document the tells by example are skipped
entirely (see LANG_SKIP).

Vault root is inferred from this script's location:
  <vault-root>/AI-Workshop/hooks/vault-verify.py
"""

import json
import os
import re
import sys
from pathlib import Path

# Infer vault root from script location
VAULT_ROOT = Path(__file__).resolve().parent.parent.parent

# Files that document the AI-tell rules by example — skip language checks on them
# (they legitimately contain tells and em-dashes as illustrations).
LANG_SKIP = {
    "main.md",
    "Context/Systems/ai-language-tells.md",
    "Context/Systems/base-rules.md",
    "Context/Agents/prose-review/AGENT.md",
}

# Directories to skip when building the wikilink index
INDEX_SKIP_DIRS = {
    ".git", ".obsidian", "__pycache__", "node_modules", "venv", ".venv",
}
# Subtree prefixes to skip (relative to vault root)
INDEX_SKIP_PREFIXES = (
    "AI-Workshop/Projects/Starter",
    "AI-Workshop/Projects/Starter.zip",
)

AI_TELLS = [
    # Vocabulary swaps (section 1)
    "delve", "underscore", "pivotal", "crucial", "vital",
    "realm", "landscape", "sphere", "harness", "leverage", "utilize",
    "facilitate", "illuminate", "foster", "cultivate",
    "streamline", "bolster", "embark", "unlock", "unleash", "unveil",
    "elevate", "robust", "seamless", "holistic", "multifaceted",
    "myriad", "plethora", "tapestry", "mosaic",
    # Hype (section 2)
    "revolutionize", "transformative", "groundbreaking", "cutting-edge",
    "game-changing", "state-of-the-art", "unparalleled", "supercharge",
    "turbocharge", "synergy",
    # Filler (section 3)
    "it's worth noting", "it is important to note", "needless to say",
    "at its core", "at the end of the day", "in today's",
    "in conclusion", "in summary",
    # Sycophancy (section 8)
    "great question", "certainly!", "absolutely!", "i'd be happy to",
    "i hope this helps", "feel free to",
    # Verdicts on the user — never tell the user they're right or wrong (memory: no-verdict)
    "you're right", "you are right", "youre right", "you're absolutely right",
    "you're correct", "you are correct", "good point", "great point",
    "fair point", "exactly right", "spot on", "well said",
    # Banned outright
    "vibe", "fluff",
]

# Structural tells with a stable textual signature (section 5).
STRUCTURAL = [
    (re.compile(r"not only\b.{1,60}?\bbut\b", re.IGNORECASE), "negative parallelism (\"not only X but Y\")"),
    (re.compile(r"not just\b.{1,50}?,\s*(it'?s|it is|its|they'?re|they are)\b", re.IGNORECASE), "negative parallelism (\"not just X, it's Y\")"),
    # Clickbait teasers / curiosity gaps (section 6) — dangling a payoff
    # instead of stating it. State the fact plainly instead.
    (re.compile(r"\bthe (one|single) (rule|trick|thing|things|secret|tip|change|mistake|fix|step|move|reason|part|piece|bit|catch|problem|issue|question|exception|point|lesson|takeaway|caveat|gotcha|kicker)\b", re.IGNORECASE),
     "clickbait teaser (\"the one/single X…\") — state the point plainly"),
    (re.compile(r"\b(rule|mistake|trick|secret|thing|part|tip)\b.{0,30}?\b(almost\s+)?(everyone|nobody|no one)\b.{0,20}?\b(miss(es)?|make(s)?|know(s)?|forget(s)?|tell(s)?)\b", re.IGNORECASE),
     "clickbait teaser (\"the X (almost) everyone misses/makes\") — state it plainly"),
    (re.compile(r"\bwhat (nobody|no one|most people) (ever )?tells? you\b", re.IGNORECASE),
     "clickbait teaser (\"what nobody tells you\") — state it plainly"),
    (re.compile(r"\bhere'?s (the|what) (part|secret|trick|thing)\b.{0,30}?\b(nobody|no one|most people)\b", re.IGNORECASE),
     "clickbait teaser (\"here's the part nobody…\") — state it plainly"),
    (re.compile(r"\band (that|this) changes everything\b", re.IGNORECASE),
     "clickbait teaser (\"and that changes everything\") — state it plainly"),
]

EM_DASH = "—"  # —


def build_note_index():
    """Return a set of lowercase note names (without .md) in the vault."""
    names = set()
    for root, dirs, files in os.walk(VAULT_ROOT):
        rel_root = os.path.relpath(root, VAULT_ROOT)
        # Skip hidden and system dirs
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in INDEX_SKIP_DIRS
        ]
        # Skip Starter subtree
        if any(rel_root == p or rel_root.startswith(p + os.sep)
               for p in INDEX_SKIP_PREFIXES):
            dirs.clear()
            continue
        for fname in files:
            if fname.endswith(".md"):
                names.add(fname[:-3].lower())
    return names


def check_broken_links(content, note_index):
    """Return wikilink targets in content that don't resolve to any note."""
    links = re.findall(r'\[\[([^\]|#\n]+?)(?:[|#][^\]]*?)?\]\]', content)
    return [lnk.strip() for lnk in links if lnk.strip().lower() not in note_index]


def prose_lines(content):
    """
    Yield prose text lines eligible for language checks.

    Fenced code blocks and blockquote lines are skipped, and inline code is
    removed, so tells inside code or quoted source are not flagged.
    """
    in_fence = False
    for raw in content.splitlines():
        stripped = raw.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith(">"):  # blockquote — often quoted source
            continue
        # Drop inline code spans
        yield re.sub(r"`[^`]*`", "", raw)


def excerpt(text):
    """A trimmed, locatable snippet of a flagged line."""
    t = text.strip()
    return t if len(t) <= 70 else t[:67] + "..."


def check_language(content):
    """Return a list of (label, excerpt) blocking language issues in the given text."""
    issues = []
    for text in prose_lines(content):
        low = text.lower()
        if EM_DASH in text:
            issues.append(("em-dash (use comma, period, or parentheses)", excerpt(text)))
        for tell in AI_TELLS:
            if tell in low:
                issues.append((f"ai tell '{tell}'", excerpt(text)))
        for pat, label in STRUCTURAL:
            if pat.search(text):
                issues.append((label, excerpt(text)))
    return issues


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path.endswith(".md"):
        sys.exit(0)

    abs_path = Path(file_path).resolve()

    # Only scan files within this vault
    try:
        rel_path = abs_path.relative_to(VAULT_ROOT)
    except ValueError:
        sys.exit(0)

    if not abs_path.exists():
        sys.exit(0)

    content = abs_path.read_text(encoding="utf-8", errors="replace")

    # Language check runs on the text this call actually introduced, not the
    # whole file — so touching a legacy file doesn't block on old tells in lines
    # you never edited. Write = the full new file; Edit = the replacement text.
    if tool_name == "Edit":
        changed = tool_input.get("new_string", "")
    else:
        changed = tool_input.get("content", content)

    advisory = []   # broken links — reported, never blocks
    blocking = []   # language tells in introduced text — forces a fix

    # 1. Broken-link scan of the whole file (advisory)
    note_index = build_note_index()
    for link in check_broken_links(content, note_index):
        advisory.append(f"  broken link  [[{link}]]")

    # 2. Language scan of the changed text (blocking) — skip files that document the tells
    if str(rel_path) not in LANG_SKIP:
        for label, snippet in check_language(changed):
            blocking.append(f"  {label}\n      in: {snippet}")

    if advisory or blocking:
        print(f"\nvault-verify: {rel_path}", file=sys.stderr)
        for issue in blocking:
            print(issue, file=sys.stderr)
        for issue in advisory:
            print(issue, file=sys.stderr)
        if blocking:
            print(
                "\n  ^ language tells in the text you just wrote must be fixed. "
                "Rewrite them in plain words (see Context/Systems/ai-language-tells.md), "
                "then save again.",
                file=sys.stderr,
            )
        print("", file=sys.stderr)

    sys.exit(2 if blocking else 0)


if __name__ == "__main__":
    main()
