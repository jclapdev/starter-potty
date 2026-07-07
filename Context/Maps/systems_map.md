# Systems Map

_Index of all active systems in this vault. Each system defines rules for a specific domain of work. Read the relevant system file before starting any task it governs._

---

| System | Path | Governs |
|---|---|---|
| document-workflow | `Context/Systems/document-workflow.md` | Document creation, output locations, backlinks |
| session-lifecycle | `Context/Systems/session-lifecycle.md` | Session start/end contract, status check, map/maintenance/handoff rules |
| agent-system | `Context/Systems/agent-system.md` | Sub-agent definitions, input/output contract, invocation pattern, registry |
| vault-rules | `Context/Systems/vault-rules.md` | Vault operating rules: meta-mode, navigation sequence, wikilinks, skills, file creation, maintenance, memory placement |
| ai-language-tells | `Context/Systems/ai-language-tells.md` | AI-language tells catalog, plain-word alternatives, and the pre-send self-check (supports the "No AI Tells" rule in `base-rules.md`) |
| base-rules | `Context/Systems/base-rules.md` | Core behavioral rules, output preferences, language guidelines, and keyword triggers — loaded via CLAUDE.md alongside personal `main.md`; ships from the Starter |
| glossary | `Context/Systems/glossary.md` | Plain-language, one-line definitions of system terms (user-facing). Paired with the per-mechanism pages in `Context/Guide/` |

---

## Memory

Persistent memory lives in `Context/Memory/` — see its `MEMORY.md` index. Memory holds **behavior preferences** (how to work with the user). It is distinct from Maps, which hold **vault structure** (where things are). The system memory path is only a redirect pointing here.

---

## Adding a New System

1. Create `Context/Systems/<system-name>.md` with a clear scope statement at the top.
2. Add a row to this table.
3. Add the system to the navigation sequence in `base-rules.md` if it applies to all tasks.
4. Update [[vault_map]] if the system introduces new folders.
5. Create its user guide: copy `Context/Guide/_template.md` to `Context/Guide/<system-name>.md`, fill the five sections, and add it to `Context/Guide/HUMAN.md`. Add glossary entries in `Context/Systems/glossary.md` for any new terms the system introduces. Docs are a byproduct of building the mechanism, not a later pass.
