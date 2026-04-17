#!/usr/bin/env python3
"""
rewrite_paths.py — Rewrite /assets/images/* references to R2 CDN URLs.

Reads path-map.json (produced by migrate_to_r2.py) and updates:
- data/articles.json: heroImage + images[] fields (JSON-aware)
- *.html files: string replacement
- server.py: string replacement (for SSR-rendered /works/{id} pages)

Preserves original files as *.bak on first run.

Usage:
    python3 rewrite_paths.py --dry-run
    python3 rewrite_paths.py               # applies changes
    python3 rewrite_paths.py --restore     # restore from .bak
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Files to rewrite. Relative to script's parent dir (village /村山良作/).
# .bak files are created on first modification.
HTML_TARGETS = [
    "index.html",
    "workflow.html",
    "teabar.html",
    "admin/index.html",
    "sort-hat/index.html",
    "wedding-packages/index.html",
    "wedding-packages/outdoor.html",
]
OTHER_TEXT_TARGETS = ["server.py"]
JSON_TARGETS = ["data/articles.json"]


def load_path_map(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def backup_once(target: Path) -> None:
    """Create {target}.bak on first modification. Idempotent."""
    bak = target.with_suffix(target.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(target, bak)


def restore_backups(base: Path, all_targets: list[str]) -> None:
    for rel in all_targets:
        t = base / rel
        bak = t.with_suffix(t.suffix + ".bak")
        if bak.exists():
            shutil.copy2(bak, t)
            print(f"  [restored] {t}")


def rewrite_json(path: Path, path_map: dict, dry_run: bool) -> int:
    """Rewrite articles.json heroImage + images[] fields."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    articles = raw["articles"] if isinstance(raw, dict) else raw

    changed = 0
    for art in articles:
        hero = art.get("heroImage")
        if hero and hero in path_map:
            art["heroImage"] = path_map[hero]
            changed += 1

        new_images = []
        for img in art.get("images", []) or []:
            if img in path_map:
                new_images.append(path_map[img])
                changed += 1
            else:
                new_images.append(img)
        if "images" in art:
            art["images"] = new_images

    if dry_run:
        print(f"  [dry] {path.name}: would change {changed} refs")
        return changed

    if changed == 0:
        return 0

    backup_once(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if isinstance(raw, dict):
        raw["articles"] = articles
        out = raw
    else:
        out = articles
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    print(f"  [OK] {path.name}: {changed} refs rewritten")
    return changed


def rewrite_text(path: Path, path_map: dict, dry_run: bool) -> int:
    """Text-based string replacement. Sorts keys by length descending to avoid
    partial replacement of shorter keys that are prefixes of longer ones."""
    content = path.read_text(encoding="utf-8")
    original = content

    # Sort longest first (prevents shorter-prefix partial matches)
    changed = 0
    for old in sorted(path_map.keys(), key=len, reverse=True):
        new = path_map[old]
        if old in content:
            occurrences = content.count(old)
            content = content.replace(old, new)
            changed += occurrences

    if content == original:
        if dry_run:
            print(f"  [dry] {path.name}: 0 refs")
        return 0

    if dry_run:
        print(f"  [dry] {path.name}: would change {changed} refs")
        return changed

    backup_once(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
    print(f"  [OK] {path.name}: {changed} refs rewritten")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Preview only")
    ap.add_argument("--restore", action="store_true", help="Restore from .bak files")
    ap.add_argument("--path-map", default="path-map.json", help="Path map JSON")
    ap.add_argument("--base", default=str(Path(__file__).parent), help="Base dir")
    args = ap.parse_args()

    base = Path(args.base).resolve()

    if args.restore:
        print(f"[INFO] Restoring from .bak in {base}")
        restore_backups(base, JSON_TARGETS + HTML_TARGETS + OTHER_TEXT_TARGETS)
        return

    pm_path = Path(args.path_map)
    if not pm_path.is_absolute():
        pm_path = (base / pm_path).resolve() if (base / pm_path).exists() else Path.cwd() / pm_path
    if not pm_path.is_file():
        print(f"[FATAL] path-map not found: {pm_path}", file=sys.stderr)
        sys.exit(1)

    path_map = load_path_map(pm_path)
    print(f"[INFO] Loaded path map: {len(path_map)} entries from {pm_path}")
    print(f"[INFO] Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print(f"[INFO] Base: {base}")
    print()

    total = 0

    print("JSON:")
    for rel in JSON_TARGETS:
        p = base / rel
        if p.is_file():
            total += rewrite_json(p, path_map, args.dry_run)
        else:
            print(f"  [MISS] {p}")

    print("HTML:")
    for rel in HTML_TARGETS:
        p = base / rel
        if p.is_file():
            total += rewrite_text(p, path_map, args.dry_run)
        else:
            print(f"  [MISS] {p}")

    print("Other text:")
    for rel in OTHER_TEXT_TARGETS:
        p = base / rel
        if p.is_file():
            total += rewrite_text(p, path_map, args.dry_run)
        else:
            print(f"  [MISS] {p}")

    print()
    print(f"[DONE] Total refs changed: {total}")


if __name__ == "__main__":
    main()
