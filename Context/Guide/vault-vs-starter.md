---
tags: [guide]
covers: AI-Workshop/public-version/build-starter.py
---

# Vault vs. Starter

_User guide. The plain-language companion to the AI reference in `AI-Workshop/public-version/build-starter.py`._

## What it's for

Keeping your private vault and the shareable system template as two separate things, so personal notes never leak into what other people install, and other people can never write back to your repos.

## How it works

There are two git repos, not one.

- **Your vault** (`potty_box`) is your real Obsidian vault. It holds everything personal: your projects, session history, open-work, memory, and your `main.md` identity. This is private to you. Day-to-day work is committed here.
- **The Starter** (`starter-potty`) is a clean template *generated from* your vault by `build-starter.py`. It carries only the reusable system: `CLAUDE.md`, `Context/Systems`, `Skills`, `Agents`, the `AI-Workshop` machinery, the `install.py` setup script, and empty placeholder files. It lives in its own repo.

`build-starter.py` copies by a whitelist. Only the paths it names get copied. Personal folders (`Projects/`, `History`, `Memory`, `Maps`, personal `main.md`) are not on that list, so they never ship. Handcrafted template files live in `AI-Workshop/public-version/starter-overlay/` and are laid on top.

Someone else installs the system by **downloading the Starter** (a zip, or the repo) and running `install.py`. A downloaded zip has no git history and no remote. Their machine ends up with the system but no connection to your repos, so they cannot push to `potty_box` or `starter-potty`.

## When it touches you

- You tell someone "install this and you'll have X." X only exists for them if it's in the **Starter**, so the Starter must be rebuilt and pushed after any change that ships.
- You add or edit a personal note. It belongs in the **vault** only. It should never appear in the Starter.
- You change a file that ships (a system file, or anything under `starter-overlay/`). The vault edit alone does nothing for other people until you rebuild the Starter.

## Best practices

- After any change meant for other machines, rebuild the Starter (`build-starter.py`) and confirm its repo is pushed. Treat Starter drift as urgent.
- Remember overlay files (`.gitignore`, template `main.md`, the `HUMAN.md` pages, `.claude/`) ship from `starter-overlay/`, not the live vault. Edit the overlay copy, not just the vault one.
- Keep personal content out of the whitelist. If you're unsure whether something ships, check `CORE_COPIES` in `build-starter.py`.

## Dig deeper →

- AI reference (the exact procedure): `AI-Workshop/public-version/build-starter.py`
- Glossary: [[glossary]] (related terms)
