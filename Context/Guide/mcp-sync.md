---
tags: [guide]
covers: Context/Skills/mcp-sync/SKILL.md
---

# mcp-sync

_User guide — the plain-language companion to the AI reference in `Context/Skills/mcp-sync/SKILL.md`._

## What it's for

Keeps your **connectors** (the extra tools Claude can use, like `vault` and `kb`) the same in both Claude apps, from one shared list. Add a connector once, and both apps see it.

## How it works

Claude Desktop and Claude Code each read their connectors from a different file on your disk. mcp-sync keeps a single template as the source of truth — a machine-independent list with placeholders instead of real paths. When you run `python AI-Workshop/setup.py`, it fills in your machine's real paths and writes the connectors into both apps' files.

It only manages the system's own connectors. Any personal connector you added yourself is left exactly as it is — sync never removes or overwrites it.

## When it touches you

- **You add or build a new connector** and want both apps to see it → re-run setup, then restart both apps.
- **A connector "isn't showing up"** in one app → the two apps are out of sync; re-run setup.
- **The two apps disagree** on what's connected → run the drift check to see the difference.
- **Setting up on a new machine** → the first `setup.py` run registers everything for that machine.

## Best practices

- **Never hand-edit the connector list in `.claude/settings.json`.** Claude Code rewrites that file during a session and your edit silently disappears. Change the template and re-run setup instead.
- **After a sync, restart both apps.** A new connector prompts for approval the first time Claude Code loads it — that's expected, not an error.
- **Check without changing anything:** `python3 AI-Workshop/mcp-sync/sync.py --check` reports whether both apps are in sync and lists any drift. Read-only — it never writes.

## Dig deeper →

- AI reference (the exact procedure): [[Context/Skills/mcp-sync/SKILL.md|mcp-sync SKILL]]
- Glossary: [[glossary]] — connector / MCP, vault connector, kb connector
