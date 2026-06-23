---
name: status
description: On-demand read-only snapshot of everything — what skills are available, what happened last session, and what's still open. Trigger this skill whenever the user says "status", "what can you do?", "what's open?", "where were we?", "give me a rundown", "what's outstanding?", or any phrase asking for a current-state summary. Also trigger when the user asks what skills or capabilities are available, even if they don't say "status" explicitly. Do not trigger at session start automatically — only on explicit request.
---

# Skill: Status

**Purpose:** Give an instant orientation snapshot — what this system can do, where we left off, and what's still open. Read-only. No files are created or modified.

---

## Process

### Step 1 — Read Source Files

Read the following in order:

1. `Context/Maps/skill_map.md` — full list of available skills
2. The most recent file in `Context/History/` (sort descending by filename; exclude `open-work.md`) — last session's focus and next steps
3. `Context/History/open-work.md` — all outstanding work

**Done when:** All three sources are read and held in context.

### Step 2 — Report

Output a single structured report using exactly this format:

---
**Skills available**
- `skill-name` — one-line purpose
- `skill-name` — one-line purpose
_(list all skills from skill_map.md; no extra commentary)_

**Last session** _(skip this section if no handoff notes exist in Context/History/)_
Two to four sentences covering: what was built, what decisions were made, and what the stated next steps were. Source: most recent handoff note.

**Open work**
- **Item name** — one-sentence summary
- **Item name** — one-sentence summary
_(list all items from the Open section of open-work.md, in the order they appear)_
---

**Done when:** Report is presented. Stop — do not take any follow-up action unless the user asks.

---

## Constraints

- Read-only. Do not write, edit, or move any file.
- Do not add commentary, recommendations, or priorities unless the user asks.
- If `Context/History/` has no handoff notes yet, skip the "Last session" section and say so.
