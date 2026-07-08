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

2. Rebuild and publish the shareable Starter:
   ```
   python AI-Workshop/public-version/build-starter.py
   ```
   This copies the latest system into the Starter, strips out anything personal, checks it, then commits and pushes the Starter automatically. If the check fails, fix what it reports and run it again. Do not move on until it says **All checks passed**. (Add `--no-push` to build without pushing.)

3. Push the main vault too (your own copy), from the vault root:
   ```
   git push
   ```

## Done when
- `build-starter.py` says "All checks passed" and pushes the Starter.
- The main vault is pushed.

## Note
Each machine then gets the update by pulling the new files and running `python AI-Workshop/install.py` (git pull, or replace the system folders by hand). The full machine-side steps are in `Workshop-Human/UPDATING-MACHINES.md`.
