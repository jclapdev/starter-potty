# Glossary

_Plain-language definitions of the system's terms, in one alphabetical list you can search. Each entry says what a term means and when it actually affects you, and links to the fuller guide page if there is one._

_For how a mechanism works in depth, see its page in `Context/Guide/`. For the exact procedure the AI follows, see the linked `SKILL.md` or system file._

---

### agent

A focused background helper the AI hands a self-contained job to (for example, scanning the vault for broken links). Runs in isolation and reports back, so a big mechanical job doesn't clog the main conversation.
**Touches you:** rarely by name — the AI decides when to spawn one. You see the result, not the work.

### connector / MCP

An extra tool Claude can use, added through a small program called an MCP server. "Connector" is the app's word for it; "MCP" is the underlying standard. This system ships two: `vault` and `kb`. The installer (`AI-Workshop/install.py`) registers them in both Claude apps.
**Touches you:** when you add or build one, or when one "isn't showing up" (re-run the installer, then restart the app).

### hook

A small check that runs automatically whenever Claude writes a file — for example, flagging a broken link or an AI-language tell right away.
**Touches you:** silently, on every file write. You only notice if it catches something.

### kb connector

The knowledge-base connector (`kb`). Adds search-by-meaning over your notes, on top of plain text search. Set up by default; skip it with `install.py --no-kb`.
**Touches you:** when you ask the AI to find notes by idea rather than exact words.

### map

An index file that says where everything is and what exists (`skill_map`, `agent_map`, `systems_map`, `vault_map`). Maps keep navigation fast as the vault grows and are the source of truth for what's registered.
**Touches you:** indirectly — the AI reads maps to orient. They must stay current, so they update whenever structure changes.

### session

One working stretch with the AI, from "read your instructions" to "wrap up." The system gives each session a warm start (it reads the last handoff) and a clean close (it updates its notes).
**Touches you:** every time you work — say `read your instructions` to start and `wrap up` to end.

### skill

A reusable, step-by-step procedure the AI follows for a recurring job (for example: wrap up a session, review a note, build a new skill). The AI picks the right one for your request on its own.
**Touches you:** constantly, usually without naming it. You describe what you want; it reaches for the matching skill.

### vault connector

The navigation connector (`vault`). A read-only server that lets the AI look up skills, search notes, and check links without loading whole files.
**Touches you:** indirectly — it powers fast startup (`read your instructions`) and in-session navigation.

### wrap-up

The end-of-session routine. Say "wrap up" and the AI reviews the session, updates its maps and memory, refreshes anything that changed, and writes a short handoff so the next session starts warm.
**Touches you:** every time you finish working — say `wrap up`.
