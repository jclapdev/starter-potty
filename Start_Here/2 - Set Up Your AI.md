# 2 - Set Up Your AI

_[[Home]] · Back: [[1 - What This Is]] · Next: [[3 - Your First Session]]_

---

Obsidian is where *you* see the files. Now point your AI at the same folder so it can read and write them too. Two steps: run the installer once, then connect Claude.

## Before you start: where this folder lives

Keep the vault in your **home folder** (`~/ClaudeVault` on Mac, `C:\Users\YourName\ClaudeVault` on Windows). The Claude desktop app only opens folders that really live inside your home folder, and on many computers OneDrive or iCloud quietly moves Desktop and Documents somewhere else. That's the cause of most confusing "can't open this folder" errors.

Don't worry about getting it wrong: the installer checks the location first and tells you exactly what to do if the folder is in a bad spot. If you want the vault reachable from your Desktop, make a shortcut or alias to it there yourself.

## Step 1: run the installer (one time)

You need Python installed (3.9 or newer, from https://python.org). Open a terminal in this folder and run:

```bash
python AI-Workshop/install.py
```

What happens:

1. It checks your Python and the folder's location, and stops with plain instructions if either is a problem.
2. It sets up the knowledge base. The first time this downloads about 1 GB, so give it a few minutes.
3. It writes the config each Claude app needs, using your own machine's paths.
4. It ends with a **PASS/FAIL check of every part**, then prints your next steps.

If everything passed, you're done with the terminal. Keep `install.py`; it is also how this machine updates later (`python AI-Workshop/install.py --update` fetches and applies the latest version by itself). If something failed, the message names the exact command that fixes it.

## Step 2, Option A: Claude desktop app (easiest)

The no-terminal path, good for everyone.

1. Fully quit and reopen the **Claude** desktop app.
2. Switch to **Cowork** mode.
3. When it asks for a folder to work in, **select this vault folder** (the same one open in Obsidian).
4. In the chat, type: **`read your instructions`**

Claude loads its rules, sees this is a fresh vault, and walks you through the start. From then on you work by chatting; anything it writes shows up in Obsidian.

## Step 2, Option B: Claude Code (more powerful)

Runs in a terminal and can do more at once: edit many files, run scripts, automate jobs.

1. Install Claude Code: https://code.claude.com/docs/en/quickstart
2. Open a terminal **inside this vault folder**.
3. Run: `claude`

It reads the vault's instruction files automatically. You can use both: the desktop app for everyday chatting, Claude Code when you want to move faster.

## If the AI can't see your files

It's almost always pointed at the wrong folder. Make sure the folder you selected (Option A) or opened the terminal in (Option B) is the **same folder shown in Obsidian's title bar**. Beyond that, the Troubleshooting section of `HUMAN.md` (in the vault root) covers the rest.

---

_[[Home]] · Back: [[1 - What This Is]] · Next: [[3 - Your First Session]]_
