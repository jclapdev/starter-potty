---
name: vault-maintenance
description: Scans the vault for broken references, stale map entries, orphaned links, and formatting inconsistencies via the vault_health tool. Use this skill after renaming files or folders, after deleting a file, after any note decomposition pass, or whenever the user asks to "run vault maintenance", "check for broken links", or "do a full scan." Also run proactively at session start if the vault hasn't been maintained recently.
---

# Skill: Vault Maintenance

**Purpose:** After any reorganization (renaming files, moving folders, adding or removing skills or systems), check the vault for broken references, stale map entries, orphaned links, and formatting inconsistencies. Fix what is safe to fix; flag what needs a decision.

The scan itself is deterministic and lives in the vault MCP server's `vault_health` tool. Never read vault files to hunt for problems yourself; one tool call covers every note, map, and entry point at near-zero cost. This skill is the judgment layer on top of the report.

---

## When to Run

- After renaming any file that other files are likely to reference (systems, skills, maps)
- After moving a folder
- After deleting a file
- After any note decomposition pass (splitting a monolithic note into child files)
- Proactively at the start of a session if the vault hasn't been maintained recently

---

## Process

### 1. Get the report

Call the `vault_health` tool (vault MCP server). It returns:

- **broken_links**: wikilinks and path references that resolve to nothing
- **orphans**: notes with no inbound links (entry points already exempted)
- **map_check**: map rows whose path is gone, real skills/agents/systems missing from their map, and vault_map structure drift
- **lint**: format problems with exact file and line, plus files missing headers that most of their sibling notes have
- **archive_candidates**: history notes no longer referenced in the Open section of open-work.md

If the tool is unavailable, the vault connector is not running. Tell the user the fix (run `python AI-Workshop/install.py`, then fully quit and restart Claude) and stop. Do not fall back to scanning files by hand.

### 2. Apply safe fixes

Safe fixes (make without asking):

- Update a reference where the old and new names are unambiguous (one clear match in the vault)
- Update map table rows where a skill or system was renamed or its path is stale with one clear match
- Lint findings from the report (the report gives file, line, and issue)

Unsafe (flag for the user, do not fix):

- Broken references where the correct target is ambiguous
- Orphaned files (surface them; leave removal to the user)
- Missing files that are referenced but don't exist (may need to be created)
- Sibling-header flags (possible incomplete notes; content judgment, not formatting)

### 3. Archive eligible history notes

For each archive candidate, confirm the heuristic holds: the note's open items are genuinely closed, not just unmentioned. Move confirmed notes to `Context/History/Archive/` (create the folder if missing). Move, never delete. Leave and flag any candidate that still looks active.

### 4. Report

Output a summary with these sections:

- **Fixed**: what was corrected, with file names
- **Flagged**: findings requiring a decision, with enough context to act
- **Archived**: history notes moved to `Archive/`
- **Clean**: confirmation that links, maps, and entry points checked out, if nothing was found

---

## Optional Deep Passes (run only when explicitly requested)

### Skill eval currency

For each skill in `Context/Skills/`, check whether it has a workspace directory (`Tests/<skill>-workspace/`) and when that workspace was last updated relative to the skill's own `SKILL.md`. A skill's evals are stale if no workspace exists (never evaluated) or `SKILL.md` changed meaningfully since the last eval run. Flag stale skills and recommend running skill-creator for each; do not run evals automatically.

### Semantic wiki health

Scan `AI-Workshop/Projects/Wiki/` for content-level issues the structural report can't catch: contradictions between pages, claims superseded by newer ingests (check recent `Context/History/log.md` entries), orphan wiki pages missing from `Context/Maps/content_index.md`, concepts mentioned across pages that lack their own page, missing cross-references between clearly related pages, and unresolved items in "Contradictions / Open Questions" sections. Fix nothing in this pass; output a flagged list only.

If this pass runs, append to `Context/History/log.md`:

```
## [<YYYY-MM-DD>] lint | vault-maintenance semantic pass
Issues found: <count> | Pages checked: <count>
```

---

## Constraints

- Do not delete files. Flag orphans but leave removal to the user.
- Do not rename files without confirming with the user unless the rename is unambiguous and was explicitly triggered by a prior action in the same session.
- Never scan vault files to find structural problems; that is the `vault_health` tool's job. The optional deep passes above are the only file-reading this skill does.
