# Agent: [Name]

_This file is a self-contained agent prompt. It is invoked by the main agent via the Agent tool and starts with no conversation history. All required context must come from the INPUTS block or be read from the filesystem._

---

## Purpose

[One paragraph: what this agent does and why it exists as an agent rather than a skill.]

---

## Inputs

The main agent appends these as a structured block at the end of this prompt:

| Parameter | Type | Description |
|---|---|---|
| `vault_path` | string | Absolute path to the vault root |
| `[param]` | string | [description] |

---

## Context to Load from Disk

Before beginning, read the following files (using vault_path as the root):

- `[file path]` — [why it's needed]

---

## Process

[Step-by-step instructions. Be explicit — this agent has no conversation history and cannot ask for clarification. Every decision point must be handled inline.]

### Step 1 — [Name]

[Instructions]

**Done when:** [Verifiable completion condition]

### Step 2 — [Name]

[Instructions]

**Done when:** [Verifiable completion condition]

---

## Output

Return a structured summary in this format:

```
STATUS: [completed | failed | partial]

[Section heading]
[Details]

[Section heading]
[Details]
```

The main agent will parse this and surface relevant parts to the user.

---

## Constraints

- [Constraint 1]
- [Constraint 2]
- Never ask for clarification — handle ambiguity using the rules defined here or skip and flag in output.
