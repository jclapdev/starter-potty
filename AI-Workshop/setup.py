#!/usr/bin/env python3
"""setup.py — one-command setup for this vault's AI system. Works on macOS,
Windows, and Linux.

Run it from the vault root with whatever Python you have:

    python AI-Workshop/setup.py

What it does, and why it makes the system portable:

  - Uses the SAME Python you ran it with (sys.executable) as the interpreter for
    the servers. That sidesteps the python3-vs-python-vs-py problem entirely —
    no command name is assumed, an absolute interpreter path is written.
  - Resolves AI-Workshop/mcp-sync/servers.template.json (placeholders only, no
    machine paths) into servers.json with real paths for THIS machine.
  - Registers the system's servers (vault, kb) in the two files the apps read:
    .mcp.json (Claude Code) and the Claude Desktop config (OS-correct location),
    via sync.py. Any other server already in those files is left alone.
  - Points the vault-verify hook at this machine's interpreter.
  - Sets up the knowledge base: creates the kb-mcp virtualenv (Scripts on
    Windows, bin on POSIX) and installs its libraries. It is part of the system.

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
def _subs() -> dict:
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


def resolve_servers() -> dict:
    if not TEMPLATE.exists():
        sys.exit("error: %s not found" % TEMPLATE)
    subs = _subs()
    servers = {}
    for name, spec in json.loads(TEMPLATE.read_text(encoding="utf-8")).items():
        servers[name] = _apply(spec, subs)
    return servers


# --------------------------------------------------------------------------- #
# kb-mcp dependency install
# --------------------------------------------------------------------------- #
def _kb_core_ok(vpy: Path) -> bool:
    """True if the kb virtualenv can import its core libraries. This is the real
    test of whether kb will run — independent of any pip exit code. A prior
    successful install still counts even if a later run hit a transient error."""
    if not vpy.exists():
        return False
    probe = "import lancedb, sentence_transformers, pypdf"
    try:
        r = subprocess.run([str(vpy), "-c", probe],
                           capture_output=True, text=True, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return r.returncode == 0


def setup_kb() -> bool:
    """Set up the knowledge base. Returns True if kb can actually run (its core
    libraries import), False otherwise. A failure never stops the rest of setup.

    Core libraries (requirements-core.txt) install with a hard check: without
    them kb cannot serve, so a failure means kb is not registered. The optional
    file-type extractors (the rest of requirements.txt) install best-effort — if
    one fails (rapidocr/onnxruntime is the usual culprit on a fresh machine), kb
    still runs for every other type, so that must not drop the whole connector."""
    print("\n== Setting up the knowledge base (kb) ==")
    venv = KB_DIR / ".venv"
    vpy = venv_python(venv)
    core_req = KB_DIR / "requirements-core.txt"
    full_req = KB_DIR / "requirements.txt"
    try:
        if not vpy.exists():
            print("  creating virtualenv %s" % venv)
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(vpy), "-m", "pip", "install", "--upgrade", "pip"], check=False)
        print("  installing core libraries (first time downloads ~1 GB, can take a few minutes)")
        subprocess.run([str(vpy), "-m", "pip", "install", "-r", str(core_req)], check=True)
    except Exception as exc:  # noqa: BLE001
        print("  WARNING: the knowledge base core didn't install (%s)." % exc)
        print("  Run setup again to retry the knowledge base.")
        return _kb_core_ok(vpy)  # a prior run may have already installed it

    # Optional extractors — best effort. Never let a failure here drop kb.
    print("  installing optional file-type extractors (best effort)")
    r = subprocess.run([str(vpy), "-m", "pip", "install", "-r", str(full_req)])
    if r.returncode != 0:
        print("  note: some optional extractors didn't install; kb still works for")
        print("        core types. Re-run setup later to retry the extractors.")

    ok = _kb_core_ok(vpy)
    print("  knowledge base ready." if ok else
          "  WARNING: kb core still won't import after install; kb not registered.")
    return ok


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
def _resolve_import_chain(entry: Path):
    """Follow @imports from CLAUDE.md exactly as Code/Claudian expand them.
    Returns (files_seen, missing_targets)."""
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
            target = m.group(1)
            for cand in ((VAULT / target), (path.parent / target)):
                if cand.exists():
                    walk(cand, depth + 1)
                    break
            else:
                missing.append(target)

    walk(entry)
    return seen, missing


def _probe_vault_server(spec: dict) -> tuple[bool, str]:
    """Launch the vault server exactly as an app would and confirm it answers a
    tools/list. Returns (ok, detail)."""
    cmd = [spec.get("command", "")] + list(spec.get("args", []))
    env = {**os.environ, **spec.get("env", {})}
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05"}})
    listing = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
    except OSError as exc:
        return False, "could not launch (%s): %s" % (cmd[0], exc)
    try:
        out, err = proc.communicate(init + "\n" + listing + "\n", timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "no response within 20s (server may be hanging)"
    for line in out.splitlines():
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        tools = (msg.get("result") or {}).get("tools")
        if isinstance(tools, list) and tools:
            return True, "%d tools" % len(tools)
    tail = (err or out).strip().splitlines()[-1:] or [""]
    return False, "started but returned no tools (%s)" % tail[0]


def verify_install(servers: dict, kb_expected: bool = True) -> bool:
    """End-of-setup self-check. Prints a plain PASS/FAIL the user can read on any
    machine — no need to send output anywhere. Returns True if all checks pass.

    kb_expected is False when the user ran --no-kb: the knowledge base is
    intentionally absent, so a missing kb server is reported as skipped, not
    failed."""
    print("\n== Verifying the install ==")
    ok = True

    # 1. Rule chain: CLAUDE.md and every @import it pulls in must resolve.
    entry = VAULT / "CLAUDE.md"
    if not entry.exists():
        print("  FAIL  rules: CLAUDE.md not found at vault root (%s)" % VAULT)
        print("        -> apps load no rules. Confirm this folder is the vault root.")
        ok = False
    else:
        _, missing = _resolve_import_chain(entry)
        if missing:
            print("  FAIL  rules: CLAUDE.md loads, but these @imports are missing:")
            for t in missing:
                print("          - %s" % t)
            print("        -> rules load only partially. Re-run update to restore them.")
            ok = False
        else:
            print("  PASS  rules: CLAUDE.md and its full @import chain resolve.")

    # 2. Vault server must actually launch and serve tools (get_session_brief etc.).
    vault_spec = servers.get("vault")
    if not vault_spec:
        print("  FAIL  vault server: not registered.")
        ok = False
    else:
        good, detail = _probe_vault_server(vault_spec)
        if good:
            print("  PASS  vault server: launches and serves tools (%s)." % detail)
        else:
            print("  FAIL  vault server: %s" % detail)
            print("        -> the vault MCP tools won't be available in the app.")
            ok = False

    # 3. kb server — part of the system. If it isn't registered, its libraries
    #    didn't finish installing; say so plainly instead of shipping without it.
    #    Checked by importing the core libs in its venv (fast, and it's what
    #    actually breaks) rather than a full MCP probe: the kb server runs a
    #    vault index scan before it serves, which can outlast a probe timeout on
    #    first run and give a false FAIL.
    kb_spec = servers.get("kb")
    if not kb_expected:
        print("  SKIP  kb server: set up without the knowledge base (--no-kb).")
    elif not kb_spec:
        print("  FAIL  kb server: not registered (its libraries didn't finish installing).")
        print("        -> knowledge-base tools won't be available. Re-run setup to retry.")
        ok = False
    else:
        vpy = Path(kb_spec.get("command", ""))
        if _kb_core_ok(vpy):
            print("  PASS  kb server: core libraries import in its virtualenv.")
        else:
            print("  FAIL  kb server: registered, but its virtualenv can't import the core libraries.")
            print("        -> re-run setup to reinstall the knowledge base.")
            ok = False

    if ok:
        print("  All checks passed. Restart the app and the system will be live.")
    else:
        print("\n  One or more checks FAILED. Fix the items above, then re-run setup.")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Set up this vault's AI system (cross-platform).")
    ap.add_argument("--no-desktop", action="store_true",
                    help="Skip writing the Claude Desktop config (Claude Code only).")
    ap.add_argument("--no-desktop-shortcut", action="store_true",
                    help="Don't add a Desktop shortcut/alias to the vault.")
    ap.add_argument("--no-kb", action="store_true",
                    help="Set up without the knowledge base (skip the ~1 GB kb install).")
    args = ap.parse_args()

    print("Vault: %s" % VAULT)
    print("Python: %s (%s)" % (sys.executable, platform.platform()))

    if args.no_kb:
        print("\n== Knowledge base (kb) ==\n  skipped (--no-kb)")
        kb_ok = False
    else:
        kb_ok = setup_kb()

    print("\n== Generating machine-specific server config ==")
    servers = resolve_servers()
    if not kb_ok:
        servers.pop("kb", None)  # skipped (--no-kb) or install failed; don't register a broken connector
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

    verify_install(servers, kb_expected=not args.no_kb)

    print("\nSetup complete.")
    print("Next: restart Claude Code and (if used) Claude Desktop so they load the servers.")
    print("In the Claude desktop app (Cowork), open this vault from the Desktop entry.")
    if not kb_ok and not args.no_kb:
        print("The knowledge base didn't finish installing; re-run setup to try again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
