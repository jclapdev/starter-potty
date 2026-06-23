# Agents

_Definitions for background helpers the AI can spin up for focused jobs._

## What this folder is for

Some jobs are better handled off to the side: reading a pile of files, running a check, writing a handoff. Each of those is an "agent" with its own instructions. Running them separately keeps your main conversation clean and fast.

## What lives here

One folder per agent, each with an `AGENT.md` that describes a single self-contained task. The AI calls on them when the moment fits. You don't run these yourself.
