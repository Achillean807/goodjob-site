#!/usr/bin/env python3
"""
migrate_to_r2.py — Batch-convert and upload村山良作 images to Cloudflare R2.

Runs on the SERVER (where 2.3GB of originals live). Converts JPG/PNG to WebP
(quality 90), organizes them under works/{article.id}/, uploads via rclone,
and emits path-map.json for the path-rewrite script to consume.

Usage:
    # On server, after rclone is configured for r2:
    python3 migrate_to_r2.py --dry-run    # preview only
    python3 migrate_to_r2.py              # actually do it
    python3 migrate_to_r2.py --article lativ-magic-platform  # single article

Requirements:
    - Pillow (pip install Pillow)
    - rclone configured as 'r2' remote pointing at bucket 'goodjob-images'
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[FATAL] Pillow required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

try:
    import pillow_avif  # noqa: F401  -- registers AVIF format with Pillow
except ImportError:
    print("[WARN] pillow-avif-plugin not installed; AVIF files will fail", file=sys.stderr)

# --- Config ----------------------------------------------------------------

SRC_ROOT = Path("/srv/weddingwish/goodjob-sit")
ARTICLES_JSON = SRC_ROOT / "data" / "articles.json"
IMG_ROOT = SRC_ROOT / "assets" / "images"
R2_REMOTE = "r2:goodjob-images"
CDN_DOMAIN = "https://goodjob-img.weddingwishlove.com"
WEBP_QUALITY = 90
TMP_DIR = Path("/tmp/r2-migrate")
CONVERTIBLE_EXT = {".jpg", ".jpeg", ".png"}
PASSTHROUGH_EXT = {".webp"}  # already-optimized, copy as-is

# --- Classification --------------------------------------------------------

def classify_filename(filename: str, article_id: str) -> str:
    """
    Map a source filename to a clean destination filename under works/{id}/.
    Returns new filename including extension (.webp for convertibles).
    """
    base, ext = os.path.splitext(filename)
    ext = ext.lower()
    out_ext = ".webp" if ext in CONVERTIBLE_EXT else ext

    # Pattern 1: ends with -hero, -detail-N, -scene-N
    m = re.search(r"-(hero|detail-\d+|scene-\d+)$", base)
    if m:
        return f"{m.group(1)}{out_ext}"

    # Pattern 2: starts with article_id prefix (CMS upload style)
    if base.startswith(f"{article_id}_"):
        rest = base[len(article_id) + 1:].strip("_")
        rest = re.sub(r"_+", "_", rest)
        return f"{rest}{out_ext}"

    # Pattern 3: 8-hex-char hash prefix (older CMS uploads)
    m = re.match(r"^[0-9a-f]{8}_(.+)$", base)
    if m:
        return f"{m.group(1)}{out_ext}"

    # Fallback: sanitize and keep basename
    safe = re.sub(r"[^\w\-]", "_", base)
    return f"{safe}{out_ext}"


# --- Conversion ------------------------------------------------------------

def convert_or_copy(src: Path, dst: Path, quality: int = WEBP_QUALITY) -> bool:
    """Convert jpg/png → webp, or copy if already webp. Returns True on success."""
    ext = src.suffix.lower()
    dst.parent.mkdir(parents=True, exist_ok=True)

    if ext in PASSTHROUGH_EXT:
        shutil.copy2(src, dst)
        return True

    if ext not in CONVERTIBLE_EXT:
        # Unknown type — copy as-is
        shutil.copy2(src, dst)
        return True

    try:
        with Image.open(src) as img:
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(dst, format="WEBP", quality=quality, method=6)
        return True
    except Exception as e:
        print(f"  [WARN] Convert failed: {src} ({e})", file=sys.stderr)
        return False


# --- Upload ----------------------------------------------------------------

def rclone_copyto(src: Path, dst_path: str, dry_run: bool = False) -> bool:
    """Upload single file via rclone copyto. dst_path is 'r2:bucket/key'."""
    if dry_run:
        return True
    try:
        result = subprocess.run(
            ["rclone", "copyto", str(src), dst_path],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"  [WARN] rclone failed: {result.stderr.strip()}", file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  [WARN] rclone timeout: {src}", file=sys.stderr)
        return False


# --- Main ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Migrate村山良作 images to R2")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, no uploads")
    ap.add_argument("--article", help="Process single article by id")
    ap.add_argument("--quality", type=int, default=WEBP_QUALITY, help="WebP quality")
    ap.add_argument("--path-map", default="path-map.json", help="Output path map")
    args = ap.parse_args()

    print(f"[INFO] Reading {ARTICLES_JSON}")
    data = json.loads(ARTICLES_JSON.read_text(encoding="utf-8"))
    articles = data["articles"] if isinstance(data, dict) else data

    if args.article:
        articles = [a for a in articles if a.get("id") == args.article]
        if not articles:
            print(f"[FATAL] Article id not found: {args.article}", file=sys.stderr)
            sys.exit(1)

    print(f"[INFO] Processing {len(articles)} article(s)")
    print(f"[INFO] Mode: {'DRY-RUN (no uploads)' if args.dry_run else 'LIVE'}")
    print()

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    path_map = {}  # old_url -> new_url
    stats = {"converted": 0, "uploaded": 0, "skipped": 0, "missing": 0, "failed": 0}

    for idx, article in enumerate(articles, 1):
        aid = article.get("id", "").strip()
        if not aid:
            continue

        urls = []
        if article.get("heroImage"):
            urls.append(article["heroImage"])
        urls.extend(article.get("images", []) or [])
        urls = list(dict.fromkeys(urls))  # dedup preserving order

        print(f"[{idx}/{len(articles)}] {aid} ({len(urls)} images)")

        seen_dst = {}  # new_filename -> old_url (detect collisions within article)

        for url in urls:
            if not url or not url.startswith("/assets/images/"):
                print(f"  [SKIP] Non-assets URL: {url}")
                stats["skipped"] += 1
                continue

            rel = url.lstrip("/")
            src = SRC_ROOT / rel
            if not src.is_file():
                print(f"  [MISS] {src}")
                stats["missing"] += 1
                continue

            filename = src.name
            new_name = classify_filename(filename, aid)

            # Collision handling: if two source files map to the same dest name,
            # append counter to the second+
            if new_name in seen_dst and seen_dst[new_name] != url:
                stem, ext = os.path.splitext(new_name)
                c = 2
                while f"{stem}-{c}{ext}" in seen_dst:
                    c += 1
                new_name = f"{stem}-{c}{ext}"
            seen_dst[new_name] = url

            new_key = f"works/{aid}/{new_name}"
            new_url = f"{CDN_DOMAIN}/{new_key}"

            if args.dry_run:
                path_map[url] = new_url
                print(f"  [dry] {filename} → {new_key}")
                stats["converted"] += 1
                continue

            tmp_path = TMP_DIR / f"{aid}__{new_name}"
            ok = convert_or_copy(src, tmp_path, args.quality)
            if not ok:
                stats["failed"] += 1
                continue
            stats["converted"] += 1

            ok = rclone_copyto(tmp_path, f"{R2_REMOTE}/{new_key}", args.dry_run)
            if not ok:
                stats["failed"] += 1
                tmp_path.unlink(missing_ok=True)
                continue
            stats["uploaded"] += 1
            path_map[url] = new_url

            print(f"  [OK] {filename} → {new_key} ({tmp_path.stat().st_size // 1024}KB)")
            tmp_path.unlink(missing_ok=True)

    # Write path map
    pm_out = Path(args.path_map)
    pm_out.write_text(json.dumps(path_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print(f"[INFO] Path map written: {pm_out.resolve()} ({len(path_map)} entries)")
    print(f"[INFO] Stats: {stats}")


if __name__ == "__main__":
    main()
