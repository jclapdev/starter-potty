# Vault Map

_High-level structure of this vault. Use this to orient before writing to or searching the vault._

---

## Structure

```
Main/
├── AI-Workshop/          # AI-managed working directory (Claude writes here)
│   ├── Artifacts/        # HTML exports, rendered guides
│   ├── vault-mcp/        # Vault navigation MCP server (stdlib, read-only) — the `vault` connector
│   ├── Projects/         # The AI's per-project working data
│   └── Scheduled/        # Scheduled task files
│
├── Workshop-Human/       # Human-managed scratch space (brain-dump intake) — excluded from scans
│
├── Session-Reports/      # Plain-English summaries of long-running sessions, for human review
│
├── Attachments/          # File attachments (currently empty)
│
├── Context/
│   ├── Agents/           # Sub-agent prompt files (one folder per agent) — see [[agent_map]]
│   ├── Diagnostics/      # System efficiency reports and fix backlogs
│   ├── History/          # Session notes + open-work.md (outstanding work)
│   ├── Maps/             # vault_map.md, skill_map.md, agent_map.md, systems_map.md
│   ├── Memory/           # Persistent memory files + MEMORY.md index
│   ├── Skills/           # Skill instruction files (one folder per skill) — see [[skill_map]]
│   └── Systems/          # System rule files (one per domain)
│
├── Tests/                # Skill eval workspaces and review output (excluded from scans)
├── Projects/             # Project notes (one .md per project)
│
└── Resources/            # Reference materials (USU theme, autodater assets, Claude Code vs. Cowork note)
```

> Skill and agent folders are intentionally not enumerated here. [[skill_map]] and [[agent_map]] are the source of truth for those lists — this map owns top-level structure only, so adding a skill or agent means editing one map, not two.

---

## Key Files

- Systems index: [[systems_map]] → `Context/Maps/systems_map.md`
- Document workflow rules: [[document-workflow]] → `Context/Systems/document-workflow.md`
- Session lifecycle rules: [[session-lifecycle]] → `Context/Systems/session-lifecycle.md`
- Agent system rules: [[agent-system]] → `Context/Systems/agent-system.md`
- Skill index: [[skill_map]] → `Context/Maps/skill_map.md`
- Agent index: [[agent_map]] → `Context/Maps/agent_map.md`
- Open work list: `Context/History/open-work.md`
- User instructions: `main.md` (vault root)

---

## Output Locations by Type

| Document Type | Location |
|---|---|
| Connector guides | `Projects/<Client>/Connector Documentation/` |
| HTML artifacts | `AI-Workshop/Artifacts/` |
| Summaries/digests | `AI-Workshop/Projects/` |
| Session notes | `Context/History/` |
| System diagnostics | `Context/Diagnostics/` |
| Long-running session reports | `Session-Reports/` |

---

## Note Status

Project notes carry a `status:` field in YAML frontmatter, queried via the `vault` connector's
`list_by_status` tool. Status is scoped to work that has a lifecycle — project notes in
`Projects/` — not reference notes, system files, maps, memory, or history, which have no
meaningful state and would only add noise to the query.

| Value | Meaning |
|---|---|
| `idea` | Captured, not started |
| `active` | In progress now |
| `blocked` | Can't proceed; waiting on an external dependency |
| `needs-eval` | Built but awaiting validation (e.g. a skill pending an eval pass) |
| `done` | Complete; no open work |

Human scratch space (`Workshop-Human/`) is excluded from scans via `Context/.vaultignore`, so
brain-dump intake files never appear in status, broken-link, or orphan queries.
