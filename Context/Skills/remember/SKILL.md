---
name: remember
description: Save a working-style preference so it sticks across sessions. Use this whenever the user says "remember this", "save this as a preference", "from now on always do X", "make this a standing rule for how you work", or gives feedback about how they want you to work. It writes the preference into the vault's memory.
---

# Remember a preference

Save how the user wants you to work, so it carries into future sessions instead of being forgotten.

## Steps

1. Put the preference in one or two plain sentences: what to do, and when to do it.

2. Save it as a new file in `Context/Memory/<short-name>.md`, with:
   - a short title (a `#` heading)
   - the preference in plain words
   - the source and date, for example: `Source: user, 2026-06-29`

3. Add one line to `Context/Memory/MEMORY.md` that links to it:
   ```
   - [Title](short-name.md) — one-line summary
   ```
   If `MEMORY.md` doesn't exist yet, create it with a `# Memory Index` heading first.

4. Tell the user it's saved, in one line.

## Done when

- The new file exists in `Context/Memory/`.
- `MEMORY.md` has a line linking to it.

## Keep it clean

- One preference per file.
- Short and specific. Say the behavior plainly, not in a long write-up.
