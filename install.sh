#!/usr/bin/env bash
#
# install.sh — first-time, zero-tools installer for the Claudian vault system (macOS).
#
# For someone starting with NOTHING installed. It puts these on the machine:
#   1. Python 3          (setup.py needs it)
#   2. Obsidian          (your window into the vault)
#   3. Claude Desktop    (the app you chat with)
#   4. Claude Code       (the terminal agent)
#   5. The vault itself  (which carries the Claudian plugin)
# ...then hands off to AI-Workshop/setup.py, which wires up the MCP servers,
# hooks, and knowledge base.
#
# Zero-tools entry point (paste into Terminal):
#   curl -fsSL https://raw.githubusercontent.com/jclapdev/starter-potty/main/install.sh | bash
#
# Hybrid install: prefers Homebrew when present, falls back to official direct
# downloads when it is not. Safe to re-run: anything already present is skipped.
#
# Flags:
#   --dry-run   Detect what is present and print the plan. Installs nothing.
#   --help      Show this help.
#
# Override the vault location with:  CLAUDIAN_VAULT_DIR=~/somewhere bash install.sh
#
set -uo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
REPO_ZIP="https://github.com/jclapdev/starter-potty/archive/refs/heads/main.zip"
REPO_TOP_DIR="starter-potty-main"   # top folder GitHub puts inside the zip
VAULT_DIR="${CLAUDIAN_VAULT_DIR:-$HOME/ClaudeVault}"

# Official Claude Desktop DMG (universal), via Anthropic's redirect.
CLAUDE_DMG_URL="https://claude.ai/api/desktop/darwin/universal/dmg/latest/redirect"
# Claude Code native installer (recommended by Anthropic; no Node needed).
CLAUDE_CODE_INSTALL="https://claude.ai/install.sh"
# Obsidian latest release metadata (used only if Homebrew is unavailable).
OBSIDIAN_RELEASES_API="https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest"
# Claudian plugin — official Obsidian community plugin (repo yishentu/claudian).
# The /releases/latest/download/ path always resolves to the newest release asset.
PLUGIN_ID="realclaudian"
PLUGIN_BASE="https://github.com/yishentu/claudian/releases/latest/download"

DRY_RUN=0

# ── Output helpers ──────────────────────────────────────────────────────────
if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
  RED=$'\033[31m'; RESET=$'\033[0m'
else
  BOLD=""; DIM=""; GREEN=""; YELLOW=""; RED=""; RESET=""
fi
say()  { printf '%s\n' "$*"; }
section() { printf '\n%s== %s ==%s\n' "$BOLD" "$*" "$RESET"; }
ok()   { printf '  %s✓%s %s\n' "$GREEN" "$RESET" "$*"; }
skip() { printf '  %s•%s %s\n' "$DIM" "$RESET" "$*"; }
warn() { printf '  %s!%s %s\n' "$YELLOW" "$RESET" "$*"; }
fail() { printf '  %s✗%s %s\n' "$RED" "$RESET" "$*"; }

# ── Summary tracking ────────────────────────────────────────────────────────
DONE_LIST=""; SKIP_LIST=""; FAIL_LIST=""
mark_done() { DONE_LIST="${DONE_LIST}  ✓ $1"$'\n'; }
mark_skip() { SKIP_LIST="${SKIP_LIST}  • $1 (already present)"$'\n'; }
mark_fail() { FAIL_LIST="${FAIL_LIST}  ✗ $1"$'\n'; }

# ── Detection ───────────────────────────────────────────────────────────────
have() { command -v "$1" >/dev/null 2>&1; }
app_installed() {
  [ -d "/Applications/$1.app" ] || [ -d "$HOME/Applications/$1.app" ]
}

