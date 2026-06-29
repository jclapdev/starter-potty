# Vault MCP Server

A small, read-only MCP server that lets Claude *query* the vault instead of loading whole files. It replaces "read all of `skill_map.md` / `agent_map.md` / `open-work.md` / the note you're looking for every task" with targeted lookups, so per-task context cost stops growing as the vault grows (see `Context/Diagnostics/2026-06-19-system-efficiency.md`, bottlenecks #4 and #7).

## Tools

All eleven tools are **read-only**. Each returns only what matches, so per-task context cost stops growing as the vault grows.

**Navigation / selection** (BM25-ranked)

| Tool | Returns | Replaces loading |
|---|---|---|
| `find_skill(query, limit=3)` | Ranked skills (name, path, description, score) | `skill_map.md` |
| `resolve_agent(task, limit=3)` | Ranked sub-agents (name, path, purpose, score) | `agent_map.md` |

**Orientation**

| Tool | Returns | Replaces loading |
|---|---|---|
| `get_open_work()` | Open items from `open-work.md` (Open section) | `open-work.md` |
| `get_session_brief()` | One bundle: latest session (topic + in-progress), open work, preferences, skill/agent capability lists | history + open-work + MEMORY + maps at session start |

**Content**

| Tool | Returns | Replaces |
|---|---|---|
| `search_notes(query, limit=5, scope=None)` | BM25 over note bodies: path + title + matching snippet (not whole files); optional folder `scope` | "read N files to find where X is discussed" |

**Link graph** (BFS over `[[wikilinks]]`)

| Tool | Returns |
|---|---|
| `get_links(note, direction="both", depth=1)` | Neighbours by link distance (`outbound` / `inbound` / `both`) — "what links here", related notes |
| `find_broken_links()` | `{source, target}` for links resolving to no note or file |
| `find_orphans()` | Notes with no inbound link (natural entry points exempted) |

**Structure / resolution**

| Tool | Returns |
|---|---|
| `resolve_note(name)` | A `[[wikilink]]` / bare name → real path(s); flags ambiguity |
| `vault_tree(path=".", depth=2)` | Compact folder layout with per-folder md counts |
| `list_by_status(status=None)` | Notes by validated `status` frontmatter; omit arg to group all |

### How it works

Ranking is BM25. The two selector tools read the live `Skills/` and `Agents/` folders on each call. Everything else is backed by a **single mtime-cached index**: on each call the server stats the tree and reparses only the files whose timestamp changed, so a query is O(result), not O(vault). The index **honours `Context/.vaultignore`**, so the Starter mirror and test trees don't double every note in the graph. Skills/agents are linked as `[[folder-name]]` (the file is `AGENT.md`/`SKILL.md`), and the resolver keys them by folder accordingly.

`list_by_status` validates against a fixed vocabulary — `idea, active, blocked, needs-eval, done` — so the field can't drift into synonyms the way free-form tags would. New skills, agents, notes, and links are all picked up automatically; adding content needs no code change.

## No install needed

The server uses **only the Python standard library** (Python 3.7+), so there is **no venv and no `pip install`**. Any system `python3` runs it.

## Register it

Run the cross-platform setup from the vault root; it registers this server in both Claude Code and Claude Desktop with the correct paths for your machine:

```bash
python AI-Workshop/setup.py
```

That writes the `vault` entry (and any others) into `.mcp.json` and the OS-correct Claude Desktop config, using the exact Python you ran setup with, then you restart the apps. You do not edit any config by hand, and there is no `python3`-vs-`python` problem to work around. See the root `HUMAN.md` for the full picture.

`VAULT_PATH` is set for you by setup; if you ever run the server directly it defaults to the repo root two levels above `server.py`.

## Quick check (optional)

To confirm the tools work against your vault before registering:

```
cd /path/to/your-vault/AI-Workshop/vault-mcp
python3 -c "import server; print(server.find_skill_core('wrap up the session', 2))"
python3 -c "import server; print(server.get_open_work_core())"
```

To exercise the actual MCP protocol (what Claude Desktop does):

```
printf '%s\n' \
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}' \
'{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"find_skill","arguments":{"query":"check for broken links"}}}' \
| python3 server.py
```

## How it fits the system

The navigation sequence in `Context/Systems/vault-rules.md` already calls `find_skill` / `resolve_agent` for selection instead of loading whole maps. Startup now calls `get_session_brief` directly: one call returns the latest session, open work, preferences, and capability lists, replacing the old session-start agent that read history, open-work, memory, and maps separately. The maps stay as the human-readable source of truth; the server is the machine-readable query layer over them.

After editing `server.py`, **restart Claude Desktop** — it loads the server once at startup, so new tools and fixes aren't live until it reconnects.

## Extending

Add a tool only when a real pain point shows up (per the open-work plan). Keep tools read-only and returning focused results.
