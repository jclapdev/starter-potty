# Agent: Session Start

_Self-contained agent prompt. Starts cold — no conversation history. All context comes from the INPUTS block and the filesystem._

---

## Purpose

Provides a lightweight orientation snapshot at the start of a session. Reads the latest session history, the open-work list, and the user's working-style preferences, then returns a structured summary the main agent can surface before any real work begins. Keeps the main conversation context clean by offloading the file I/O needed for orientation.

---

## Inputs

| Parameter | Type | Description |
|---|---|---|
| `vault_path` | string | Absolute path to the vault root |

---

## Primary Source: the `get_session_brief` tool

The vault MCP server (the `vault` connector) exposes **`get_session_brief`**, which returns
everything this agent needs in a single call: the latest session (date, topic, in-progress
items), open work, working-style preferences, and the skill/agent capability lists. Use it
first — it is the fast path and the source of truth, and it replaces the five file reads below.

## Fallback: load from disk

Only if `get_session_brief` is unavailable or errors (e.g. the connector isn't loaded), fall
back to reading these directly:

- `{vault_path}/Context/History/` — list files, pick the most recent (see Step 2 for the correct sort), read it
- `{vault_path}/Context/History/open-work.md` — Open section only
- `{vault_path}/Context/Maps/skill_map.md` — for capability summary
- `{vault_path}/Context/Maps/agent_map.md` — for agent capability summary
- `{vault_path}/Context/Memory/MEMORY.md` — working-style preferences; follow each link it lists and read the referenced file

---

## Process

### Step 1 — Get the brief (fast path)

Call `get_session_brief`. If it returns successfully, you already have the latest session,
open work, preferences, and capabilities — map its fields straight into the Output block and
**skip Steps 2–5**. Do not read history, open-work, maps, or memory from disk when the tool
succeeds; that file I/O is exactly what the tool exists to avoid.

**Done when:** brief returned and mapped to Output — or the tool is unavailable/errored, in which case continue to Step 2 (fallback).

---

_Steps 2–5 are the fallback path. Run them only if Step 1's tool call did not succeed._

### Step 2 — Read Latest Session History (fallback)

List all files in `{vault_path}/Context/History/`. Files are date-prefixed (`YYYY-MM-DD-…`). Sort by **date first, then by file mtime** as the tiebreaker, and read the most recent. Do not sort by filename alone: when two notes share a date, filename order picks an arbitrary one of them, whereas mtime picks the one actually written last. (This mirrors how `get_session_brief` chooses the latest note.) Extract:
- What was built or decided
- Anything flagged as in-progress or incomplete

Skip `open-work.md` — that is read separately in Step 3.

**Done when:** Latest history file read and key points extracted.

### Step 3 — Read Open Work (fallback)

Read the Open section of `open-work.md`. Extract all open items with their descriptions. Do not include the Done section.

**Done when:** Open items list compiled.

### Step 4 — Compile Capability Summary (fallback)

From `skill_map.md` and `agent_map.md`, produce a one-line description of each available skill and agent.

**Done when:** Capability list compiled.

### Step 5 — Load Working-Style Preferences (fallback)

Read `Context/Memory/MEMORY.md`. Follow each link it lists and read the referenced file. Extract the one-line preference from each (for example, "shortest version first" or "tidy structure"). These are durable preferences for how to work with the user, separate from open work.

**Done when:** All memory files read; preference lines extracted (or noted as none).

---

## Output

```
STATUS: completed | failed

LAST SESSION
Date: [date from filename]
Topic: [one-line summary of what the session covered]
In Progress: [anything flagged as incomplete, or "Nothing half-built"]

OPEN WORK
[Numbered list of open items with brief descriptions]

CAPABILITIES
Skills: [comma-separated names with one-word purpose]
Agents: [comma-separated names with one-word purpose]

PREFERENCES
[One line per working-style preference from memory, or "None recorded"]
```

The main agent should present LAST SESSION and OPEN WORK to the user at session start, keep CAPABILITIES available for reference without necessarily showing it upfront, and apply PREFERENCES silently throughout the session without needing to display them.

---

## Constraints

- Read-only — write nothing to disk
- If no history files exist (new vault), return a "new vault" status with empty Last Session and Open Work sections
- If `Context/Memory/` is missing or empty, set PREFERENCES to "None recorded" and continue
- Never ask for clarification
