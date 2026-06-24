---
name: system-update
description: Re-orient after copying base-rules.md from the Starter into an existing vault. Trigger when the user says "I updated the system", "I copied base-rules.md", "re-orient after update", "what changed in the system", "sync from Starter", or "what's new after the update". Reads git history to summarize what changed in base-rules.md, checks the vault for stale references to anything removed, and surfaces new behaviors or customization opportunities in main.md. Also use when the user wants to understand what a recent Starter update actually changed in practice.
---

# Skill: System Update Orientation

Re-orient after a Starter update. Diff `base-rules.md` against its previous version, check the vault for anything that broke or went stale, and surface what's new so the session can proceed with current context.

---

## Process

### 1. Check git history for base-rules.md

```bash
git log --oneline -10 -- Context/Systems/base-rules.md
```

- **Multiple commits:** identify the most recent update commit, then diff it against the one before:
  ```bash
  git diff <prev-hash>..<current-hash> -- Context/Systems/base-rules.md
  ```
- **Single commit (first install):** no diff available — summarize the file's key sections instead and note this is a first-time setup.
- **No git repo or file missing:** flag it and stop.

### 2. Analyze the changes

From the diff (or summary for first install), categorize:

- **New** — rules, sections, or capabilities that didn't exist before
- **Removed** — anything deleted (agents, rules, references, workflow steps)
- **Modified** — clarifications or rewrites of existing rules worth noting

Focus on behavioral changes. Skip whitespace or formatting noise.

### 3. Scan for stale vault references

For each item identified as **removed** in Step 2, run a grep across the vault:

```bash
grep -r "<removed-term>" . --include="*.md" -l \
  --exclude-dir=.git --exclude-dir=AI-Workshop/Projects/Starter
```

Collect any files still referencing removed concepts. These are cleanup candidates.

### 4. Review main.md

Read `main.md`. Check for:
- Rules in `main.md` that duplicate something already in `base-rules.md` (now redundant)
- New sections in `base-rules.md` the user might want to customize via a `main.md` override
- Anything in `main.md` that conflicts with updated rules

### 5. Report

```
## System Update: <date or commit>

### What's New
- <bullet per new rule/capability>

### What Was Removed
- <item> — <vault files still referencing it, if any>

### What Changed
- <bullet per notable modification>

### main.md Review
- <conflicts, redundancies, or customization suggestions>

### Verdict
Clean — no action needed.
  — OR —
Action items: <list>
```

If no meaningful changes were found (e.g. minor wording), say so in one line.

---

## Done When

- Git history checked and diff (or summary) produced
- Vault scanned for stale references to anything removed
- `main.md` reviewed for conflicts and customization opportunities
- Report delivered to the user
