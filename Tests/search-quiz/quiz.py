#!/usr/bin/env python3
"""Search quiz — the regression gate for search_notes.

A fixed set of questions, each with the note(s) that count as the right
answer. Run it before shipping ANY change that touches search (server code,
fusion weights, indexing): if the score drops against the last recorded
baseline, the change does not ship. This exists because a search capability
was once switched off with no measurement (2026-07-11) and nothing caught it.

Usage (from the vault root, with the kb venv python for hybrid mode):
    AI-Workshop/mcp-servers/kb/.venv/bin/python Tests/search-quiz/quiz.py

Plain python3 runs it too — it then measures keyword-only mode, which is the
score a machine without the kb install gets.

Add cases over time (one line each); never remove one because it fails.
Baseline 2026-07-11 (12 cases): hybrid 11/12, keyword-only 4/12.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("VAULT_PATH", str(ROOT))
os.environ.setdefault("KB_VAULT_PATH", str(ROOT))
os.environ.setdefault("KB_DATA_PATH", str(ROOT / "AI-Workshop" / "mcp-servers" / "kb" / "data"))

# (question, kind, substrings — a hit is any top-3 path containing one)
CASES = [
    ("stop sounding like a chatbot when I write", "vague", ["ai-language-tells"]),
    ("closing everything down at the end of a work session", "vague",
     ["wrap-up", "session-lifecycle", "session-handoff"]),
    ("what to do with old files nobody uses anymore", "vague",
     ["vault-rules", "vault-maintenance"]),
    ("breaking a huge note into smaller pieces", "vague", ["note-decomposition"]),
    ("saving something so the AI remembers it next time", "vague", ["remember"]),
    ("adding outside documents into my knowledge base", "vague", ["ingest"]),
    ("weighing the good and bad sides of a decision", "vague", ["pros-cons"]),
    ("when to hand work to a subagent instead of doing it inline", "vague", ["agent-system"]),
    ("archived tag frontmatter", "keyword", ["vault-rules"]),
    ("session lifecycle", "keyword", ["session-lifecycle"]),
    ("em-dash", "keyword", ["ai-language-tells", "base-rules"]),
    ("backlink scan", "keyword", ["vault-backlink-scan"]),
]


def main():
    spec = importlib.util.spec_from_file_location(
        "vault_server", ROOT / "AI-Workshop" / "mcp-servers" / "vault" / "server.py")
    server = importlib.util.module_from_spec(spec)
    sys.modules["vault_server"] = server
    spec.loader.exec_module(server)

    print("search mode:", server.search_mode())
    server.search_notes_core("warm up", 1)

    total = {"vague": [0, 0], "keyword": [0, 0]}
    failed = []
    for q, kind, truth in CASES:
        paths = [m["path"] for m in server.search_notes_core(q, 3)["matches"]]
        hit = any(t in p for p in paths for t in truth)
        total[kind][0] += hit
        total[kind][1] += 1
        print(("PASS" if hit else "MISS"), "[%s]" % kind, q)
        if not hit:
            failed.append({"query": q, "expected": truth, "got": paths})

    score = sum(v[0] for v in total.values())
    n = sum(v[1] for v in total.values())
    for kind, (h, k) in total.items():
        print("%s: %d/%d" % (kind, h, k))
    print("TOTAL: %d/%d" % (score, n))
    if failed:
        print(json.dumps(failed, indent=1))
    return score, n


if __name__ == "__main__":
    main()
