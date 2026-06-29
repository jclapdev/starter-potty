# kb-mcp — operational notes

**Needs a venv** (unlike stdlib-only vault-mcp). Deps: lancedb, sentence-transformers, pypdf.
Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

**Run:** stdio transport, registered as the `kb` connector in `.claude/settings.json` → points the venv python at `server.py`. Cross-platform alternative is `uv run` (see README) — not used here because `uv` isn't installed.

**After editing `server.py` or `settings.json`:** restart the host to reload.

**5 tools:** `query_patterns` (read), `list_tools` (read), `get_patterns_summary` (read), `record_fix` (write), `ingest_kb` (write).

**Auto-ingest:** drop `.md`/`.txt`/`.pdf` in `Resources/`, restart — startup scan indexes new/changed files. Idempotent; failures log to stderr and never abort startup.

**Ingestion pipeline lives in `server.py`** (`_gather_files` / `_process_file`); `ingest.py` is a thin CLI wrapper that imports it. One source of truth.

**Paths via env vars:** `KB_DATA_PATH`, `KB_RESOURCES_PATH`, `KB_MODEL_NAME`. `data/` and `.venv/` are gitignored.
