# Agent Map

_Registry of all sub-agents in this vault. Each agent runs in isolation and handles heavy or mechanical work that would otherwise consume main-context tokens._

_For how agents work, see [[agent-system]] at `Context/Systems/agent-system.md`._

---

| Agent | Path | Purpose | Triggered By |
|---|---|---|---|
| backlink-scan | [[Context/Agents/backlink-scan/AGENT.md]] | Scans vault for notes related to a target document and inserts wikilinks where connection is substantive | After any new note or skill is created; on demand |
| skill-eval-runner | [[Context/Agents/skill-eval-runner/AGENT.md]] | Runs a single eval prompt with or without a skill and saves outputs + timing data | skill-creator (spawns pairs in parallel) |
| agent-detector | [[Context/Agents/agent-detector/AGENT.md]] | Analyzes recent session history to identify tasks that would benefit from becoming a new agent; surfaces candidates with justification | On demand; periodically during vault maintenance |
| prose-review | [[Context/Agents/prose-review/AGENT.md]] | Fresh-eyes reviewer for the judgment-layer AI-language tells the vault-verify hook can't catch (rule-of-three, tone, audience-wrong jargon); returns flagged lines and rewrites | Before finalizing a user-facing prose doc; over session docs at wrap-up |
