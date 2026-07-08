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

Handled by the startup sequence in `base-rules.md`, which calls `get_session_brief` directly. Do not read history files inline.

## Skills

Skills live in two homes. Shared skills live in `Context/Skills/<skill-name>/SKILL.md` and work on every surface. Skills that need git or scripts (building MCP servers, creating skills, publishing updates) live in `.claude/skills/<skill-name>/SKILL.md`, which Claude Code and Claudian read natively and Desktop never sees. One home per skill, never both. Skill instructions extend system rules, they do not replace them. Read both.

**Skills are built _from_ learning sessions, not from a cold spec.** When a new tool, plugin, or capability looks skill-worthy, do not jump straight to building. First run a dedicated _learning session_: use the tool together with the user, work out the best way to operate it, and capture what you learn as a wiki page (`AI-Workshop/Projects/Wiki/`, via the [[ingest]] pattern or a direct page). The skill is then built from those documented findings — workflows that were actually tried, not a guess at what the workflow should be. This is the standard path for every new skill from here on.

**When building the skill, always route through skill-creator:** `.claude/skills/skill-creator/SKILL.md`. Do not write a SKILL.md directly without running that process — it exists to ensure skills are tested and validated, not just drafted. Feed it the learning-session findings as the starting intent.

Wrap-up still scans for skill opportunities (see `Context/Skills/wrap-up/SKILL.md`). Those scans surface _candidates for a learning session_, not skills to build on the spot: a flagged candidate becomes a queued learning session, and the skill follows once that session has produced findings.

**Never look at the Cowork plugin skills directory** (e.g., `/var/folders/.../skills/` or any path containing `claude-hostloop-plugins`). That is a system directory for Cowork's own tools, not your skills. If a task involves skills, the only valid locations are `Context/Skills/` and `.claude/skills/`.

## Maintenance Rule

When vault structure changes (new skill, new folder, new system), update the relevant map file immediately. Maps are the source of truth — stale maps break navigation.

## Archiving

When a file is superseded and no longer part of the active system, archive it rather than leaving it in place or deleting it. This follows common Obsidian practice: a folder for the physical archive, a tag for state, a graph color group for visual distinction.

1. Move it to a category-local `Archive/` folder (e.g. `Context/Agents/Archive/`, mirroring `Context/History/Archive/`).
2. Add `#archived` (frontmatter `tags: [archived]`) so its state is queryable wherever it sits.
3. In its registry (`agent_map`, `skill_map`), move the row to an `## Archived` section rather than deleting it, so the record survives.
4. Repoint any `[[wikilinks]]` to the new path; leave historical prose mentions as-is.

The graph has a color group on `tag:#archived` that greys archived notes, so they read differently from active ones at a glance. New users get this from the Starter.

## File Creation

**Never create files outside the vault without asking first.** If a file needs to exist somewhere other than its natural vault location, ask where and why before creating it.

**When a file deletion fails with "Operation not permitted", call `allow_cowork_file_delete` immediately** — do not surface the error to the user or ask them to handle it.

## Before Deleting or Restructuring

Before deleting, moving, or restructuring any system file or folder, do two checks first:

1. **Understand the design.** Load the relevant source-of-truth (latest handoff, plans, the maps, and any index file like `content_index.md`) and confirm how the piece is actually used. Do not act on an assumption about how the system works, verify it.
2. **Check what references it.** Grep the vault for the path before removing it. A file being clean and pushed does not mean it is unused, a folder can be load-bearing for skills, agents, hooks, or scheduled tasks that reference it by path.

"Is it committed and safe to delete?" is the wrong question. "What breaks if this is gone?" is the right one.

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
