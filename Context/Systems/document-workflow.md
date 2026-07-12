# Document Workflow System

_Governs how documents are created, saved, and linked in this vault. Read this before any task that produces or edits a note or document._

---

## 1. Backlink Rule

After creating or significantly editing any markdown document in this vault, run the [[vault-backlink-scan]] process before saving the final file.

- Scan the vault for existing notes that are topically related to the document just created.
- Add `[[wikilinks]]` inline where relevant notes are referenced or implied.
- Do not add backlinks speculatively; only link where the connection is substantive.
- Do not create links to notes that don't exist unless the task explicitly calls for stub creation.

## 2. Source Path Rule

When a skill references a source file (PDF, doc, txt), use the real relative path from the vault root, not an Obsidian wikilink. Wikilinks are for notes, not source files.

Example: `Reference/Manuals/CONNECTORS/Crowdstrike_Falcon_Connector_Guide.pdf`

## 3. Output Location Rule

- Artifacts and HTML exports → `AI-Workshop/Projects/` (saved with the project they belong to)
- Summaries and digests → `AI-Workshop/Projects/`
- Wiki pages (source summaries, concept pages, entity pages, filed analyses) → `AI-Workshop/Projects/Wiki/`
- Skills stay in `Context/Skills/`
- System files stay in `Context/Systems/`

## 4. Wikilink Behavior

Per [[main]]: follow a `[[wikilink]]` only when the linked file is needed for the current task. Do not follow links out of index or map files. Load a map only when you need that specific index.

## 5. Prose Review Rule

Language enforcement has two layers. The `vault-verify` hook blocks the deterministic tells on every `.md` write (em-dashes, banned words, negative parallelism), so those never reach a saved file. It cannot catch the judgment-layer tells: rule-of-three cadence, tone, restated openers, tacked-on summaries, and jargon that is wrong for the reader.

So before finalizing a substantial **user-facing** prose doc (a `Context/Guide/` page, the glossary, a `HUMAN.md`, a Wiki page, or a report), run the [[prose-review]] agent over it and apply the rewrites it returns. The author is blind to their own tells, so a fresh-eyes reader catches what a re-scan misses. Skip it for short edits, AI-facing system files, and code. Wrap-up runs this pass over the session's user-facing docs as a backstop.

---

_See [[skill_map]] for the full skill index, [[vault_map]] for vault structure, [[systems_map]] for all active systems, and [[session-lifecycle]] for map maintenance, vault maintenance, and session handoff rules._
