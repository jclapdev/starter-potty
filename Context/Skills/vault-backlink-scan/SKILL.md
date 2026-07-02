---
name: vault-backlink-scan
description: Scans the vault for notes related to a target document and inserts wikilinks inline where the connection is substantive. Use this skill whenever a document has just been created or significantly edited and needs backlinks added, or when the user asks to "add backlinks", "link this note", or "run the backlink scan." Also run automatically as the final step after any note decomposition pass.
---

# Skill: Vault Backlink Scan

**Purpose:** Scan the vault for notes related to a target document and insert `[[wikilinks]]` inline where the connection is substantive.

---

## Process

1. **Identify the target document** — the file just created or the file explicitly specified.

2. **Scan the vault** — read the file names and, where necessary, the contents of notes in:
   - `Projects/`
   - `Reference/`
   - `AI-Workshop/`
   - `Context/`
   - Any other top-level folders containing markdown notes

   Skip any path listed in `Context/.vaultignore` (the `Starter/` mirror, virtual environments, tests, eval workspaces, `node_modules`) — these add noise and can create links into duplicate trees.

3. **Identify link candidates** — a note is a candidate if:
   - Its title or subject is directly referenced or implied in the target document
   - It provides meaningful context a reader would benefit from following
   - The connection is specific, not generic (e.g. link to `[[Crowdstrike Falcon Connector Guide]]`, not to `[[Connectors]]` as a vague category)

4. **Insert wikilinks** — edit the target document in place:
   - Replace the first occurrence of a referenced term/title with `[[note name]]`
   - Do not repeat the wikilink for the same note more than once per document
   - Do not alter the surrounding prose — only wrap the term

5. **Report what was linked** — after editing, output a short list of links added and why. If no links were added, say so explicitly.

---

## Constraints

- Only link to notes that exist. Do not create stubs.
- Do not link to system files (`document-workflow.md`, any file in `Context/Systems/`, `SKILL.md`, `main.md`, `CLAUDE.md`) unless the document is itself a meta/system document.
- Do not add a backlinks section at the bottom — links go inline only.
- If the target document is inside `Context/Systems/` or `Context/Skills/`, apply judgment — link conservatively.

