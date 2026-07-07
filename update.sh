#!/usr/bin/env bash
#
# update.sh — one-line updater for the Claudian vault system (macOS / Linux).
#
# The companion to install.sh. install.sh is run once on a bare machine; this is
# run whenever you want the latest system improvements. It never touches your
# notes, projects, history, memory, main.md, or machine settings — only the
# system files are refreshed.
#
# One-liner (paste into Terminal):
#   curl -fsSL https://raw.githubusercontent.com/jclapdev/starter-potty/main/update.sh | bash
#
# It finds your vault, makes sure the updater is present (fetching it the first
# time if needed), and runs it. Safe to re-run.
#
# Override the vault location with:  CLAUDIAN_VAULT_DIR=~/somewhere bash update.sh
# Pass through to the updater, e.g. offline:  bash update.sh --from new-version.zip
#
set -euo pipefail

RAW_BASE="https://raw.githubusercontent.com/jclapdev/starter-potty/main"
VAULT_DIR="${CLAUDIAN_VAULT_DIR:-$HOME/ClaudeVault}"

say()  { printf '  %s\n' "$1"; }
die()  { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

# 1. Locate the vault. If the default isn't there and the current folder is a
#    vault, use that instead — so running this from inside a vault just works.
if [ ! -d "$VAULT_DIR/AI-Workshop" ]; then
  if [ -d "$PWD/AI-Workshop" ]; then
    VAULT_DIR="$PWD"
  else
    die "No vault found at $VAULT_DIR (no AI-Workshop folder).
       Set CLAUDIAN_VAULT_DIR to your vault, or run this from inside it.
       Starting fresh on a bare machine? Use install.sh instead."
  fi
fi
say "Vault: $VAULT_DIR"

# 2. Pick a Python.
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || die "Python 3 is not installed. Install it, then re-run."

# 3. Make sure the updater is present; fetch it the first time if not.
UPDATER="$VAULT_DIR/AI-Workshop/update.py"
if [ ! -f "$UPDATER" ]; then
  say "First run on this machine — fetching the updater…"
  mkdir -p "$VAULT_DIR/AI-Workshop"
  curl -fsSL "$RAW_BASE/AI-Workshop/update.py" -o "$UPDATER" \
    || die "Could not download the updater (no internet?)."
fi

# 4. Run it from the vault folder, passing through any extra flags.
say "Updating…"
( cd "$VAULT_DIR" && "$PY" AI-Workshop/update.py "$@" )
