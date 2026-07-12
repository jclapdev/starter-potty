---
tags: [guide]
covers: .claude/skills/safe-system-refactor/SKILL.md
---

# Safe System Refactor

_User guide, the plain-language companion to the AI reference in `.claude/skills/safe-system-refactor/SKILL.md`._

## What it's for

Moving or removing parts of the system (a folder, a skill, a helper program) without quietly breaking something that depended on it. Four past reorganizations each taught a lesson the hard way; this skill is those lessons written down so they never repeat.

## How it works

Before anything moves, the AI checks how the piece is really used and searches for everything that points at it. The work happens on a disposable copy, not the live vault. Moves keep their history, retired pieces get archived instead of deleted, and every pointer gets fixed in all the places a copy lives (the vault, the shareable Starter, and the build script). Then it proves the result: the files are really tracked at the new spot, the installer check passes, the health check is clean, and the search test still scores what it scored before. It only counts as done when the change is merged and published, because until then nothing has actually reached you or your other machines.

## When it touches you

- You ask to move, rename, or delete any folder or system piece.
- You ask to retire a skill, an agent, or a helper.
- A bigger plan includes a step like "relocate X", even a small one. The small moves are the ones that have broken machines before.

## Best practices

- If a file should end up somewhere outside the vault folder, the AI must ask you first, every time. That is your decision, never a plan detail.
- Expect the AI to say what still needs a restart or an update command afterward; that's part of the job, not an extra.

## Dig deeper →

- AI reference (the exact procedure): `.claude/skills/safe-system-refactor/SKILL.md`
- The four source runs: the 2026-07-07, 2026-07-08, and 2026-07-11 notes in `Context/History/`
- Glossary: [[glossary]]
