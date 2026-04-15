#!/usr/bin/env python3
"""
Murayama Good Job Site — API + Static File Server

A lightweight HTTP server built on the standard library that serves static
files and exposes JSON API endpoints for article management.

Usage:
    python3 server.py
    python3 server.py --port 10814
    python3 server.py --bind 0.0.0.0 --port 8080
"""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
import io
import uuid
from http import HTTPStatus
try:
    from PIL import Image as _PILImage
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

# ---------------------------------------------------------------------------
# Paths (resolved relative to the script's own directory)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTICLES_PATH = os.path.join(DATA_DIR, "articles.json")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path):
    """Read and parse a JSON file.  Returns None on any error."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _write_json_atomic(path, data):
    """Write *data* as JSON to *path* atomically via a temp file + os.replace."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp_path, path)


def _load_config():
    """Return the admin config dict, or an empty dict on failure."""
    return _read_json(CONFIG_PATH) or {}


def _load_articles():
    """Return the articles list from disk, or an empty list."""
    data = _read_json(ARTICLES_PATH)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("articles"), list):
        return data["articles"]
    return []


def _save_articles(articles):
    """Persist the articles list to disk atomically."""
    os.makedirs(DATA_DIR, exist_ok=True)
    _write_json_atomic(ARTICLES_PATH, {"articles": articles})


def _json_bytes(obj, status_hint=200):
    """Serialise *obj* to UTF-8 JSON bytes."""
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")


