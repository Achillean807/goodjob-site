#!/usr/bin/env python3
"""
cleanup_migrated.py — Delete local originals that have been migrated to R2.

Reads path-map.json and deletes the local source files whose R2 URLs match
the given article slug. Verifies each file exists in R2 before deleting,
so a missing R2 object aborts the delete instead of losing data.

Usage:
    # Preview what would be deleted for one article
    python3 cleanup_migrated.py --article renai-civil --dry-run

    # Actually delete, with R2 verification per file
    python3 cleanup_migrated.py --article renai-civil

    # Delete for ALL migrated articles (dangerous, use after full confidence)
    python3 cleanup_migrated.py --all

Safety:
    - Only deletes files whose path appears as a key in path-map.json
    - Verifies R2 has the corresponding object before unlinking (default)
    - --no-verify skips the R2 check (faster, only for batch after spot checks)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SRC_ROOT = Path("/srv/weddingwish/goodjob-sit")
R2_REMOTE = "r2:goodjob-images"
CDN_HOST = "goodjob-img.weddingwishlove.com"
RCLONE_BIN = os.environ.get("GOODJOB_RCLONE_BIN", "rclone")


def r2_has(key: str) -> bool:
    """Return True if the bucket key exists in R2."""
    try:
        result = subprocess.run(
            [RCLONE_BIN, "lsf", f"{R2_REMOTE}/{key}"],
            capture_output=True, text=True, timeout=15,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except subprocess.TimeoutExpired:
        return False


def article_from_r2_url(url: str) -> str | None:
    """Extract article slug from R2 URL like
    https://goodjob-img.weddingwishlove.com/works/renai-civil/hero.webp
    """
    m = re.search(r"/works/([^/]+)/", url)
    return m.group(1) if m else None


def key_from_r2_url(url: str) -> str | None:
    """Extract the bucket key from a CDN URL."""
    m = re.search(rf"https?://{re.escape(CDN_HOST)}/(.+)$", url)
    return m.group(1) if m else None


def collect_targets(path_map: dict, article: str | None):
    """Return list of (local_path, r2_key) tuples to consider for deletion."""
    targets = []
    for local_url, r2_url in path_map.items():
        slug = article_from_r2_url(r2_url)
        if article and slug != article:
            continue
        if not slug:
            continue
        local_rel = local_url.lstrip("/")
        local_path = SRC_ROOT / local_rel
        key = key_from_r2_url(r2_url)
        if key:
            targets.append((local_path, key, slug))
    return targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--article", help="Restrict to a single article slug")
    ap.add_argument("--all", action="store_true", help="Process all migrated articles")
    ap.add_argument("--dry-run", action="store_true", help="Preview only")
    ap.add_argument("--no-verify", action="store_true",
                    help="Skip R2 existence check per file (risky)")
    ap.add_argument("--path-map", default="path-map.json")
    args = ap.parse_args()

    if not args.article and not args.all:
        print("[FATAL] Pass --article <slug> or --all", file=sys.stderr)
        sys.exit(2)

    pm_path = Path(args.path_map)
    if not pm_path.is_file():
        print(f"[FATAL] path-map not found: {pm_path}", file=sys.stderr)
        sys.exit(1)

    path_map = json.loads(pm_path.read_text(encoding="utf-8"))
    targets = collect_targets(path_map, None if args.all else args.article)
    if not targets:
        print("[INFO] No targets found")
        sys.exit(0)

    # Group by article for human-readable output
    by_article = {}
    for local_path, key, slug in targets:
        by_article.setdefault(slug, []).append((local_path, key))

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    verify_mode = "skip" if args.no_verify else "check-each"
    print(f"[INFO] Mode: {mode} | Verify R2: {verify_mode}")
    print(f"[INFO] Articles: {len(by_article)}, files: {len(targets)}")
    print()

    stats = {"deleted": 0, "missing_local": 0, "missing_r2": 0, "failed": 0}

    for slug in sorted(by_article.keys()):
        items = by_article[slug]
        print(f"[{slug}] {len(items)} files")

        for local_path, key in items:
            if not local_path.is_file():
                stats["missing_local"] += 1
                print(f"  [SKIP] already gone: {local_path}")
                continue

            if not args.no_verify and not args.dry_run:
                if not r2_has(key):
                    stats["missing_r2"] += 1
                    print(f"  [STOP] R2 missing {key}, NOT deleting {local_path}")
                    continue

            if args.dry_run:
                size_kb = local_path.stat().st_size // 1024
                print(f"  [dry] rm {local_path.name} ({size_kb}KB)")
                stats["deleted"] += 1
                continue

            try:
                local_path.unlink()
                stats["deleted"] += 1
                print(f"  [OK] removed {local_path.name}")
            except OSError as e:
                stats["failed"] += 1
                print(f"  [FAIL] {local_path}: {e}", file=sys.stderr)

    print()
    print(f"[DONE] {stats}")


if __name__ == "__main__":
    main()
