# Vault Map

_High-level structure of this vault. Use this to orient before writing to or searching the vault._

---

## Structure

```
YourVault/
├── AI-Workshop/          # AI-managed working directory (Claude writes here)
│   ├── Artifacts/        # HTML exports, rendered guides
│   ├── hooks/            # PostToolUse hooks (vault-verify runs on every file write)
│   ├── mcp-servers/      # System MCP servers: vault/ (navigation, stdlib) and kb/ (LanceDB knowledge base)
│   ├── install.py        # Run once to set the system up on this machine, then delete it (also updates)
│   ├── Projects/         # The AI's per-project working data
│   │   └── Wiki/         # LLM-owned knowledge layer (source summaries, concept pages, filed analyses)
│   └── Scheduled/        # Scheduled task files
│
├── Workshop-Human/       # Human-managed scratch space (brain-dump intake) — excluded from scans
│
├── Attachments/          # File attachments (currently empty)
├── Input/                # Drop files here for the AI to process
├── Start_Here/           # Onboarding — read these first to get set up
│
├── Context/
│   ├── Agents/           # Sub-agent prompt files (one folder per agent) — see [[agent_map]]
│   ├── History/          # Session notes + open-work.md (outstanding work)
│   ├── Maps/             # vault_map.md, skill_map.md, agent_map.md, systems_map.md
│   ├── Memory/           # Persistent memory files + MEMORY.md index
│   ├── Skills/           # Skill instruction files (one folder per skill) — see [[skill_map]]
│   └── Systems/          # System rule files (one per domain)
│
├── Projects/             # Project notes (one .md per project)
└── Resources/            # Reference materials
```

> Skill and agent folders are not enumerated here. [[skill_map]] and [[agent_map]] are the source of truth for those lists.

---

## Key Files

- Systems index: [[systems_map]] → `Context/Maps/systems_map.md`
- Document workflow rules: [[document-workflow]] → `Context/Systems/document-workflow.md`
- Session lifecycle rules: [[session-lifecycle]] → `Context/Systems/session-lifecycle.md`
- Agent system rules: [[agent-system]] → `Context/Systems/agent-system.md`
- Skill index: [[skill_map]] → `Context/Maps/skill_map.md`
- Agent index: [[agent_map]] → `Context/Maps/agent_map.md`
- Open work list: `Context/History/open-work.md`
- Activity log: `Context/History/log.md`
- Content index: [[content_index]] → `Context/Maps/content_index.md`
- Personal settings: `main.md` (vault root) — Who I Am, project-specific overrides
- System rules: [[base-rules]] → `Context/Systems/base-rules.md` — behavioral rules, output preferences, language guidelines

---

## Output Locations by Type

| Document Type | Location |
|---|---|
| HTML artifacts | `AI-Workshop/Artifacts/` |
| Summaries / digests | `AI-Workshop/Projects/` |
| Session notes | `Context/History/` |
| Wiki pages (source summaries, concept pages, filed analyses) | `AI-Workshop/Projects/Wiki/` |

---

## Note Status

Project notes carry a `status:` field in YAML frontmatter, queried via the `vault` connector's
`list_by_status` tool. Status is scoped to project notes in `Projects/` only.

| Value | Meaning |
|---|---|
| `idea` | Captured, not started |
| `active` | In progress now |
| `blocked` | Can't proceed; waiting on an external dependency |
| `needs-eval` | Built but awaiting validation |
| `done` | Complete; no open work |

Human scratch space (`Workshop-Human/`) is excluded from scans via `Context/.vaultignore`.