def _parse_multipart(body, content_type):
    """
    Minimal multipart/form-data parser.

    Returns a list of dicts:
        [{"name": ..., "filename": ..., "content_type": ..., "data": bytes}, ...]

    Only handles the subset we need (file uploads).
    """
    # Extract boundary from Content-Type header
    m = re.search(r"boundary=([^\s;]+)", content_type)
    if not m:
        return []
    boundary = m.group(1).encode("utf-8")
    # RFC 2046: the actual delimiter is "--" + boundary
    delimiter = b"--" + boundary
    parts = body.split(delimiter)
    results = []
    for part in parts:
        # Skip preamble / epilogue
        if part in (b"", b"--", b"--\r\n", b"\r\n"):
            continue
        if part.startswith(b"--"):
            continue
        # Split headers from body (separated by \r\n\r\n)
        sep = part.find(b"\r\n\r\n")
        if sep == -1:
            continue
        header_block = part[:sep].decode("utf-8", errors="replace")
        file_data = part[sep + 4:]
        # Trim trailing \r\n left before next boundary
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]

        info = {"data": file_data}
        # Parse Content-Disposition
        for line in header_block.splitlines():
            line = line.strip()
            if line.lower().startswith("content-disposition:"):
                for token in line.split(";"):
                    token = token.strip()
                    if token.startswith("name="):
                        info["name"] = token.split("=", 1)[1].strip('" ')
                    elif token.startswith("filename="):
                        info["filename"] = token.split("=", 1)[1].strip('" ')
            elif line.lower().startswith("content-type:"):
                info["content_type"] = line.split(":", 1)[1].strip()
        results.append(info)
    return results


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class MurayamaHandler(SimpleHTTPRequestHandler):
    """Extends SimpleHTTPRequestHandler with JSON API routes."""

    # Override server_version for log output
    server_version = "MurayamaServer/1.0"

    # ------------------------------------------------------------------
    # Routing helpers
    # ------------------------------------------------------------------

    def _is_api(self):
        return self.path.startswith("/api/")

    def _is_admin_page(self):
        """Check if requesting /admin or /admin/"""
        stripped = self.path.split("?")[0].split("#")[0]
        return stripped in ("/admin", "/admin/")

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def _send_json(self, data, status=200):
        body = _json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status, message):
        self._send_json({"error": message}, status=status)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _check_auth(self):
        """
        Validate HTTP Basic Auth against data/config.json.
        Returns True if authenticated, False otherwise (and sends 401).
        """
        cfg = _load_config()
        expected_user = cfg.get("adminUser", "")
        expected_hash = cfg.get("adminPasswordHash", "")
        salt = cfg.get("adminSalt", "")

        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            self._send_401()
            return False

        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            user, password = decoded.split(":", 1)
        except Exception:
            self._send_401()
            return False

        computed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        if user != expected_user or computed != expected_hash:
            self._send_401()
            return False
        return True

    def _send_401(self):
        body = _json_bytes({"error": "Unauthorized"})
        self.send_response(401)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    # ------------------------------------------------------------------
    # Body reading
    # ------------------------------------------------------------------

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _read_json_body(self):
        raw = self._read_body()
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # ------------------------------------------------------------------
    # API: articles
    # ------------------------------------------------------------------

    def _api_get_articles(self):
        """GET /api/articles — return all articles with computed heroImage."""
        articles = _load_articles()
        for art in articles:
            # Compute heroImage path if images list exists
            images = art.get("images", [])
            if images and not art.get("heroImage"):
                art["heroImage"] = images[0]
        self._send_json({"articles": articles})

    def _api_get_images(self, article_id):
        """GET /api/images/{id} — return image list for an article."""
        articles = _load_articles()
        article = None
        for a in articles:
            if str(a.get("id")) == article_id:
                article = a
                break
        if article is None:
            self._send_error_json(404, "Article not found")
            return
        images = article.get("images", [])
        self._send_json({"id": article_id, "images": images})

    def _api_create_article(self):
        """POST /api/articles — create a new article (auth required)."""
        if not self._check_auth():
            return
        data = self._read_json_body()
        if not data or not isinstance(data, dict):
            self._send_error_json(400, "Invalid JSON body")
            return

        articles = _load_articles()
        # Assign a unique id
        new_id = data.get("id") or str(uuid.uuid4())[:8]
        # Ensure unique
        existing_ids = {str(a.get("id")) for a in articles}
        if new_id in existing_ids:
            self._send_error_json(409, f"Article id '{new_id}' already exists")
            return

        data["id"] = new_id
        data.setdefault("images", [])
        data.setdefault("createdAt", time.strftime("%Y-%m-%dT%H:%M:%S"))
        data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        articles.append(data)
        _save_articles(articles)
        self._send_json(data, status=201)

    def _api_update_article(self, article_id):
        """PUT /api/articles/{id} — update an existing article (auth required)."""
        if not self._check_auth():
            return
        data = self._read_json_body()
        if not data or not isinstance(data, dict):
            self._send_error_json(400, "Invalid JSON body")
            return

        articles = _load_articles()
        idx = None
        for i, a in enumerate(articles):
            if str(a.get("id")) == article_id:
                idx = i
                break
        if idx is None:
            self._send_error_json(404, "Article not found")
            return

        # Merge fields (preserve id)
        article = articles[idx]
        for key, val in data.items():
            if key == "id":
                continue  # never overwrite id
            article[key] = val
        article["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        articles[idx] = article
        _save_articles(articles)
        self._send_json(article)

    def _api_delete_article(self, article_id):
        """DELETE /api/articles/{id} — remove an article (auth required)."""
        if not self._check_auth():
            return

        articles = _load_articles()
        new_articles = [a for a in articles if str(a.get("id")) != article_id]
        if len(new_articles) == len(articles):
            self._send_error_json(404, "Article not found")
            return
        _save_articles(new_articles)
        self._send_json({"deleted": article_id})

    def _api_upload(self, article_id):
        """POST /api/upload/{id} — upload image for an article (auth required)."""
        if not self._check_auth():
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_error_json(400, "Expected multipart/form-data")
            return

        body = self._read_body()
        parts = _parse_multipart(body, content_type)
        if not parts:
            self._send_error_json(400, "No files found in upload")
            return

        # Find the article
        articles = _load_articles()
        article = None
        art_idx = None
        for i, a in enumerate(articles):
            if str(a.get("id")) == article_id:
                article = a
                art_idx = i
                break
        if article is None:
            self._send_error_json(404, "Article not found")
            return

        saved_paths = []
        for part in parts:
            filename = part.get("filename")
            if not filename:
                continue
            # Sanitise filename: keep only safe characters
            safe_name = re.sub(r"[^\w.\-]", "_", filename)
            # Prefix with article id to organise images
            target_name = f"{article_id}_{safe_name}"
            # Convert to WebP if Pillow is available
            img_data = part["data"]
            if _PILLOW_AVAILABLE:
                try:
                    img = _PILImage.open(io.BytesIO(img_data))
                    img = img.convert("RGBA" if img.mode in ("RGBA", "P") else "RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="WEBP", quality=85)
                    img_data = buf.getvalue()
                    target_name = os.path.splitext(target_name)[0] + ".webp"
                except Exception:
                    pass  # fallback: keep original
            target_path = os.path.join(IMAGES_DIR, target_name)
            with open(target_path, "wb") as fh:
                fh.write(img_data)
            # Relative web path
            web_path = f"/assets/images/{target_name}"
            saved_paths.append(web_path)

        # Update article images list
        if "images" not in article:
            article["images"] = []
        article["images"].extend(saved_paths)
        article["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        articles[art_idx] = article
        _save_articles(articles)

        self._send_json({"uploaded": saved_paths}, status=201)

    # ------------------------------------------------------------------
    # Route dispatcher
    # ------------------------------------------------------------------

    def _route_api(self, method):
        """Dispatch an API request.  Returns True if handled."""
        path = self.path.split("?")[0].rstrip("/")
        path = unquote(path)

        # GET /api/articles
        if method == "GET" and path == "/api/articles":
            self._api_get_articles()
            return True

        # GET /api/images/{id}
        if method == "GET" and path.startswith("/api/images/"):
            article_id = path[len("/api/images/"):]
            if article_id:
                self._api_get_images(article_id)
                return True

        # POST /api/articles
        if method == "POST" and path == "/api/articles":
            self._api_create_article()
            return True

        # PUT /api/articles/{id}
        if method == "PUT" and path.startswith("/api/articles/"):
            article_id = path[len("/api/articles/"):]
            if article_id:
                self._api_update_article(article_id)
                return True

        # DELETE /api/articles/{id}
        if method == "DELETE" and path.startswith("/api/articles/"):
            article_id = path[len("/api/articles/"):]
            if article_id:
                self._api_delete_article(article_id)
                return True

        # POST /api/upload/{id}
        if method == "POST" and path.startswith("/api/upload/"):
            article_id = path[len("/api/upload/"):]
            if article_id:
                self._api_upload(article_id)
                return True

        return False

    # ------------------------------------------------------------------
    # HTTP method overrides
    # ------------------------------------------------------------------

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self._is_api():
            if not self._route_api("GET"):
                self._send_error_json(404, "Not found")
            return
        # Serve /admin and /admin/ as admin/index.html
        if self._is_admin_page():
            self.path = "/admin/index.html"
        clean_path = self.path.split("?")[0].split("#")[0]
        # Serve /sitemap.xml dynamically
        if clean_path == "/sitemap.xml":
            self._serve_sitemap()
            return
        # Serve /works/{id} as dynamic SEO page
        if clean_path.startswith("/works/"):
            article_id = clean_path[len("/works/"):].strip("/")
            if article_id:
                self._serve_works_page(article_id)
                return
        # Fall through to static file serving
        super().do_GET()

    def _serve_works_page(self, article_id):
        """Dynamically generate an SEO-friendly HTML page for a work."""
        articles = _load_articles()
        article = next((a for a in articles if a.get("id") == article_id), None)
        if not article:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")
            return

        site_url = "https://goodjob.weddingwishlove.com"
        page_url = f"{site_url}/works/{article_id}"
        title = article.get("title", "")
        description = article.get("description", "")
        # Truncate description for meta (160 chars)
        meta_desc = description[:157] + "..." if len(description) > 160 else description
        # Hero image
        hero = article.get("heroImage") or ""
        if hero and not hero.startswith("http"):
            og_image = site_url + hero
        else:
            og_image = hero or f"{site_url}/assets/images/og-default.jpg"

        cat_labels = {
            "business": "主題活動", "party": "春酒尾牙",
            "magic": "魔法學院", "civil": "戶政改造"
        }
        cat_label = cat_labels.get(article.get("category", ""), "作品")
        images = article.get("images") or ([hero] if hero else [])

        # Gallery HTML — alt = 標題 + 分類 + 關鍵字，幫助 Google Image Search
        img_alt_suffix = f"{cat_label}活動佈置 村山良作"
        gallery_html = ""
        for i, img in enumerate(images[:20], 1):
            escaped = img.replace('"', '&quot;')
            alt = f"{title} {img_alt_suffix} {i}"
            gallery_html += f'<img src="{escaped}" alt="{alt}" loading="lazy">\n'

        # JSON-LD structured data
        jsonld = {
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            "name": title,
            "description": meta_desc,
            "image": og_image,
            "url": page_url,
            "author": {
                "@type": "Organization",
                "name": "村山良作 Murayama Goodjob",
                "url": site_url
            },
            "genre": cat_label
        }
        import json as _json
        jsonld_str = _json.dumps(jsonld, ensure_ascii=False)

        css_v = "20260406b"
        html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}｜村山良作 Murayama Goodjob</title>
  <meta name="description" content="{meta_desc}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}｜村山良作">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:site_name" content="村山良作 Murayama Goodjob">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}｜村山良作">
  <meta name="twitter:description" content="{meta_desc}">
  <meta name="twitter:image" content="{og_image}">
  <link rel="canonical" href="{page_url}">
  <link rel="stylesheet" href="/assets/site.css?v={css_v}">
  <script type="application/ld+json">{jsonld_str}</script>
  <style>
    .works-page {{ max-width: 960px; margin: 0 auto; padding: 100px 24px 60px; }}
    .works-hero {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; border-radius: 8px; display: block; }}
    .works-meta {{ margin: 24px 0 8px; display: flex; align-items: center; gap: 12px; }}
    .works-title {{ font-size: clamp(1.8rem, 3vw, 2.8rem); margin: 0 0 20px; line-height: 1.2; }}
    .works-desc {{ font-size: 1rem; line-height: 1.9; color: rgba(255,255,255,.74); white-space: pre-wrap; margin: 0 0 40px; }}
    .works-gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-top: 32px; }}
    .works-gallery img {{ width: 100%; aspect-ratio: 4/3; object-fit: cover; border-radius: 6px; display: block; }}
    .works-back {{ display: inline-flex; align-items: center; gap: 8px; color: rgba(255,255,255,.6); text-decoration: none; font-size: .9rem; margin-bottom: 32px; }}
    .works-back:hover {{ color: #fff; }}
  </style>
</head>
<body>
  <header class="site-header">
    <nav class="site-nav">
      <a href="/" class="site-logo">
        <img src="/assets/images/logo.png" alt="村山良作" width="40" height="40">
        <span class="site-name">村山良作</span>
      </a>
      <div class="site-nav-links">
        <a href="/sort-hat/">分類帽</a>
        <a href="/teabar.html">囍茶方案</a>
        <a href="/workflow.html">合作流程</a>
      </div>
    </nav>
  </header>

  <main class="works-page">
    <a href="/#shelf" class="works-back">← 所有作品</a>
    <img class="works-hero" src="{hero}" alt="{title} {cat_label}活動佈置 村山良作">
    <div class="works-meta">
      <span class="detail-tag">{cat_label}</span>
    </div>
    <h1 class="works-title">{title}</h1>
    <p class="works-desc">{description}</p>
    <section>
      <h2 style="font-size:1.4rem;margin:0 0 16px;">精彩花絮</h2>
      <div class="works-gallery">
        {gallery_html}
      </div>
    </section>
  </main>
</body>
</html>"""

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_sitemap(self):
        """Dynamically generate sitemap.xml with all works pages."""
        import xml.etree.ElementTree as ET
        articles = _load_articles()
        site_url = "https://goodjob.weddingwishlove.com"

        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        # Static pages
        for loc in ["", "/teabar.html", "/workflow.html", "/wedding-packages/", "/wedding-packages/outdoor.html"]:
            lines.append(f"  <url><loc>{site_url}{loc}</loc></url>")
        # Dynamic works pages
        for a in articles:
            aid = a.get("id", "")
            if aid:
                lines.append(f"  <url><loc>{site_url}/works/{aid}</loc></url>")
        lines.append("</urlset>")

        body = "\n".join(lines).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        if self._is_api():
            if not self._route_api("GET"):
                self._send_error_json(404, "Not found")
            return
        if self._is_admin_page():
            self.path = "/admin/index.html"
        super().do_HEAD()

    def do_POST(self):
        if self._is_api():
            if not self._route_api("POST"):
                self._send_error_json(404, "Not found")
            return
        self._send_error_json(405, "Method not allowed")

    def do_PUT(self):
        if self._is_api():
            if not self._route_api("PUT"):
                self._send_error_json(404, "Not found")
            return
        self._send_error_json(405, "Method not allowed")

    def do_DELETE(self):
        if self._is_api():
            if not self._route_api("DELETE"):
                self._send_error_json(404, "Not found")
            return
        self._send_error_json(405, "Method not allowed")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log_message(self, format, *args):
        """Log to stdout with timestamp."""
        sys.stdout.write("[%s] %s - %s\n" % (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            self.address_string(),
            format % args,
        ))
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Murayama Good Job Site Server")
    parser.add_argument("--port", type=int, default=10814, help="Port to listen on (default: 10814)")
    parser.add_argument("--bind", default="127.0.0.1", help="Address to bind to (default: 127.0.0.1)")
    args = parser.parse_args()

    # Ensure we serve files from the script's directory
    os.chdir(BASE_DIR)

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Create articles.json if missing
    if not os.path.isfile(ARTICLES_PATH):
        _write_json_atomic(ARTICLES_PATH, [])
        print(f"[init] Created empty {ARTICLES_PATH}")

    # Validate config
    cfg = _load_config()
    if not cfg.get("adminUser"):
        print("[warn] data/config.json missing or incomplete — admin auth will reject all requests")

    server = HTTPServer((args.bind, args.port), MurayamaHandler)
    print(f"Murayama server running on http://{args.bind}:{args.port}/")
    print(f"  Static root : {BASE_DIR}")
    print(f"  Data dir    : {DATA_DIR}")
    print(f"  Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
