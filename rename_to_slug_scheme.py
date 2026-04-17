#!/usr/bin/env python3
"""
rename_to_slug_scheme.py — Rename all existing R2 gallery images to
`works/{slug}/{slug}-{N}.webp` + move their -thumb.webp siblings alongside.

Walks data/articles.json in `images` order (so sequence N matches display order).
`hero.webp` / `hero-thumb.webp` are left untouched (they keep their special name).
articles.json is updated in-place; a `.pre-rename` backup is written first.

Usage:
    python3 rename_to_slug_scheme.py --dry-run    # preview
    python3 rename_to_slug_scheme.py              # do it
    python3 rename_to_slug_scheme.py --article {slug}

Requirements:
    - rclone configured with the same remote server.py uses
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_PATH = os.path.join(BASE_DIR, "data", "articles.json")

R2_REMOTE = os.environ.get("GOODJOB_R2_REMOTE", "r2:goodjob-images")
CDN_DOMAIN = os.environ.get("GOODJOB_CDN_DOMAIN", "https://goodjob-img.weddingwishlove.com")
RCLONE_BIN = os.environ.get("GOODJOB_RCLONE_BIN", "rclone")


def url_to_r2_key(url):
    if not url or not url.startswith(CDN_DOMAIN + "/"):
        return None
    return url[len(CDN_DOMAIN) + 1:]


def r2_url(key):
    return f"{CDN_DOMAIN}/{key}"


def r2_exists(key):
    try:
        result = subprocess.run(
            [RCLONE_BIN, "lsf", f"{R2_REMOTE}/{key}"],
            capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"[lsf-timeout] {key}\n")
        return False
    return result.returncode == 0 and result.stdout.strip() != ""


def r2_moveto(old_key, new_key):
    try:
        result = subprocess.run(
            [RCLONE_BIN, "moveto", f"{R2_REMOTE}/{old_key}", f"{R2_REMOTE}/{new_key}"],
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"[moveto-timeout] {old_key} -> {new_key}\n")
        return False
    if result.returncode != 0:
        sys.stderr.write(f"[moveto-fail] {old_key} -> {new_key}: {result.stderr.strip()}\n")
        return False
    return True


def basename(key):
    return key.rsplit("/", 1)[-1] if "/" in key else key


def is_hero_or_thumb(fname):
    lower = fname.lower()
    if lower in ("hero.webp", "hero-thumb.webp"):
        return True
    return lower.endswith("-thumb.webp")  # all thumbs handled via main file


def main():
    parser = argparse.ArgumentParser(description="Rename R2 objects to {slug}-{N}.webp")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--article", help="limit to one article slug")
    args = parser.parse_args()

    with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not args.dry_run:
        backup = ARTICLES_PATH + ".pre-rename"
        shutil.copy2(ARTICLES_PATH, backup)
        print(f"[backup] {backup}")

    articles = data.get("articles", [])

    total_renamed = 0
    total_skipped = 0
    total_failed = 0

    for article in articles:
        slug = str(article.get("id", ""))
        if args.article and slug != args.article:
            continue

        images = list(article.get("images") or [])
        hero_url = article.get("heroImage")
        url_map = {}  # old_url -> new_url, for heroImage post-fix

        seq = 0
        new_images = []
        for url in images:
            key = url_to_r2_key(url)
            if not key:
                new_images.append(url)
                continue
            fname = basename(key)
            if is_hero_or_thumb(fname):
                new_images.append(url)
                continue

            seq += 1
            new_fname = f"{slug}-{seq}.webp"
            new_key = f"works/{slug}/{new_fname}"

            if key == new_key:
                new_images.append(url)
                total_skipped += 1
                continue

            thumb_old = key[:-5] + "-thumb.webp" if key.lower().endswith(".webp") else None
            thumb_new = new_key[:-5] + "-thumb.webp"

            if args.dry_run:
                print(f"[dry] {slug}: {fname} -> {new_fname}")
                new_images.append(r2_url(new_key))
                url_map[url] = r2_url(new_key)
                total_renamed += 1
                continue

            # Catch-up: R2 already renamed on a prior partial run but articles.json
            # still has the old URL — just repoint.
            if not r2_exists(key) and r2_exists(new_key):
                new_url = r2_url(new_key)
                new_images.append(new_url)
                url_map[url] = new_url
                total_renamed += 1
                print(f"[catchup] {slug}: {fname} -> {new_fname}")
                continue

            if not r2_moveto(key, new_key):
                new_images.append(url)
                total_failed += 1
                continue

            if thumb_old and r2_exists(thumb_old):
                r2_moveto(thumb_old, thumb_new)

            new_url = r2_url(new_key)
            new_images.append(new_url)
            url_map[url] = new_url
            total_renamed += 1
            print(f"[ok] {slug}: {fname} -> {new_fname}")
            time.sleep(0.03)

        article["images"] = new_images

        # Update heroImage if it was pointing at a renamed object
        if hero_url and hero_url in url_map:
            article["heroImage"] = url_map[hero_url]

        # Persist progress after each article so a mid-script crash doesn't
        # lose work.  We write the FULL articles structure every time — cheap
        # since the file is small.
        if not args.dry_run and url_map:
            tmp = ARTICLES_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            os.replace(tmp, ARTICLES_PATH)

    if not args.dry_run:
        tmp = ARTICLES_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, ARTICLES_PATH)
        print(f"[write] {ARTICLES_PATH}")

    print(f"\nrenamed={total_renamed} skipped={total_skipped} failed={total_failed}")


if __name__ == "__main__":
    main()
