#!/usr/bin/env python3
"""install.py — set up this vault's AI system on the machine you run it on.

    python AI-Workshop/install.py

Run it once. When it prints "All checks passed", restart Claude and the system
is live. Safe to run again anytime: it checks first and only changes what needs
changing, so install, update, and repair are the same command. On a machine
that already works, a re-run changes nothing and says so.

    python AI-Workshop/install.py --check

only inspects and prints PASS/FAIL; it never changes anything. Use it to answer
"is this machine set up right?" without touching the machine.

What it does, all in this one file:
  - Checks this vault has the current system files before touching anything,
    and stops with plain update steps if they are missing or out of date.
  - Cleans up folders left over from older versions (kb-mcp, vault-mcp,
    installers), keeping any knowledge-base source files found there.
  - Registers the system's servers (vault, kb) in the two files the apps read:
    .mcp.json (Claude Code / Claudian) and the Claude Desktop config. It writes
    the ABSOLUTE path of the Python you ran it with, so no "python vs python3"
    guessing. Your own servers are left alone; system entries that point at
    files which no longer exist are removed.
  - Sets up the knowledge base (kb) if it isn't already working: builds its
    virtualenv and installs its libraries. Skip with --no-kb.
  - Points the vault-verify hook at this machine's Python, keeping any other
    hooks you added yourself.
  - Verifies the result (both servers actually launch) and prints PASS/FAIL.

Nothing machine-specific is committed; it is all generated here from your own
Python and paths. Pure standard library, so any machine that runs the system
runs this.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]        # AI-Workshop/install.py -> vault root
AIW = VAULT / "AI-Workshop"
VAULT_SERVER = AIW / "mcp-servers" / "vault" / "server.py"
KB_DIR = AIW / "mcp-servers" / "kb"
HOOK = AIW / "hooks" / "vault-verify.py"
CODE_MCP = VAULT / ".mcp.json"
CLAUDE_SETTINGS = VAULT / ".claude" / "settings.json"

# Pre-2026-07 layout, replaced by mcp-servers/. Safe to remove: their contents
# ship with the system, except kb sources, which get moved first.
LEGACY_DIRS = ("kb-mcp", "vault-mcp", "installers")
REQUIRED_FILES = (
    VAULT / "CLAUDE.md",
    VAULT_SERVER,
    KB_DIR / "server.py",
    KB_DIR / "requirements-core.txt",
    KB_DIR / "requirements.txt",
    HOOK,
)


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")


def suggested_home_spot() -> str:
    return "C:\\Users\\<you>\\ClaudeVault" if os.name == "nt" else "~/ClaudeVault"


def check_environment() -> bool:
    """Catch the two things that break installs before doing any work:
    an old Python, and a vault folder the Claude desktop app will reject.
    Returns False when setup must stop."""
    if sys.version_info < (3, 9):
        print("FAIL  Python %d.%d is too old; this system needs Python 3.9 or newer."
              % sys.version_info[:2])
        print("      Install a current Python from python.org, then run this again.")
        return False

    home = Path.home().resolve()
    path_str = str(VAULT)
    # Cloud-synced locations: the folder's real location is not in the home
    # folder, and the Claude desktop app refuses to open it.
    synced = "OneDrive" in path_str or "Mobile Documents" in path_str
    outside_home = not str(VAULT).startswith(str(home) + os.sep) and VAULT != home
    if synced or outside_home:
        why = ("it is inside a OneDrive/iCloud-synced folder" if synced
               else "its real location is outside your home folder")
        print("FAIL  This folder is at:  %s" % VAULT)
        print("      Claude's desktop app will refuse to open it because %s." % why)
        print("      (OneDrive and iCloud quietly move Desktop and Documents out of")
        print("      your home folder — that is the confusing part.)")
        print("\n      The fix, once:")
        print("        1. Move this whole folder to %s" % suggested_home_spot())
        print("        2. Open a terminal in the moved folder and run this script again.")
        return False

    try:
        top = VAULT.relative_to(home).parts[0]
    except ValueError:
        top = ""
    if top in ("Desktop", "Documents", "Downloads"):
        print("WARN  This folder sits in your %s folder. That often works, but Desktop," % top)
        print("      Documents, and Downloads are the folders OneDrive/iCloud relocate and")
        print("      the ones that trigger extra permission prompts. If you hit folder-access")
        print("      errors, move the vault to %s and run this again." % suggested_home_spot())
    return True


def preflight(fix: bool) -> tuple[bool, bool]:
    """Confirm the system files around this script are the current layout
    before anything is touched, and clean up leftovers from older versions.
    Returns (ok, changed). With fix=False nothing is ever changed."""
    print("\n== Checking this vault's files ==")
    missing = [p for p in REQUIRED_FILES if not p.exists()]
    if missing:
        print("  FAIL  this vault's system files are incomplete or from an older version:")
        for p in missing:
            print("          missing  %s" % p.relative_to(VAULT))
        print("\n      Nothing was changed. Get the current files first, then run this again:")
        if (VAULT / ".git").exists():
            print("        1. In this folder run:  git pull")
            print("        2. Run this script again.")
        else:
            print("        1. Download the latest Starter.")
            print("        2. In this vault, replace these folders with the new ones:")
            print("           Context/Skills, Context/Systems, Context/Agents, Context/Maps, AI-Workshop")
            print("           (leave Context/History, Context/Memory, main.md, and your notes alone)")
            print("        3. Run this script again.")
        return False, False

    legacy = [AIW / d for d in LEGACY_DIRS if (AIW / d).exists()]
    if not legacy:
        print("  PASS  files: current layout, nothing left over from older versions.")
        return True, False
    if not fix:
        print("  WARN  folders from an older version are still here (a normal run cleans them up):")
        for d in legacy:
            print("          - %s" % d.relative_to(VAULT))
        return True, False

    # Keep the user's knowledge-base source files, then drop the old folders.
    old_sources = AIW / "kb-mcp" / "sources"
    if old_sources.is_dir():
        new_sources = KB_DIR / "sources"
        new_sources.mkdir(parents=True, exist_ok=True)
        for item in sorted(old_sources.iterdir()):
            dest = new_sources / item.name
            if not dest.exists():
                shutil.move(str(item), str(dest))
                print("  kept your kb source: %s -> %s" % (item.name, new_sources.relative_to(VAULT)))
    for d in legacy:
        shutil.rmtree(d, ignore_errors=True)
        print("  removed old-version folder: %s" % d.relative_to(VAULT))
    return True, True


def desktop_config_path():
    """Claude Desktop config location for this OS (None if unknown)."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        base = os.environ.get("APPDATA")
        return Path(base) / "Claude" / "claude_desktop_config.json" if base else None
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def config_targets(include_desktop: bool) -> list:
    targets = [("Claude Code (.mcp.json)", CODE_MCP)]
    desktop = desktop_config_path()
    if include_desktop and desktop is not None:
        targets.append(("Claude Desktop (claude_desktop_config.json)", desktop))
    return targets


