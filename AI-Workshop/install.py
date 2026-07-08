#!/usr/bin/env python3
"""install.py — set up this vault's AI system on the machine you run it on.

    python AI-Workshop/install.py

Run it once. When it prints "All checks passed", restart Claude and the system
is live. You can delete this file afterward — nothing at runtime needs it. To
update later, get the newer files (git pull, or re-download) and run it again;
re-running just rewrites the config, so install and update are the same command.

What it does, all in this one file:
  - Registers the system's servers (vault, kb) in the two files the apps read:
    .mcp.json (Claude Code / Claudian) and the Claude Desktop config. It writes
    the ABSOLUTE path of the Python you ran it with, so no "python vs python3"
    guessing. Any other server already in those files is left alone.
  - Sets up the knowledge base (kb): builds its virtualenv and installs its
    libraries. Skip with --no-kb.
  - Points the vault-verify hook at this machine's Python.
  - Verifies the result and prints a plain PASS/FAIL.

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
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]        # AI-Workshop/install.py -> vault root
AIW = VAULT / "AI-Workshop"
VAULT_SERVER = AIW / "mcp-servers" / "vault" / "server.py"
KB_DIR = AIW / "mcp-servers" / "kb"
HOOK = AIW / "hooks" / "vault-verify.py"
CODE_MCP = VAULT / ".mcp.json"
CLAUDE_SETTINGS = VAULT / ".claude" / "settings.json"


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


def desktop_config_path():
    """Claude Desktop config location for this OS (None if unknown)."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        base = os.environ.get("APPDATA")
        return Path(base) / "Claude" / "claude_desktop_config.json" if base else None
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


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


def setup_kb() -> bool:
    """Build the kb virtualenv and install its libraries. Returns True if kb can
    actually run. A failure never stops the rest of the install."""
    print("\n== Setting up the knowledge base (kb) ==")
    venv = KB_DIR / ".venv"
    vpy = venv_python(venv)
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
        return _kb_core_ok(vpy)
    print("  installing optional file-type extractors (best effort)")
    if subprocess.run([str(vpy), "-m", "pip", "install", "-r", str(full_req)]).returncode != 0:
        print("  note: some optional extractors didn't install; kb still works for core types.")
    ok = _kb_core_ok(vpy)
    print("  knowledge base ready." if ok else "  WARNING: kb core still won't import; kb not registered.")
    return ok


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


def register(servers: dict, include_desktop: bool) -> None:
    """Add/update the system's servers in each app config; leave others alone."""
    targets = [("Claude Code (.mcp.json)", CODE_MCP)]
    desktop = desktop_config_path()
    if include_desktop and desktop is not None:
        targets.append(("Claude Desktop (claude_desktop_config.json)", desktop))
    print("\n== Registering servers ==")
    print("system servers: %s" % ", ".join(sorted(servers)))
    for label, path in targets:
        block = _for_target(servers, label)
        data = _load(path)
        if path.exists():
            shutil.copy(str(path), str(path) + ".bak")
        mcp = data.get("mcpServers", {})
        kept = [k for k in mcp if k not in block]
        mcp.update(block)
        data["mcpServers"] = mcp
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        note = (" (left alone: %s)" % ", ".join(sorted(kept))) if kept else ""
        print("  registered %s -> %s%s" % (", ".join(sorted(block)), label, note))


def wire_hook() -> None:
    """Point the vault-verify PostToolUse hook at this machine's Python."""
    print("\n== Wiring the vault-verify hook ==")
    cmd = '"%s" "%s"' % (sys.executable, HOOK)
    data = _load(CLAUDE_SETTINGS)
    data.setdefault("hooks", {})["PostToolUse"] = [
        {"matcher": "Write", "hooks": [{"type": "command", "command": cmd}]},
        {"matcher": "Edit", "hooks": [{"type": "command", "command": cmd}]},
    ]
    CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("  hook -> %s" % cmd)


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


def _probe_vault_server(spec: dict):
    """Launch the vault server as an app would and confirm it lists tools."""
    cmd = [spec.get("command", "")] + list(spec.get("args", []))
    env = {**os.environ, **spec.get("env", {})}
    msgs = (json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05"}}) + "\n" +
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + "\n")
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
    except OSError as exc:
        return False, "could not launch (%s)" % exc
    try:
        out, err = proc.communicate(msgs, timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "no response within 20s"
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

    good, detail = _probe_vault_server(servers["vault"])
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
    elif _kb_core_ok(Path(servers["kb"]["command"])):
        print("  PASS  kb server: core libraries import in its virtualenv.")
    else:
        print("  FAIL  kb server: registered, but its virtualenv can't import the core libraries.")
        ok = False

    print("\n  All checks passed. Restart Claude and the system is live." if ok
          else "\n  One or more checks FAILED. Fix the items above, then run again.")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Set up this vault's AI system on this machine.")
    ap.add_argument("--no-kb", action="store_true", help="Skip the knowledge base (skip the ~1 GB install).")
    ap.add_argument("--no-desktop", action="store_true", help="Register for Claude Code only, not Claude Desktop.")
    args = ap.parse_args()

    print("Vault:  %s" % VAULT)
    print("Python: %s (%s)" % (sys.executable, platform.platform()))

    if not check_environment():
        return 1
    kb_ok = False if args.no_kb else setup_kb()
    servers = build_servers(kb_ok)
    register(servers, include_desktop=not args.no_desktop)
    wire_hook()
    ok = verify(servers, kb_expected=not args.no_kb, include_desktop=not args.no_desktop)

    if ok:
        print("\nNext steps:")
        print("  1. Fully quit Claude (not just the window) and start it again.")
        print("  2. Open THIS folder in Claude:  %s" % VAULT)
        print("  3. Type:  read your instructions")
        print("\nYou can delete this file; nothing at runtime needs it. Run it again anytime to reconfigure or update.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
