# Vault MCP — operational notes

**No install needed.** Pure Python stdlib (3.7+). Any system `python3` runs it.

**Run:** stdio transport, registered via `claude_desktop_config.json`. Set `VAULT_PATH` env var to the vault root (defaults to three levels above `server.py` if unset).

**After editing `server.py`:** restart Claude Desktop to reload.

**12 tools (all read-only):**

| Tool | Purpose |
|---|---|
| `find_skill(query)` | BM25-ranked skill match — replaces loading skill_map.md |
| `resolve_agent(task)` | BM25-ranked agent match — replaces loading agent_map.md |
| `get_open_work()` | Open section of open-work.md |
| `get_session_brief()` | One-call startup bundle: last session + open work + preferences + capabilities |
| `search_notes(query, scope?)` | Full-text BM25 over note bodies, returns path + snippet |
| `get_links(note, direction, depth)` | BFS over wikilink graph |
| `find_broken_links()` | Links resolving to no note or file |
| `find_orphans()` | Notes with no inbound links |
| `resolve_note(name)` | Wikilink/bare name → real vault path(s) |
| `vault_tree(path, depth)` | Compact folder layout with md-file counts |
| `list_by_status(status?)` | Notes by `status` frontmatter field |
| `vault_health()` | One-call maintenance report: broken links, orphans, map verification, lint, archive candidates. Read-only; the caller applies fixes |

**Index:** mtime-cached — only changed files are reparsed on each call. Honors `Context/.vaultignore`.
