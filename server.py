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
import secrets
import subprocess
import sys
import tempfile
import time
import io
import uuid
from http import HTTPStatus
try:
    from PIL import Image as _PILImage
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False
try:
    import pillow_avif  # noqa: F401 -- registers AVIF format with Pillow if installed
except ImportError:
    pass
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

# ---------------------------------------------------------------------------
# Paths (resolved relative to the script's own directory)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTICLES_PATH = os.path.join(DATA_DIR, "articles.json")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
ACCOUNTS_PATH = os.path.join(DATA_DIR, "accounts.json")
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")

VALID_ROLES = {"admin", "editor", "viewer", "custom"}
VALID_PERMISSIONS = {
    "articles.read",
    "articles.write",
    "articles.delete",
    "uploads.write",
    "accounts.manage",
}
ACCOUNT_PUBLIC_FIELDS = ("username", "name", "role", "enabled", "permissions",
                         "createdAt", "updatedAt")

# R2 / CDN config — admin uploads go directly to R2 object storage.
# Override via env vars for dev / alternative deployments.
R2_REMOTE = os.environ.get("GOODJOB_R2_REMOTE", "r2:goodjob-images")
CDN_DOMAIN = os.environ.get("GOODJOB_CDN_DOMAIN", "https://goodjob-img.weddingwishlove.com")
RCLONE_BIN = os.environ.get("GOODJOB_RCLONE_BIN", "rclone")
WEBP_QUALITY = int(os.environ.get("GOODJOB_WEBP_QUALITY", "90"))
# Cap uploaded images at this pixel width before WebP encoding — huge raw photos
# (iPhone ProRAW, mirrorless 8000px JPEGs) would otherwise stall Pillow for tens
# of seconds and produce unnecessarily large output.
MAX_UPLOAD_WIDTH = int(os.environ.get("GOODJOB_MAX_UPLOAD_WIDTH", "3000"))
# Thumbnail config — small preview variant for admin gallery / table.
THUMB_WIDTH = int(os.environ.get("GOODJOB_THUMB_WIDTH", "400"))
THUMB_QUALITY = int(os.environ.get("GOODJOB_THUMB_QUALITY", "75"))


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


