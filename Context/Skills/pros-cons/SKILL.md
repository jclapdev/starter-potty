---
name: pros-cons
description: Structures pros/cons breakdowns to cover both immediate and scalable perspectives, flag when the two framings diverge, and close with a synthesized recommendation. Use when the user asks to "weigh the options", "pros and cons of X", "compare these approaches", "what are the tradeoffs", or any similar request for a structured tradeoff analysis. Also enforces the main.md rule requiring both framings — if the user specifies one framing explicitly, use it; if not, cover both.
---

# Skill: Pros and Cons

**Purpose:** Produce structured, decision-useful pros/cons breakdowns that always address both the immediate situation and the scaled-up version of it. The most common failure mode in tradeoff analysis is optimizing for one time horizon while ignoring the other — this skill prevents that.

---

## When to Use

- User asks for pros/cons, tradeoffs, a comparison, or "help me decide between X and Y"
- Any decision where different time horizons could reasonably lead to different conclusions
- When main.md's "Pros and Cons Breakdowns" rule applies (i.e., always)

---

## Process

### Step 1 — Identify the framing

Before writing anything, determine whether the user has specified a framing:

- **User specified "right now" / "for where we are"** → cover only the immediate perspective. Skip the scalable framing. Note at the end: "If you want the at-scale framing, ask."
- **User specified "at scale" / "long-term"** → cover only the scalable perspective. Note at the end: "If you want the immediate framing, ask."
- **No framing specified** → cover both. Assume the user may not realize the two framings exist or could diverge.

**Done when:** Framing determined. Do not guess — if "at scale" vs. "right now" is ambiguous from context, default to both.

### Step 2 — Build the breakdown

For each option being evaluated, assess:

**Right now (immediate)**
What are the actual pros and cons given the user's current situation — team size, existing tools, constraints, workload, time available? Avoid abstracting away from reality into hypotheticals.

**At scale (future-state)**
What are the pros and cons if volume increases, the team grows, more users depend on it, or the system has to be maintained by someone who didn't build it? Identify what becomes a liability at scale even if it's fine today.

Format the output as two clearly labeled sections per option, or as a side-by-side table if there are more than three options. Tables compress well when the user is comparing multiple choices; prose works better for binary decisions.

**Done when:** Every option has been assessed through both lenses (or the specified lens). No option has been evaluated on only one framing when two were requested.

### Step 3 — Flag divergence

If right now and at scale point in different directions — one option wins immediately but loses at scale, or vice versa — **call this out explicitly**. Do not bury the divergence in the body text. Use a clear marker:

> **Note: these framings diverge.** [Option A] is the better choice right now; [Option B] wins at scale. The right pick depends on your time horizon.

If they do not diverge, confirm that: "Both framings point the same direction — [Option X] holds up either way."

**Done when:** Divergence explicitly flagged or convergence confirmed. This line must appear regardless of which option "wins."

### Step 4 — Recommend

Close with a recommendation that synthesizes both framings. The recommendation must:

1. Name a clear winner (or explicitly name the condition under which each option wins, if the decision genuinely depends on a factor outside your view)
2. State the reasoning in one to three sentences — not a re-summary of the full breakdown
3. If the framings diverged, state which time horizon the recommendation optimizes for and why

Do not hedge into "it depends" without naming what it depends on and giving the user a way to resolve it. An unresolved "it depends" is a non-answer.

**Done when:** Recommendation written. It names a winner or names the deciding condition. It does not restate the full breakdown.

---

## Constraints

- Never cover only one framing when none was specified — this is the skill's core constraint, not optional.
- Never produce a balanced list of pros and cons without a recommendation unless the user explicitly says they want to make the call themselves. Balanced lists without a conclusion offload the hard work back to the user.
- Do not pad. A tight three-paragraph breakdown is better than a six-section document with filler.
- If the user asks for a pros/cons breakdown mid-task (not as the primary request), keep it proportional — don't turn a sidebar decision into a full analysis.
- This skill does not replace domain knowledge. If the decision requires information you don't have, say what's missing rather than producing a confident breakdown from incomplete data.
