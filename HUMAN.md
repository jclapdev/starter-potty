# The Owner's Manual

_One page that explains the whole system: what each piece is, what it does for you, and how to use it day to day._

---

## The whole idea

Everything lives in this one folder. You read and write notes in **Obsidian**, a free notes app. **Claude** opens the same folder and reads, writes, and organizes the same notes. Because it is one folder, anything Claude writes shows up for you instantly, and anything you write is there for Claude next time.

Nothing is hidden in an app or a cloud somewhere. Every note, every rule, even Claude's own instructions are plain text files you can open and change. If you stopped using Obsidian or Claude tomorrow, every note would still open in any text editor.

Claude's job is to help you write, research, organize, and remember. The six helpers below all exist for that one reason: they make Claude better at reading, finding, writing, and remembering your notes.

---

## The six helpers

**1. The finder.** A small program that runs quietly in the background whenever Claude is open. When Claude needs a note, a saved procedure, or the list of unfinished work, it asks the finder instead of opening folders and reading file after file. You never see it work; you just notice Claude gets to the right note fast.

**2. The meaning memory.** Search that works even when you can't remember the exact words. Ask about "that note where we compared the two servers" and it finds the note because it matches what you *mean*, not the letters you typed. It lives inside the finder, so there is one background program doing both jobs, and it comes with a graded test (questions with known right answers) that every search change must pass before it ships.

**3. Skills.** Step-by-step procedures Claude has written down for jobs that repeat, like ending a session cleanly or building something new. When you ask for that kind of job, Claude follows its saved steps instead of improvising, so the job comes out the same way every time. When you notice yourself asking for the same thing again and again, say "turn this into a skill" and it becomes one.

**4. Memory files.** Short notes Claude keeps about how you like to work: plain words, no padding, make the call and do the work. It reads them at the start of every session, so you never have to repeat a preference twice.

**5. The maps.** Index pages that list what exists and where it lives: one for the folders, one for the skills, one for the background helpers, one for the rules. Whenever something new is added, its map is updated in the same breath. This is what keeps the folder useful as it grows instead of turning into a junk drawer.

**6. The Starter and the installer.** The Starter is a cleaned copy of this whole system with nothing personal in it, ready to hand to a friend or put on your own second computer. The installer (`AI-Workshop/install.py`) wires the system to a machine, checks every part, and prints PASS or FAIL so you can see it worked. The same command later fetches and applies updates.

Two files sit above all of this: **`main.md`** holds your personal settings and rules (who you are, how you want Claude to talk), and **`CLAUDE.md`** is the short pointer that sends Claude to it.

---

## Getting set up

You install three things yourself, once: **Python** (3.9 or newer), **Obsidian**, and **Claude** (the desktop app, Claude Code in the terminal, or both).

**Where the folder goes:** keep the vault in your home folder (`~/ClaudeVault` on Mac, `C:\Users\YourName\ClaudeVault` on Windows). The Claude desktop app only opens folders that really live in your home folder, and on many computers OneDrive or iCloud quietly relocates Desktop and Documents. The installer checks this first and tells you exactly what to do if the spot is bad.

**Then run the installer.** Open a terminal in this folder and run:

```bash
python AI-Workshop/install.py
```

It sets up the meaning memory (the first run downloads about 1 GB, so give it a few minutes), writes the settings each Claude app needs using your machine's own paths, and ends with a PASS/FAIL check of every part. If something failed, the message names the exact command that fixes it. To set up without the 1 GB download, add `--no-kb`.

**Then connect Claude**, either way or both:

1. **Claude desktop app:** fully quit and reopen Claude, switch to Cowork mode, pick this folder when asked, and type `read your instructions`.
2. **Claude Code (terminal):** open a terminal in this folder and run `claude`. It finds the instruction files on its own.

If Claude can't see your files, it is pointed at the wrong folder: make sure the folder Claude opened is the same one shown in Obsidian's title bar.

---

## Your first ten minutes

1. Open `main.md` and fill in the **Who I Am** section: your name, what you do, what you want this for. A few sentences is plenty. Claude reads it every session.
2. In the chat, type `read your instructions`. On a fresh vault Claude confirms setup worked and offers a starting point.
3. Try something real, in your own words: "Research a topic I care about and file it as a note I can come back to," or "Here's what I'm working on, make a project note for each."
4. When you're done, say `wrap up`. Claude files what happened and writes itself a handoff note, so the next session starts where this one stopped.

---

## Day to day

You mostly just talk. Describe what you want; Claude picks the right skill on its own. A few words trigger set behaviors any time:

| Say this | Claude does |
|---|---|
| `read your instructions` | Loads your rules, shows the last session and what's open |
| `status` | A read-only snapshot: what it can do, what's open |
| `wrap up` | The full end-of-session cleanup and handoff |
| `research` | Searches first, labels confidence, links every source |

Two habits make the system compound:

- **The inbox.** Drop messy ideas, half-thoughts, and pasted links in `Workshop-Human/` and tell Claude to process them. You write messy; it turns the mess into real notes and plans.
- **The wrap-up.** Ending sessions with `wrap up` is what carries context across days. Skipping it breaks nothing, but every session after a wrap-up starts warm instead of cold.

The system also maintains itself: a weekly health check (in `AI-Workshop/Scheduled/`) validates the links and maps and flags anything drifting.

---

## Updating

One command on any machine:

```bash
python AI-Workshop/install.py --update
```

It fetches the latest system files itself, applies them, and re-runs the setup check. It never touches your own work: your notes, history, memory, and `main.md` stay exactly as they are, and every file it replaces is backed up first to `AI-Workshop/.update-backups/`. Restart Claude when it finishes. To inspect a machine without changing anything, run `python AI-Workshop/install.py --check`.

---

## Sharing it

This vault doubles as a kit you can give away. A build script (`AI-Workshop/Starter/build-starter.py`) produces the Starter: the same system with everything personal stripped out. The person you give it to installs Python, Obsidian, and Claude, unzips the folder into their home folder, and runs the same one installer command. It works the same on Mac, Windows, and Linux because nothing in the shared files assumes a particular machine.

---

## If something's off

- **"Invalid folder" when picking the folder in the desktop app:** the vault's real location is outside your home folder (usually OneDrive or iCloud relocated it). Move the vault into your home folder and run the installer again.
- **Claude can't see your files:** wrong folder. Match it to the one in Obsidian's title bar.
- **A helper isn't showing up:** run the installer again, then fully restart the Claude app. Claude Code asks you to approve new helpers the first time; that's expected.
- **Errors about downloading during install:** that's the 1 GB meaning-memory download. Everything else still works without it; run the installer again to retry.

---

## Looking something up

- **The Guide** (`Context/Guide/`): one plain page per mechanism, including the Obsidian shortcuts set up for you.
- **The glossary** (`Context/Systems/glossary.md`): one-line definitions for any term you hit.
- **The folder map** (`Context/Maps/vault_map.md`): what every folder is for.

Obsidian's own help lives at https://help.obsidian.md, with links between notes explained at https://help.obsidian.md/links.