# Bring Homebrew onto PATH for this session, whichever prefix it uses.
load_brew_env() {
  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

# ── Homebrew ────────────────────────────────────────────────────────────────
ensure_homebrew() {
  section "Homebrew (package manager)"
  load_brew_env
  if have brew; then
    ok "Homebrew present"
    return 0
  fi
  if [ "$DRY_RUN" = 1 ]; then
    warn "would install Homebrew (interactive: asks for your password)"
    return 0
  fi
  warn "installing Homebrew — it will ask for your password and install Apple's command-line tools"
  if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
    load_brew_env
    have brew && { ok "Homebrew installed"; return 0; }
  fi
  warn "Homebrew did not install; falling back to direct downloads"
  return 1
}

# ── Generic DMG app install ─────────────────────────────────────────────────
# install_dmg <url> <AppName>
install_dmg() {
  local url="$1" app="$2" tmp mount appsrc dest
  tmp="$(mktemp -d)"
  say "  downloading ${app}.app ..."
  if ! curl -fsSL "$url" -o "$tmp/$app.dmg"; then
    rm -rf "$tmp"; return 1
  fi
  mount="$(mktemp -d)"
  if ! hdiutil attach "$tmp/$app.dmg" -nobrowse -mountpoint "$mount" >/dev/null 2>&1; then
    rm -rf "$tmp"; return 1
  fi
  appsrc="$(/usr/bin/find "$mount" -maxdepth 1 -name '*.app' -print -quit)"
  if [ -z "$appsrc" ]; then
    hdiutil detach "$mount" >/dev/null 2>&1; rm -rf "$tmp"; return 1
  fi
  dest="/Applications"
  if ! cp -R "$appsrc" "$dest/" 2>/dev/null; then
    dest="$HOME/Applications"; mkdir -p "$dest"
    cp -R "$appsrc" "$dest/" 2>/dev/null || { hdiutil detach "$mount" >/dev/null 2>&1; rm -rf "$tmp"; return 1; }
  fi
  # Remove the quarantine flag so first launch is smoother (best effort).
  xattr -dr com.apple.quarantine "$dest/$(basename "$appsrc")" 2>/dev/null || true
  hdiutil detach "$mount" >/dev/null 2>&1
  rm -rf "$tmp"
  return 0
}

# ── Python ──────────────────────────────────────────────────────────────────
PY="python3"
ensure_python() {
  section "Python 3"
  if have python3; then
    ok "python3 present ($(python3 --version 2>&1))"
    mark_skip "Python 3"; return 0
  fi
  if [ "$DRY_RUN" = 1 ]; then warn "would install Python 3 (brew, else python.org)"; return 0; fi
  if have brew && brew install python; then
    load_brew_env; ok "Python installed via Homebrew"; mark_done "Python 3"; return 0
  fi
  warn "could not install Python automatically"
  warn "install it from https://www.python.org/downloads/ then re-run this script"
  mark_fail "Python 3 (install manually from python.org)"
  return 1
}

# ── Obsidian ────────────────────────────────────────────────────────────────
ensure_obsidian() {
  section "Obsidian"
  if app_installed "Obsidian"; then ok "Obsidian present"; mark_skip "Obsidian"; return 0; fi
  if [ "$DRY_RUN" = 1 ]; then warn "would install Obsidian (brew cask, else .dmg)"; return 0; fi
  if have brew && brew install --cask obsidian; then
    ok "Obsidian installed via Homebrew"; mark_done "Obsidian"; return 0
  fi
  say "  fetching the latest Obsidian .dmg ..."
  local dmg
  dmg="$(curl -fsSL "$OBSIDIAN_RELEASES_API" \
        | grep -oE '"browser_download_url": *"[^"]*\.dmg"' \
        | grep -iE 'universal|\.dmg' | head -n1 \
        | sed -E 's/.*"(https[^"]*)".*/\1/')"
  if [ -n "$dmg" ] && install_dmg "$dmg" "Obsidian"; then
    ok "Obsidian installed from official .dmg"; mark_done "Obsidian"; return 0
  fi
  fail "could not install Obsidian — get it from https://obsidian.md/download"
  mark_fail "Obsidian (install manually from obsidian.md)"
  return 1
}

# ── Claude Desktop ──────────────────────────────────────────────────────────
ensure_claude_desktop() {
  section "Claude Desktop"
  if app_installed "Claude"; then ok "Claude Desktop present"; mark_skip "Claude Desktop"; return 0; fi
  if [ "$DRY_RUN" = 1 ]; then warn "would install Claude Desktop (brew cask, else official .dmg)"; return 0; fi
  if have brew && brew install --cask claude 2>/dev/null; then
    ok "Claude Desktop installed via Homebrew"; mark_done "Claude Desktop"; return 0
  fi
  if install_dmg "$CLAUDE_DMG_URL" "Claude"; then
    ok "Claude Desktop installed from official .dmg"; mark_done "Claude Desktop"; return 0
  fi
  fail "could not install Claude Desktop — get it from https://claude.ai/download"
  mark_fail "Claude Desktop (install manually from claude.ai/download)"
  return 1
}