# --------------------------------------------------------------------------- #
# Knowledge base (kb)
# --------------------------------------------------------------------------- #
def _kb_core_ok(vpy: Path) -> bool:
    """True if the kb virtualenv can import its core libraries — the real test
    of whether kb will run, independent of any pip exit code."""
    if not vpy.exists():
        return False
    try:
        r = subprocess.run([str(vpy), "-c", "import lancedb, sentence_transformers, pypdf"],
                           capture_output=True, text=True, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return r.returncode == 0


def setup_kb() -> tuple[bool, bool]:
    """Build the kb virtualenv and install its libraries, unless it already
    works — a healthy kb is left completely alone. Returns (kb_ok, changed).
    A failure never stops the rest of the install."""
    print("\n== Setting up the knowledge base (kb) ==")
    venv = KB_DIR / ".venv"
    vpy = venv_python(venv)
    if _kb_core_ok(vpy):
        print("  already set up and working; leaving it alone.")
        return True, False
    core_req, full_req = KB_DIR / "requirements-core.txt", KB_DIR / "requirements.txt"
    try:
        if not vpy.exists():
            print("  creating virtualenv %s" % venv)
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(vpy), "-m", "pip", "install", "--upgrade", "pip"], check=False)
        print("  installing core libraries (first time downloads ~1 GB, can take a few minutes)")
        subprocess.run([str(vpy), "-m", "pip", "install", "-r", str(core_req)], check=True)
    except Exception as exc:  # noqa: BLE001
        print("  WARNING: the kb core didn't install (%s). Re-run to retry." % exc)
        return _kb_core_ok(vpy), True
    print("  installing optional file-type extractors (best effort)")
    if subprocess.run([str(vpy), "-m", "pip", "install", "-r", str(full_req)]).returncode != 0:
        print("  note: some optional extractors didn't install; kb still works for core types.")
    ok = _kb_core_ok(vpy)
    print("  knowledge base ready." if ok else "  WARNING: kb core still won't import; kb not registered.")
    return ok, True


