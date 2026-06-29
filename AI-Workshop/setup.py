#!/usr/bin/env python3
"""setup.py — one-command setup for this vault's AI system. Works on macOS,
Windows, and Linux.

Run it from the vault root with whatever Python you have:

    python AI-Workshop/setup.py            # core only (no installs)
    python AI-Workshop/setup.py --with-kb  # also set up the knowledge-base server

What it does, and why it makes the system portable:

  - Uses the SAME Python you ran it with (sys.executable) as the interpreter for
    the servers. That sidesteps the python3-vs-python-vs-py problem entirely —
    no command name is assumed, an absolute interpreter path is written.
  - Resolves AI-Workshop/mcp-sync/servers.template.json (placeholders only, no
    machine paths) into servers.json with real paths for THIS machine.
  - Merges optional personal servers from servers.local.json if present (kept out
    of the shared Starter via .gitignore).
  - Registers the servers in the two files the apps read: .mcp.json (Claude Code)
    and the Claude Desktop config (OS-correct location), via sync.py.
  - Points the vault-verify hook at this machine's interpreter.
  - With --with-kb: creates the kb-mcp virtualenv (Scripts on Windows, bin on
    POSIX) and installs its requirements.

Nothing machine-specific is committed; everything is generated here, on the
recipient's machine, from their own Python and paths.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]   # AI-Workshop/setup.py -> vault root
AIW = VAULT / "AI-Workshop"
MCP_SYNC = AIW / "mcp-sync"
TEMPLATE = MCP_SYNC / "servers.template.json"
LOCAL = MCP_SYNC / "servers.local.json"
SERVERS = MCP_SYNC / "servers.json"
KB_DIR = AIW / "kb-mcp"
CLAUDE_SETTINGS = VAULT / ".claude" / "settings.json"


# --------------------------------------------------------------------------- #
# OS-aware paths
# --------------------------------------------------------------------------- #
def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


# --------------------------------------------------------------------------- #
# Template resolution
# --------------------------------------------------------------------------- #
def _subs(with_kb: bool) -> dict:
    s = {
        "{{PYTHON}}": sys.executable,
        "{{VAULT}}": str(VAULT),
        "{{VAULT_MCP_SERVER}}": str(AIW / "vault-mcp" / "server.py"),
        "{{KB_SERVER}}": str(KB_DIR / "server.py"),
        "{{KB_VENV_PYTHON}}": str(venv_python(KB_DIR / ".venv")),
    }
    return s


def _apply(obj, subs):
    if isinstance(obj, str):
        for k, v in subs.items():
            obj = obj.replace(k, v)
        return obj
    if isinstance(obj, list):
        return [_apply(x, subs) for x in obj]
    if isinstance(obj, dict):
        return {k: _apply(v, subs) for k, v in obj.items()}
    return obj


def resolve_servers(with_kb: bool) -> dict:
    if not TEMPLATE.exists():
        sys.exit("error: %s not found" % TEMPLATE)
    subs = _subs(with_kb)
    # Include kb if explicitly requested OR already installed — so re-running
    # setup.py without the flag never silently drops an existing kb server.
    include_kb = with_kb or venv_python(KB_DIR / ".venv").exists()
    servers = {}
    for name, spec in json.loads(TEMPLATE.read_text(encoding="utf-8")).items():
        if name == "kb" and not include_kb:
            continue
        servers[name] = _apply(spec, subs)
    # Personal/local servers (not shipped in the Starter).
    if LOCAL.exists():
        for name, spec in json.loads(LOCAL.read_text(encoding="utf-8")).items():
            servers[name] = _apply(spec, subs)
        print("  merged personal servers from servers.local.json")
    return servers


# --------------------------------------------------------------------------- #
# kb-mcp dependency install
# --------------------------------------------------------------------------- #
def setup_kb() -> None:
    print("\n== Setting up kb-mcp (knowledge base) ==")
    venv = KB_DIR / ".venv"
    vpy = venv_python(venv)
    if not vpy.exists():
        print("  creating virtualenv %s" % venv)
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    req = KB_DIR / "requirements.txt"
    print("  installing requirements (this can take a few minutes the first time)")
    subprocess.run([str(vpy), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(vpy), "-m", "pip", "install", "-r", str(req)], check=True)
    print("  kb-mcp ready.")


# --------------------------------------------------------------------------- #
# Hook wiring (vault-verify) with this machine's interpreter
# --------------------------------------------------------------------------- #
def wire_hooks() -> None:
    hook_script = "AI-Workshop/hooks/vault-verify.py"  # relative; cwd is the vault root
    cmd = '"%s" %s' % (sys.executable, hook_script)
    data = {}
    if CLAUDE_SETTINGS.exists():
        try:
            data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    hooks = data.setdefault("hooks", {})
    hooks["PostToolUse"] = [
        {"matcher": "Write", "hooks": [{"type": "command", "command": cmd}]},
        {"matcher": "Edit", "hooks": [{"type": "command", "command": cmd}]},
    ]
    CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("  wired vault-verify hook -> %s" % cmd)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Set up this vault's AI system (cross-platform).")
    ap.add_argument("--with-kb", action="store_true",
                    help="Also install the knowledge-base (kb) server's dependencies.")
    ap.add_argument("--no-desktop", action="store_true",
                    help="Skip writing the Claude Desktop config (Claude Code only).")
    args = ap.parse_args()

    print("Vault: %s" % VAULT)
    print("Python: %s (%s)" % (sys.executable, platform.platform()))

    if args.with_kb:
        setup_kb()

    print("\n== Generating machine-specific server config ==")
    servers = resolve_servers(with_kb=args.with_kb)
    SERVERS.write_text(json.dumps(servers, indent=2) + "\n", encoding="utf-8")
    print("  wrote %s (%s)" % (SERVERS.name, ", ".join(servers)))

    # Propagate into .mcp.json and the Desktop config via sync.py.
    sys.path.insert(0, str(MCP_SYNC))
    import sync  # noqa: E402  (path set above)
    if args.no_desktop:
        sync.TARGETS = [t for t in sync.TARGETS if "Code" in t[0]]
    print("\n== Registering servers ==")
    sync.sync()

    print("\n== Wiring hooks ==")
    wire_hooks()

    print("\nSetup complete.")
    print("Next: restart Claude Code and (if used) Claude Desktop so they load the servers.")
    if not args.with_kb:
        print("The knowledge-base server was skipped. Run with --with-kb to enable it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
