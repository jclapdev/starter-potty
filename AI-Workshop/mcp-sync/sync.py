#!/usr/bin/env python3
"""Sync MCP server registrations across Claude Code and Claude Desktop.

One canonical list (servers.json) is written into the two files each app
actually reads reliably:

  Claude Code     -> <vault>/.mcp.json                       (project scope)
  Claude Desktop  -> ~/Library/Application Support/Claude/claude_desktop_config.json

Why these two files, not `.claude/settings.json`: Claude Code rewrites
settings.json during a session (it auto-appends permissions), which clobbers
any mcpServers added there out-of-band. `.mcp.json` is the project-scoped MCP
config Code is designed to read and does not rewrite, so registrations stick.

Both targets keep all their other keys — only the `mcpServers` block is
replaced. A `.bak` of each target is written before any change.

Usage:
  python sync.py            # write canonical servers into both targets
  python sync.py --check    # report drift only; exit 1 if out of sync (no writes)

Edit servers.json to add/remove/change a server, then run sync. servers.json
is the single source of truth.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
CANON = _DIR / "servers.json"
# _DIR is <vault>/AI-Workshop/mcp-sync -> vault root is two levels up.
VAULT = _DIR.parents[1]
CODE_MCP = VAULT / ".mcp.json"


def desktop_config_path():
    """Claude Desktop config location for the current OS (None if unknown)."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        base = os.environ.get("APPDATA")
        return Path(base) / "Claude" / "claude_desktop_config.json" if base else None
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"  # Linux


DESKTOP = desktop_config_path()

TARGETS = [("Claude Code (.mcp.json)", CODE_MCP)]
if DESKTOP is not None:
    TARGETS.append(("Claude Desktop (claude_desktop_config.json)", DESKTOP))


def _load(path):
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _dump(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def _canonical():
    if not CANON.exists():
        sys.exit("error: canonical %s not found" % CANON)
    return _load(CANON)


def _warn_missing_commands(servers):
    """Flag server commands that are absolute paths to files that don't exist."""
    for name, spec in servers.items():
        cmd = spec.get("command", "")
        if cmd and Path(cmd).is_absolute() and not Path(cmd).exists():
            print("  WARNING: %s -> command not found on disk: %s" % (name, cmd))


def check():
    """Confirm the system's servers (vault, kb) are present and correct in each
    target. Any other server already in the config is the user's own and is
    ignored."""
    servers = _canonical()
    drift = False
    for label, path in TARGETS:
        current = _load(path).get("mcpServers", {})
        missing = [k for k in servers if k not in current]
        differs = [k for k in servers if k in current and current[k] != servers[k]]
        if not missing and not differs:
            print("in sync: %s" % label)
        else:
            drift = True
            print("DRIFT:   %s" % label)
            if missing:
                print("    missing: %s" % ", ".join(sorted(missing)))
            if differs:
                print("    differs: %s" % ", ".join(sorted(differs)))
    return 1 if drift else 0


def sync():
    """Add/update the system's own servers in each target, and leave every other
    server already there untouched."""
    servers = _canonical()
    print("system servers: %s" % ", ".join(sorted(servers)))
    _warn_missing_commands(servers)
    for label, path in TARGETS:
        data = _load(path)
        if path.exists():
            shutil.copy(str(path), str(path) + ".bak")
        mcp = data.get("mcpServers", {})
        kept = [k for k in mcp if k not in servers]
        mcp.update(servers)          # add/update ours; leave the rest alone
        data["mcpServers"] = mcp
        path.parent.mkdir(parents=True, exist_ok=True)
        _dump(path, data)
        note = (" (left alone: %s)" % ", ".join(sorted(kept))) if kept else ""
        print("updated %s -> %s%s" % (", ".join(sorted(servers)), label, note))
    print("done. Restart Claude Code and Claude Desktop to load changes.")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        raise SystemExit(check())
    raise SystemExit(sync())
