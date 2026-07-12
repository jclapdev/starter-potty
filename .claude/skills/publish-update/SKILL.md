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

2. Fact-check the user-facing docs against the tooling as it actually behaves right now. Read `HUMAN.md` (the owner's manual), the `Context/Guide/` pages, and `Workshop-Human/` (both the live copies and any starter-overlay copies), plus any other doc that describes the install or update path, and compare every claim about setup with what the code really does, especially `AI-Workshop/install.py`. If a page says setup creates something, prints something, or asks for something, confirm the script actually does it. Fix any claim that has drifted before building. (This step exists because shipped claims have drifted more than once: a Desktop shortcut that was never created, a Reference/ folder that does not exist in the Starter, the wrong main.md placeholder format, and 2026-07-09's hand-copy update steps that survived in `Workshop-Human/UPDATING-MACHINES.md` and this skill's own Note after the tooling changed.)

3. Rebuild and publish the shareable Starter:
   ```
   python AI-Workshop/Starter/build-starter.py
   ```
   This copies the latest system into the Starter, strips out anything personal, checks it, then commits and pushes the Starter automatically. If the check fails, fix what it reports and run it again. Do not move on until it says **All checks passed**. (Add `--no-push` to build without pushing.)

4. Push the main vault too (your own copy), from the vault root:
   ```
   git push
   ```

## Done when
- `build-starter.py` says "All checks passed" and pushes the Starter.
- The main vault is pushed.

## Note
Each machine then gets the update with one command: `python AI-Workshop/install.py --update` (it git-pulls on a git clone, downloads the published Starter otherwise). The full machine-side steps, including the one-time step for machines whose installer predates `--update`, are in `Workshop-Human/UPDATING-MACHINES.md`.
