---
name: safe-system-refactor
description: Run a structural change to the vault system safely, moving, renaming, archiving, or deleting folders, skills, servers, or system files. Use this whenever a task moves or removes anything the system depends on, including "move X to Y", "archive this skill", "restructure this folder", "delete this server", or any plan step that relocates system files. Trigger it even for a single-folder move; the small moves are the ones that have broken machines before.
---

# Safe System Refactor

Move, rename, archive, or delete system pieces without breaking the vault, the Starter, or the machines that pull from them.

Every rule below comes from a failure in a real refactor (four documented runs: 2026-07-07 install collapse, 2026-07-08 skills split, 2026-07-08 agent archive, 2026-07-11 Personal/ restructure). The dates in parentheses say which run taught the lesson; read the matching handoff in `Context/History/` when you need the full story.

## Step 1: Scope, and the two pre-checks

Before touching anything, run the two checks from `Context/Systems/vault-rules.md` ("Before Deleting or Restructuring"):

1. **Understand the design.** Read the latest handoff, the maps, and any index that covers the piece. Confirm how it is actually used; do not act on an assumption. A folder that looks like a redundant duplicate can be the load-bearing build target (this exact mistake deleted the Starter clone once, 2026-06-30).
2. **Check what references it.** Search the whole vault for the old path before moving it. Search for the folder name AND the path string, in `.md`, `.py`, and `.json` files. Skills, agents, hooks, scheduled tasks, and installers reference paths literally; servers also *compute* paths (parent-folder counts in `server.py`, fixed bootstrap URLs), so read the path logic in code, not just string matches (2026-07-07).

**Any destination outside the vault root is its own explicit question to the user, never a plan line item** (2026-07-11: personal files moved to `~/Desktop/Personal-Notes/` off one approved plan line, and the user could not find their own notes). "Remove from the system" means a vaultignored folder inside the vault.

Done when: you can list every file that moves, every file that references it, and no destination leaves the vault root without the user's explicit answer.

## Step 2: Work in a worktree

Do the refactor on an isolated git worktree branch, never directly on the live vault (all four runs). If the environment did not already give you a worktree, create one. This makes a botched refactor disposable.

## Step 3: Move with git, archive instead of deleting

- Use `git mv` for moves so history follows the file.
- A superseded piece gets archived, not deleted: category-local `Archive/` folder, frontmatter `tags: [archived]`, and its registry row (skill_map, agent_map) moves to an `## Archived` section instead of being removed (2026-07-08 agent archive run).

## Step 4: Sweep the references, all three copy layers

Fix every reference found in Step 1, and remember the vault is not one copy of the truth:

1. **The live vault** files.
2. **The Starter overlay** (`AI-Workshop/public-version/starter-overlay/`): overlay copies of HUMAN.md pages, Guide pages, `.gitignore`, and settings ship from there, not from the live vault. Edit the overlay copy separately; editing only the live copy ships nothing (2026-07-07, 2026-07-11).
3. **The build script itself** (`AI-Workshop/public-version/build-starter.py`): its ship lists (`CORE_COPIES`, `OVERLAY_ROOTS`), its generated templates (the vault-map text block), and its verify checks all name paths literally.

Update the maps in the same pass; stale maps break navigation silently (`Context/Systems/vault-rules.md` maintenance rule).

Done when: a fresh search for the old path returns only history notes and archived files.

## Step 5: Verify git tracks the result, in BOTH repos

The quiet killer: a `.gitignore` rule can silently drop moved content from the vault repo and from the Starter, so every machine that pulls loses the files while your working tree looks fine (2026-07-08: both repos ignored all of `.claude/` right after skills moved there).

- Run `git status --short` and confirm the moved files show as tracked changes at the new path.
- Run `git check-ignore -v <new path>` in the vault repo, and after the Starter rebuild confirm the files exist in the built Starter tree.

Done when: both repos show the files tracked at the new path.

## Step 6: Test the change, nothing ships untested

Match the verification to what was touched (`Context/Systems/vault-rules.md`, Nothing Ships Untested):

- **Always:** `python AI-Workshop/install.py --check` (servers launch, config wired, PASS/FAIL per part), and the `vault_health` tool (broken links, orphans, map drift, all should be clean).
- **If server or search code was touched:** run the graded search quiz, `Tests/search-quiz/quiz.py`, under the kb venv python from the real vault root (a worktree has no search index and scores low for that reason alone; point `VAULT_PATH` at the real vault to compare fairly). A score below the recorded baseline blocks the ship.
- **If the build script was touched:** `python3 AI-Workshop/public-version/build-starter.py --dry-run` before the real build.

Done when: every check that applies has actually run and passed, and you can name the output.

## Step 7: Merge, then publish. The flow ends with the merge

- Deliverables on a worktree branch are invisible to the user and to every other machine until the branch merges; do not report "done" from an unmerged branch (2026-07-11: work sat unmerged while the summary said done).
- After the merge: rebuild the Starter (`build-starter.py`) and push both repos. Starter drift is always urgent; a vault change that ships to no one is not shipped.
- Note for the user what needs a restart (Claude apps reload servers only on full restart) and what remote machines run to catch up (`python AI-Workshop/install.py --update`).

Done when: branch merged, both repos pushed, restart/update steps stated.

## Quick reference: the four failure modes this skill exists to stop

| Failure | Where it bit | The step that stops it |
|---|---|---|
| Deleted a "duplicate" that was load-bearing | 2026-06-30, Starter clone | Step 1, understand the design |
| Moved files silently dropped by .gitignore in both repos | 2026-07-08, skills split | Step 5 |
| Personal files moved outside the vault off a plan line | 2026-07-11, Personal-Notes | Step 1, outside-root question |
| "Done" reported from an unmerged worktree branch | 2026-07-11, FTS5 session | Step 7 |
