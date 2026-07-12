#!/usr/bin/env python3
"""
Graded structural check for a generated .excalidraw.md file. Answer-key style:
every check is derived from the working reference file's decoded structure
(Personal/Albion/albion-pvp-progression-map.excalidraw.md, decoded 2026-07-12),
not from documentation. A FAIL on any check blocks shipping the generator.

Usage: python3 check_diagram.py <file.excalidraw.md>
"""

import json
import re
import sys
from pathlib import Path

REQUIRED_COMMON = {"id", "type", "x", "y", "width", "height", "angle",
                   "strokeColor", "backgroundColor", "fillStyle", "strokeWidth",
                   "strokeStyle", "roughness", "opacity", "groupIds", "frameId",
                   "roundness", "seed", "version", "versionNonce", "isDeleted",
                   "boundElements", "updated", "link", "locked"}
REQUIRED_TEXT = {"text", "rawText", "originalText", "fontSize", "fontFamily",
                 "textAlign", "verticalAlign", "containerId", "lineHeight", "baseline"}
REQUIRED_ARROW = {"points", "startBinding", "endBinding", "startArrowhead", "endArrowhead"}


def check(path):
    raw = Path(path).read_text(encoding="utf-8")
    results = []
    ok = lambda name, cond, detail="": results.append((name, bool(cond), detail))

    ok("frontmatter parsed flag", "excalidraw-plugin: parsed" in raw.split("---")[1])
    ok("excalidraw tag", re.search(r"tags:.*excalidraw", raw.split("---")[1]))
    ok("Text Elements section", "## Text Elements" in raw)

    m = re.search(r"## Drawing\n```json\n(.*?)\n```", raw, re.S)
    ok("plain json Drawing block", m)
    if not m:
        return report(results)
    try:
        scene = json.loads(m.group(1))
        ok("Drawing JSON parses", True)
    except Exception as e:
        ok("Drawing JSON parses", False, str(e))
        return report(results)

    ok("scene envelope", all(k in scene for k in ("type", "version", "source", "elements", "appState", "files"))
       and scene["type"] == "excalidraw" and scene["version"] == 2)

    els = scene["elements"]
    ids = [e["id"] for e in els]
    ok("ids unique", len(ids) == len(set(ids)))

    anchors = re.findall(r" \^(\w+)\n", raw.split("## Drawing")[0])
    text_ids = [e["id"] for e in els if e["type"] == "text"]
    ok("every text element anchored", set(anchors) == set(text_ids),
       f"anchors={len(anchors)} texts={len(text_ids)}")

    # Parse Text Elements entries: blocks separated by blank lines, each ending " ^id"
    section = raw.split("## Text Elements", 1)[1].split("## Drawing", 1)[0]
    by_anchor = {}
    for chunk in re.split(r"\n\s*\n", section):
        m2 = re.match(r"(.+?) \^(\w+)\s*$", chunk.strip(), re.S)
        if m2:
            by_anchor[m2.group(2)] = m2.group(1)
    bad = [e["id"] for e in els if e["type"] == "text" and by_anchor.get(e["id"], "").strip() != e["text"].strip()]
    ok("anchor text matches element text", not bad, f"mismatched: {bad}")

    for e in els:
        missing = REQUIRED_COMMON - set(e)
        if e["type"] == "text":
            missing |= REQUIRED_TEXT - set(e)
        if e["type"] == "arrow":
            missing |= REQUIRED_ARROW - set(e)
        if missing:
            ok(f"required fields ({e['type']} {e['id']})", False, f"missing {sorted(missing)}")
            break
    else:
        ok("required fields on every element", True)

    for e in els:
        if e["type"] == "arrow":
            pts = e["points"]
            good = isinstance(pts, list) and len(pts) >= 2 and pts[0] == [0, 0]
            if not good:
                ok(f"arrow points shape ({e['id']})", False, str(pts))
                break
    else:
        ok("arrow points start at [0,0]", True)

    return report(results)


def report(results):
    width = max(len(n) for n, _, _ in results)
    failed = 0
    for name, passed, detail in results:
        print(f"{'PASS' if passed else 'FAIL'}  {name:<{width}}  {detail}")
        failed += 0 if passed else 1
    print(f"\nTOTAL: {len(results) - failed}/{len(results)}")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if check(sys.argv[1]) else 1)
