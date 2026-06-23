# Agent System

_Governs how sub-agents are defined, registered, and invoked. Read this before creating or calling any agent._

---

## What Agents Are

Agents are isolated sub-processes spawned by the main agent to handle heavy, mechanical, or parallelizable work. Unlike skills — which run inline and share the main conversation context — agents start cold with no conversation history, work entirely from filesystem state, and return a structured result.

**When to use an agent instead of a skill:**

- The task is heavy on file I/O (reading many files, scanning the vault) and would consume significant main-context tokens
- The task is fully mechanical — no judgment calls that require conversation history
- The task could benefit from parallelism (e.g., running eval pairs simultaneously)
- Isolating the work makes the main session cleaner and more responsive

**When to keep it inline:**
- The task requires conversation history (e.g., reviewing what happened this session)
- The task is fast and token-light
- The user needs real-time back-and-forth during execution

---

## How Agents Differ from Skills

| | Skills | Agents |
|---|---|---|
| Runs in | Main conversation context | Isolated sub-agent process |
| Has conversation history | Yes | No — starts cold |
| File access | Via main agent's tools | Own tools (Read, Write, Edit, Bash) |
| Invocation | Main agent follows SKILL.md inline | Main agent spawns via Agent tool |
| Self-contained | No — can rely on context | Yes — must declare all inputs explicitly |
| Returns | N/A (inline execution) | Structured result to main agent |
| Registered in | skill_map.md | agent_map.md |

---

## Agent File Structure

Each agent lives in `Context/Agents/<agent-name>/AGENT.md`. The file is the agent's complete prompt — everything it needs to do its job, since it has no context from the calling session.

```
Context/Agents/
├── TEMPLATE.md           # Standard template for new agents
├── wrap-up/
│   └── AGENT.md
├── vault-maintenance/
│   └── AGENT.md
├── session-start/
│   └── AGENT.md
├── backlink-scan/
│   └── AGENT.md
├── skill-eval-runner/
│   └── AGENT.md
└── handoff-writer/
    └── AGENT.md
```

Agents may also include a `scripts/` or `references/` directory following the same pattern as skills.

---

## Input/Output Contract

Every AGENT.md declares:

**Inputs** — parameters the main agent must pass at invocation time. These are appended to the agent prompt as a structured block:

```
--- INPUTS ---
vault_path: /Users/john/Desktop/Main
[other parameters...]
```

**Outputs** — what the agent returns to the main agent when done. Agents return a structured text summary that the main agent can parse and surface to the user. Format is defined per-agent in the AGENT.md.

---

## Invocation Pattern

To invoke an agent, the main agent:

1. Reads `Context/Agents/<name>/AGENT.md`
2. Appends the `--- INPUTS ---` block with the required parameters
3. Spawns the agent via the Agent tool with the combined content as the prompt
4. Receives the agent's result and surfaces relevant parts to the user

```
Agent({
  description: "<agent name> — <one-line task description>",
  prompt: "[AGENT.md contents]\n\n--- INPUTS ---\nvault_path: ...\n[other inputs]"
})
```

---

## Adding a New Agent

1. Create `Context/Agents/<agent-name>/AGENT.md` using `Context/Agents/TEMPLATE.md` as the starting point
2. Add a row to `Context/Maps/agent_map.md`
3. If the agent replaces or augments an existing skill, update that skill's SKILL.md to invoke the agent instead of running inline
4. Update `Context/Maps/vault_map.md` if the new agent introduces new folders

Do not add agents to `skill_map.md` — agents and skills are tracked separately.

---

## Meta-Agent (Planned)

A future agent — the **agent-detector** — will monitor session work and proactively identify tasks that would benefit from being extracted into a new agent. It will analyze patterns: repeated heavy file I/O, multi-step mechanical processes that recur across sessions, tasks that consume disproportionate main-context tokens. When it identifies a candidate, it surfaces a recommendation with justification.

See `open-work.md` for current status.

---

_See [[agent_map]] for the agent registry. See [[skill_map]] for skills. See [[systems_map]] for all active systems._
