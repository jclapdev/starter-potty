# Document Workflow System

_Governs how documents are created, saved, and linked in this vault. Read this before any task that produces or edits a note or document._

---

## 1. Backlink Rule

After creating or significantly editing any markdown document in this vault, run the [[vault-backlink-scan]] process before saving the final file.

- Scan the vault for existing notes that are topically related to the document just created.
- Add `[[wikilinks]]` inline where relevant notes are referenced or implied.
- Do not add backlinks speculatively — only link where the connection is substantive.
- Do not create links to notes that don't exist unless the task explicitly calls for stub creation.

## 2. Source Path Rule

When a skill references a source file (PDF, doc, txt), use the real relative path from the vault root — not an Obsidian wikilink. Wikilinks are for notes, not source files.

Example: `Reference/Manuals/CONNECTORS/Crowdstrike_Falcon_Connector_Guide.pdf`

## 3. Output Location Rule

- Artifacts and HTML exports → `AI-Workshop/Artifacts/`
- Summaries and digests → `AI-Workshop/Projects/`
- Wiki pages (source summaries, concept pages, entity pages, filed analyses) → `AI-Workshop/Projects/Wiki/`
- Skills stay in `Context/Skills/`
- System files stay in `Context/Systems/`

## 4. Wikilink Behavior

Per [[main]]: follow a `[[wikilink]]` only when the linked file is needed for the current task. Do not follow links out of index or map files — load a map only when you need that specific index.

---

_See [[skill_map]] for the full skill index, [[vault_map]] for vault structure, [[systems_map]] for all active systems, and [[session-lifecycle]] for map maintenance, vault maintenance, and session handoff rules._
