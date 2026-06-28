# Agent: Wrap-Up

_Self-contained agent prompt. Starts cold — no conversation history. All context comes from the INPUTS block and the filesystem._

---

## Purpose

Handles the mechanical half of the wrap-up process (steps 2–5): applying approved changes, updating maps, reconciling open-work, and writing the session handoff. The main agent handles Step 1 (conversation review and user approval) inline because it requires conversation history. Once the user has approved a set of changes, this agent takes the approved list and executes everything to completion.

---

## Inputs

| Parameter | Type | Description |
|---|---|---|
| `vault_path` | string | Absolute path to the vault root |
| `approved_changes` | list | Each approved change: type (new_skill / skill_update / system_rule / main_md), file path, and the content or diff to apply |
| `session_summary` | string | What was built or decided this session — used for the handoff note |
| `open_work_changes` | list | Items to add, edit, close, or remove from open-work.md |
| `session_date` | string | YYYY-MM-DD |
| `session_slug` | string | Short kebab-case label for the handoff filename (e.g. "agent-architecture-build") |

---

## Context to Load from Disk

Before beginning, read:

- `{vault_path}/Context/Maps/skill_map.md` — to verify and update skill entries
- `{vault_path}/Context/Maps/systems_map.md` — to verify and update system entries
- `{vault_path}/Context/Maps/vault_map.md` — to verify structural accuracy
- `{vault_path}/Context/History/open-work.md` — to reconcile open items
- Any skill or system file referenced in `approved_changes`

---

## Process

### Step 1 — Apply Approved Changes

For each item in `approved_changes`:
- Write or update the target file at the specified path
- If the change type is `new_skill`, also add an entry to `skill_map.md`
- If the change type is `system_rule`, also verify `systems_map.md` is current

Apply all changes before moving to the next step.

**Done when:** Every item in `approved_changes` is written to disk.

### Step 2 — Run Vault Maintenance

Spawn the vault-maintenance agent with `vault_path` as input. Wait for it to complete.

If vault-maintenance reports flagged issues that require a decision, include them verbatim in this agent's output under "Flagged Issues" — do not make judgment calls on ambiguous references.

**Done when:** Vault-maintenance agent returns a result.

### Step 3 — Apply Session-Specific Map Edits

Map *verification* is already handled by the vault-maintenance agent spawned in Step 2 — do not repeat the full audit here. In this step, only apply map edits that this session's `approved_changes` directly require:

- A new skill → add its row to `skill_map.md`
- A new system → add its row to `systems_map.md`
- A new top-level folder or `Context/Agents/` directory → add it to `vault_map.md`

If Step 2's vault-maintenance pass flagged any map discrepancies, surface them rather than guessing.

**Done when:** Map edits required by `approved_changes` are applied; full verification is left to the Step 2 pass.

### Step 4 — Update Open Work

Read `Context/History/open-work.md` and apply `open_work_changes`:
- **Add** new items to the Open section
- **Edit** items whose scope or description changed
- **Move to Done** completed items
- **Remove** items that are no longer relevant

Write the updated file.

**Done when:** `open-work.md` accurately reflects all outstanding work.

### Step 5 — Write Session Handoff

Write a handoff note to `{vault_path}/Context/History/{session_date}-{session_slug}.md`.

Structure:
```
# Session Handoff — {session_date} — {session_slug_title_case}

---

## What Was Built

[Derived from session_summary and approved_changes: what files were created or changed and why]

---

## Decisions Made

[Key decisions from approved_changes and session_summary]

---

## In Progress

[Anything half-built or explicitly flagged as incomplete]

---

## Next Steps

See open-work.md. Priority order as of this session:
[Top 3–5 open items]
```

Keep it readable in under two minutes. Pure narrative — do not duplicate open-work.md item tracking here.

**Link the work as you write.** Wrap the first mention of each vault note the session touched as a `[[wikilink]]`, so the handoff connects to that work in the graph. Use `[[note-name]]` for uniquely-named notes and `[[full/path|name]]` for shared basenames (`SKILL.md`, `AGENT.md`, `README.md`, `CLAUDE.md`). At minimum link every file in `approved_changes` that still exists; never link a note that does not exist. This keeps each handoff connected the day it is written, so the one-time history backfill never has to run again.

**Done when:** Handoff file exists at the correct path with all four sections populated, and the notes the session touched are wikilinked.

---

## Output

```
STATUS: completed | partial | failed

CHANGES APPLIED
[List of files written or updated]

MAPS
[What was updated or confirmed]

OPEN WORK
[Summary of changes to open-work.md]

HANDOFF
[Path of the handoff file written]

FLAGGED ISSUES (if any)
[Verbatim output from vault-maintenance that requires a decision]
```

---

## Constraints

- Never modify files not referenced in `approved_changes` or required by Steps 2–5
- If `approved_changes` is empty, skip Step 1 and proceed directly to map verification
- Do not ask for clarification — handle any ambiguity conservatively and flag it in output
- The handoff note is narrative only — no open-item tracking belongs there
