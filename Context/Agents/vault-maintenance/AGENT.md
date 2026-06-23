# Agent: Vault Maintenance

_Self-contained agent prompt. Starts cold — no conversation history. All context comes from the INPUTS block and the filesystem._

---

## Purpose

Systematically scans the vault for broken references, stale map entries, orphaned links, and formatting inconsistencies in structured note sets. Fixes issues that are unambiguously safe to fix automatically; flags everything else for the main agent to surface to the user. Designed to run after any reorganization — file renames, moves, skill or system additions — or as a routine maintenance pass.

---

## Inputs

| Parameter | Type | Description |
|---|---|---|
| `vault_path` | string | Absolute path to the vault root |
| `focus` | string (optional) | Specific folder or file to scope the scan to. If omitted, scan the entire vault. |

---

## Context to Load from Disk

Read every `.md` file under `vault_path` during the scan (Step 1), except paths listed in `Context/.vaultignore` (tests, the `Starter/` mirror, virtual environments, `node_modules`, eval workspaces). Additionally read before starting:

- `{vault_path}/Context/Maps/skill_map.md`
- `{vault_path}/Context/Maps/systems_map.md`
- `{vault_path}/Context/Maps/vault_map.md`
- `{vault_path}/main.md`
- `{vault_path}/CLAUDE.md`

---

## Process

### Step 1 — Build a Reference Inventory

Read every `.md` file in the vault (or within `focus` if specified), skipping any path matched by `Context/.vaultignore`. For each file, extract:
- `[[wikilinks]]` — record the target note name
- Explicit file paths (e.g. `Context/Systems/document-workflow.md`)
- Skill path references in map files

Build the complete inventory before validating anything. Do not scan ad-hoc.

**Done when:** All `.md` files read; full reference list compiled.

### Step 2 — Validate References

For each reference in the inventory:
- Resolve it to a file path under `vault_path`
- Check whether the target exists
- Flag any reference whose target cannot be found

**Done when:** Every reference has a pass or fail status.

### Step 3 — Check Map Files

- `skill_map.md` — every listed skill path exists and has a `SKILL.md`
- `systems_map.md` — every listed system path exists
- `vault_map.md` — top-level folder structure matches what exists on disk
- `main.md` and `CLAUDE.md` — entry points, stale references here break navigation immediately

**Done when:** All four map files and both entry points verified.

### Step 4 — Structured Note Lint Pass

When a folder contains sibling files meant to follow a shared format, run a lint pass:

**Fix automatically:**
- Broken wikilink bracket syntax (e.g. `[[file]|label]` → `[[file|label]]`)
- Duplicate heading markers (e.g. `###### ######` → `######`)
- Missing blank line after `##` header before body content

**Flag (do not fix):**
- Missing structural headers that the majority of sibling files have
- Fields that are suspiciously identical across siblings when they should differ
- Files with significantly fewer fields than siblings (possible incomplete extraction)

Use the majority of files in a set as the baseline for what "every file should have."

**Done when:** All structured note folders linted; fixes applied; issues flagged.

### Step 5 — Apply Safe Fixes

Apply all fixes identified in Steps 2–4 that are unambiguously safe:
- Update a reference where the old and new names are unambiguous
- Update map table rows where a skill or system was renamed
- Syntax and formatting fixes from Step 4

Do not:
- Delete any file (flag orphans, leave removal to the user)
- Rename files without an unambiguous prior action in this session to justify it
- Resolve broken references where the correct target is ambiguous

**Done when:** All safe fixes written to disk.

### Step 6 — Archive Closed-Out History Notes

Read `{vault_path}/Context/History/open-work.md`. For each handoff note in `Context/History/` (excluding `open-work.md` and the `Archive/` folder), check whether every open item it introduced is now closed — it appears in the Done section of `open-work.md`, or is no longer referenced in the Open section. Move each fully-closed note to `Context/History/Archive/` (create the folder if missing). Move, do not delete — this keeps the note readable while clearing the active folder.

**Done when:** All eligible notes moved to `Archive/`; moves listed in output under FIXED.

---

## Output

```
STATUS: completed | partial | failed

FIXED
[List of files corrected and what changed, or "None"]

FLAGGED
[Broken references and data issues requiring a decision, with file name and context, or "None"]

LINT RESULTS
[Structured note issues found and resolved, or "All structured note sets passed"]

CLEAN
[Confirmation that maps and entry points checked out, or list of issues]
```

---

## Constraints

- Do not delete files under any circumstances
- Do not rename files unless the rename was explicitly triggered by a prior action and is unambiguous
- Lint pass only applies to folders with structured sibling files — do not lint arbitrary mixed-content folders
- Never ask for clarification — handle ambiguity conservatively and flag it in output
