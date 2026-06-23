# Agent: Handoff Writer

_Self-contained agent prompt. Starts cold — no conversation history. All context comes from the INPUTS block and the filesystem._

---

## Purpose

Writes the session handoff note to `Context/History/`. Separates the act of synthesizing what happened (done by the main agent or wrap-up agent, which have context) from the act of writing the file (mechanical, no context needed). Keeping this isolated means the handoff file is always written consistently, regardless of which agent or skill triggers it.

---

## Inputs

| Parameter | Type | Description |
|---|---|---|
| `vault_path` | string | Absolute path to the vault root |
| `session_date` | string | YYYY-MM-DD |
| `session_slug` | string | Short kebab-case label for the filename (e.g. `agent-architecture-build`) |
| `what_was_built` | string | Narrative description of files created, changed, and why |
| `decisions_made` | string | Key decisions and the reasoning behind them |
| `in_progress` | string | Anything half-built or explicitly flagged as incomplete, or "Nothing half-built" |
| `next_steps` | string | Top 3–5 open items from open-work.md, in priority order |

---

## Context to Load from Disk

None required — all content is passed via inputs.

---

## Process

### Step 1 — Construct the Handoff Note

Assemble the note using the template below. Use the inputs verbatim where provided — do not paraphrase or summarize further. The main agent or wrap-up agent already did the synthesis; this agent's job is faithful transcription.

```markdown
# Session Handoff — {session_date} — {session_slug_as_title}

---

## What Was Built

{what_was_built}

---

## Decisions Made

{decisions_made}

---

## In Progress

{in_progress}

---

## Next Steps

See `open-work.md`. Priority order as of this session:
{next_steps}
```

For `session_slug_as_title`: convert kebab-case to Title Case (e.g. `agent-architecture-build` → `Agent Architecture Build`).

**Done when:** Note content assembled.

### Step 2 — Write the File

Write the note to `{vault_path}/Context/History/{session_date}-{session_slug}.md`.

Create the directory if it does not exist (it should already exist).

**Done when:** File written and confirmed at the correct path.

---

## Output

```
STATUS: completed | failed

HANDOFF FILE
Path: Context/History/{session_date}-{session_slug}.md
```

---

## Constraints

- Write only to `{vault_path}/Context/History/`
- Do not modify any other file
- Do not interpret or condense the input fields — write them as provided
- If a file already exists at the target path, overwrite it (this handles re-runs)
