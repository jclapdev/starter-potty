# kb-mcp — Queryable Knowledge Base MCP Server

A shared knowledge layer: agents look up how a past problem with a specific tool was solved, and record new fixes as they resolve them. Backed by a local vector store ([LanceDB](https://lancedb.github.io/lancedb/)) with local embeddings (sentence-transformers `all-MiniLM-L6-v2`), so there is no API cost and nothing leaves the machine.

Follows the same fast-path/fallback pattern as the `vault` server: call the MCP tool first, fall back to file reads if the server is unavailable.

## Tools (5)

| Tool | Direction | Description |
|---|---|---|
| `query_patterns(tool, problem, limit=5)` | read | Semantic search scoped to a tool. Returns ranked problem/fix pairs. |
| `list_tools()` | read | Every tool in the KB with record counts. |
| `get_patterns_summary(tool)` | read | Record count, top tags, and date range for a tool. |
| `record_fix(tool, problem, fix, project?, tags?)` | write | Store a problem/fix. Deduplicated by content hash. |
| `ingest_kb(source_path, tool?)` | write | Incrementally ingest a file or directory (`.md`/`.txt`/`.pdf`). |

## Data model

`kb_records` — one row per chunk: `id` (SHA-256 of chunk text, the dedup key), `vector` (float32[384]), `tool`, `project`, `type` (`problem_fix`|`reference`|`pattern`), `problem`, `fix`, `tags` (JSON list), `source_path`, `date_added`.

`ingested_files` — ingestion checkpoint (`path`, `mtime`, `chunk_count`, `date_ingested`) so unchanged files are not reprocessed.

## Auto-ingestion

On startup the server scans `sources/` for new or changed `.md`/`.txt`/`.pdf` files and ingests them before serving. No file watcher — drop a file in `sources/` and restart the server to index it. Scan failures are logged to stderr and never abort startup.

## Setup

Heavy dependencies (LanceDB, sentence-transformers, pypdf) mean this server needs a virtual environment — unlike the stdlib-only `vault` server.

```bash
cd AI-Workshop/mcp-servers/kb
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The first `query_patterns` / `record_fix` call downloads the `all-MiniLM-L6-v2` model (~90 MB) once, then caches it.

### Cross-platform alternative (uv)

For machines that ship with [`uv`](https://docs.astral.sh/uv/) (single binary, all platforms), you can skip the manual venv and wire the server as `uv run`, which reads `requirements.txt` and manages the environment automatically:

```json
"kb": { "command": "uv", "args": ["run", "AI-Workshop/mcp-servers/kb/server.py"] }
```

This is the portable form to use when distributing via the Starter. It is **not** the form wired on this machine, because `uv` is not installed here.

## How it is wired (this machine)

`.claude/settings.json` → `mcpServers.kb` points the venv's Python at `server.py` (mirrors how the `vault` server is wired), with the five `mcp__kb__*` permissions in `permissions.allow`:

```json
"kb": {
  "command": "/path/to/your-vault/AI-Workshop/mcp-servers/kb/.venv/bin/python",
  "args": ["/path/to/your-vault/AI-Workshop/mcp-servers/kb/server.py"]
}
```

After editing `server.py` or `settings.json`, restart the host (Claude Desktop / Claude Code) to reload.

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `KB_DATA_PATH` | `<server_dir>/data` | LanceDB storage (gitignored) |
| `KB_RESOURCES_PATH` | `<server_dir>/sources` | auto-ingest drop folder |
| `KB_MODEL_NAME` | `all-MiniLM-L6-v2` | embedding model |

## Bulk ingestion CLI

For large one-off loads, use the CLI instead of the `ingest_kb` tool:

```bash
.venv/bin/python ingest.py <path> [--tool <name>]
```

Idempotent — re-running skips unchanged files and duplicate chunks. The CLI imports its pipeline from `server.py`, so there is one source of truth.

## Agent integration (the fast-path pattern)

Any agent that handles a tool's problem-solving workflow should query the KB first and record fixes after. Add these steps to that agent's `AGENT.md` (modeled on how `session-start` calls `get_session_brief`):

```
## Step 1 — KB lookup (fast path)
Call mcp__kb__query_patterns(tool="<this-tool>", problem="<description>").
If results return, surface the top match before proceeding.
If the KB server is unavailable, continue without it — do not abort.

## Final step — Record the fix (if a problem was resolved this session)
Call mcp__kb__record_fix(tool="<this-tool>", problem="...", fix="...").
```

**Current state:** the active agents are all vault-meta agents (backlink-scan, skill-eval-runner, agent-detector, prose-review); none debug external tools, so none is a correct home for this fast-path yet. Wire it in when a tool-problem-solving agent exists (e.g. a comic-generator agent for the ComfyUI pipeline).

## Verification

Tested against real LanceDB:

1. `list_tools` on an empty DB returns `{"tools": []}`.
2. `record_fix` → `created`; the same call again → `duplicate`.
3. `query_patterns` returns the record for a semantically similar phrase and is scoped by `tool` (vector field stripped from results).
4. `ingest_kb` / `ingest.py` ingest a file once; a second run skips it as unchanged.
5. `list_tools` and `get_patterns_summary` report counts, tags, and date range.
6. The startup scan is idempotent (no new chunks on rescan).
7. MCP protocol loop: `initialize` returns serverInfo, `tools/list` returns all five tools.
8. End-to-end with the real `all-MiniLM-L6-v2` model: a paraphrased query ("images are fuzzy and lack sharpness") correctly retrieved a recorded "blurry panels" fix — semantic retrieval, not keyword match.

The remaining step is host-side: restart Claude Desktop / Claude Code so it loads the `kb` connector, then confirm `mcp__kb__list_tools` routes from the client.
