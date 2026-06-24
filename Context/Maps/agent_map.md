# Agent Map

_Registry of all sub-agents in this vault. Each agent runs in isolation and handles heavy or mechanical work that would otherwise consume main-context tokens._

_For how agents work, see [[agent-system]] at `Context/Systems/agent-system.md`._

---

| Agent | Path | Purpose | Triggered By |
|---|---|---|---|
| wrap-up | `Context/Agents/wrap-up/AGENT.md` | Applies approved session changes, updates maps and open-work, writes handoff note (steps 2–5 of the wrap-up process) | wrap-up skill after Step 1 approval |
| vault-maintenance | `Context/Agents/vault-maintenance/AGENT.md` | Full vault scan: validates all references, checks maps, lints structured note sets, fixes safe issues automatically | wrap-up agent post-changes; any file rename/move/delete; on demand |
| session-start | `Context/Agents/session-start/AGENT.md` | Reads latest session history and open-work; returns orientation summary for the main agent to surface | Session start (non-trivial tasks) |
| backlink-scan | `Context/Agents/backlink-scan/AGENT.md` | Scans vault for notes related to a target document and inserts wikilinks where connection is substantive | After any new note or skill is created; on demand |
| skill-eval-runner | `Context/Agents/skill-eval-runner/AGENT.md` | Runs a single eval prompt with or without a skill and saves outputs + timing data | skill-creator (spawns pairs in parallel) |
| handoff-writer | `Context/Agents/handoff-writer/AGENT.md` | Writes the session handoff note to Context/History/ from a structured summary | wrap-up agent (step 5) |
| agent-detector | `Context/Agents/agent-detector/AGENT.md` | Analyzes recent session history to identify tasks that would benefit from becoming a new agent; surfaces candidates with justification | On demand; periodically during vault maintenance |

---

_See [[skill_map]] for skills. Agents and skills are tracked separately._
