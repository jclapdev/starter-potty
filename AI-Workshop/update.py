#!/usr/bin/env python3
"""update.py — update an existing vault to the latest system, on any machine.

Run from the vault root:

    python AI-Workshop/update.py               # download the latest from GitHub
    python AI-Workshop/update.py --from kit.zip # use a zip you already have
    python AI-Workshop/update.py --no-setup     # don't re-run setup.py afterward

What it does:
  1. Gets the latest system (download, or from the zip you point it at).
  2. Saves a backup of your current system files first, so nothing is lost.
  3. Replaces ONLY the system files: skills, systems, agents, the four system
     maps, and the helper programs.
  4. Leaves everything personal untouched: your Projects, Resources, notes,
     history, memory, your main.md, and your machine settings.
  5. Re-runs setup.py so paths and config are correct for this machine.

No git required. Pure Python standard library, so any machine that can run the
system can run this.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]   # AI-Workshop/update.py -> vault root
STARTER_ZIP_URL = "https://github.com/jclapdev/starter-potty/archive/refs/heads/main.zip"

# The system. Everything here is replaced from the latest version. Anything not
# listed is never touched, so personal content is safe by default.
SYSTEM_FILES = [
    "CLAUDE.md",
    "HUMAN.md",
    "install.sh",
    "install.ps1",
    "update.sh",
    "update.ps1",
    "AI-Workshop/setup.py",
    "AI-Workshop/update.py",
    "Context/Maps/skill_map.md",
    "Context/Maps/systems_map.md",
    "Context/Maps/agent_map.md",
    "Context/Maps/vault_map.md",
]
SYSTEM_DIRS = [
    "Context/Skills",
    "Context/Systems",
    "Context/Agents",
    "AI-Workshop/vault-mcp",
    "AI-Workshop/kb-mcp",
    "AI-Workshop/mcp-sync",
    "AI-Workshop/hooks",
    "Start_Here",
]
# Inside a system folder, these are personal/machine items: never delete them
# even when the new version doesn't include them.
KEEP_DIRS = {".venv", "venv", "data", "__pycache__", "Archive", ".git"}
KEEP_FILES = {"servers.json", "servers.local.json"}
KEEP_SUFFIXES = (".bak",)

# A file that marks the root of an extracted system, used to locate it inside a zip.
ROOT_MARKER = "AI-Workshop/setup.py"


def _keep_file(name: str) -> bool:
    return name in KEEP_FILES or name.endswith(KEEP_SUFFIXES)


# --------------------------------------------------------------------------- #
# Getting the latest system into a temp folder
# --------------------------------------------------------------------------- #
def fetch_system(from_zip: str | None) -> tuple[Path, tempfile.TemporaryDirectory]:
    """Return (system_root, tempdir_handle). Caller keeps tempdir alive."""
    tmp = tempfile.TemporaryDirectory(prefix="vault-update-")
    tmp_path = Path(tmp.name)

    if from_zip:
        zip_path = Path(from_zip).expanduser()
        if not zip_path.exists():
            sys.exit("Could not find the zip file: %s" % zip_path)
        print("Using local zip: %s" % zip_path)
    else:
        zip_path = tmp_path / "system.zip"
        print("Downloading the latest system from GitHub...")
        try:
            import urllib.request
            urllib.request.urlretrieve(STARTER_ZIP_URL, str(zip_path))
        except Exception as exc:  # noqa: BLE001
            sys.exit("Could not download the update (no internet?).\n"
                     "Details: %s\n"
                     "If you are offline, run with --from path/to/kit.zip instead." % exc)

    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir()
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
    except zipfile.BadZipFile:
        sys.exit("That file is not a valid zip: %s" % zip_path)

    root = _locate_root(extract_dir)
    if root is None:
        sys.exit("The downloaded package doesn't look like the system "
                 "(couldn't find %s inside it)." % ROOT_MARKER)
    return root, tmp


def _locate_root(extract_dir: Path) -> Path | None:
    """Find the folder that contains ROOT_MARKER (handles the wrapper folder a
    zip usually adds, e.g. starter-potty-main/ or Starter/)."""
    if (extract_dir / ROOT_MARKER).exists():
        return extract_dir
    for child in sorted(extract_dir.iterdir()):
        if child.is_dir() and (child / ROOT_MARKER).exists():
            return child
    # Last resort: search a couple levels deep.
    for marker in extract_dir.rglob("setup.py"):
        if marker.parent.name == "AI-Workshop":
            return marker.parents[1]
    return None


# --------------------------------------------------------------------------- #
# Backup + apply
# --------------------------------------------------------------------------- #
def backup_current(backup_root: Path) -> int:
    count = 0
    for rel in SYSTEM_FILES:
        p = VAULT / rel
        if p.exists():
            dest = backup_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            count += 1
    for rel in SYSTEM_DIRS:
        p = VAULT / rel
        if p.exists():
            # Don't copy heavy/personal items into the backup.
            shutil.copytree(p, backup_root / rel,
                            ignore=shutil.ignore_patterns(*KEEP_DIRS),
                            dirs_exist_ok=True)
            count += 1
    return count


def mirror_dir(src: Path, dst: Path) -> None:
    """Make dst match src, but never delete personal/machine items (KEEP_*)."""
    dst.mkdir(parents=True, exist_ok=True)
    present = set()
    for root, _dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            present.add(str(rel / f))
            shutil.copy2(Path(root) / f, dst / rel / f)
    # Remove files the new version dropped, leaving KEEP_* alone.
    for root, dirs, files in os.walk(dst, topdown=True):
        dirs[:] = [d for d in dirs if d not in KEEP_DIRS]
        rel = Path(root).relative_to(dst)
        for f in files:
            if _keep_file(f):
                continue
            if str(rel / f) not in present:
                (Path(root) / f).unlink()


def apply_update(new_root: Path) -> tuple[int, int]:
    files_done = dirs_done = 0
    for rel in SYSTEM_FILES:
        src = new_root / rel
        if src.exists():
            dst = VAULT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            files_done += 1
    for rel in SYSTEM_DIRS:
        src = new_root / rel
        if src.exists():
            mirror_dir(src, VAULT / rel)
            dirs_done += 1
    return files_done, dirs_done


def run_setup() -> None:
    import subprocess
    setup = VAULT / "AI-Workshop" / "setup.py"
    if not setup.exists():
        print("  (setup.py not found; skipping)")
        return
    print("\nRe-running setup for this machine...")
    subprocess.run([sys.executable, str(setup)], cwd=str(VAULT))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Update this vault to the latest system.")
    ap.add_argument("--from", dest="from_zip", default=None,
                    help="Update from a zip file you already have, instead of downloading.")
    ap.add_argument("--no-setup", action="store_true",
                    help="Don't re-run setup.py after updating.")
    args = ap.parse_args()

    print("Vault: %s" % VAULT)
    new_root, tmp = fetch_system(args.from_zip)
    try:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_root = VAULT / "AI-Workshop" / ".update-backups" / stamp
        n = backup_current(backup_root)
        print("Backed up %d current system items to %s" % (n, backup_root))

        files_done, dirs_done = apply_update(new_root)
        print("Updated %d system files and %d system folders." % (files_done, dirs_done))
        print("Your projects, notes, history, and settings were not touched.")
    finally:
        tmp.cleanup()

    if not args.no_setup:
        run_setup()

    print("\nUpdate complete. Restart Claude so it loads the new system.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
