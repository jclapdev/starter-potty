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

### Step 2: Apply and Close (inline, no agent)

Once the user has approved (or rejected) all findings from Step 1, run the close-out directly. The mechanics live in two vault MCP tools, so this costs little context: no vault scanning, no subagent.

1. **Apply approved changes.** Write or edit each approved file. A new skill or system also gets its row added to `skill_map.md` / `systems_map.md`, and `vault_map.md` gets any new top-level folder.
2. **Health check with fixes.** Call `vault_health` with `fix: true`. The server applies the deterministic safe fixes itself (unambiguous link and map-path repoints, mechanical lint) and returns what it fixed, what it skipped, and what remains. Resolve any remaining findings that have one clear fix; surface the ambiguous ones to the user. Do not scan vault files yourself. If the tool is unavailable (connector down), skip this and say so.
3. **Close the session.** Call `wrap_session` with one payload: `session_date` (YYYY-MM-DD), `session_slug` (short kebab-case label), `handoff` (the full handoff note, format below), `open_work_changes` (items to add/edit/close/remove), `current_focus` (one-paragraph replacement for the focus line), and `archive` (any history notes from the health report's archive candidates whose open items are plainly inactive; when in doubt, leave the note and flag it). The tool writes the handoff file, reconciles open-work.md, and moves the archived notes. Report any errors it returns.

**Handoff note format** (composed by you, written verbatim by the tool):

```
# Session Handoff — {date} — {Slug Title Case}

---

## What Was Built

## Decisions Made

## In Progress

## Next Steps
(top 3–5 open items, priority order — see open-work.md)
```

Keep it readable in under two minutes, pure narrative; item tracking lives in open-work.md. Wrap the first mention of each vault note the session touched as a wikilink (use the full-path-plus-alias form for shared basenames like SKILL.md); never link a note that does not exist.

**Done when:** Approved changes are on disk, the health report is clean or its leftovers are surfaced, and `wrap_session` returned no errors.

---

## Constraints

- Never create or edit files in Step 1 — surface findings first. Improvements build only after the user approves; broken-thing fixes are pre-approved but still applied in Step 2, not Step 1.
- Broken things (factual errors, stale references, broken links) are fixed or attempted during the session, never logged and deferred. Only judgment-based improvements wait for approval.
- If nothing meaningful happened in the session, say so and skip Steps 2–4.
- Keep the handoff note tight. Readable in under two minutes.
