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
    # Full path so the hook works no matter what folder Claude runs it from.
    hook_script = str(VAULT / "AI-Workshop" / "hooks" / "vault-verify.py")
    cmd = '"%s" "%s"' % (sys.executable, hook_script)
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
# Cowork access: real path must be inside home; give a Desktop entry point
# --------------------------------------------------------------------------- #
def _inside_home(path: Path) -> bool:
    home = Path.home().resolve()
    real = path.resolve()
    return real == home or home in real.parents


def desktop_dir() -> Path:
    """The user's real Desktop folder, even if the OS has redirected it."""
    if platform.system() == "Windows":
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "[Environment]::GetFolderPath('Desktop')"],
                capture_output=True, text=True, timeout=10)
            p = out.stdout.strip()
            if p:
                return Path(p)
        except Exception:
            pass
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    return Path.home() / "Desktop"


def make_desktop_shortcut() -> None:
    """Put a Desktop entry that opens this vault, so it is reachable from the
    Desktop on every machine. Cowork resolves the shortcut to the vault's real
    path, which (being inside home) it accepts. No-op if the vault already lives
    directly on the Desktop.
    """
    dd = desktop_dir()
    if not dd.exists():
        print("  (no Desktop folder found; skipping shortcut)")
        return
    try:
        if VAULT.resolve().parent == dd.resolve():
            print("  vault is already on the Desktop; nothing to add")
            return
    except OSError:
        pass

    name = VAULT.name
    if platform.system() == "Windows":
        lnk = dd / (name + ".lnk")
        ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
              "$s.TargetPath='%s';$s.Save()" % (str(lnk), str(VAULT)))
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps])
        print("  created Desktop shortcut: %s" % lnk if r.returncode == 0
              else "  WARNING: could not create Desktop shortcut")
    else:
        link = dd / name
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            print("  Desktop already has a '%s' entry; leaving it" % name)
            return
        os.symlink(VAULT, link)
        print("  created Desktop alias: %s -> %s" % (link, VAULT))


def report_cowork_access() -> None:
    if _inside_home(VAULT):
        print("  OK: this vault is inside your home folder, so Cowork can open it.")
    else:
        print("  ATTENTION: this vault's real location is OUTSIDE your home folder:")
        print("      %s" % VAULT.resolve())
        print("  Claude Cowork only opens folders whose real path is inside your")
        print("  home folder. Move the whole vault into your home folder (for")
        print("  example ~/%s) and run setup again. The Desktop shortcut step" % VAULT.name)
        print("  will then give you Desktop access that works on every machine.")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Set up this vault's AI system (cross-platform).")
    ap.add_argument("--with-kb", action="store_true",
                    help="Also install the knowledge-base (kb) server's dependencies.")
    ap.add_argument("--no-desktop", action="store_true",
                    help="Skip writing the Claude Desktop config (Claude Code only).")
    ap.add_argument("--no-desktop-shortcut", action="store_true",
                    help="Don't add a Desktop shortcut/alias to the vault.")
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

    print("\n== Desktop access ==")
    report_cowork_access()
    if not args.no_desktop_shortcut:
        make_desktop_shortcut()

    print("\nSetup complete.")
    print("Next: restart Claude Code and (if used) Claude Desktop so they load the servers.")
    print("In the Claude desktop app (Cowork), open this vault from the Desktop entry.")
    if not args.with_kb:
        print("The knowledge-base server was skipped. Run with --with-kb to enable it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
