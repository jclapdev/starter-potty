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
- Patterns that suggest an improvement anywhere in the system: a missing or weak skill, a hook, a system or system rule, an agent, a scheduled task, or a `main.md` preference
- Any mechanism (skill or system) whose behavior changed this session and whose user guide (`Context/Guide/<name>.md`) or glossary entry is now stale. A stale guide is a broken thing, fix it this session (see the Documentation Currency Rule in [[session-lifecycle]])
- Any user-facing prose doc written or edited this session (a `Context/Guide/` page, the glossary, a `HUMAN.md`, a Wiki page, a report). Run the [[Context/Agents/prose-review/AGENT.md|prose-review]] agent over it (per [[document-workflow]] §5) and fold its rewrites into the approved fixes. The hook already caught the deterministic tells on write; this catches the judgment-layer ones it can't

For each finding, sort it into one of two kinds:

- **Broken thing.** A factual error, stale reference, broken link, or internal inconsistency with one correct fix. Not a judgment call.
- **Improvement.** Anything that would make the system work better: a new or changed skill, hook, agent, system, rule, or `main.md` preference. There is no fixed menu. If it would help, it counts.

Handle them differently:

- **Broken things get fixed this session, never just logged.** One correct fix exists, so fold it into the approved set and apply it in Step 2. Surface it as *fixed*, not proposed. If a fix can't be completed safely, attempt what you can, then name the blocker and what's needed.
- **Improvements wait for approval, and you have to earn the proposal.** Research each one first (how others handle it, official guidance) and give a concrete reason before recommending it. Present each; apply only what the user approves. Don't propose vague or unresearched changes, and don't self-approve. Machine-local memory preferences don't need approval: save them and report what you saved.

**Done when:** All findings are presented; broken-thing fixes are queued for Step 2; the user has approved or rejected each improvement; and no unresolved discussion remains.

### Step 2 — Spawn Wrap-Up Agent

Once the user has approved (or rejected) all findings from Step 1, compile the following and spawn the wrap-up agent (`Context/Agents/wrap-up/AGENT.md`):

- `approved_changes` — the list of approved changes with type, file path, and content/diff
- `session_summary` — a narrative of what was built or decided this session
- `open_work_changes` — items to add, edit, close, or remove from open-work.md
- `session_date` — today's date (YYYY-MM-DD)
- `session_slug` — a short kebab-case label for the handoff filename

The agent handles Steps 2–5 (apply changes, vault health check via the `vault_health` tool, update maps, update open-work, write handoff) in isolation. When it returns, surface any flagged issues to the user.

**Done when:** Wrap-up agent returns STATUS: completed or partial. Any flagged issues presented to user.

---

## Constraints

- Never create or edit files in Step 1 — surface findings first. Improvements build only after the user approves; broken-thing fixes are pre-approved but still applied in Step 2, not Step 1.
- Broken things (factual errors, stale references, broken links) are fixed or attempted during the session, never logged and deferred. Only judgment-based improvements wait for approval.
- If nothing meaningful happened in the session, say so and skip Steps 2–4.
- Keep the handoff note tight. Readable in under two minutes.
