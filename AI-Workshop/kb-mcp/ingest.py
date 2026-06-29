#!/usr/bin/env python3
"""Bulk ingestion CLI for the KB.

    python ingest.py <path> [--tool <name>]

Ingests a single file or a whole directory (recursively) of .md/.txt/.pdf into
the same LanceDB store the server uses. Idempotent — unchanged files and
duplicate chunks are skipped, so re-running is safe and cheap.

This is a thin wrapper: the real pipeline (_gather_files / _process_file) lives
in server.py so there is one source of truth. Use this for large one-off loads;
use the ingest_kb MCP tool for ad-hoc ingestion from inside an agent session.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import server  # same directory


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ingest files into the KB.")
    parser.add_argument("path", help="File or directory to ingest.")
    parser.add_argument("--tool", default=None,
                        help="Tool name to tag chunks with (default: each file's stem).")
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        print("error: path not found: %s" % root, file=sys.stderr)
        return 1

    files = server._gather_files(root)
    if not files:
        print("no .md/.txt/.pdf files found under %s" % root, file=sys.stderr)
        return 1

    total_chunks = total_dupes = skipped = errors = 0
    for f in files:
        try:
            r = server._process_file(f, args.tool)
            ing = r.get("ingested", 0)
            if ing:
                total_chunks += ing
                total_dupes += r.get("duplicates", 0)
                print("ingested %-4d chunks  %s" % (ing, f))
            else:
                skipped += 1
                print("skipped (%s)  %s" % (r.get("skipped", "?"), f))
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print("ERROR  %s: %s" % (f, exc), file=sys.stderr)

    print("\ndone: %d files, %d chunks ingested, %d skipped, %d duplicate chunks, %d errors"
          % (len(files), total_chunks, skipped, total_dupes, errors))
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
