# Vault Rules System

_Governs how to operate when a task involves this vault: creating or editing files, or working on the system itself. Read this when a vault task begins. Not needed for pure conversation or one-off questions. The pointer to this file lives in `main.md`._

_These apply automatically whenever a task involves creating or editing files in this vault._

---

## Meta-Mode: Discussing the System vs. Running It

**When the task is to explain, review, discuss, or edit the system itself** — `main.md`, the maps, systems, skills, or how the vault works — **treat it as a read-only conversation.** Do not trigger the navigation sequence, do not read session history, do not run any lifecycle step. Answer the question or make the requested edit, then stop. Fire the navigation sequence and lifecycle only when the task is actual vault _work_, not a discussion of how that work happens.

## Wikilinks

- **Follow `[[wikilinks]]` only when the linked file is needed for the current task.** Never follow links out of index or map files (`vault_map`, `skill_map`, `systems_map`, `agent_map`) — load a map only when you need that specific index. This stops one file's links from pulling in a cascade of others.
- **Create wikilinks** when referencing related files or concepts that exist (or should exist) as separate notes.

## Navigation Sequence

**Fires when a vault task begins — not at session start.**

`systems_map.md` → relevant system files (always includes `session-lifecycle.md`) → `find_skill` *(only when selecting a skill)* → `resolve_agent` *(only when considering an agent)* → `SKILL.md` or `AGENT.md` (execute) → `vault-backlink-scan` (finalize).

"Relevant system files" means only the systems that govern the current task. Do not read every system file by default — read only what the task requires. To choose a skill, call the `find_skill` tool; to choose an agent, call `resolve_agent` — each returns the top matches with their file paths. Don't load `skill_map.md` or `agent_map.md` for selection; call the tool only when actually choosing, not on every task. (The maps stay the source of truth for the startup summary and for registering new skills and agents.) For personal or creative tasks that produce no vault files, skip the navigation sequence entirely.

When a task is heavy on file I/O, fully mechanical, or would benefit from isolation, prefer spawning an agent over running a skill inline. See `Context/Systems/agent-system.md` for the full decision criteria and invocation pattern.

## Start of Session

Handled by the [[session-start]] agent via the startup sequence. Do not read history files inline.

## Skills

Each skill lives in `Context/Skills/<skill-name>/SKILL.md`. Skill instructions extend system rules — they do not replace them. Read both.

**When building a new skill, always route through skill-creator first:** `Context/Skills/skill-creator/SKILL.md`. Do not write a SKILL.md directly without running that process — it exists to ensure skills are tested and validated, not just drafted.

**Never look at the Cowork plugin skills directory** (e.g., `/var/folders/.../skills/` or any path containing `claude-hostloop-plugins`). That is a system directory for Cowork's own tools — not your skills. If a task involves skills, the only valid location is `Context/Skills/`.

## Maintenance Rule

When vault structure changes (new skill, new folder, new system), update the relevant map file immediately. Maps are the source of truth — stale maps break navigation.

## File Creation

**Never create files outside the vault without asking first.** If a file needs to exist somewhere other than its natural vault location, ask where and why before creating it.

**When a file deletion fails with "Operation not permitted", call `allow_cowork_file_delete` immediately** — do not surface the error to the user or ask them to handle it.

## Wiki Layer

The vault has a knowledge layer at `AI-Workshop/Projects/Wiki/`. The LLM writes and maintains it; the human reads it and directs what goes in.

**Filing answers:** When a query produces a synthesis, comparison, or analysis worth keeping, file it as a wiki page rather than letting it disappear into chat history. Create `AI-Workshop/Projects/Wiki/<slug>.md`, add a row to `Context/Maps/content_index.md` under Analyses & Filed Answers, and append to `Context/History/log.md`:
```
## [<YYYY-MM-DD>] filed | <Title>
```

**The rule of thumb:** if you'd want to reference this answer in a future session, it belongs in the wiki.

**Ingest:** Adding new raw sources to the wiki goes through the [[ingest]] skill (`Context/Skills/ingest/SKILL.md`). Don't write wiki pages from a source without running that process — it exists to ensure cross-references and index entries are maintained, not just the summary page.

---

## Memory vs. main.md vs. base-rules.md

When recommending where something belongs, state the reasoning explicitly:
- **Memory** — working style preferences built up from interactions (how to work with the user). Persists across sessions, written by the AI.
- **main.md** — personal identity settings (Who I Am, project-specific overrides). Rarely changes. Owned by the user.
- **base-rules.md** (`Context/Systems/base-rules.md`) — behavioral rules and system guidelines (how to operate in the vault). Updates from the Starter. Do not edit for personal preferences.

---

_See [[systems_map]] for all active systems, [[session-lifecycle]] for session and maintenance rules, and `main.md` for always-on behavioral rules._
