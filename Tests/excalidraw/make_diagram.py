#!/usr/bin/env python3
"""
Generate an Obsidian Excalidraw file (.excalidraw.md) in the plain "parsed" format.

Format learned 2026-07-12 from the working reference
a known-good reference drawing (decoded from its
compressed-json block with lzstring). Facts this generator relies on:

  - Frontmatter needs `excalidraw-plugin: parsed` and an `excalidraw` tag.
  - `## Text Elements` lists every text element's text followed by ` ^<id>`,
    and each anchor id must equal the JSON element's id exactly.
  - `## Drawing` holds a fenced `json` block with the whole Excalidraw scene.
    Writing plain json is valid; the plugin compresses it on its next save.
  - The reference uses free-floating text placed over rectangles (no
    containerId binding) and unbound arrows (startBinding/endBinding null),
    which keeps generation simple and renders fine.
  - fontFamily 2 = normal (Helvetica-like), 1 = hand-drawn, 3 = monospace.

Spec format (python dicts; see build_six_helpers() at the bottom for a real one):
  boxes:  {id, x, y, w, h, bg}
  texts:  {id, x, y, text, size=20, align="center"}
  arrows: {id, x, y, points=[[0,0],[dx,dy]]}
"""

import json
import random
import string
from pathlib import Path

FRONT = """---
excalidraw-plugin: parsed
tags: [excalidraw]
---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==


# Excalidraw Data

## Text Elements
"""


def _rid(n=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def _base(el_id, x, y, w, h):
    """Fields shared by every element, values copied from the working reference."""
    return {
        "id": el_id, "type": None, "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": None, "seed": random.randint(1, 2**31), "version": 1,
        "versionNonce": random.randint(1, 2**31), "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
    }


def rect(spec):
    e = _base(spec["id"], spec["x"], spec["y"], spec["w"], spec["h"])
    e.update(type="rectangle", roundness={"type": 3},
             backgroundColor=spec.get("bg", "#a5d8ff"))
    return e


def text(spec):
    body = spec["text"]
    size = spec.get("size", 20)
    lines = body.split("\n")
    w = spec.get("w", max(len(l) for l in lines) * size * 0.6)
    h = len(lines) * size * 1.25
    e = _base(spec["id"], spec["x"], spec["y"], w, h)
    e.update(type="text", text=body, rawText=body, originalText=body,
             fontSize=size, fontFamily=2, textAlign=spec.get("align", "center"),
             verticalAlign="middle", containerId=None, autoResize=True,
             lineHeight=1.25, baseline=int(h - size * 0.25), hasTextLink=False)
    return e


def arrow(spec):
    pts = spec.get("points", [[0, 0], [60, 0]])
    w = max(abs(p[0]) for p in pts)
    h = max(abs(p[1]) for p in pts)
    e = _base(spec["id"], spec["x"], spec["y"], w, h)
    e.update(type="arrow", points=pts, lastCommittedPoint=None,
             startBinding=None, endBinding=None,
             startArrowhead=None, endArrowhead="arrow",
             roundness={"type": 2}, elbowed=False)
    return e


def build(boxes, texts, arrows, extra_tags=None):
    elements = [rect(b) for b in boxes] + [text(t) for t in texts] + [arrow(a) for a in arrows]
    scene = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin",
        "elements": elements,
        "appState": {"theme": "light", "viewBackgroundColor": "#ffffff",
                     "gridSize": 20, "gridStep": 5, "gridModeEnabled": False},
        "files": {},
    }
    out = FRONT
    if extra_tags:
        out = out.replace("tags: [excalidraw]", f"tags: [excalidraw, {', '.join(extra_tags)}]")
    for t in texts:
        out += f"{t['text']} ^{t['id']}\n\n"
    out += "\n## Drawing\n```json\n" + json.dumps(scene) + "\n```\n"
    return out


def build_six_helpers():
    """A real diagram: the six helpers from the owner's manual."""
    helpers = [
        ("The finder", "answers 'where is X'\nwithout reading every file", "#a5d8ff"),
        ("The meaning memory", "search by what you mean,\nnot the exact words", "#b2f2bb"),
        ("Skills", "saved step-by-step\nprocedures for repeat jobs", "#ffec99"),
        ("Memory files", "how you like to work,\nread every session", "#ffd8a8"),
        ("The maps", "index pages: what exists\nand where it lives", "#eebefa"),
        ("Starter + installer", "the give-away copy and the\ncommand that wires a machine", "#ffc9c9"),
    ]
    boxes, texts, arrows = [], [], []
    title_id = _rid()
    texts.append({"id": title_id, "x": 240, "y": 20,
                  "text": "One folder. Six helpers. All so Claude reads, finds,\nwrites, and remembers your notes better.", "size": 24})
    for i, (name, desc, bg) in enumerate(helpers):
        col, row = i % 3, i // 3
        x, y = 60 + col * 320, 140 + row * 220
        bid, nid, did = _rid(), _rid(), _rid()
        boxes.append({"id": bid, "x": x, "y": y, "w": 280, "h": 150, "bg": bg})
        texts.append({"id": nid, "x": x + 20, "y": y + 20, "text": name, "size": 22, "w": 240})
        texts.append({"id": did, "x": x + 20, "y": y + 62, "text": desc, "size": 16, "w": 240})
        if col < 2:
            arrows.append({"id": _rid(), "x": x + 285, "y": y + 75, "points": [[0, 0], [30, 0]]})
    return build(boxes, texts, arrows, extra_tags=["system"])


if __name__ == "__main__":
    import sys
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "sample" / "six-helpers-map.excalidraw.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(build_six_helpers(), encoding="utf-8")
    print(f"wrote {dest}")
