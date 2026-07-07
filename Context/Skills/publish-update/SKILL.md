---
name: publish-update
description: Publish system changes so every machine can get them. Use this whenever the user wants to release or ship an update, push the latest skills/systems/tools out to everyone, update the shareable Starter, or "make this available to all my machines". It rebuilds the Starter, checks it, and pushes.
---

# Publish a system update

Use this after we change the system (skills, systems, agents, maps, or the helper programs) and you want every machine to be able to pick it up.

## Steps

1. Commit anything pending in the main vault. Skip if there's nothing to commit.
   ```
   git add -A
   git commit -m "describe the change"
   ```

2. Rebuild the shareable Starter:
   ```
   python AI-Workshop/maintainer/build-starter.py
   ```
   This copies the latest system into the Starter, strips out anything personal, checks it, and commits the Starter. If the check fails, fix what it reports and run it again. Do not move on until it says **All checks passed**.

3. Push the Starter so machines can pull the update:
   ```
   cd AI-Workshop/Projects/Starter
   git push
   ```

4. Push the main vault too (your own copy):
   ```
   git push
   ```
   (run from the vault root)

## Done when
- `build-starter.py` says "All checks passed."
- The Starter is pushed, so the `update.py` download link is current.

## Note
Each machine then gets the update by running `python AI-Workshop/update.py`. The full machine-side steps are in `Workshop-Human/UPDATING-MACHINES.md`.
