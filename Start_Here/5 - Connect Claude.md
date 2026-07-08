# 5 - Connect Claude

_[[Home]] · Back: [[4 - Folders and Backlinks]] · Next: [[6 - Next Steps]]_

---

Obsidian is where *you* see the files. Now point your AI at the same folder so it can read and write them too. There are two ways. Start with the first.

## Where to keep this folder

Keep the `ClaudeVault` folder in your **home folder** (`~/ClaudeVault` on Mac, `C:\Users\YourName\ClaudeVault` on Windows). When you run setup in the next step, it automatically puts a **shortcut to the vault on your Desktop**, so you can open it from the Desktop and it will work on any machine. Open the vault through that Desktop shortcut.

(This is because the Claude desktop app only opens a folder whose real location is inside your home folder. Some computers relocate the Desktop and Documents folders via OneDrive or iCloud, so a folder placed directly on the Desktop can be rejected. The shortcut sidesteps that for everyone. If you put the vault somewhere outside your home folder, setup will tell you.)

## First: run the installer (one time)

This registers the vault's helper servers and works on macOS, Windows, and Linux. You need Python installed (3.9 or newer). Open a terminal in this folder and run:

```bash
python AI-Workshop/install.py
```

It writes the config each Claude app needs, using your own machine's paths, and sets up the knowledge base (the first time this downloads about 1 GB, so give it a few minutes). Restart Claude afterward. You can delete the file when it's done; run it again anytime to reconfigure or update.

## Option A: Claude desktop app (easiest)

This is the no-terminal path, good for everyone.

1. Open the **Claude** desktop app.
2. Switch to **Cowork** mode.
3. When it asks for a folder to work in, **select this vault folder** (the same folder you have open in Obsidian).
4. In the chat, type: **`read your instructions`**

Claude reads `main.md`, learns your rules, and tells you what it can do. From then on, you work by chatting. Anything it writes shows up in Obsidian, because it's the same folder.

## Option B: Claude Code (more powerful)

This runs in a terminal and can do more at once: edit many files, run scripts, and automate jobs. It needs a one-time install.

1. Install Claude Code by following the quickstart: https://code.claude.com/docs/en/quickstart
2. Open a terminal **inside this vault folder**.
3. Run: `claude`
4. Claude reads `CLAUDE.md` automatically, which points it to `main.md`.

You can use both. The desktop app for everyday chatting, Claude Code when you want to move faster. The page on [[6 - Next Steps]] points to a deeper note on what Claude Code adds.

## If the AI can't see your files

It almost always means the AI is pointed at the wrong folder. Make sure the folder you selected (Option A) or opened the terminal in (Option B) is the **same folder open in Obsidian's title bar**.

Reference: Claude documentation home is https://docs.claude.com and support is at https://support.claude.com

---

_[[Home]] · Back: [[4 - Folders and Backlinks]] · Next: [[6 - Next Steps]]_