# --------------------------------------------------------------------------- #
# Server registration
# --------------------------------------------------------------------------- #
def build_servers(kb_ok: bool) -> dict:
    """The system's own servers, with this machine's absolute paths."""
    servers = {
        "vault": {
            "command": sys.executable,
            "args": [str(VAULT_SERVER)],
            "env": {"VAULT_PATH": str(VAULT)},
        }
    }
    if kb_ok:
        servers["kb"] = {
            "command": str(venv_python(KB_DIR / ".venv")),
            "args": [str(KB_DIR / "server.py")],
        }
    return servers


def _load(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _write_json(path: Path, data: dict) -> bool:
    """Write JSON only when the content would actually change. Keeps a one-time
    .bak of the file as it was before this system first changed it."""
    text = json.dumps(data, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    if path.exists() and not Path(str(path) + ".bak").exists():
        shutil.copy(str(path), str(path) + ".bak")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _points_at_missing(entry: dict) -> bool:
    """True when a server entry references a path inside this vault's
    AI-Workshop folder (where every system server has ever lived) that no
    longer exists — such an entry cannot work, so removing it is safe.
    Paths anywhere else are never judged."""
    for part in [entry.get("command", "")] + list(entry.get("args", [])):
        try:
            p = Path(part)
        except (TypeError, ValueError):
            continue
        if p.is_absolute() and str(p).startswith(str(AIW) + os.sep) and not p.exists():
            return True
    return False


def _for_target(servers: dict, label: str) -> dict:
    """Claude Desktop doesn't load CLAUDE.md, so its `vault` server needs
    VAULT_MCP_INJECT_RULES=1 to receive the same rules Code and Claudian load
    natively. The Code target is left without it so those two don't double-load."""
    if "Desktop" not in label:
        return servers
    out = json.loads(json.dumps(servers))
    if out.get("vault") is not None:
        out["vault"].setdefault("env", {})["VAULT_MCP_INJECT_RULES"] = "1"
    return out


def register(servers: dict, include_desktop: bool) -> bool:
    """Add/update the system's servers in each app config. The user's own
    entries are left alone; system entries pointing at files that no longer
    exist are removed. Only writes a file whose content actually changes.
    Returns True if anything changed."""
    print("\n== Registering servers ==")
    print("system servers: %s" % ", ".join(sorted(servers)))
    changed = False
    for label, path in config_targets(include_desktop):
        block = _for_target(servers, label)
        data = _load(path)
        mcp = data.get("mcpServers", {})
        removed = sorted(k for k in list(mcp)
                         if k not in block
                         and isinstance(mcp[k], dict) and _points_at_missing(mcp[k]))
        for k in removed:
            del mcp[k]
        kept = sorted(k for k in mcp if k not in block)
        mcp.update(block)
        data["mcpServers"] = mcp
        if _write_json(path, data):
            changed = True
            note = "".join([
                (" (removed dead entries: %s)" % ", ".join(removed)) if removed else "",
                (" (left alone: %s)" % ", ".join(kept)) if kept else "",
            ])
            print("  registered %s -> %s%s" % (", ".join(sorted(block)), label, note))
        else:
            print("  %s: already up to date." % label)
    return changed


def wire_hook() -> bool:
    """Point the vault-verify PostToolUse hook at this machine's Python.
    Hooks the user added themselves are kept as they are. Returns True if
    anything changed."""
    print("\n== Wiring the vault-verify hook ==")
    cmd = '"%s" "%s"' % (sys.executable, HOOK)
    data = _load(CLAUDE_SETTINGS)
    entries = data.setdefault("hooks", {}).get("PostToolUse", [])

    def is_ours(entry: dict) -> bool:
        return any("vault-verify.py" in h.get("command", "") for h in entry.get("hooks", []))

    data["hooks"]["PostToolUse"] = (
        [e for e in entries if not is_ours(e)] +
        [{"matcher": m, "hooks": [{"type": "command", "command": cmd}]} for m in ("Write", "Edit")]
    )
    if _write_json(CLAUDE_SETTINGS, data):
        print("  hook -> %s" % cmd)
        return True
    print("  already up to date.")
    return False


# --------------------------------------------------------------------------- #
# Verify
# --------------------------------------------------------------------------- #
def _resolve_import_chain(entry: Path):
    """Follow @imports from CLAUDE.md as the apps do. Returns (seen, missing)."""
    import re
    imp = re.compile(r"^\s*@(\S+)\s*$")
    seen: list[Path] = []
    missing: list[str] = []

    def walk(path: Path, depth=0):
        path = path.resolve()
        if depth > 10 or path in seen:
            return
        if not path.exists():
            missing.append(str(path))
            return
        seen.append(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            m = imp.match(line)
            if not m:
                continue
            for cand in ((VAULT / m.group(1)), (path.parent / m.group(1))):
                if cand.exists():
                    walk(cand, depth + 1)
                    break
            else:
                missing.append(m.group(1))

    walk(entry)
    return seen, missing


def _probe_server(spec: dict, timeout: int = 20, extra_env: dict | None = None):
    """Launch a server exactly as an app would and confirm it lists tools."""
    cmd = [spec.get("command", "")] + list(spec.get("args", []))
    env = {**os.environ, **spec.get("env", {}), **(extra_env or {})}
    msgs = (json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05"}}) + "\n" +
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + "\n")
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
    except OSError as exc:
        return False, "could not launch (%s)" % exc
    try:
        out, err = proc.communicate(msgs, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "no response within %ds" % timeout
    for line in out.splitlines():
        try:
            tools = (json.loads(line).get("result") or {}).get("tools")
        except ValueError:
            continue
        if isinstance(tools, list) and tools:
            return True, "%d tools" % len(tools)
    return False, "started but returned no tools"


def verify(servers: dict, kb_expected: bool, include_desktop: bool) -> bool:
    """Self-check with a plain PASS/FAIL. Returns True if everything passed."""
    print("\n== Verifying ==")
    ok = True

    entry = VAULT / "CLAUDE.md"
    if not entry.exists():
        print("  FAIL  rules: CLAUDE.md not found (%s). Is this the vault root?" % VAULT)
        ok = False
    else:
        _, missing = _resolve_import_chain(entry)
        if missing:
            print("  FAIL  rules: CLAUDE.md loads but these @imports are missing:")
            for t in missing:
                print("          - %s" % t)
            ok = False
        else:
            print("  PASS  rules: CLAUDE.md and its full @import chain resolve.")

    if "vault" not in servers:
        print("  FAIL  vault server: not registered. Run this script without --check to fix it.")
        ok = False
    else:
        good, detail = _probe_server(servers["vault"])
        print(("  PASS  vault server: launches and serves tools (%s)." % detail) if good
              else ("  FAIL  vault server: %s" % detail))
        ok = ok and good

    if include_desktop:
        desktop = desktop_config_path()
        registered = set((_load(desktop) if desktop else {}).get("mcpServers", {}))
        expected = set(servers)
        if desktop is None:
            print("  SKIP  desktop config: no known location on this OS.")
        elif expected <= registered:
            print("  PASS  desktop config: %s registered for the Claude desktop app." % ", ".join(sorted(expected)))
        else:
            print("  FAIL  desktop config: %s missing from %s. Run this script again."
                  % (", ".join(sorted(expected - registered)), desktop))
            ok = False

    if not kb_expected:
        print("  SKIP  kb server: set up without the knowledge base (--no-kb).")
    elif "kb" not in servers:
        print("  FAIL  kb server: not registered (its libraries didn't install). Re-run to retry.")
        ok = False
    else:
        # Probe with the startup ingest scan pointed at an empty folder so the
        # answer comes back fast; real ingestion runs when the app starts it.
        empty = tempfile.mkdtemp(prefix="kb-probe-")
        good, detail = _probe_server(servers["kb"], timeout=120,
                                     extra_env={"KB_INGEST_PATHS": "", "KB_RESOURCES_PATH": empty})
        print(("  PASS  kb server: launches and serves tools (%s)." % detail) if good
              else ("  FAIL  kb server: %s" % detail))
        ok = ok and good

    # Entries that point at system files which no longer exist cannot work.
    for label, path in config_targets(include_desktop):
        for name, spec in _load(path).get("mcpServers", {}).items():
            if isinstance(spec, dict) and _points_at_missing(spec):
                print("  FAIL  %s entry in %s points at files that don't exist."
                      " Run this script without --check to clean it up." % (name, label))
                ok = False

    print("\n  All checks passed. Restart Claude and the system is live." if ok
          else "\n  One or more checks FAILED. Fix the items above, then run again.")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Set up this vault's AI system on this machine.")
    ap.add_argument("--no-kb", action="store_true", help="Skip the knowledge base (skip the ~1 GB install).")
    ap.add_argument("--no-desktop", action="store_true", help="Register for Claude Code only, not Claude Desktop.")
    ap.add_argument("--check", action="store_true", help="Only inspect and print PASS/FAIL; change nothing.")
    args = ap.parse_args()

    print("Vault:  %s" % VAULT)
    print("Python: %s (%s)" % (sys.executable, platform.platform()))

    if not check_environment():
        return 1
    ok, changed = preflight(fix=not args.check)
    if not ok:
        return 1

    if args.check:
        registered = _load(CODE_MCP).get("mcpServers", {})
        servers = {k: registered[k] for k in ("vault", "kb") if isinstance(registered.get(k), dict)}
        return 0 if verify(servers, kb_expected="kb" in servers,
                           include_desktop=not args.no_desktop) else 1

    if args.no_kb:
        kb_ok = False
    else:
        kb_ok, kb_changed = setup_kb()
        changed = changed or kb_changed
    servers = build_servers(kb_ok)
    changed = register(servers, include_desktop=not args.no_desktop) or changed
    changed = wire_hook() or changed
    ok = verify(servers, kb_expected=not args.no_kb, include_desktop=not args.no_desktop)

    if ok and not changed:
        print("\nEverything was already set up; nothing was changed, no restart needed.")
    elif ok:
        print("\nNext steps:")
        print("  1. Fully quit Claude (not just the window) and start it again.")
        print("  2. Open THIS folder in Claude:  %s" % VAULT)
        print("  3. Type:  read your instructions")
        print("\nRun this script again anytime to update or repair, or with --check to just inspect.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
