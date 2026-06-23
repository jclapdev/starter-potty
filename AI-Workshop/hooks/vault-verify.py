#!/usr/bin/env python3
"""
PostToolUse hook — runs after Write/Edit on .md files in the vault.
Checks: broken outgoing wikilinks, AI-tell word scan.
Always exits 0 (non-blocking). Prints findings to stderr.

Vault root is inferred from this script's location:
  <vault-root>/AI-Workshop/hooks/vault-verify.py
"""

import json
import os
import re
import sys
from pathlib import Path

# Infer vault root from script location
VAULT_ROOT = Path(__file__).resolve().parent.parent.parent

# These files document the AI-tell rules — skip the AI-tell check on them
AI_TELL_SKIP = {
    "main.md",
    "Context/Systems/ai-language-tells.md",
}

# Directories to skip when building the wikilink index
INDEX_SKIP_DIRS = {
    ".git", ".obsidian", "__pycache__", "node_modules", "venv", ".venv",
}
# Subtree prefixes to skip (relative to vault root)
INDEX_SKIP_PREFIXES = (
    "AI-Workshop/Projects/Starter",
    "AI-Workshop/Projects/Starter.zip",
)

AI_TELLS = [
    # Vocabulary swaps (section 1)
    "delve", "underscore", "pivotal", "crucial", "vital",
    "realm", "landscape", "sphere", "harness", "leverage", "utilize",
    "facilitate", "illuminate", "foster", "cultivate",
    "streamline", "bolster", "embark", "unlock", "unleash", "unveil",
    "elevate", "robust", "seamless", "holistic", "multifaceted",
    "myriad", "plethora", "tapestry", "mosaic",
    # Hype (section 2)
    "revolutionize", "transformative", "groundbreaking", "cutting-edge",
    "game-changing", "state-of-the-art", "unparalleled", "supercharge",
    "turbocharge", "synergy",
    # Filler (section 3)
    "it's worth noting", "it is important to note", "needless to say",
    "at its core", "at the end of the day", "in today's",
    "in conclusion", "in summary",
    # Sycophancy (section 8)
    "great question", "certainly!", "absolutely!", "i'd be happy to",
    "i hope this helps", "feel free to",
    # Banned outright
    "vibe", "fluff",
]


def build_note_index():
    """Return a set of lowercase note names (without .md) in the vault."""
    names = set()
    for root, dirs, files in os.walk(VAULT_ROOT):
        rel_root = os.path.relpath(root, VAULT_ROOT)
        # Skip hidden and system dirs
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in INDEX_SKIP_DIRS
        ]
        # Skip Starter subtree
        if any(rel_root == p or rel_root.startswith(p + os.sep)
               for p in INDEX_SKIP_PREFIXES):
            dirs.clear()
            continue
        for fname in files:
            if fname.endswith(".md"):
                names.add(fname[:-3].lower())
    return names


def check_broken_links(content, note_index):
    """Return wikilink targets in content that don't resolve to any note."""
    links = re.findall(r'\[\[([^\]|#\n]+?)(?:[|#][^\]]*?)?\]\]', content)
    return [lnk.strip() for lnk in links if lnk.strip().lower() not in note_index]


def check_ai_tells(content):
    """Return AI-tell strings found in content (case-insensitive)."""
    lower = content.lower()
    return [t for t in AI_TELLS if t in lower]


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path.endswith(".md"):
        sys.exit(0)

    abs_path = Path(file_path).resolve()

    # Only scan files within this vault
    try:
        rel_path = abs_path.relative_to(VAULT_ROOT)
    except ValueError:
        sys.exit(0)

    if not abs_path.exists():
        sys.exit(0)

    content = abs_path.read_text(encoding="utf-8", errors="replace")
    issues = []

    # 1. Broken-link scan
    note_index = build_note_index()
    for link in check_broken_links(content, note_index):
        issues.append(f"  broken link  [[{link}]]")

    # 2. AI-tell scan (skip rule/catalog files)
    if str(rel_path) not in AI_TELL_SKIP:
        for tell in check_ai_tells(content):
            issues.append(f"  ai tell      '{tell}'")

    if issues:
        print(f"\nvault-verify: {rel_path}", file=sys.stderr)
        for issue in issues:
            print(issue, file=sys.stderr)
        print("", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
