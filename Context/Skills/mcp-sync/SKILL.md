---
name: mcp-sync
description: Register, remove, or sync MCP servers (connectors) so Claude Code and Claude Desktop both see the same set. Use this whenever the user adds or builds a new MCP server, mentions a connector "not showing up", says the two apps are "out of sync", asks to "register the connector in both", or edits MCP server config by hand. Always route MCP-server registration through this skill instead of hand-editing settings.json or claude_desktop_config.json — direct edits to settings.json get clobbered by Claude Code's permission auto-writer and silently disappear.
---

# MCP Sync

Keeps MCP server registrations identical across Claude Code and Claude Desktop from a single source of truth.

## Why this exists

Claude Code and Claude Desktop read MCP servers from **different files**, and one of them is unsafe to edit by hand:

| App | File it reads | Safe to edit directly? |
|---|---|---|
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | yes |
| Claude Code | `<vault>/.mcp.json` (project scope) | yes |
| Claude Code | `<vault>/.claude/settings.json` → `mcpServers` | **no** — Code rewrites this file during a session (auto-appending permissions) and drops out-of-band `mcpServers` edits |

The fix is one canonical, **machine-independent** template plus a generator. Do not register servers anywhere else, and do not hand-edit `servers.json` (it is generated).

## Source of truth

Two files in `AI-Workshop/mcp-sync/`:

| File | Committed? | Role |
|---|---|---|
| `servers.template.json` | yes (shared) | The system's servers (vault, kb), using **placeholders** — no machine paths. `{{PYTHON}}`, `{{VAULT}}`, `{{VAULT_MCP_SERVER}}`, `{{KB_VENV_PYTHON}}`, `{{KB_SERVER}}`. |
| `servers.json` | no (generated) | Resolved output for this machine, produced by `setup.py`. Don't edit by hand. |

`AI-Workshop/setup.py` resolves the template into `servers.json` with real paths for the current machine, then registers those servers. It uses `sys.executable` (the Python you ran it with) as the interpreter, so there is no `python3`-vs-`python` assumption and no hardcoded path. This is what makes the Starter portable across macOS/Windows/Linux.

The sync only manages the system's own servers. Any other server already in a machine's config (a personal one the user added) is left exactly as it is — the system never removes or overwrites it.

## Workflow

### First-time setup on any machine
```bash
python AI-Workshop/setup.py
```
Sets up the full system (vault + knowledge base), generates `servers.json`, writes the system's servers into `.mcp.json` (Claude Code) and the OS-correct Claude Desktop config (leaving any other servers there alone), and wires the vault-verify hook to this machine's interpreter. Re-running is safe and idempotent.

### Add or change a system server (everyone gets it)
1. Add or edit its entry in `servers.template.json` using placeholders.
2. Re-run `python AI-Workshop/setup.py` to re-resolve and re-register.
3. Tell the user to **restart Claude Code and Claude Desktop**. A new server in `.mcp.json` prompts for approval on first load — expected.

### A personal server on one machine
Just add it to that machine's Claude config (or `.mcp.json`) yourself. The system's sync leaves servers it doesn't manage alone, so it won't touch or remove it.

### Remove a system server
Delete its entry from `servers.template.json`, then edit it out of the machine's config (the sync adds and updates the system's servers but does not delete on its own).

### Check for drift (no writes)
```bash
python3 AI-Workshop/mcp-sync/sync.py --check
```
Reports each target as `in sync` or `DRIFT` (listing missing/extra/differing servers) and exits non-zero on drift. Use this to confirm a sync took, or as the body of a scheduled drift check.

## Done when
- `sync.py --check` reports both targets `in sync`.
- The user has been told to restart both apps.

## Notes
- `setup.py` and `sync.py` resolve the vault root relative to their own location, and `sync.py` picks the Claude Desktop config path per-OS (macOS/Windows/Linux), so both are path-portable.
- `.mcp.json` is the project-scoped MCP file Claude Code is designed to read and does not rewrite — that is why registrations there stick where `settings.json` ones do not.
- Never commit `servers.json` — it holds machine-specific absolute paths. The `.gitignore` and the Starter build both exclude it.