# ── Claude Code ─────────────────────────────────────────────────────────────
ensure_claude_code() {
  section "Claude Code (terminal agent)"
  if have claude; then ok "Claude Code present ($(claude --version 2>&1 | head -n1))"; mark_skip "Claude Code"; return 0; fi
  [ -x "$HOME/.local/bin/claude" ] && { ok "Claude Code present (~/.local/bin)"; mark_skip "Claude Code"; return 0; }
  if [ "$DRY_RUN" = 1 ]; then warn "would install Claude Code (official native installer)"; return 0; fi
  say "  running the official Claude Code installer ..."
  if curl -fsSL "$CLAUDE_CODE_INSTALL" | bash; then
    ok "Claude Code installed"; mark_done "Claude Code"; return 0
  fi
  if have brew && brew install --cask claude-code; then
    ok "Claude Code installed via Homebrew"; mark_done "Claude Code"; return 0
  fi
  fail "could not install Claude Code — see https://code.claude.com/docs/en/setup"
  mark_fail "Claude Code (see code.claude.com/docs/en/setup)"
  return 1
}

# ── The vault (brings the Claudian plugin) ──────────────────────────────────
fetch_vault() {
  section "The vault (Claudian system + plugin)"
  if [ -d "$VAULT_DIR" ]; then
    warn "$VAULT_DIR already exists — leaving it untouched"
    mark_skip "Vault ($VAULT_DIR)"
    return 0
  fi
  if [ "$DRY_RUN" = 1 ]; then warn "would download the vault to $VAULT_DIR"; return 0; fi
  local tmp zip
  tmp="$(mktemp -d)"; zip="$tmp/vault.zip"
  say "  downloading the vault ..."
  if ! curl -fsSL "$REPO_ZIP" -o "$zip"; then
    fail "download failed"; rm -rf "$tmp"; mark_fail "Vault download"; return 1
  fi
  if ! /usr/bin/unzip -q "$zip" -d "$tmp"; then
    fail "could not unzip the vault"; rm -rf "$tmp"; mark_fail "Vault unzip"; return 1
  fi
  local extracted="$tmp/$REPO_TOP_DIR"
  [ -d "$extracted" ] || extracted="$(/usr/bin/find "$tmp" -maxdepth 1 -type d -name '*starter*' -print -quit)"
  if [ -z "$extracted" ] || [ ! -d "$extracted" ]; then
    fail "unexpected zip layout"; rm -rf "$tmp"; mark_fail "Vault extract"; return 1
  fi
  mkdir -p "$(dirname "$VAULT_DIR")"
  mv "$extracted" "$VAULT_DIR"
  rm -rf "$tmp"
  ok "vault ready at $VAULT_DIR"
  mark_done "Vault ($VAULT_DIR)"
  return 0
}

# ── Claudian plugin (into the vault's .obsidian) ────────────────────────────
enable_community_plugin() {
  local id="$1" cpj="$VAULT_DIR/.obsidian/community-plugins.json"
  if have python3; then
    python3 - "$cpj" "$id" <<'PY'
import json, os, sys
path, pid = sys.argv[1], sys.argv[2]
data = []
if os.path.exists(path):
    try:
        data = json.load(open(path))
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []
if pid not in data:
    data.append(pid)
json.dump(data, open(path, "w"), indent=2)
open(path, "a").write("\n")
PY
  else
    # No python yet: only write if there is no existing list to merge with.
    [ -f "$cpj" ] || printf '[\n  "%s"\n]\n' "$id" > "$cpj"
  fi
}

install_claudian_plugin() {
  section "Claudian plugin"
  if [ "$DRY_RUN" = 1 ]; then warn "would download the Claudian plugin into the vault and enable it"; return 0; fi
  if [ ! -d "$VAULT_DIR/.obsidian" ]; then
    warn "the vault has no .obsidian folder — skipping."
    warn "you can install Claudian later from Obsidian → Settings → Community plugins → search 'Claudian'."
    mark_fail "Claudian plugin (install from Obsidian community store)"
    return 1
  fi
  local dir="$VAULT_DIR/.obsidian/plugins/$PLUGIN_ID"
  mkdir -p "$dir"
  local all_ok=1
  for f in main.js manifest.json styles.css; do
    curl -fsSL "$PLUGIN_BASE/$f" -o "$dir/$f" || all_ok=0
  done
  if [ "$all_ok" != 1 ]; then
    fail "could not download the Claudian plugin."
    warn "install it later from Obsidian → Settings → Community plugins → search 'Claudian'."
    mark_fail "Claudian plugin (install from Obsidian community store)"
    return 1
  fi
  enable_community_plugin "$PLUGIN_ID"
  ok "Claudian plugin installed and enabled ($dir)"
  mark_done "Claudian plugin"
  return 0
}

