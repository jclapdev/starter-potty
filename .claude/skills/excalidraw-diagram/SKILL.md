---
name: excalidraw-diagram
description: Create an Excalidraw diagram as an Obsidian note (.excalidraw.md), including flowcharts, progression maps, box-and-arrow overviews, and visual maps of any content. Use whenever the user asks for a diagram, a visual map, a flowchart, "draw this", or an .excalidraw file, and also when a note would clearly land better as boxes and arrows than as prose.
---

# Excalidraw Diagram

Generate a drawing the user opens in Obsidian's Excalidraw view. The format knowledge comes from a decoded known-good file, and the workflow is: build the scene with the generator, grade it with the checker, ship only at full marks. Full findings: `AI-Workshop/Projects/Wiki/excalidraw-diagrams.md`.

## Step 1: Plan the scene on a grid

Sketch the layout as data before touching files: which boxes, what text sits on which box, which arrows connect them. Work on a rough grid (the reference uses ~320px column spacing, ~220px rows, boxes ~280x150). Keep text short; a diagram that needs paragraphs should be a note instead.

## Step 2: Generate with the shared builder

Use `Tests/excalidraw/make_diagram.py` as a library (import `rect`, `text`, `arrow`, `build`) or extend it with a new `build_*` function. Do not hand-write the JSON; the builder carries the exact per-element field set a working file needs, and hand-rolled elements drift.

Format rules the builder enforces (do not fight them):

- The Drawing block is plain `json`; the plugin compresses it on its own next save.
- Every text element's id appears in `## Text Elements` as `<text> ^<id>`, matching exactly.
- Text floats free over boxes (`containerId: null`); arrows stay unbound. Both verified against the reference; both keep generation simple.
- Ids: short random strings, unique in the scene.

## Step 3: Grade before shipping

Run the answer-key check:

```bash
python3 Tests/excalidraw/check_diagram.py <the-new-file>.excalidraw.md
```

Anything under full marks (11/11) does not ship; fix and re-run. This is the Nothing Ships Untested gate for diagrams.

## Step 4: Deliver

- Default destination: next to the note the diagram illustrates, or where the user says. Name it `<topic>.excalidraw.md`.
- Tell the user: open the note, and the first time, switch to Excalidraw view from the note's More Options menu. If it renders wrong, say so; the structural check cannot see visual layout problems, only broken files.
- Add a `[[wikilink]]` to the diagram from the note it belongs to, so it is not an orphan.
