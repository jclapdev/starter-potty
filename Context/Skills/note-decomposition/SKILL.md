---
name: note-decomposition
description: Breaks a monolithic note into focused child files and replaces extracted content with wikilinks. Use this skill whenever a note is getting too long to scan, has repeating structured blocks that should each be their own file, or the user asks to "split this note", "break this out into separate files", or "decompose" a document. Do not skip the clarifying questions in Step 1 — jumping straight to file creation without confirming the extraction unit, output folder, format template, and replacement pattern is the most common failure mode.
---

# Skill: Note Decomposition

**Purpose:** Break a monolithic note into a set of focused child files, each covering one logical unit, and replace the extracted content in the parent with wikilinks. Keeps notes navigable as they grow.

---

## When to Use

- A note has repeating structured blocks (e.g. one block per connector, per system, per vendor) that are getting too long to scan
- A section has grown to the point where it belongs in its own file
- You are reorganizing a project and want to split responsibilities across multiple notes

---

## Process

### Step 1 — Understand the structure before touching anything

Read the full parent note. Before writing a single file, confirm all four of the following:

- The **extraction unit** — what is one child file? (e.g. one connector, one system, one vendor). Ask the user if it isn't obvious.
- The **output folder** — where will the child files live? Ask if not specified.
- An **existing example**, if one exists. If the user has already done one manually, read it and use it as the format template. Do not invent a format when a reference exists.
- The **replacement pattern** — what stays in the parent after extraction? (typically a wikilink, possibly with a short label or connector type line)

All four must be clear before proceeding to Step 2. If any are missing, ask — do not guess and proceed.

**Done when:** All four items confirmed (extraction unit, output folder, format template, replacement pattern). No ambiguity remains that would require stopping mid-extraction to ask.

### Step 2 — Audit before extracting

Before creating any files, scan for issues in the source material:
- Duplicate heading levels (e.g. `###### ######`)
- Copy-paste errors (fields that are identical when they shouldn't be — same table name for different tasks, wrong linked references)
- Broken wikilink syntax (e.g. `[[file]|label]` instead of `[[file|label]]`)
- References that look wrong in context (a connector doc pointing at an unrelated connector)

Flag all issues found. Fix safe ones (syntax errors, double headings) automatically. For ambiguous ones (wrong table names, wrong references), ask before changing.

**Done when:** Full source note scanned. All issues found, either fixed automatically or listed for user decision. No unresolved ambiguities that would cause errors during extraction.

### Step 3 — Create child files

For each extraction unit:
1. Name the file after the logical unit (e.g. `ServiceNow CMDB.md`, `Adobe Sign.md`) — not after the connector type or table
2. Apply the format template from Step 1 consistently across all files:
   - Same header structure
   - Same field order (Task → Table → Agent → Doc reference)
   - Same wikilink format (`[[filename|Display Name]]`, never bare `[[filename]]`)
   - Connector Type line present in every file
3. Write all child files before editing the parent

**Done when:** Every child file is written to disk. Zero child files still pending or partially written. The parent note is unchanged.

### Step 4 — Update the parent note

Replace each extracted section with a wikilink (or a short labeled entry + wikilink if the parent needs to remain scannable). Keep enough structure in the parent that it still functions as a navigation index — don't reduce it to a flat list of links with no context.

**Done when:** Every extracted section in the parent is replaced with the appropriate wikilink or labeled entry. Parent note still readable as a navigation index. No extracted content remains in the parent as raw text.

### Step 5 — Format check

After all files are written, verify every child file against the format template:
- `## Tasks` header present
- `Connector Type:` line present (or appropriate equivalent)
- All list items indented consistently
- All wikilinks have display names
- No broken bracket syntax

Fix any that don't match before reporting done.

**Done when:** Every child file verified against the format template. All mismatches fixed. No file has a missing required section, broken wikilink syntax, or inconsistent indentation.

### Step 6 — Report

Summarize:
- Files created and what each contains
- Issues found during audit (fixed vs. flagged)
- Anything left unresolved that needs the user's input

**Done when:** Report delivered. All created files listed. All flagged issues communicated. No unresolved items unknown to the user.

---

## Constraints

- Always read an existing example before creating new files. Format consistency matters more than your default preferences.
- Never silently fix a data issue (wrong table name, wrong reference). Flag it and ask unless the fix is unambiguous from context.
- Do not reduce the parent note to just a list of wikilinks if the parent is also used as a navigation index. Preserve enough structure to stay useful.
- If the extraction unit is ambiguous, ask — don't guess and create 30 files that need to be redone.
