#!/usr/bin/env python3
"""
cleanup_orphans.py — Quarantine local images not referenced anywhere.

Scans all HTML/CSS/JS/Python source for `/assets/images/*` references, then
moves any image file in assets/images/ that isn't referenced (and isn't in
path-map.json) into assets/images-trash/ — preserving relative layout.

Files are MOVED, not deleted. Run with `--purge` after a verification period
to remove the trash directory permanently.

Usage:
    python3 cleanup_orphans.py                   # dry-run (default)
    python3 cleanup_orphans.py --apply           # quarantine to trash
    python3 cleanup_orphans.py --restore         # move trash back
    python3 cleanup_orphans.py --purge           # rm -rf trash (irreversible)

Safety:
    - Reads path-map.json and adds its keys to the protected set
    - Scans .html/.css/.js/.py/.md/.json/.xml for references
    - Skips .bak / .pre-r2 backup files (stale refs don't block cleanup)
    - Default is dry-run; --apply required to modify
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

SRC_ROOT = Path("/srv/weddingwish/goodjob-sit")
IMAGES_DIR = SRC_ROOT / "assets" / "images"
TRASH_DIR = SRC_ROOT / "assets" / "images-trash"
PATH_MAP = SRC_ROOT / "path-map.json"

SOURCE_EXT = {".html", ".css", ".js", ".py", ".md", ".json", ".xml", ".txt"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico", ".avif"}
SKIP_SUFFIX = {".bak", ".pre-r2", ".tmp"}

# Reference regex: grab any `/assets/images/...ext` where ext is an image type.
# Require explicit leading slash to avoid greedy cross-URL captures (an earlier
# `\b`-anchored variant was pulling the whole host+path when `assets/images/`
# appeared multiple times in a single line).
REF_REGEX = re.compile(
    r"/assets/images/([\w\-./]+?\.(?:jpg|jpeg|png|webp|gif|svg|ico|avif))",
    re.IGNORECASE,
)


def is_skippable_source(path: Path) -> bool:
    """Skip backups, trash contents, and files inside assets/images/."""
    # Any parent equal to IMAGES_DIR or TRASH_DIR
    for parent in path.parents:
        if parent == IMAGES_DIR or parent == TRASH_DIR:
            return True
    # Skip backup files like articles.json.bak / articles.json.pre-r2
    for skip in SKIP_SUFFIX:
        if path.name.endswith(skip):
            return True
    return False


def collect_references() -> set[str]:
    """Walk source tree, return set of referenced relative paths under assets/images/."""
    refs = set()
    for p in SRC_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SOURCE_EXT:
            continue
        if is_skippable_source(p):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in REF_REGEX.finditer(content):
            # match.group(1) is everything after "assets/images/"
            refs.add(match.group(1).lstrip("/"))
    return refs


def load_path_map_protected() -> set[str]:
    """Keys from path-map.json as extra protected leaves."""
    if not PATH_MAP.is_file():
        return set()
    try:
        pm = json.loads(PATH_MAP.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    protected = set()
    for k in pm.keys():
        # k is like /assets/images/foo.webp
        leaf = k.lstrip("/")
        if leaf.startswith("assets/images/"):
            protected.add(leaf[len("assets/images/"):])
    return protected


def iter_image_files():
    """Yield (abs_path, leaf) for each image file under assets/images/."""
    if not IMAGES_DIR.is_dir():
        return
    for f in IMAGES_DIR.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in IMAGE_EXT:
            continue
        rel = str(f.relative_to(IMAGES_DIR)).replace("\\", "/")
        yield f, rel


def do_restore():
    if not TRASH_DIR.is_dir():
        print(f"[INFO] No trash to restore: {TRASH_DIR}")
        return
    moved = 0
    for f in TRASH_DIR.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(TRASH_DIR)
        dst = IMAGES_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), str(dst))
        moved += 1
    print(f"[DONE] Restored {moved} files from trash")


def do_purge():
    if not TRASH_DIR.is_dir():
        print(f"[INFO] No trash to purge: {TRASH_DIR}")
        return
    count = sum(1 for _ in TRASH_DIR.rglob("*") if _.is_file())
    size_mb = sum(f.stat().st_size for f in TRASH_DIR.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"[WARN] About to delete {count} files ({size_mb:.1f}MB) from {TRASH_DIR}")
    print("[WARN] This is IRREVERSIBLE. Ctrl-C within 5 seconds to abort.")
    try:
        import time
        for i in range(5, 0, -1):
            sys.stdout.write(f"\r  ... {i}s")
            sys.stdout.flush()
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        print("\n[ABORT] user cancelled")
        return
    shutil.rmtree(TRASH_DIR)
    print(f"[DONE] Purged {count} files ({size_mb:.1f}MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Move orphans to trash")
    ap.add_argument("--restore", action="store_true", help="Move trash contents back")
    ap.add_argument("--purge", action="store_true", help="Delete trash directory (irreversible)")
    args = ap.parse_args()

    if args.restore:
        do_restore()
        return
    if args.purge:
        do_purge()
        return

    # Build protected set
    refs = collect_references()
    pm_keys = load_path_map_protected()
    protected = refs | pm_keys
    print(f"[INFO] Source refs: {len(refs)} | path-map keys: {len(pm_keys)} | protected total: {len(protected)}")

    # Partition
    kept, orphans = [], []
    for f, leaf in iter_image_files():
        if leaf in protected:
            kept.append((f, leaf))
        else:
            orphans.append((f, leaf))

    total_size = sum(f.stat().st_size for f, _ in orphans)
    mb = total_size / 1024 / 1024
    print(f"[INFO] Kept: {len(kept)} | Orphans: {len(orphans)} ({mb:.1f}MB)")

    if not orphans:
        print("[DONE] Nothing to quarantine")
        return

    if not args.apply:
        print("\n[DRY-RUN] Sample orphans (first 20):")
        for f, leaf in sorted(orphans, key=lambda x: -x[0].stat().st_size)[:20]:
            print(f"  {leaf} ({f.stat().st_size // 1024}KB)")
        print(f"\n  ... total {len(orphans)} files, {mb:.1f}MB")
        print("\nRun with --apply to move these to assets/images-trash/")
        return

    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f, leaf in orphans:
        dst = TRASH_DIR / leaf
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(f), str(dst))
            moved += 1
        except OSError as e:
            print(f"[FAIL] {leaf}: {e}", file=sys.stderr)
    print(f"[DONE] Quarantined {moved}/{len(orphans)} files to {TRASH_DIR}")


if __name__ == "__main__":
    main()
