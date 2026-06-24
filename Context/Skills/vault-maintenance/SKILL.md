---
name: vault-maintenance
description: Scans the vault for broken references, stale map entries, orphaned links, and formatting inconsistencies in structured note sets. Use this skill after renaming files or folders, after deleting a file, after any note decomposition pass, or whenever the user asks to "run vault maintenance", "check for broken links", or "do a full scan." Also run proactively at session start if the vault hasn't been maintained recently.
---

# Skill: Vault Maintenance

**Purpose:** After any reorganization — renaming files, moving folders, adding or removing skills or systems — scan the vault for broken references, stale map entries, orphaned links, and formatting inconsistencies in structured note sets. Fix what can be fixed automatically; flag what needs a decision.

---

## When to Run

- After renaming any file that other files are likely to reference (systems, skills, maps)
- After moving a folder
- After deleting a file
- After any note decomposition pass (splitting a monolithic note into child files)
- Proactively at the start of a session if the vault hasn't been maintained recently

---

## Process

### 1. Build a reference inventory

This is a systematic scan, not a spot-check. Read every `.md` file in the vault — except paths listed in `Context/.vaultignore` (tests, the `Starter/` mirror, virtual environments, `node_modules`, eval workspaces) — and extract:
- `[[wikilinks]]` — record the target note name from each occurrence
- Explicit file paths (e.g. `Context/Systems/document-workflow.md`)
- Skill path references in `skill_map.md` and `systems_map.md`

Build a complete list before validating anything. Skipping files or scanning ad-hoc will miss stale references in less-visited corners of the vault.

### 2. Validate each reference

For each reference found:
- Check whether the target file exists at the expected path
- Flag any reference where the target cannot be found

### 3. Check map files

- `Context/Maps/skill_map.md` — verify every listed skill path exists and has a `SKILL.md`
- `Context/Maps/systems_map.md` — verify every listed system path exists
- `Context/Maps/vault_map.md` — verify top-level folder structure matches reality

Pay special attention to `main.md` and `CLAUDE.md` — they are entry points and stale references there break navigation immediately.

### 4. Structured note lint pass

When a folder contains a set of files that are meant to follow a shared format (e.g. `Tasks_by_Connector/`, a set of system files, a set of connector guides), run a lint pass across all files in the set:

**Detect and fix automatically:**
- Broken wikilink bracket syntax (e.g. `[[file]|label]` → `[[file|label]]`)
- Duplicate heading markers (e.g. `###### ######` → `######`)
- Bare wikilinks with no display name (e.g. `[[file.pdf]]` → `[[file.pdf|File Name]]`) — infer display name from filename; flag if ambiguous
- Missing blank line after `##` header before body content

**Detect and flag (do not fix without confirmation):**
- Missing structural headers that every file in the set should have (e.g. `## Tasks`, `Connector Type:`) — flag which files are missing them
- Fields that are suspiciously identical across sibling files when they should differ (e.g. same table name for different tasks)
- References that are inconsistent with the file's subject (e.g. a Microsoft 365 task referencing an Adobe Sign PDF)
- Files in the set with significantly fewer fields than siblings (possible incomplete extraction)

To determine what "every file in the set should have," use the majority of files as the baseline. If 12 of 15 files have a `Connector Type:` line, the 3 that don't are flagged.

### 5. Map accuracy checklist

This is the canonical map-accuracy check — `session-lifecycle`'s Map Update Rule and the `wrap-up` agent both defer here rather than restating their own. Verify that the three map files are complete and accurate:

**`Context/Maps/skill_map.md`**
- Every folder in `Context/Skills/` that contains a `SKILL.md` appears as a row in this table
- Every path listed in the table resolves to a real file on disk
- No rows reference skills that no longer exist

**`Context/Maps/systems_map.md`**
- Every file in `Context/Systems/` appears as a row in this table
- Every path listed in the table resolves to a real file on disk

**`Context/Maps/vault_map.md`**
- Top-level folder structure matches what actually exists on disk
- Key files listed in the file references section exist at their stated paths

Fix map rows that are clearly wrong (missing entry, stale path). Flag anything ambiguous.

**Done when:** All three maps verified. Discrepancies either fixed automatically or listed under Flagged.

### 6. Old-note cleanup pass

Check `Context/History/` for handoff notes that are eligible to be archived:

