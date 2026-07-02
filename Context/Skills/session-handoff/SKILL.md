---
name: session-handoff
description: Writes an end-of-session handoff note and reads it at session start. Use this skill whenever the user says they're done for the day, asks to "write up the handoff", or starts a new session and asks what was left off. Also invoked automatically as the final step of the wrap-up skill. At session start, always read the most recent handoff before beginning any non-trivial task.
---

# Skill: Session Handoff

**Purpose:** At the end of a working session, write a handoff note to `Context/History/` capturing what was built and any decisions that aren't obvious from the files alone. At the start of a new session, read the most recent handoff note to start warm.

---

## When to Run

- **End of session:** any time a meaningful amount of work was done — new files created, systems changed, skills added, decisions made.
- **Start of session:** read the most recent file in `Context/History/` before starting any non-trivial task, if one exists.

---

## End-of-Session Process

1. **Review what changed this session** — scan files modified or created, and recall decisions made in conversation that aren't captured in the files themselves.

2. **Reconcile `Context/History/open-work.md` first** — this must happen before writing the handoff note, not after. `open-work.md` is the single source of truth for outstanding work. Check off anything completed this session (move it to the Done section), carry forward anything still open, and add any new open items that came up. The handoff note will point to it, so it needs to be accurate first.

3. **Write a handoff note** to `Context/History/` named `YYYY-MM-DD-<short-slug>.md` (e.g. `2026-06-11-context-system-setup.md`).

4. **The note must include:**

   ### What Was Built
   List files created or significantly edited, with paths and one-line descriptions.

   ### Decisions Made
   Any choices made during the session that aren't self-evident from reading the files — naming conventions chosen, approaches rejected, tradeoffs accepted.

   ### Next Steps
   Concrete actions for the next session, if any were identified.

5. **Keep it tight.** The note should be readable in under two minutes. No padding.

---

## Start-of-Session Process

1. List files in `Context/History/` sorted by date.
2. Read the most recent one.
3. If a "Next Steps" section is present, flag it to the user before starting the new task.

---

## Constraints

- Do not summarize conversation transcript — capture decisions and state, not dialogue.
- Do not duplicate information already clear from reading the files themselves.
- If nothing meaningful happened in a session, skip the handoff note.
