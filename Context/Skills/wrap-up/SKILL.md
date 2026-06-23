---
name: wrap-up
description: End-of-session orchestrator that reviews the conversation, surfaces improvements, updates maps and open work, and writes a session handoff. Triggers immediately when the user says "wrap up", "let's wrap", "we're done", "end of session", "close out", or any clear equivalent. Do not wait for an explicit skill invocation — if the phrase signals session end, run this skill.
---

# Skill: Wrap-Up

**Purpose:** Systematically close out a conversation or task by running all end-of-session skills in the correct order and surfacing any improvements identified during the session.

---

## Process

Run the following steps in sequence. Do not skip steps — each one depends on the session being fresh in context.

### Step 1 — Conversation Review

Review the full conversation for:
- Anything that went wrong or required correction (approach taken, output format, missing context)
- Anything that worked well and should be repeated
- Patterns that suggest a missing skill, a gap in an existing skill, or a needed adjustment to a system rule or `main.md`

For each finding, categorize it as one of:
- **New skill candidate** — a repeatable process that doesn't have a skill yet
- **Skill improvement** — an existing skill that needs updating
- **System rule change** — a rule in `Context/Systems/` that needs adding or amending
- **main.md adjustment** — a preference or behavior in `main.md` that needs updating

Present all findings to the user — including obvious factual corrections to vault files. Do not apply any change before the user has seen it and approved it. Self-approving a finding, even a minor one, skips the point of this step.

**Done when:** All findings are presented, user has approved or rejected each one, and no unresolved discussion remains.

### Step 2 — Spawn Wrap-Up Agent

Once the user has approved (or rejected) all findings from Step 1, compile the following and spawn the wrap-up agent (`Context/Agents/wrap-up/AGENT.md`):

- `approved_changes` — the list of approved changes with type, file path, and content/diff
- `session_summary` — a narrative of what was built or decided this session
- `open_work_changes` — items to add, edit, close, or remove from open-work.md
- `session_date` — today's date (YYYY-MM-DD)
- `session_slug` — a short kebab-case label for the handoff filename

The agent handles Steps 2–5 (apply changes, vault-maintenance, update maps, update open-work, write handoff) in isolation. When it returns, surface any flagged issues to the user.

**Done when:** Wrap-up agent returns STATUS: completed or partial. Any flagged issues presented to user.

---

## Constraints

- Never create or edit files in Step 1 — surface findings first, build only after the user approves.
- If nothing meaningful happened in the session, say so and skip Steps 2–4.
- Keep the handoff note tight. Readable in under two minutes.
