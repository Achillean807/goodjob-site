#!/usr/bin/env python3
"""
upload_asset.py — Upload a single non-article image to R2 as site-wide static.

Use this for hero banners, section images, or any image referenced directly
from HTML (NOT from articles.json). Converts to WebP quality 90, uploads to
r2:goodjob-images/static/ (by default), prints the public CDN URL.

For CMS-managed article images, use the /admin/ upload UI instead — that
goes through server.py and updates articles.json automatically.

Typical workflow (from dev machine):

    # 1. Transfer image to server's /tmp
    scp my-banner.png achilean@100.102.51.64:/tmp/

    # 2. Convert + upload on server, capture URL
    ssh achilean@100.102.51.64 \\
      'python3 /srv/weddingwish/goodjob-sit/upload_asset.py /tmp/my-banner.png'
    # → https://goodjob-img.weddingwishlove.com/static/my-banner.webp

    # 3. Paste URL into your HTML/CSS, commit

Flags:
    --prefix static       R2 prefix under the bucket root (default: static)
    --name <filename>     Override destination filename (keeps original by default)
    --quality 90          WebP quality (1-100, default 90)
    --no-convert          Upload original bytes, skip WebP conversion
                          (use for .webp, .svg, .gif already optimized)
"""

import argparse
import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[FATAL] Pillow required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

R2_REMOTE = os.environ.get("GOODJOB_R2_REMOTE", "r2:goodjob-images")
CDN_DOMAIN = os.environ.get("GOODJOB_CDN_DOMAIN", "https://goodjob-img.weddingwishlove.com")
RCLONE_BIN = os.environ.get("GOODJOB_RCLONE_BIN", "rclone")
DEFAULT_PREFIX = "static"
DEFAULT_QUALITY = 90


def sanitize_key_component(name: str) -> str:
    """Keep URL-safe chars; replace spaces and odd chars with dash."""
    stem, ext = os.path.splitext(name)
    stem = re.sub(r"[\s]+", "-", stem)
    stem = re.sub(r"[^\w\-.]", "_", stem)
    return f"{stem}{ext.lower()}"


def to_webp(src_path: Path, quality: int) -> bytes:
    with Image.open(src_path) as img:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=quality, method=6)
        return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="Path to source image")
    ap.add_argument("--prefix", default=DEFAULT_PREFIX, help="Bucket prefix (default: static)")
    ap.add_argument("--name", help="Override destination filename")
    ap.add_argument("--quality", type=int, default=DEFAULT_QUALITY, help="WebP quality 1-100")
    ap.add_argument("--no-convert", action="store_true", help="Upload original bytes (no WebP)")
    args = ap.parse_args()

    src = Path(args.image)
    if not src.is_file():
        print(f"[FATAL] File not found: {src}", file=sys.stderr)
        sys.exit(1)

    ext = src.suffix.lower()
    convertible = ext in (".jpg", ".jpeg", ".png") and not args.no_convert
    passthrough_ext = {".webp", ".svg", ".gif", ".ico"}
    if args.no_convert or ext in passthrough_ext:
        data = src.read_bytes()
        out_name = args.name or src.name
    elif convertible:
        data = to_webp(src, args.quality)
        out_name = args.name or f"{src.stem}.webp"
    else:
        # Unknown/other format — upload raw
        data = src.read_bytes()
        out_name = args.name or src.name

    out_name = sanitize_key_component(out_name)
    key = f"{args.prefix.strip('/')}/{out_name}"

    # Upload via rclone subprocess
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(out_name).suffix or ".bin")
    try:
        tmp.write(data)
        tmp.close()
        result = subprocess.run(
            [RCLONE_BIN, "copyto", tmp.name, f"{R2_REMOTE}/{key}"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            print(f"[FATAL] rclone failed: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    url = f"{CDN_DOMAIN}/{key}"
    print(url)


if __name__ == "__main__":
    main()
