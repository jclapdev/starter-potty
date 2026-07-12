# kb-mcp — operational notes

**Needs a venv** (unlike stdlib-only vault-mcp). Core deps: lancedb, sentence-transformers, pypdf. Extractor deps (optional, one per file type): python-docx, python-pptx, beautifulsoup4, striprtf, EbookLib, openpyxl, rapidocr-onnxruntime. A missing extractor lib skips that type, never crashes ingestion.
Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

**Run:** stdio transport, registered as the `kb` connector in `.claude/settings.json` → points the venv python at `server.py`. Cross-platform alternative is `uv run` (see README) — not used here because `uv` isn't installed.

**After editing `server.py` or `settings.json`:** restart the host to reload.

**5 tools:** `query_patterns` (read), `list_tools` (read), `get_patterns_summary` (read), `record_fix` (write), `ingest_kb` (write).

**Auto-ingest:** drop a supported file in `sources/`, restart — startup scan indexes new/changed files. Idempotent; failures log to stderr and never abort startup.

**Supported types (20):** prose `.md .txt .pdf .docx .pptx .html .htm .rtf .epub`; structured `.json .xml` (flattened to key paths); tables `.csv .xlsx` (one chunk per row, text cells only — numeric-only rows skipped); images `.png .jpg .jpeg .webp .bmp .tiff .tif` (rapidocr OCR). Registry: `_extract_chunks` in `server.py`.

**Ingestion pipeline lives in `server.py`** (`_gather_files` / `_process_file`); `ingest.py` is a thin CLI wrapper that imports it. One source of truth.

**Served through the vault server since v3.** This folder is the engine, not a registered server: `vault/server.py` loads it when its libraries are installed, serves the 5 kb tools from the one `vault` connector, and fuses its meaning-based ranking into `search_notes`. The standalone registration is removed by `install.py`.

**Vault self-index: on by default** (`Context/` + `Reference/`, hidden folders skipped). Reversed 2026-07-11 after benchmarking: meaning-based recall answers vaguely worded questions that keyword search misses entirely (quiz: keyword-only 4/12, hybrid 11/12), so it is a distinct capability, not duplicate work. Set `KB_INGEST_PATHS` to override the folders, or empty to disable.

**index+note (transpose):** `ingest_kb(..., write_note=True)` writes a clean Obsidian note per non-Markdown source into the wiki folder (`AI-Workshop/Projects/Wiki/`), not just an index row.

**Paths via env vars:** `KB_DATA_PATH`, `KB_RESOURCES_PATH`, `KB_MODEL_NAME`, `KB_VAULT_PATH`, `KB_INGEST_PATHS` (os.pathsep-separated; empty disables vault self-index), `KB_WIKI_PATH`. `data/` and `.venv/` are gitignored.
