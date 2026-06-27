---
name: status
description: On-demand read-only snapshot of everything — what skills are available, what happened last session, and what's still open. Trigger this skill whenever the user says "status", "what can you do?", "what's open?", "where were we?", "give me a rundown", "what's outstanding?", or any phrase asking for a current-state summary. Also trigger when the user asks what skills or capabilities are available, even if they don't say "status" explicitly. Do not trigger at session start automatically — only on explicit request.
---

# Skill: Status

**Purpose:** Give an instant orientation snapshot — what this system can do, where we left off, and what's still open. Read-only. No files are created or modified.

---

## Process

### Step 1 — Get the Brief

Call `get_session_brief` from the vault MCP server (the `vault` connector). It returns last session, open work, preferences, and capabilities (skills + agents) in one call.

**Done when:** Brief returned successfully. If the tool is unavailable, fall back to reading `Context/Maps/skill_map.md`, the most recent file in `Context/History/` (exclude `open-work.md`), and `Context/History/open-work.md` separately.

### Step 2 — Report

Output a single structured report using exactly this format:

---
**Skills available**
- `skill-name` — one-line purpose
_(list all from capabilities.skills; no extra commentary)_

**Last session** _(skip if last_session is null)_
Two to four sentences: what was built, decisions made, stated next steps. Source: last_session from the brief.

**Open work**
- **Item name** — one-sentence summary
_(all items from open_work, in order)_
---

**Done when:** Report is presented. Stop — do not take any follow-up action unless the user asks.

---

## Constraints

- Read-only. Do not write, edit, or move any file.
- Do not add commentary, recommendations, or priorities unless the user asks.
- If last_session is null, skip the "Last session" section and say so.
