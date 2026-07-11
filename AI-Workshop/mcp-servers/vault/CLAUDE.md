# Vault MCP — operational notes

**No install needed.** Pure Python stdlib (3.7+). Any system `python3` runs it.

**Run:** stdio transport, registered via `claude_desktop_config.json`. Set `VAULT_PATH` env var to the vault root (defaults to three levels above `server.py` if unset).

**After editing `server.py`:** restart Claude Desktop to reload.

**13 tools (read-only except the two noted):**

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
| `vault_health(fix?)` | One-call maintenance report: broken links, orphans, map verification, lint, archive candidates. `fix=true` also applies the deterministic safe fixes (writes) |
| `wrap_session(...)` | Session close: writes the handoff note verbatim, applies structured open-work.md changes, moves history notes to Archive/ (writes) |

**Index:** two modes, switched automatically. Small vaults (under 5,000 notes) use the in-memory mtime cache, reparsing only changed files per call. Larger vaults switch to a persistent SQLite FTS5 index in `data/` (gitignored, one file per vault path): note bodies stay on disk, searches answer from the index in milliseconds, and each call pays only an mtime diff of changed files. Override with `VAULT_INDEX=memory|sqlite`; `VAULT_INDEX_DB` relocates the database. Both modes honor `Context/.vaultignore`. Measured at 100k synthetic notes: in-memory took 14 s per search at 7 GB RAM; FTS5 answers the same search in under 10 ms at flat RAM.
