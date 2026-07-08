---
name: ingest
description: Process a new source into the vault's knowledge layer. Trigger when the user says "ingest [file/topic]", "process this source", "add this to the wiki", "file this", or drops a file in `Reference/` (or the KB `sources/` folder) and asks Claude to work with it. Also trigger when the user wants to compile research notes, a document, or a reference into the vault so it's searchable and cross-referenced. Ingest reads the source, extracts entities and concepts, writes a summary page, updates related wiki pages, refreshes the content index, and logs the operation — so each source compounds the vault rather than disappearing into chat.
---

# Skill: Ingest

Compile a source into the vault's wiki layer. A single ingest should touch multiple pages — that compounding is the point. Re-deriving knowledge from raw sources on every query is RAG; the wiki layer exists so the synthesis is already there.

---

## Setup

The wiki lives at `AI-Workshop/Projects/Wiki/`. Sources you keep in the vault live in `Reference/`; bulk sources for the KB drop into the machine-local `AI-Workshop/mcp-servers/kb/sources/` folder. When the user says to ingest something, confirm the source path before reading.

---

## Process

### 1. Read the source

Read the full file. For PDFs or long documents, use the `pages` parameter on Read and take notes as you go through sections. The goal is not a summary — it's extraction: what is here that's worth keeping and cross-referencing?

### 2. Identify what matters

Before writing anything, surface to the user:
- **Entities** — named people, projects, tools, organizations
- **Concepts** — recurring ideas, frameworks, techniques
- **Key claims** — assertions, findings, data worth preserving
- **Contradictions** — anything that conflicts with existing vault content

One sentence each. Confirm emphasis before writing. The user knows what's important; get their signal before filing.

### 3. Write the summary page

Create `AI-Workshop/Projects/Wiki/<source-slug>.md`:

```markdown
---
type: source-summary
source: Reference/<filename>
ingested: <YYYY-MM-DD>
tags: [<relevant tags>]
---

# <Title>

## Key Points
<3–7 bullet points — the claims and facts worth keeping>

## Entities
[[entity-name]] — one per line, wikilinked

## Concepts
[[concept-name]] — one per line, wikilinked

## Contradictions / Open Questions
<conflicts with other vault content, or questions this source raises>
```

### 4. Update related wiki pages

For each entity and concept identified in Step 2:
- **Page exists:** add a new section or integrate the new information. Add a backlink `[[source-slug]]` where the connection is substantive.
- **No page:** create a stub at `AI-Workshop/Projects/Wiki/<slug>.md` with a one-line definition and a backlink to the summary.

Don't be conservative. If a source substantively informs a concept, that concept page should reflect it. A single ingest touching 5–10 pages is normal.

### 5. Update content_index.md

Open `Context/Maps/content_index.md`. Add a row under **Sources**:

```
| [[source-slug]] | <one-line description> | <YYYY-MM-DD> |
```

Add rows under **Concept Pages** or **Entity Pages** for any new pages created in Step 4.

### 6. Log the operation

Append to `Context/History/log.md`:

```
## [<YYYY-MM-DD>] ingest | <Source Title>
Pages touched: <comma-separated list of pages created or updated>
```

---

## Done When

- Summary page exists at `AI-Workshop/Projects/Wiki/<source-slug>.md`
- Every identified entity and concept has a wiki page (new or updated)
- `Context/Maps/content_index.md` has a row for the source and any new pages
- `Context/History/log.md` has a new entry

---

## Output to User

After completing: one-paragraph summary of what was filed, a list of pages created vs. updated, and any contradictions or open questions worth acting on.
