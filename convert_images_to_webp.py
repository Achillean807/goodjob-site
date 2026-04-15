#!/usr/bin/env python3
"""
convert_images_to_webp.py
Batch-convert all JPEG/PNG images under assets/images/ to WebP,
and update all references in data/articles.json accordingly.
Original files are deleted after successful conversion.

Usage:
    cd src
    python convert_images_to_webp.py
    python convert_images_to_webp.py --quality 90   # default is 85
    python convert_images_to_webp.py --dry-run       # preview only
"""

import argparse
import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
ARTICLES_PATH = os.path.join(BASE_DIR, "data", "articles.json")

CONVERTIBLE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Exclude UI-only assets that should not be converted
EXCLUDE_PATTERNS = [
    r"favicon",
    r"apple-touch-icon",
    r"murayama-logo",
    r"weddingwish-logo",
    r"murayama-favicon",
]
EXCLUDE_RE = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)


def should_exclude(filename):
    return bool(EXCLUDE_RE.search(filename))


def collect_images(root):
    """Recursively find all convertible images."""
    targets = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in CONVERTIBLE_EXTENSIONS and not should_exclude(fname):
                targets.append(os.path.join(dirpath, fname))
    return targets


def convert_one(src_path, quality, dry_run):
    """Convert src_path to WebP. Returns webp path on success, None on failure."""
    dst_path = re.sub(r"\.[^.]+$", ".webp", src_path)

    if dry_run:
        print("  [dry-run] {} -> {}".format(src_path, dst_path))
        return dst_path

    try:
        with Image.open(src_path) as img:
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(dst_path, format="WEBP", quality=quality, method=6)
        return dst_path
    except Exception as exc:
        print("  [WARN] Conversion failed for {}: {}".format(src_path, exc))
        return None


def to_web_path(abs_file):
    """Convert absolute path to /assets/... web-relative path."""
    rel = os.path.relpath(abs_file, BASE_DIR).replace("\\", "/")
    if not rel.startswith("/"):
        rel = "/" + rel
    return rel


def update_articles_json(path_map, dry_run):
    """
    Update image paths in articles.json.
    path_map: dict of {old_web_path: new_web_path}
    Returns count of changed references.
    """
    try:
        with open(ARTICLES_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:
        print("[WARN] Cannot read articles.json: {}".format(exc))
        return 0

    articles = raw if isinstance(raw, list) else raw.get("articles", [])
    changed = 0

    for article in articles:
        # heroImage
        hero = article.get("heroImage", "")
        if hero in path_map:
            article["heroImage"] = path_map[hero]
            changed += 1

        # images[]
        new_images = []
        for img_path in article.get("images", []):
            if img_path in path_map:
                new_images.append(path_map[img_path])
                changed += 1
            else:
                new_images.append(img_path)
        article["images"] = new_images

    if dry_run:
        print("  [dry-run] Would update {} path references in articles.json".format(changed))
        return changed

    # Atomic write
    tmp = ARTICLES_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            if isinstance(raw, list):
                json.dump(articles, fh, ensure_ascii=False, indent=2)
            else:
                raw["articles"] = articles
                json.dump(raw, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, ARTICLES_PATH)
    except Exception as exc:
        print("[WARN] Failed to save articles.json: {}".format(exc))
        return 0

    return changed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Batch convert JPG/PNG images to WebP")
    parser.add_argument("--quality", type=int, default=85, help="WebP quality 1-100 (default: 85)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write any files")
    args = parser.parse_args()

    print("[INFO] Scanning: {}".format(IMAGES_DIR))
    targets = collect_images(IMAGES_DIR)
    print("       Found {} convertible images\n".format(len(targets)))

    if not targets:
        print("[OK] No images to convert.")
        return

    path_map = {}  # {old_web_path: new_web_path}
    converted = 0
    failed = 0

    for src in targets:
        old_web = to_web_path(src)
        dst = convert_one(src, args.quality, args.dry_run)
        if dst:
            new_web = to_web_path(dst)
            path_map[old_web] = new_web
            converted += 1
            if not args.dry_run:
                if os.path.isfile(dst):
                    os.remove(src)
                    print("  [OK] {} -> {}".format(
                        os.path.basename(src), os.path.basename(dst)))
        else:
            failed += 1

    print("\n[INFO] Updating articles.json ...")
    json_changes = update_articles_json(path_map, args.dry_run)
    print("       Updated {} path references".format(json_changes))

    if args.dry_run:
        print("\n[DONE] dry-run complete (no files written). Converted: {}, Failed: {}".format(converted, failed))
    else:
        print("\n[DONE] Converted: {}, Failed: {}".format(converted, failed))


if __name__ == "__main__":
    main()