# ── Hand off to setup.py ────────────────────────────────────────────────────
run_setup() {
  section "Configuring the system (setup.py)"
  local setup="$VAULT_DIR/AI-Workshop/setup.py"
  if [ "$DRY_RUN" = 1 ]; then warn "would run: python3 $setup"; return 0; fi
  if [ ! -f "$setup" ]; then
    warn "setup.py not found at $setup — skipping (vault may not have downloaded)"
    mark_fail "setup.py (not found)"
    return 1
  fi
  if ! have python3; then
    warn "Python 3 is not available, so setup.py can't run yet."
    warn "install Python, then run:  cd \"$VAULT_DIR\" && python3 AI-Workshop/setup.py"
    mark_fail "setup.py (needs Python)"
    return 1
  fi
  ( cd "$VAULT_DIR" && python3 AI-Workshop/setup.py ) && { mark_done "System configured (setup.py)"; return 0; }
  warn "setup.py did not finish cleanly — you can re-run it later:"
  warn "  cd \"$VAULT_DIR\" && python3 AI-Workshop/setup.py"
  mark_fail "setup.py (re-run manually)"
  return 1
}

# ── Summary + manual gates ──────────────────────────────────────────────────
print_summary() {
  section "Summary"
  [ -n "$DONE_LIST" ] && { say "${GREEN}Installed:${RESET}"; printf '%s' "$DONE_LIST"; }
  [ -n "$SKIP_LIST" ] && { say "${DIM}Already present:${RESET}"; printf '%s' "$SKIP_LIST"; }
  [ -n "$FAIL_LIST" ] && { say "${RED}Needs your attention:${RESET}"; printf '%s' "$FAIL_LIST"; }

  section "Last steps (these need you — they can't be automated)"
  say "  1. ${BOLD}Sign in${RESET} to Claude Desktop and to Claude Code (run 'claude' once in a terminal)."
  say "  2. ${BOLD}Open the vault in Obsidian${RESET}: Open folder as vault → choose:"
  say "        $VAULT_DIR"
  say "     The Claudian plugin is already installed and enabled. Obsidian may ask"
  say "     you to turn on community plugins / trust the author the first time —"
  say "     approve it."
  say "  3. ${BOLD}Restart Claude Desktop and Claude Code${RESET} so they load the new servers."
  say "  4. In either one, say: ${BOLD}read your instructions${RESET}"
  say ""
  say "  Full guide: $VAULT_DIR/HUMAN.md"
}

usage() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# ── Main ────────────────────────────────────────────────────────────────────
main() {
  case "${1:-}" in
    --help|-h) usage ;;
    --dry-run|--check) DRY_RUN=1 ;;
    "") : ;;
    *) fail "unknown option: $1"; exit 2 ;;
  esac

  say "${BOLD}Claudian first-time installer (macOS)${RESET}"
  say "Vault target: $VAULT_DIR"
  [ "$DRY_RUN" = 1 ] && say "${YELLOW}DRY RUN — detecting only, installing nothing.${RESET}"

  ensure_homebrew || true
  ensure_python || true
  ensure_obsidian || true
  ensure_claude_desktop || true
  ensure_claude_code || true
  fetch_vault || true
  install_claudian_plugin || true
  run_setup || true

  if [ "$DRY_RUN" = 1 ]; then
    head "Dry run complete"
    say "  Re-run without --dry-run to actually install."
    return 0
  fi
  print_summary
}

# Run only when executed directly, never when sourced (so tests can call
# individual functions without triggering a live install). The `return` trick is
# the portable way to detect sourcing; the $0/BASH_SOURCE comparison is unreliable.
( return 0 2>/dev/null ) && _CLAUDIAN_SOURCED=1 || _CLAUDIAN_SOURCED=0
if [ "$_CLAUDIAN_SOURCED" = 0 ]; then
  main "$@"
fi