def _upload_to_r2(data_bytes, r2_key):
    """Upload raw bytes to R2 at the given object key.

    Returns the public CDN URL on success, or None on failure.
    Uses rclone subprocess so zero new Python dependencies are required.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
    try:
        tmp.write(data_bytes)
        tmp.close()
        result = subprocess.run(
            [RCLONE_BIN, "copyto", tmp.name, f"{R2_REMOTE}/{r2_key}"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            sys.stderr.write(f"[r2-upload] rclone failed: {result.stderr.strip()}\n")
            return None
        return f"{CDN_DOMAIN}/{r2_key}"
    except (OSError, subprocess.TimeoutExpired) as e:
        sys.stderr.write(f"[r2-upload] exception: {e}\n")
        return None
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _classify_upload_name(filename, article_id):
    """Map an uploaded filename to a clean key under works/{article_id}/.

    Mirrors migrate_to_r2.py logic so admin uploads share the same naming
    convention as the initial bulk migration.
    """
    base, ext = os.path.splitext(filename)
    ext = ext.lower()
    out_ext = ".webp" if ext in {".jpg", ".jpeg", ".png"} else ext

    m = re.search(r"-(hero|detail-\d+|scene-\d+)$", base)
    if m:
        return f"{m.group(1)}{out_ext}"
    if base.startswith(f"{article_id}_"):
        rest = re.sub(r"_+", "_", base[len(article_id) + 1:].strip("_"))
        return f"{rest}{out_ext}"
    m = re.match(r"^[0-9a-f]{8}_(.+)$", base)
    if m:
        return f"{m.group(1)}{out_ext}"
    safe = re.sub(r"[^\w\-]", "_", base)
    return f"{safe}{out_ext}"


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


def _load_accounts():
    """Return the accounts list from accounts.json, or [] if missing."""
    data = _read_json(ACCOUNTS_PATH)
    if isinstance(data, dict) and isinstance(data.get("accounts"), list):
        return data["accounts"]
    return []


def _save_accounts(accounts):
    """Persist the accounts list to disk atomically."""
    os.makedirs(DATA_DIR, exist_ok=True)
    _write_json_atomic(ACCOUNTS_PATH, {"accounts": accounts})


def _hash_password(salt, password):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _generate_salt():
    return secrets.token_hex(16)


def _public_account(account):
    """Return account dict with sensitive fields stripped."""
    return {k: account.get(k) for k in ACCOUNT_PUBLIC_FIELDS if k in account}


def _find_account(accounts, username):
    for a in accounts:
        if a.get("username") == username:
            return a
    return None


def _count_active_admins(accounts, exclude_username=None):
    """Count enabled accounts with accounts.manage permission."""
    count = 0
    for a in accounts:
        if exclude_username and a.get("username") == exclude_username:
            continue
        if a.get("enabled") and "accounts.manage" in (a.get("permissions") or []):
            count += 1
    return count


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
        Validate HTTP Basic Auth against data/accounts.json (preferred) or
        data/config.json (legacy single-user fallback).

        On success, stores the matched account dict on `self._auth_account`
        and returns True. On failure, sends 401 and returns False.
        """
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

        accounts = _load_accounts()
        if accounts:
            account = _find_account(accounts, user)
            if (account
                    and account.get("enabled")
                    and _hash_password(account.get("salt", ""), password)
                        == account.get("passwordHash", "")):
                self._auth_account = account
                return True
            self._send_401()
            return False

        # Legacy fallback: single-user config.json
        cfg = _load_config()
        expected_user = cfg.get("adminUser", "")
        expected_hash = cfg.get("adminPasswordHash", "")
        salt = cfg.get("adminSalt", "")
        if (user == expected_user and expected_hash
                and _hash_password(salt, password) == expected_hash):
            self._auth_account = {
                "username": expected_user,
                "name": expected_user,
                "role": "admin",
                "enabled": True,
                "permissions": sorted(VALID_PERMISSIONS),
            }
            return True
        self._send_401()
        return False

    def _require_permission(self, permission):
        """Check the authenticated account has *permission*; send 403 if not."""
        account = getattr(self, "_auth_account", None)
        if account and permission in (account.get("permissions") or []):
            return True
        self._send_error_json(403, "Forbidden: missing permission " + permission)
        return False

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
        if not self._require_permission("articles.write"):
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
        if not self._require_permission("articles.write"):
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
        if not self._require_permission("articles.delete"):
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
        if not self._require_permission("uploads.write"):
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

        # Compute next sequential index for this article's uploads.
        # Scheme: {article_id}-{N}.webp — keeps all filenames ASCII and clearly
        # tied to the owning article. Scans existing images (any `-\d+.webp` tail)
        # so newly-uploaded files don't collide with legacy detail-N/scene-N.
        seq_re = re.compile(r"-(\d+)\.webp(?:[?#].*)?$", re.IGNORECASE)
        next_idx = 0
        for url in (article.get("images") or []):
            m = seq_re.search(url or "")
            if m:
                try:
                    n = int(m.group(1))
                    if n > next_idx:
                        next_idx = n
                except ValueError:
                    pass

        saved_paths = []
        failed = []
        for part in parts:
            filename = part.get("filename")
            if not filename:
                continue
            img_data = part["data"]
            thumb_data = None

            # Convert to WebP when Pillow is available (quality matches migration).
            if _PILLOW_AVAILABLE:
                try:
                    img = _PILImage.open(io.BytesIO(img_data))
                    img = img.convert("RGBA" if img.mode in ("RGBA", "P") else "RGB")
                    # Pre-resize oversized photos so encoding doesn't stall for 30+s.
                    if img.width > MAX_UPLOAD_WIDTH:
                        img.thumbnail((MAX_UPLOAD_WIDTH, MAX_UPLOAD_WIDTH * 10),
                                      _PILImage.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=4)
                    img_data = buf.getvalue()
                    # Generate small thumbnail for admin gallery preview.
                    try:
                        thumb_img = img.copy()
                        thumb_img.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 10), _PILImage.LANCZOS)
                        thumb_buf = io.BytesIO()
                        thumb_img.save(thumb_buf, format="WEBP", quality=THUMB_QUALITY, method=4)
                        thumb_data = thumb_buf.getvalue()
                    except Exception as e:
                        sys.stderr.write(f"[upload] thumb generation failed for {filename}: {e}\n")
                except Exception as e:
                    sys.stderr.write(f"[upload] WebP conversion failed for {filename}: {e}\n")

            # Auto-name as {article_id}-{N}.webp — drops any non-ASCII / raw
            # client filename. R2 key + public URL stay clean ASCII.
            next_idx += 1
            target_name = f"{article_id}-{next_idx}.webp"
            r2_key = f"works/{article_id}/{target_name}"
            cdn_url = _upload_to_r2(img_data, r2_key)
            if cdn_url is None:
                failed.append(filename)
                continue
            saved_paths.append(cdn_url)

            # Upload thumbnail alongside (best-effort; skip log on failure).
            if thumb_data:
                thumb_key = f"works/{article_id}/{target_name[:-5]}-thumb.webp"
                _upload_to_r2(thumb_data, thumb_key)

        if failed and not saved_paths:
            self._send_error_json(500, f"All uploads failed: {failed}")
            return

        # Update article images list
        if "images" not in article:
            article["images"] = []
        article["images"].extend(saved_paths)
        article["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        articles[art_idx] = article
        _save_articles(articles)

        resp = {"uploaded": saved_paths}
        if failed:
            resp["failed"] = failed
        self._send_json(resp, status=201)

    # ------------------------------------------------------------------
    # API: session
    # ------------------------------------------------------------------

    def _api_get_session(self):
        """GET /api/session — return current authenticated account profile."""
        if not self._check_auth():
            return
        self._send_json({"account": _public_account(self._auth_account)})

    # ------------------------------------------------------------------
    # API: accounts
    # ------------------------------------------------------------------

    def _validate_account_payload(self, data, *, require_username, require_password):
        """Validate fields shared by create / update.  Returns (ok, error_msg)."""
        if not isinstance(data, dict):
            return False, "Invalid JSON body"

        if require_username:
            username = (data.get("username") or "").strip()
            if not username or not re.match(r"^[A-Za-z0-9_.\-]{2,32}$", username):
                return False, "Invalid username (2-32 chars, A-Z a-z 0-9 _ . -)"

        if require_password or data.get("password"):
            password = data.get("password") or ""
            if len(password) < 6:
                return False, "Password must be at least 6 characters"

        if "role" in data and data["role"] not in VALID_ROLES:
            return False, "Invalid role"

        if "permissions" in data:
            perms = data["permissions"]
            if not isinstance(perms, list):
                return False, "permissions must be a list"
            for p in perms:
                if p not in VALID_PERMISSIONS:
                    return False, f"Invalid permission: {p}"
        return True, None

    def _api_list_accounts(self):
        """GET /api/accounts — list all accounts (auth + accounts.manage)."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return
        accounts = _load_accounts()
        self._send_json({"accounts": [_public_account(a) for a in accounts]})

    def _api_create_account(self):
        """POST /api/accounts — create a new account (auth + accounts.manage)."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return

        data = self._read_json_body()
        ok, err = self._validate_account_payload(
            data, require_username=True, require_password=True
        )
        if not ok:
            self._send_error_json(400, err)
            return

        username = data["username"].strip()
        accounts = _load_accounts()
        if _find_account(accounts, username):
            self._send_error_json(409, f"Account '{username}' already exists")
            return

        salt = _generate_salt()
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        new_account = {
            "username": username,
            "name": (data.get("name") or username).strip(),
            "role": data.get("role") or "custom",
            "enabled": bool(data.get("enabled", True)),
            "permissions": list(data.get("permissions") or []),
            "salt": salt,
            "passwordHash": _hash_password(salt, data["password"]),
            "createdAt": now,
            "updatedAt": now,
        }
        accounts.append(new_account)
        _save_accounts(accounts)
        self._send_json({"account": _public_account(new_account)}, status=201)

    def _api_update_account(self, username):
        """PUT /api/accounts/{username} — update an existing account."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return

        data = self._read_json_body()
        ok, err = self._validate_account_payload(
            data, require_username=False, require_password=False
        )
        if not ok:
            self._send_error_json(400, err)
            return

        accounts = _load_accounts()
        account = _find_account(accounts, username)
        if account is None:
            self._send_error_json(404, "Account not found")
            return

        # Compute the post-update state to enforce last-admin invariant.
        new_enabled = bool(data["enabled"]) if "enabled" in data else account.get("enabled", True)
        new_perms = list(data["permissions"]) if "permissions" in data else (account.get("permissions") or [])
        was_active_admin = account.get("enabled") and "accounts.manage" in (account.get("permissions") or [])
        will_be_active_admin = new_enabled and "accounts.manage" in new_perms
        if was_active_admin and not will_be_active_admin:
            if _count_active_admins(accounts, exclude_username=username) == 0:
                self._send_error_json(400, "Cannot demote the last active admin")
                return

        if "name" in data:
            account["name"] = (data["name"] or username).strip()
        if "role" in data:
            account["role"] = data["role"]
        if "enabled" in data:
            account["enabled"] = new_enabled
        if "permissions" in data:
            account["permissions"] = new_perms
        if data.get("password"):
            account["salt"] = _generate_salt()
            account["passwordHash"] = _hash_password(account["salt"], data["password"])
        account["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        _save_accounts(accounts)
        self._send_json({"account": _public_account(account)})

    def _api_delete_account(self, username):
        """DELETE /api/accounts/{username} — remove an account."""
        if not self._check_auth():
            return
        if not self._require_permission("accounts.manage"):
            return

        if self._auth_account.get("username") == username:
            self._send_error_json(400, "Cannot delete your own account")
            return

        accounts = _load_accounts()
        target = _find_account(accounts, username)
        if target is None:
            self._send_error_json(404, "Account not found")
            return

        was_active_admin = target.get("enabled") and "accounts.manage" in (target.get("permissions") or [])
        if was_active_admin and _count_active_admins(accounts, exclude_username=username) == 0:
            self._send_error_json(400, "Cannot delete the last active admin")
            return

        accounts = [a for a in accounts if a.get("username") != username]
        _save_accounts(accounts)
        self._send_json({"deleted": username})

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

        # GET /api/session
        if method == "GET" and path == "/api/session":
            self._api_get_session()
            return True

        # GET /api/accounts
        if method == "GET" and path == "/api/accounts":
            self._api_list_accounts()
            return True

        # POST /api/accounts
        if method == "POST" and path == "/api/accounts":
            self._api_create_account()
            return True

        # PUT /api/accounts/{username}
        if method == "PUT" and path.startswith("/api/accounts/"):
            username = path[len("/api/accounts/"):]
            if username:
                self._api_update_account(username)
                return True

        # DELETE /api/accounts/{username}
        if method == "DELETE" and path.startswith("/api/accounts/"):
            username = path[len("/api/accounts/"):]
            if username:
                self._api_delete_account(username)
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

    # Validate auth source: prefer accounts.json, fall back to config.json
    accounts = _load_accounts()
    cfg = _load_config()
    if accounts:
        active_admins = _count_active_admins(accounts)
        print(f"[auth] {len(accounts)} account(s) loaded ({active_admins} active admin(s))")
        if active_admins == 0:
            print("[warn] no active admin account — accounts.manage operations will be locked")
    elif cfg.get("adminUser"):
        print(f"[auth] legacy single-user mode (adminUser='{cfg.get('adminUser')}')")
    else:
        print("[warn] no accounts.json and no adminUser in config.json — admin auth will reject all requests")

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
