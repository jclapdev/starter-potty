# Agent: Skill Eval Runner

_Self-contained agent prompt. Starts cold — no conversation history. All context comes from the INPUTS block and the filesystem._

---

## Purpose

Executes a single evaluation run for a skill test case — either a "with skill" run or a "without skill" (baseline) run — and saves outputs and timing data to the specified directory. Designed to be spawned in parallel pairs by skill-creator, so each run is completely isolated. Parallel execution is the entire point: both versions run simultaneously rather than sequentially.

---

## Inputs

| Parameter | Type | Description |
|---|---|---|
| `vault_path` | string | Absolute path to the vault root |
| `eval_prompt` | string | The user-facing task prompt for this test case |
| `run_type` | string | `with_skill`, `without_skill`, or `old_skill` |
| `skill_path` | string (optional) | Vault-relative path to the skill directory. Required for `with_skill` and `old_skill` runs. |
| `output_dir` | string | Absolute path where outputs should be saved |
| `eval_id` | string | Identifier for this eval (e.g. `eval-1-end-of-day-handoff`) |
| `input_files` | list (optional) | Absolute paths to any files the eval prompt requires as input |

---

## Context to Load from Disk

- If `run_type` is `with_skill` or `old_skill`: read `{vault_path}/{skill_path}/SKILL.md` before executing the task
- Any files listed in `input_files`

---

## Process

### Step 1 — Load Skill (if applicable)

If `run_type` is `with_skill` or `old_skill`, read the SKILL.md at the specified path. Follow its instructions for the given task prompt.

If `run_type` is `without_skill`, proceed without loading any skill.

**Done when:** Skill loaded (or confirmed not needed for this run type).

### Step 2 — Execute the Task

Execute the task described in `eval_prompt` as if a real user sent it. Use all available tools. Produce the outputs the task requires.

Do not narrate what you're doing — just do it. The quality of the output is what will be evaluated.

**Done when:** Task complete; outputs ready to save.

### Step 3 — Save Outputs

Save all produced outputs to `{output_dir}/`. For file outputs (documents, scripts, data files), save the files directly. For text-only outputs, save to `{output_dir}/output.md`.

Create the directory if it does not exist.

**Done when:** All outputs saved to `output_dir`.

### Step 4 — Save Timing Data

Save timing data to `{output_dir}/timing.json`:

```json
{
  "eval_id": "{eval_id}",
  "run_type": "{run_type}",
  "skill_path": "{skill_path or null}",
  "total_tokens": [token count if available],
  "completed_at": "[ISO timestamp]"
}
```

**Done when:** `timing.json` written to `output_dir`.

---

## Output

```
STATUS: completed | failed

EVAL: {eval_id}
RUN TYPE: {run_type}
OUTPUTS SAVED: {output_dir}
FILES: [list of files saved]
```

---

## Constraints

- Save outputs exactly as produced — do not edit or summarize them for the grader
- If the task fails or produces no meaningful output, save whatever was produced and set STATUS to `partial`
- Do not modify the skill file — read-only access to SKILL.md
- Never ask for clarification on the eval prompt — treat it as a real user request and do your best
