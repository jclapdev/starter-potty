# How this works

_The whole operation, in one page. This is an AI second brain: an Obsidian vault that Claude reads, writes, and maintains alongside you._

You see the files in Obsidian. Claude works in the same folder. Nothing is hidden in an app somewhere else, it is all plain Markdown on your disk.

---

## Contents

1. [The big idea](#the-big-idea)
2. [Where to put this folder](#where-to-put-this-folder)
3. [Setup (one command)](#setup-one-command)
4. [Two ways to run Claude](#two-ways-to-run-claude)
5. [How a session works](#how-a-session-works)
6. [The pieces](#the-pieces)
7. [Day to day](#day-to-day)
8. [Keeping it healthy](#keeping-it-healthy)
9. [Sharing this system](#sharing-this-system)
10. [Updating to a new version](#updating-to-a-new-version)
11. [Troubleshooting](#troubleshooting)

---

## The big idea

One folder, two viewers. **Obsidian** is your window into the notes. **Claude** (in the desktop app or in the terminal) opens the same folder and can read and edit those notes, run small programs, and keep the system tidy. Because it is the same folder, anything Claude writes appears in Obsidian instantly, and anything you write is there for Claude next time.

The system gives Claude a memory and a set of habits so it does not start cold every session. Those habits live in the `Context/` folder as plain text you can read.

---

## Where to put this folder

Put the vault in your **home folder** (`~/ClaudeVault` on Mac, `C:\Users\YourName\ClaudeVault` on Windows), then run setup (next section). Setup automatically puts a **shortcut to the vault on your Desktop**, so you open it from the Desktop like any other folder, and it works on every machine.

You do not have to think about any of this. The short version:

1. Put the `ClaudeVault` folder in your home folder.
2. Run `python AI-Workshop/setup.py`.
3. Open the new **ClaudeVault** shortcut on your Desktop in both Obsidian and Claude.

Why it is done this way: the Claude desktop app (Cowork) only opens a folder whose real location is inside your home folder. On some computers the Desktop and Documents folders are quietly relocated by OneDrive or iCloud, so a vault placed directly on the Desktop can be rejected. Keeping the real folder in your home folder and pointing at it through a Desktop shortcut gives you the Desktop convenience while always satisfying that rule, no matter how the machine is configured. If you ever move the vault somewhere outside your home folder, setup will tell you and point you back.

---

## Setup (one command)

You need three things first: **Python** (3.9+), **Obsidian**, and **Claude** (the desktop app, Claude Code, or both).

Then, from this folder, run:

```bash
python AI-Workshop/setup.py
```

That is the whole setup. It works on macOS, Windows, and Linux because it uses the exact Python you just ran it with, figures out your own paths, and writes the config files each Claude app needs. It also sets up the knowledge base, which the first time downloads about 1 GB of libraries, so give it a few minutes.

In the rare case you want to skip the knowledge base, run `python AI-Workshop/setup.py --no-kb`.

After setup, restart Claude. That is it. See [Two ways to run Claude](#two-ways-to-run-claude) for how to point Claude at this folder.

> Why one command matters: everything machine-specific (where Python lives, where this folder is, Windows vs Mac path styles) is worked out on your machine at setup time. The shared files contain none of it, so the same package works for everyone.

---

## Two ways to run Claude

Both read the same vault. Use either or both.

1. **Claude desktop app (Cowork)** — no terminal. Open Claude, switch to Cowork, pick this folder when asked, then type **`read your instructions`**. You work by chatting.
2. **Claude Code** — a terminal tool that can do more at once (edit many files, run scripts). Install it, open a terminal in this folder, and run `claude`. It reads `CLAUDE.md` automatically.

The `Start_Here/` folder has step-by-step onboarding if this is your first time.

---

## How a session works

Three moments:

1. **Start:** say **`read your instructions`**. Claude loads your rules and tells you the last session and what is open. It does not guess, it reads.
2. **Work:** just describe what you want. Claude picks the right habit ("skill") for the job. You do not need to name files or steps.
3. **End:** say **`wrap up`**. Claude reviews the session, updates its maps and memory, and writes a short handoff note so the next session has context.

A few words trigger set behaviors any time:

| Say this | Claude does |
|---|---|
| `read your instructions` | Loads rules, shows last session + open work |
| `status` | A read-only snapshot: what it can do, what is open |
| `wrap up` | The full end-of-session cleanup and handoff |
| `research` | Searches first, labels confidence, cites sources |

---

## The pieces

Everything Claude uses to stay consistent lives in `Context/`. You rarely edit these by hand; Claude maintains them.

- **Skills** (`Context/Skills/`) — reusable, step-by-step procedures (for example: wrap up a session, review a vault, build a new skill). Claude chooses the right one for your request.
- **Systems** (`Context/Systems/`) — the rules of how the vault works: behavior and tone (`base-rules.md`), how vault work happens (`vault-rules.md`), and the session lifecycle. Your personal preferences live in `main.md` at the root.
- **Maps** (`Context/Maps/`) — index files that say where everything is and what exists: `skill_map`, `agent_map`, `systems_map`, `vault_map`. These keep navigation fast as the vault grows.
- **Agents** (`Context/Agents/`) — focused background helpers Claude can hand a self-contained job to (for example, scanning the vault for broken links).
- **Memory and history** (`Context/Memory/`, `Context/History/`) — durable notes on how you like to work, dated session notes, and `open-work.md`, the single list of what is still open.

The engines that make this fast live in `AI-Workshop/`:

- **`vault-mcp/`** — the navigation server (the `vault` connector). Pure Python standard library, nothing to install. It lets Claude look up skills, search notes, and check links without loading whole files.
- **`kb-mcp/`** — the knowledge base (the `kb` connector). Adds search by meaning over your notes. Set up by default; skip it with `setup.py --no-kb`.
- **`mcp-sync/`** — keeps those servers registered in both Claude apps from one shared list. `setup.py` uses it.
- **`hooks/`** — small checks that run automatically when Claude writes a file (for example, flagging a broken link right away).

---

## Day to day

You mostly just talk to it. Some examples:

- "Read your instructions, then help me plan this week."
- "Summarize the three notes in Projects and file the result in the wiki."
- "Review this note and link it to anything related."
- "Wrap up."

Claude reaches for the right skill on its own. If a request is ambiguous, it asks before guessing. If it needs something only the terminal can do, it will say so.

---

## Keeping it healthy

The system maintains itself, with two habits:

- **Wrap up** at the end of a working session keeps maps, memory, and open work current.
- A **weekly health check** (in `AI-Workshop/Scheduled/`) validates links and maps and flags anything drifting, including whether the Claude apps are still in sync on their servers.

You do not have to run these manually beyond saying "wrap up."

---

## Sharing this system

This vault doubles as a shareable starter kit. The build that produces the shareable copy lives in `AI-Workshop/build-starter.py`; it strips out anything personal and machine-specific, leaving the system skeleton plus the setup tooling.

The recipient does exactly one thing after unzipping: run `python AI-Workshop/setup.py`. Because none of the shared files contain absolute paths or assume a particular Python, it works the same on a fresh Windows, macOS, or Linux machine. That run also sets up the knowledge base, which downloads about 1 GB of libraries the first time. If that download ever fails, the rest of the system still works and re-running setup finishes it.

---

## Updating to a new version

This is for machines that already run the system and just need the latest improvements. It does not start over and it does not touch your work.

Run this from the vault folder:

```
python AI-Workshop/update.py
```

First time on an older machine that doesn't have `update.py` yet? Get it once, then run it:

```
curl -L -o AI-Workshop/update.py https://raw.githubusercontent.com/jclapdev/starter-potty/main/AI-Workshop/update.py
python AI-Workshop/update.py
```

(Or open that link in a browser, save it into the `AI-Workshop` folder as `update.py`, then run the second line.) That first run pulls in the whole latest system.

It downloads the latest system, saves a backup of the current system files, and replaces only the system parts: skills, systems, agents, the system maps, and the helper programs. Your projects, notes, history, memory, your `main.md`, and your machine settings are left exactly as they are. When it finishes, restart Claude.

No internet on that machine? Update from a copy of the latest version instead:

```
python AI-Workshop/update.py --from new-version.zip
```

You do not need git for either one. The backups it makes are kept in `AI-Workshop/.update-backups/`.

---

## Troubleshooting

- **"Invalid folder" / "outside your home directory" when picking the folder in the Claude desktop app.** The vault's real location is outside your home folder (often because it sits on a Desktop that OneDrive or iCloud has relocated, or on an external drive). Move the `ClaudeVault` folder into your home folder and run `python AI-Workshop/setup.py` again. Setup will confirm the location is valid and put a working shortcut on your Desktop. See [Where to put this folder](#where-to-put-this-folder).
- **"Claude can't see my files."** It is pointed at the wrong folder. Make sure the folder Claude opened is the same one open in Obsidian's title bar.
- **"A connector isn't showing up."** Run `python AI-Workshop/setup.py` again, then fully restart the Claude app. New servers in Claude Code prompt for approval the first time, which is expected.
- **"I got errors about installing something."** That is the knowledge base download (about 1 GB). The rest of the system still works without it. Run `python AI-Workshop/setup.py` again to retry, or `python AI-Workshop/setup.py --no-kb` to set up without it.
- **"The apps disagree on what's connected."** Run `python AI-Workshop/mcp-sync/sync.py --check` to see the difference, then `python AI-Workshop/setup.py` to fix it.

---

_For the structure of every folder, see `Context/Maps/vault_map.md`. For your personal settings, see `main.md`._
