#!/usr/bin/env python3
"""
generate_thumbs.py — Back-fill `-thumb.webp` variants for existing R2 images.

Walks data/articles.json, for each image URL derives the R2 key, checks whether
a `{name}-thumb.webp` sibling already exists in R2, and if not, downloads the
original from the CDN, resizes to THUMB_WIDTH, and uploads via rclone.

Usage:
    python3 generate_thumbs.py             # do it
    python3 generate_thumbs.py --dry-run   # preview only
    python3 generate_thumbs.py --article {slug}   # limit to one article

Requirements:
    - Pillow
    - rclone configured with the same remote server.py uses
"""

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_PATH = os.path.join(BASE_DIR, "data", "articles.json")

R2_REMOTE = os.environ.get("GOODJOB_R2_REMOTE", "r2:goodjob-images")
CDN_DOMAIN = os.environ.get("GOODJOB_CDN_DOMAIN", "https://goodjob-img.weddingwishlove.com")
RCLONE_BIN = os.environ.get("GOODJOB_RCLONE_BIN", "rclone")
THUMB_WIDTH = int(os.environ.get("GOODJOB_THUMB_WIDTH", "400"))
THUMB_QUALITY = int(os.environ.get("GOODJOB_THUMB_QUALITY", "75"))

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS


def url_to_r2_key(url):
    if not url or not url.startswith(CDN_DOMAIN + "/"):
        return None
    return url[len(CDN_DOMAIN) + 1:]


def thumb_key_for(key):
    if not key.lower().endswith(".webp"):
        return None
    if key.endswith("-thumb.webp"):
        return None
    return key[:-5] + "-thumb.webp"


def r2_exists(key):
    result = subprocess.run(
        [RCLONE_BIN, "lsf", f"{R2_REMOTE}/{key}"],
        capture_output=True, text=True, timeout=15,
    )
    return result.returncode == 0 and result.stdout.strip() != ""


def r2_upload(data_bytes, key):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".webp")
    try:
        tmp.write(data_bytes)
        tmp.close()
        result = subprocess.run(
            [RCLONE_BIN, "copyto", tmp.name, f"{R2_REMOTE}/{key}"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            sys.stderr.write(f"[upload-fail] {key}: {result.stderr.strip()}\n")
            return False
        return True
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def fetch_original(url):
    req = urllib.request.Request(url, headers={"User-Agent": "generate_thumbs/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def make_thumb(data_bytes):
    img = Image.open(io.BytesIO(data_bytes))
    img = img.convert("RGBA" if img.mode in ("RGBA", "P") else "RGB")
    img.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 10), RESAMPLE)
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=THUMB_QUALITY, method=6)
    return buf.getvalue()


def main():
    parser = argparse.ArgumentParser(description="Back-fill R2 thumbnails.")
    parser.add_argument("--dry-run", action="store_true", help="preview without uploading")
    parser.add_argument("--article", help="limit to one article slug")
    parser.add_argument("--force", action="store_true", help="regenerate even if thumb exists")
    args = parser.parse_args()

    with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    total, skipped, generated, failed = 0, 0, 0, 0

    for article in articles:
        slug = str(article.get("id", ""))
        if args.article and slug != args.article:
            continue

        urls = list(article.get("images") or [])
        hero = article.get("heroImage")
        if hero and hero not in urls:
            urls.append(hero)

        for url in urls:
            key = url_to_r2_key(url)
            if not key:
                continue
            thumb_key = thumb_key_for(key)
            if not thumb_key:
                continue

            total += 1

            if not args.force and r2_exists(thumb_key):
                skipped += 1
                continue

            if args.dry_run:
                print(f"[dry] {slug}: would generate {thumb_key}")
                generated += 1
                continue

            try:
                orig = fetch_original(url)
            except Exception as e:
                sys.stderr.write(f"[fetch-fail] {url}: {e}\n")
                failed += 1
                continue

            try:
                thumb_bytes = make_thumb(orig)
            except Exception as e:
                sys.stderr.write(f"[resize-fail] {url}: {e}\n")
                failed += 1
                continue

            if r2_upload(thumb_bytes, thumb_key):
                print(f"[ok] {slug}: {thumb_key} ({len(thumb_bytes)} bytes)")
                generated += 1
            else:
                failed += 1

            time.sleep(0.05)

    print(f"\ntotal={total} generated={generated} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