A note is eligible when every open item it introduced is now closed (appears in the Done section of `open-work.md`, or is not referenced at all in the Open section).

Process:
1. List all `.md` files in `Context/History/` excluding `open-work.md`
2. For each note, identify any open-work items it mentions or introduced
3. Cross-reference with the current Open section of `open-work.md`
4. Flag notes where all associated items are now closed — do not archive automatically, just surface them

Do not delete notes. Move eligible notes to `Context/History/Archive/` (create the folder if it doesn't exist) and list what was moved in the report. Moving rather than deleting keeps them readable while clearing the active `History/` folder.

**Done when:** All notes checked. Eligible notes moved to `Archive/` and listed in the report.

### 7. Skill eval currency check _(optional — run when explicitly requested or when skills have changed)_

For each skill in `Context/Skills/`, check whether it has a corresponding workspace directory (`Tests/<skill>-workspace/`) and when that workspace was last updated relative to the skill's own `SKILL.md`.

A skill's evals are considered stale if:
- No workspace directory exists (never evaluated), OR
- `SKILL.md` has been meaningfully modified since the last eval run in the workspace

Flag stale skills in the report. Do not run evals automatically — just surface which skills need attention and recommend running skill-creator for each.

This step folds in the periodic eval cycle: rather than a separate scheduled pass, currency is checked as part of vault maintenance and acted on when the user is ready.

**Done when:** All skills checked. Stale eval candidates listed in the report with last-eval date (or "never evaluated").

### 8. Semantic wiki health check _(optional — run when explicitly requested or when the wiki layer has grown)_

Scan `AI-Workshop/Projects/Wiki/` for content-level issues that structural maintenance won't catch:

**Contradictions** — find pages that make conflicting claims about the same entity or concept. Flag them with both page names and the specific conflict.

**Stale claims** — check recent `Context/History/log.md` entries for ingests; if a new source supersedes an older claim on an existing page, flag which page needs updating.

**Orphan wiki pages** — pages in `AI-Workshop/Projects/Wiki/` that are not linked from any other page and do not appear in `Context/Maps/content_index.md`. Surface them; don't delete.

**Missing concept pages** — concepts mentioned by name across multiple wiki pages but lacking their own dedicated page. Flag as stubs to create.

**Missing cross-references** — two pages that clearly relate (share entities, reference the same events, make related claims) but don't link to each other.

**Data gaps** — open questions or contradiction flags recorded in source-summary pages (the "Contradictions / Open Questions" section) that haven't been resolved. Surface them as candidates for new sources or research.

Fix nothing automatically in this step. Output a flagged list only.

**Done when:** All wiki pages checked. Findings listed under Flagged in the report.

---

### 9. Fix automatically where safe

Safe fixes (make without asking):
- Update a reference where the old name and new name are unambiguous (e.g. file was renamed with only one match in the vault)
- Update map table rows where a skill or system was renamed
- Syntax and formatting fixes listed in Step 4

Unsafe fixes (flag for user decision):
- Broken references where the correct target is ambiguous
- Orphaned files — files that exist but are referenced nowhere
- Missing files that are referenced but don't exist (may need to be created)
- Data inconsistencies identified in the lint pass

### 10. Report

Output a summary with these sections:
- **Fixed** — what was corrected automatically, with file names
- **Flagged** — broken references, map discrepancies, data issues, and semantic health findings requiring a decision, with enough context to act
- **Lint results** — structured note issues found and resolved, or confirmation that all sets passed
- **Wiki health** — semantic issues found (only if Step 8 was run): contradictions, orphans, stale claims, data gaps
- **Archive candidates** — handoff notes eligible to be collapsed, with reason (all items closed)
- **Stale evals** — skills whose evals are overdue (only if Step 7 was run)
- **Clean** — confirmation that maps and links checked out if no issues found

If Step 8 was run, append to `Context/History/log.md`:
```
## [<YYYY-MM-DD>] lint | vault-maintenance semantic pass
Issues found: <count> | Pages checked: <count>
```

---

## Constraints

- Do not delete files. Flag orphans but leave removal to the user.
- Do not rename files without confirming with the user unless the rename is unambiguous and was explicitly triggered by a prior action in the same session.
- The lint pass only applies to folders that contain a structured set of sibling files. Do not lint arbitrary mixed-content folders as if they share a schema.
