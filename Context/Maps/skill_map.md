# Skill Map

_Index of all skills in this vault. Read the linked SKILL.md for full instructions._

Skills live in two homes. Shared skills sit in `Context/Skills/` and work on every surface (Code, Desktop, Claudian). Skills that need git or scripts sit in `.claude/skills/`, which only Claude Code and Claudian read; Desktop never sees them, by design.

---

| Skill               | Path                                          | Purpose                                                                                                               |
| ------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| vault-backlink-scan | [[Context/Skills/vault-backlink-scan/SKILL.md]] | Scans the vault for notes related to a target document and inserts wikilinks inline where the connection is substantive |
| session-handoff     | [[Context/Skills/session-handoff/SKILL.md]]     | Writes an end-of-session handoff note to Context/History/ and reads the most recent one at session start              |
| vault-maintenance   | [[Context/Skills/vault-maintenance/SKILL.md]]   | Systematic scan for broken references, stale map entries, orphaned links, and formatting inconsistencies; fixes safe issues automatically |
| note-decomposition  | [[Context/Skills/note-decomposition/SKILL.md]]  | Breaks a monolithic note into focused child files and replaces extracted content with wikilinks                        |
| wrap-up             | [[Context/Skills/wrap-up/SKILL.md]]             | End-of-session orchestrator — reviews conversation, surfaces improvements for approval, updates maps and open work, writes session handoff |
| theme-factory       | [[Context/Skills/theme-factory/SKILL.md]]       | Apply consistent professional styling (10 preset themes or custom) to artifacts: slides, docs, reports, HTML pages   |
| status              | [[Context/Skills/status/SKILL.md]]              | On-demand snapshot of available skills, last session focus, and all open work — read-only, no files modified          |
| pros-cons           | [[Context/Skills/pros-cons/SKILL.md]]           | Structures pros/cons breakdowns across immediate and scalable perspectives; flags divergence; closes with a recommendation |
| ingest              | [[Context/Skills/ingest/SKILL.md]]              | Process a source file into the wiki layer — writes a summary page, updates related concept/entity pages, refreshes content_index, and logs the operation |
| remember            | [[Context/Skills/remember/SKILL.md]]            | Save a working-style preference into `Context/Memory/` so it carries across sessions |

---

## Code/Claudian-only (native, `.claude/skills/`)

Claude Code and Claudian pick these up natively; they need git or scripts, so Desktop does not get them.

| Skill          | Path                                    | Purpose                                                                                                      |
| -------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| mcp-builder    | `.claude/skills/mcp-builder/SKILL.md`   | Guide for creating high-quality MCP servers in Python (FastMCP) or Node/TypeScript; covers tool design, API coverage, and error handling |
| skill-creator  | `.claude/skills/skill-creator/SKILL.md` | Create new skills from scratch, edit or optimize existing skills, run evals, and benchmark skill performance |
| publish-update | `.claude/skills/publish-update/SKILL.md` | Publish system changes to every machine: rebuild the Starter, check it, and push it plus the main vault      |
| system-update  | `.claude/skills/system-update/SKILL.md` | Re-orient after copying base-rules.md from the Starter: diffs the change, scans for stale references, reviews main.md, and produces a structured update report |


---

## Archived

_Superseded skills, kept for history. Tagged `#archived`; not part of the active roster._

| Skill | Path | Superseded | Replaced by |
|---|---|---|---|
| mcp-sync | [[Context/Skills/Archive/mcp-sync/SKILL.md]] | 2026-07-07 | `AI-Workshop/install.py` (re-run to reconfigure or update) |

---

## System Rules

All skills inherit from [[systems_map]] at `Context/Maps/systems_map.md`.

---

_See [[vault_map]] for overall vault structure and [[systems_map]] for active systems._
