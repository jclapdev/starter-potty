# Session Lifecycle System

_Governs how every working session starts, runs, and ends. Read this before starting any non-trivial task._

---

## 1. Session Start

Spawn the [[session-start]] agent (`Context/Agents/session-start/AGENT.md`) with `vault_path`. It reads the latest history file and open-work, then returns a structured orientation summary. Surface the Last Session and Open Work sections to the user before beginning new work.

Skip this if the session is clearly a one-off question with no vault work involved.

---

## 2. Session End

Run [[wrap-up]] when the user says "wrap up" or any clear equivalent. The wrap-up skill is the single entry point — it orchestrates the full end-of-session sequence in order:

1. Conversation review — surface improvements, flag candidates for new or updated skills/systems
2. Apply approved changes
3. Update maps
4. Update [[open-work]] — add new items, edit changed items, close completed items, remove irrelevant items
5. Run [[session-handoff]] — write the handoff note (pure narrative, no open-item tracking)

Do not run [[session-handoff]] or [[vault-maintenance]] manually as a shortcut for wrap-up unless the user explicitly asks. The full sequence exists for a reason.

---

## 3. Status Check

**Trigger:** User says "status".

**Purpose:** On-demand snapshot of vault capability and current work state. Not run automatically.

**Output:**

1. **What I can do** — list active skills from [[skill_map]] with one-line descriptions
2. **What we're working on** — current session's open tasks, if any
3. **What's still open** — contents of [[open-work]] (Open section only)

Run `Context/Skills/status/SKILL.md`.

---

## 4. Maintenance and Handoff Rules

These rules previously lived in `Context/Systems/document-workflow.md` sections 5–7. They now live here.

### Map Update Rule

When any of the following changes occur, update the relevant map files immediately — do not wait until the next session. This table is the immediate-update reminder only; full map verification is owned by [[vault-maintenance]] (run at every wrap-up), so it is not duplicated here.

| Change | File to update |
|---|---|
| New skill added | `Context/Maps/skill_map.md` |
| Skill removed or renamed | `Context/Maps/skill_map.md` |
| New top-level folder added | `Context/Maps/vault_map.md` |
| New system file added | `Context/Maps/systems_map.md` + [[main]] if navigation changes |
| Output location changes | `Context/Maps/vault_map.md` + [[document-workflow]] section 3 |

### Vault Maintenance Rule

Run [[vault-maintenance]] after any of the following:

- A file or folder is renamed
- A skill or system is added, removed, or relocated
- A map file is manually edited

Do not skip — stale references break navigation silently.

### Session Handoff Rule

Run [[session-handoff]] (via [[wrap-up]]) at the end of any session where meaningful work was done. At the start of a new session, read the most recent file in `Context/History/` before beginning non-trivial tasks.

---

_See [[skill_map]] for the full skill index, [[vault_map]] for vault structure, [[systems_map]] for all active systems, and [[document-workflow]] for document creation rules._
