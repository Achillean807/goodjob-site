# Quote Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-folder password protection and admin management for static proposal pages under `quote/`.

**Architecture:** Store proposal state in `data/quote_manifest.json`, intercept `/quote/...` requests in `server.py`, and expose authenticated `/api/quotes` management endpoints. Extend the existing vanilla JS admin to list proposals, set passwords, hide/show them, and move deleted folders into `quote/_deleted/`.

**Tech Stack:** Python 3 stdlib `HTTPServer`, JSON manifest, salted SHA-256, HMAC-signed HttpOnly cookies, `unittest`, vanilla HTML/CSS/JS admin.

---

## File Structure

- Modify `server.py`: add quote manifest helpers, quote request gate, quote password POST handler, `/api/quotes` endpoints, `quotes.manage` permission, and test-only env path overrides.
- Modify `admin/index.html`: add proposal management button, modal markup, account permission checkbox, and cache-busted admin JS URL.
- Modify `admin/app.js`: add proposal management state, permission labels, modal rendering, API calls, and button handlers.
- Modify `tests/test_quote_auth.py`: convert existing public quote tests into protected quote integration tests against a temporary data/quote directory.
- Create `tests/test_admin_quote_ui.py`: lightweight static regression tests for required admin UI hooks.

## Task 1: Quote Gate Red Tests

**Files:**
- Modify: `tests/test_quote_auth.py`

- [ ] **Step 1: Rewrite the test fixture to run against temporary data and quote folders**

Replace the module setup helpers in `tests/test_quote_auth.py` with this structure. It creates an isolated SQLite DB, account seed, manifest, and proposal folders so tests never move real files in `quote/`.

```python
import base64
import hashlib
import http.cookiejar
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def password_hash(salt, password):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class QuoteAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="goodjob-quote-test-")
        cls.data_dir = os.path.join(cls.tmpdir, "data")
        cls.quote_dir = os.path.join(cls.tmpdir, "quote")
        cls.manifest_path = os.path.join(cls.data_dir, "quote_manifest.json")
        os.makedirs(cls.data_dir, exist_ok=True)
        os.makedirs(cls.quote_dir, exist_ok=True)
        cls._write_quote("260606")
        cls._write_quote("260613")
        cls._write_accounts()

        cls.port = free_port()
        env = os.environ.copy()
        env["GOODJOB_ALLOW_SQLITE"] = "1"
        env["GOODJOB_ALLOW_JSON_SEED"] = "1"
        env["GOODJOB_DATA_DIR"] = cls.data_dir
        env["GOODJOB_QUOTE_DIR"] = cls.quote_dir
        env["GOODJOB_QUOTE_MANIFEST_PATH"] = cls.manifest_path
        cls.proc = subprocess.Popen(
            [
                sys.executable,
                os.path.join(ROOT, "server.py"),
                "--bind",
                "127.0.0.1",
                "--port",
                str(cls.port),
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/", timeout=0.5).close()
                return
            except OSError:
                if cls.proc.poll() is not None:
                    break
                time.sleep(0.1)
        raise RuntimeError("test server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def setUp(self):
        for quote_id in ("260606", "260613"):
            shutil.rmtree(os.path.join(self.quote_dir, quote_id), ignore_errors=True)
            self._write_quote(quote_id)
        shutil.rmtree(os.path.join(self.quote_dir, "_deleted"), ignore_errors=True)
        with open(self.manifest_path, "w", encoding="utf-8") as fh:
            json.dump({"quotes": {}}, fh)

    @classmethod
    def _write_quote(cls, quote_id):
        root = os.path.join(cls.quote_dir, quote_id)
        os.makedirs(os.path.join(root, "images"), exist_ok=True)
        with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(f"<!doctype html><title>{quote_id}</title><h1>proposal {quote_id}</h1>")
        with open(os.path.join(root, "images", "003.jpg"), "wb") as fh:
            fh.write(b"fake-jpg")

    @classmethod
    def _write_accounts(cls):
        salt = "adminsalt"
        payload = {
            "accounts": [
                {
                    "username": "admin",
                    "name": "Admin",
                    "role": "admin",
                    "enabled": True,
                    "permissions": [
                        "articles.read",
                        "articles.write",
                        "articles.delete",
                        "uploads.write",
                        "accounts.manage",
                        "quotes.manage",
                    ],
                    "salt": salt,
                    "passwordHash": password_hash(salt, "adminpass"),
                    "createdAt": "2026-05-17T00:00:00",
                    "updatedAt": "2026-05-17T00:00:00",
                },
                {
                    "username": "viewer",
                    "name": "Viewer",
                    "role": "viewer",
                    "enabled": True,
                    "permissions": ["articles.read"],
                    "salt": "viewersalt",
                    "passwordHash": password_hash("viewersalt", "viewerpass"),
                    "createdAt": "2026-05-17T00:00:00",
                    "updatedAt": "2026-05-17T00:00:00",
                }
            ]
        }
        with open(os.path.join(cls.data_dir, "accounts.json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def basic_auth(self, username="admin", password="adminpass"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def request(self, path, method="GET", data=None, auth=False, opener=None, headers=None):
        body = None
        req_headers = dict(headers or {})
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        if auth is True:
            req_headers["Authorization"] = self.basic_auth()
        elif auth:
            req_headers["Authorization"] = auth
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=body,
            headers=req_headers,
            method=method,
        )
        active_opener = opener or urllib.request
        try:
            with active_opener.urlopen(req, timeout=5) as response:
                return response.status, response.headers, response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8", errors="replace")

    def form_request(self, path, fields, opener=None):
        body = urllib.parse.urlencode(fields).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        active_opener = opener or urllib.request
        try:
            with active_opener.urlopen(req, timeout=5) as response:
                return response.status, response.headers, response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8", errors="replace")
```

- [ ] **Step 2: Add failing tests for locked-by-default and no-cache/noindex headers**

Append these tests inside `QuoteAuthTest`.

```python
    def test_unconfigured_quote_shows_paused_page(self):
        status, headers, body = self.request("/quote/260606/")
        self.assertEqual(status, 200)
        self.assertIn("此提案暫停開放", body)
        self.assertNotIn("proposal 260606", body)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

    def test_unconfigured_quote_asset_is_not_public(self):
        status, headers, body = self.request("/quote/260606/images/003.jpg")
        self.assertEqual(status, 200)
        self.assertIn("此提案暫停開放", body)
        self.assertNotIn("fake-jpg", body)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

    def test_public_home_does_not_require_quote_password(self):
        status, headers, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)

    def test_robots_is_not_cached_by_origin(self):
        status, headers, body = self.request("/robots.txt")
        self.assertEqual(status, 200)
        self.assertIn("no-store", headers.get("Cache-Control", ""))
```

- [ ] **Step 3: Run the new red tests**

Run:

```powershell
python -m unittest tests.test_quote_auth.QuoteAuthTest.test_unconfigured_quote_shows_paused_page tests.test_quote_auth.QuoteAuthTest.test_unconfigured_quote_asset_is_not_public -v
```

Expected: both tests fail because `server.py` currently serves `/quote/...` files directly.

- [ ] **Step 4: Commit the red tests**

```powershell
git add tests/test_quote_auth.py
git commit -m "新增提案預設不開放測試"
```

## Task 2: Quote Manifest And Public Gate

**Files:**
- Modify: `server.py`
- Test: `tests/test_quote_auth.py`

- [ ] **Step 1: Add imports and env-overridable paths**

Modify the imports near the top of `server.py`.

```python
import hmac
import posixpath
import shutil
from http import cookies
from urllib.parse import parse_qs, unquote
```

Replace the existing `DATA_DIR` and related path constants with env-aware equivalents.

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("GOODJOB_DATA_DIR", os.path.join(BASE_DIR, "data"))
ARTICLES_PATH = os.path.join(DATA_DIR, "articles.json")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
ACCOUNTS_PATH = os.path.join(DATA_DIR, "accounts.json")
DB_PATH = os.environ.get("GOODJOB_DB_PATH", os.path.join(DATA_DIR, "goodjob.sqlite3"))
DATABASE_URL = os.environ.get("GOODJOB_DATABASE_URL", "").strip()
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
QUOTE_DIR = os.environ.get("GOODJOB_QUOTE_DIR", os.path.join(BASE_DIR, "quote"))
QUOTE_MANIFEST_PATH = os.environ.get(
    "GOODJOB_QUOTE_MANIFEST_PATH",
    os.path.join(DATA_DIR, "quote_manifest.json"),
)
QUOTE_DELETED_DIRNAME = "_deleted"
QUOTE_COOKIE_MAX_AGE = 7 * 24 * 60 * 60
QUOTE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
```

- [ ] **Step 2: Add quote manifest helpers after `_generate_salt()`**

```python
def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _is_safe_quote_id(quote_id):
    return bool(quote_id and QUOTE_ID_RE.match(quote_id))


def _quote_path(*parts):
    root = os.path.abspath(QUOTE_DIR)
    target = os.path.abspath(os.path.join(root, *parts))
    if target != root and not target.startswith(root + os.sep):
        raise ValueError("quote path escapes quote root")
    return target


def _load_quote_manifest():
    data = _read_json(QUOTE_MANIFEST_PATH)
    if not isinstance(data, dict) or not isinstance(data.get("quotes"), dict):
        return {"quotes": {}}
    return data


def _save_quote_manifest(manifest):
    os.makedirs(os.path.dirname(QUOTE_MANIFEST_PATH), exist_ok=True)
    _write_json_atomic(QUOTE_MANIFEST_PATH, manifest)


def _quote_record(manifest, quote_id):
    record = manifest.get("quotes", {}).get(quote_id)
    return record if isinstance(record, dict) else None


def _quote_has_password(record):
    return bool(record and record.get("passwordSalt") and record.get("passwordHash"))


def _quote_cookie_name(quote_id):
    return "quote_auth_" + quote_id


def _quote_cookie_signature(quote_id, record, issued_at):
    key = (record.get("passwordHash") or "").encode("utf-8")
    message = f"{quote_id}:{issued_at}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _make_quote_cookie_value(quote_id, record):
    issued_at = str(int(time.time()))
    sig = _quote_cookie_signature(quote_id, record, issued_at)
    return issued_at + ":" + sig


def _valid_quote_cookie(quote_id, record, raw_cookie):
    if not _quote_has_password(record) or not raw_cookie:
        return False
    try:
        jar = cookies.SimpleCookie(raw_cookie)
        morsel = jar.get(_quote_cookie_name(quote_id))
        if morsel is None:
            return False
        issued_at, sig = morsel.value.split(":", 1)
        if int(time.time()) - int(issued_at) > QUOTE_COOKIE_MAX_AGE:
            return False
    except (ValueError, TypeError):
        return False
    expected = _quote_cookie_signature(quote_id, record, issued_at)
    return hmac.compare_digest(sig, expected)
```

- [ ] **Step 3: Add quote response helpers inside `MurayamaHandler` before API methods**

```python
    def _quote_parts(self):
        clean = unquote(self.path.split("?", 1)[0].split("#", 1)[0])
        if clean == "/quote":
            return "", ""
        if not clean.startswith("/quote/"):
            return None, None
        rest = clean[len("/quote/"):]
        quote_id, sep, rel = rest.partition("/")
        return quote_id, rel

    def _send_html(self, html, status=200, head_only=False):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _send_quote_paused(self, head_only=False):
        self._send_html(
            "<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>此提案暫停開放</title></head><body>"
            "<main style=\"min-height:80vh;display:grid;place-items:center;"
            "font-family:system-ui,'Noto Sans TC',sans-serif;background:#141414;color:#fff\">"
            "<section style=\"max-width:420px;padding:32px;text-align:center\">"
            "<h1 style=\"font-size:1.4rem\">此提案暫停開放</h1>"
            "<p style=\"color:rgba(255,255,255,.68);line-height:1.8\">"
            "請聯絡村山良作窗口確認提案開放狀態。</p>"
            "</section></main></body></html>",
            head_only=head_only,
        )

    def _send_quote_login(self, quote_id, error="", head_only=False):
        error_html = (
            "<p style=\"color:#fca5a5;margin:0 0 12px\">密碼錯誤，請再試一次。</p>"
            if error else ""
        )
        html = (
            "<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>提案密碼｜{quote_id}</title></head><body>"
            "<main style=\"min-height:100vh;display:grid;place-items:center;"
            "font-family:system-ui,'Noto Sans TC',sans-serif;background:#141414;color:#fff\">"
            f"<form method=\"post\" action=\"/quote/{quote_id}/auth\" style=\"width:min(360px,calc(100vw - 40px));"
            "background:#1f1f1f;border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:28px\">"
            "<h1 style=\"font-size:1.35rem;margin:0 0 16px\">請輸入提案密碼</h1>"
            f"{error_html}"
            "<input type=\"password\" name=\"password\" autocomplete=\"current-password\" autofocus "
            "style=\"width:100%;box-sizing:border-box;padding:11px 12px;border-radius:6px;"
            "border:1px solid rgba(255,255,255,.18);background:#2a2a2a;color:#fff\">"
            "<button type=\"submit\" style=\"width:100%;margin-top:14px;padding:11px 12px;"
            "border:0;border-radius:6px;background:#e50914;color:#fff;font-weight:700\">進入提案</button>"
            "</form></main></body></html>"
        )
        self._send_html(html, head_only=head_only)
```

- [ ] **Step 4: Add protected static serving inside `MurayamaHandler`**

```python
    def _serve_quote_static(self, quote_id, rel_path, head_only=False):
        if not rel_path or rel_path.endswith("/"):
            rel_path = rel_path + "index.html"
        normalized = posixpath.normpath("/" + rel_path).lstrip("/")
        try:
            file_path = _quote_path(quote_id, *normalized.split("/"))
        except ValueError:
            self.send_error(404, "Not found")
            return
        if not os.path.isfile(file_path):
            self.send_error(404, "Not found")
            return
        ctype = self.guess_type(file_path)
        try:
            with open(file_path, "rb") as fh:
                body = fh.read()
        except OSError:
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _serve_quote_request(self, head_only=False):
        quote_id, rel_path = self._quote_parts()
        if quote_id is None:
            return False
        if not _is_safe_quote_id(quote_id):
            self.send_error(404, "Not found")
            return True
        quote_root = _quote_path(quote_id)
        manifest = _load_quote_manifest()
        record = _quote_record(manifest, quote_id)
        if not os.path.isdir(quote_root) and not (record and record.get("status") == "deleted"):
            self.send_error(404, "Not found")
            return True
        if not record or record.get("status") != "active" or not _quote_has_password(record):
            self._send_quote_paused(head_only=head_only)
            return True
        if not _valid_quote_cookie(quote_id, record, self.headers.get("Cookie", "")):
            self._send_quote_login(quote_id, head_only=head_only)
            return True
        self._serve_quote_static(quote_id, rel_path, head_only=head_only)
        return True
```

- [ ] **Step 5: Route quote GET and HEAD before static file fallback**

In `do_GET`, add this immediately after the API branch.

```python
        if self._is_quote_path():
            if self._serve_quote_request(head_only=False):
                return
```

In `do_HEAD`, add this immediately after the API branch.

```python
        if self._is_quote_path():
            if self._serve_quote_request(head_only=True):
                return
```

- [ ] **Step 6: Run Task 1 tests to verify green**

Run:

```powershell
python -m unittest tests.test_quote_auth.QuoteAuthTest.test_unconfigured_quote_shows_paused_page tests.test_quote_auth.QuoteAuthTest.test_unconfigured_quote_asset_is_not_public -v
```

Expected: PASS.

- [ ] **Step 7: Commit quote gate implementation**

```powershell
git add server.py tests/test_quote_auth.py
git commit -m "實作提案預設暫停開放"
```

## Task 3: Quote API And Password Flow Red Tests

**Files:**
- Modify: `tests/test_quote_auth.py`

- [ ] **Step 1: Add a helper for setting manifest state through API**

Add this method to `QuoteAuthTest`.

```python
    def set_quote(self, quote_id, payload):
        status, headers, body = self.request(
            f"/api/quotes/{quote_id}",
            method="PUT",
            data=payload,
            auth=True,
        )
        self.assertIn(status, (200, 201), body)
        return json.loads(body)
```

- [ ] **Step 2: Add failing password and cookie behavior tests**

```python
    def test_active_quote_requires_password_then_serves_html_after_login(self):
        self.set_quote("260606", {"title": "Proposal A", "status": "active", "password": "clientpass"})

        status, headers, body = self.request("/quote/260606/")
        self.assertEqual(status, 200)
        self.assertIn("請輸入提案密碼", body)
        self.assertNotIn("proposal 260606", body)

        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        status, headers, body = self.form_request("/quote/260606/auth", {"password": "wrong"}, opener=opener)
        self.assertEqual(status, 200)
        self.assertIn("密碼錯誤", body)
        self.assertEqual(len(list(jar)), 0)

        status, headers, body = self.form_request("/quote/260606/auth", {"password": "clientpass"}, opener=opener)
        self.assertEqual(status, 200)
        self.assertIn("proposal 260606", body)
        cookies = list(jar)
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0].path, "/quote/260606/")
        self.assertTrue(cookies[0].has_nonstandard_attr("HttpOnly"))

        status, headers, body = self.request("/quote/260606/images/003.jpg", opener=opener)
        self.assertEqual(status, 200)
        self.assertIn("fake-jpg", body)

    def test_quote_cookie_does_not_unlock_another_quote(self):
        self.set_quote("260606", {"title": "Proposal A", "status": "active", "password": "clientpass"})
        self.set_quote("260613", {"title": "Proposal B", "status": "active", "password": "otherpass"})

        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        status, headers, body = self.form_request("/quote/260606/auth", {"password": "clientpass"}, opener=opener)
        self.assertEqual(status, 200)
        self.assertIn("proposal 260606", body)

        status, headers, body = self.request("/quote/260613/", opener=opener)
        self.assertEqual(status, 200)
        self.assertIn("請輸入提案密碼", body)
        self.assertNotIn("proposal 260613", body)

    def test_hidden_quote_shows_paused_page_even_with_password(self):
        self.set_quote("260606", {"title": "Proposal A", "status": "hidden", "password": "clientpass"})
        status, headers, body = self.request("/quote/260606/")
        self.assertEqual(status, 200)
        self.assertIn("此提案暫停開放", body)
        self.assertNotIn("請輸入提案密碼", body)

    def test_quotes_api_requires_quotes_manage_permission(self):
        status, headers, body = self.request("/api/quotes")
        self.assertEqual(status, 401)

        status, headers, body = self.request(
            "/api/quotes",
            auth=self.basic_auth("viewer", "viewerpass"),
        )
        self.assertEqual(status, 403)

        status, headers, body = self.request("/api/quotes", auth=True)
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([q["id"] for q in payload["quotes"]], ["260606", "260613"])

    def test_delete_quote_moves_folder_to_deleted_and_marks_manifest(self):
        self.set_quote("260613", {"title": "Proposal B", "status": "active", "password": "otherpass"})
        src = os.path.join(self.quote_dir, "260613")
        self.assertTrue(os.path.isdir(src))

        status, headers, body = self.request("/api/quotes/260613", method="DELETE", auth=True)
        self.assertEqual(status, 200, body)
        payload = json.loads(body)
        self.assertEqual(payload["quote"]["status"], "deleted")
        self.assertFalse(os.path.exists(src))
        self.assertTrue(os.path.isdir(os.path.join(self.quote_dir, "_deleted")))
        self.assertTrue(payload["quote"]["deletedPath"].startswith("quote/_deleted/260613-"))

        status, headers, body = self.request("/quote/260613/")
        self.assertEqual(status, 200)
        self.assertIn("此提案暫停開放", body)
```

- [ ] **Step 3: Run quote API flow tests and verify red**

Run:

```powershell
python -m unittest tests.test_quote_auth.QuoteAuthTest.test_active_quote_requires_password_then_serves_html_after_login tests.test_quote_auth.QuoteAuthTest.test_quote_cookie_does_not_unlock_another_quote tests.test_quote_auth.QuoteAuthTest.test_hidden_quote_shows_paused_page_even_with_password tests.test_quote_auth.QuoteAuthTest.test_quotes_api_requires_quotes_manage_permission tests.test_quote_auth.QuoteAuthTest.test_delete_quote_moves_folder_to_deleted_and_marks_manifest -v
```

Expected: FAIL because `/api/quotes` and `/quote/{id}/auth` do not exist yet.

- [ ] **Step 4: Commit the red tests**

```powershell
git add tests/test_quote_auth.py
git commit -m "新增提案密碼與刪除流程測試"
```

## Task 4: Quote API And Auth Implementation

**Files:**
- Modify: `server.py`
- Test: `tests/test_quote_auth.py`

- [ ] **Step 1: Add `quotes.manage` permission**

Modify `VALID_PERMISSIONS`.

```python
VALID_PERMISSIONS = {
    "articles.read",
    "articles.write",
    "articles.delete",
    "uploads.write",
    "accounts.manage",
    "quotes.manage",
}
```

In `_init_db`, run this block immediately before the `GOODJOB_ALLOW_JSON_SEED` early return branch, and run the same block again immediately after the optional accounts JSON import block. This covers both existing databases and JSON-seeded test/dev databases.

```python
        conn.execute(
            """
            INSERT OR IGNORE INTO account_permissions (username, permission)
            SELECT username, 'quotes.manage'
            FROM accounts
            WHERE role = 'admin'
            """
        )
```

In `_init_pg_db`, after table creation, add the PostgreSQL equivalent.

```python
            cur.execute(
                """
                INSERT INTO account_permissions (username, permission)
                SELECT username, 'quotes.manage'
                FROM accounts
                WHERE role = 'admin'
                ON CONFLICT DO NOTHING
                """
            )
```

- [ ] **Step 2: Add quote list and public DTO helpers after manifest helpers**

```python
def _scan_quote_dirs():
    try:
        names = os.listdir(QUOTE_DIR)
    except OSError:
        return []
    quote_ids = []
    for name in names:
        if name == QUOTE_DELETED_DIRNAME or not _is_safe_quote_id(name):
            continue
        try:
            if os.path.isdir(_quote_path(name)):
                quote_ids.append(name)
        except ValueError:
            continue
    return sorted(quote_ids)


def _public_quote_record(quote_id, record, exists=True):
    status = (record or {}).get("status") or "hidden"
    has_password = _quote_has_password(record)
    if status == "active" and not has_password:
        status = "hidden"
    return {
        "id": quote_id,
        "title": (record or {}).get("title") or quote_id,
        "status": status,
        "hasPassword": has_password,
        "exists": bool(exists),
        "url": f"/quote/{quote_id}/",
        "createdAt": (record or {}).get("createdAt"),
        "updatedAt": (record or {}).get("updatedAt"),
        "deletedAt": (record or {}).get("deletedAt"),
        "deletedPath": (record or {}).get("deletedPath"),
    }
```

- [ ] **Step 3: Add quote API methods inside `MurayamaHandler` before route dispatcher**

```python
    def _api_list_quotes(self):
        if not self._check_auth():
            return
        if not self._require_permission("quotes.manage"):
            return
        manifest = _load_quote_manifest()
        quotes = []
        for quote_id in _scan_quote_dirs():
            quotes.append(_public_quote_record(quote_id, _quote_record(manifest, quote_id), exists=True))
        self._send_json({"quotes": quotes})

    def _api_update_quote(self, quote_id):
        if not self._check_auth():
            return
        if not self._require_permission("quotes.manage"):
            return
        if not _is_safe_quote_id(quote_id):
            self._send_error_json(400, "Invalid quote id")
            return
        if not os.path.isdir(_quote_path(quote_id)):
            self._send_error_json(404, "Quote folder not found")
            return
        data = self._read_json_body()
        if not isinstance(data, dict):
            self._send_error_json(400, "Invalid JSON body")
            return
        requested_status = data.get("status")
        if requested_status is not None and requested_status not in ("active", "hidden"):
            self._send_error_json(400, "Invalid quote status")
            return
        password = data.get("password")
        if password is not None and len(password) < 6:
            self._send_error_json(400, "Password must be at least 6 characters")
            return

        manifest = _load_quote_manifest()
        quotes = manifest.setdefault("quotes", {})
        now = _now_iso()
        record = quotes.get(quote_id) or {
            "id": quote_id,
            "title": quote_id,
            "status": "hidden",
            "createdAt": now,
            "updatedAt": now,
            "deletedAt": None,
            "deletedPath": None,
        }
        if "title" in data:
            record["title"] = (data.get("title") or quote_id).strip() or quote_id
        if password:
            salt = _generate_salt()
            record["passwordSalt"] = salt
            record["passwordHash"] = _hash_password(salt, password)
        if requested_status:
            if requested_status == "active" and not _quote_has_password(record):
                self._send_error_json(400, "Cannot activate quote without a password")
                return
            record["status"] = requested_status
        elif password and record.get("status") not in ("active", "hidden"):
            record["status"] = "hidden"
        record["deletedAt"] = None
        record["deletedPath"] = None
        record["updatedAt"] = now
        quotes[quote_id] = record
        try:
            _save_quote_manifest(manifest)
        except OSError:
            self._send_error_json(500, "Failed to save quote manifest")
            return
        self._send_json({"quote": _public_quote_record(quote_id, record, exists=True)})

    def _api_delete_quote(self, quote_id):
        if not self._check_auth():
            return
        if not self._require_permission("quotes.manage"):
            return
        if not _is_safe_quote_id(quote_id):
            self._send_error_json(400, "Invalid quote id")
            return
        src = _quote_path(quote_id)
        if not os.path.isdir(src):
            self._send_error_json(404, "Quote folder not found")
            return
        deleted_root = _quote_path(QUOTE_DELETED_DIRNAME)
        os.makedirs(deleted_root, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target_name = f"{quote_id}-{stamp}"
        target = _quote_path(QUOTE_DELETED_DIRNAME, target_name)
        if os.path.exists(target):
            self._send_error_json(500, "Deleted target already exists")
            return
        try:
            shutil.move(src, target)
        except OSError:
            self._send_error_json(500, "Failed to move quote folder")
            return

        manifest = _load_quote_manifest()
        quotes = manifest.setdefault("quotes", {})
        now = _now_iso()
        record = quotes.get(quote_id) or {
            "id": quote_id,
            "title": quote_id,
            "createdAt": now,
        }
        record["status"] = "deleted"
        record["deletedAt"] = now
        record["deletedPath"] = os.path.join("quote", QUOTE_DELETED_DIRNAME, target_name).replace("\\", "/")
        record["updatedAt"] = now
        quotes[quote_id] = record
        try:
            _save_quote_manifest(manifest)
        except OSError:
            try:
                shutil.move(target, src)
            except OSError:
                pass
            self._send_error_json(500, "Failed to save quote manifest")
            return
        self._send_json({"quote": _public_quote_record(quote_id, record, exists=False)})
```

- [ ] **Step 4: Add quote password POST handler inside `MurayamaHandler`**

```python
    def _handle_quote_auth_post(self):
        quote_id, rel_path = self._quote_parts()
        if quote_id is None or rel_path != "auth" or not _is_safe_quote_id(quote_id):
            return False
        manifest = _load_quote_manifest()
        record = _quote_record(manifest, quote_id)
        if not record or record.get("status") != "active" or not _quote_has_password(record):
            self._send_quote_paused()
            return True
        raw = self._read_body()
        try:
            params = parse_qs(raw.decode("utf-8"))
        except UnicodeDecodeError:
            params = {}
        password = (params.get("password") or [""])[0]
        if _hash_password(record.get("passwordSalt", ""), password) != record.get("passwordHash", ""):
            self._send_quote_login(quote_id, error="invalid")
            return True
        cookie_value = _make_quote_cookie_value(quote_id, record)
        cookie = cookies.SimpleCookie()
        cookie[_quote_cookie_name(quote_id)] = cookie_value
        cookie[_quote_cookie_name(quote_id)]["path"] = f"/quote/{quote_id}/"
        cookie[_quote_cookie_name(quote_id)]["max-age"] = str(QUOTE_COOKIE_MAX_AGE)
        cookie[_quote_cookie_name(quote_id)]["httponly"] = True
        cookie[_quote_cookie_name(quote_id)]["samesite"] = "Lax"
        self.send_response(303)
        self.send_header("Set-Cookie", cookie.output(header="").strip())
        self.send_header("Location", f"/quote/{quote_id}/")
        self.end_headers()
        return True
```

If the redirect complicates tests, adjust `form_request` to use an opener that follows redirects. The final response should be the proposal HTML with status `200`.

- [ ] **Step 5: Route quote APIs and quote auth POST**

Add to `_route_api` before account routes.

```python
        if method == "GET" and path == "/api/quotes":
            self._api_list_quotes()
            return True

        if method == "PUT" and path.startswith("/api/quotes/"):
            quote_id = path[len("/api/quotes/"):]
            if quote_id:
                self._api_update_quote(quote_id)
                return True

        if method == "DELETE" and path.startswith("/api/quotes/"):
            quote_id = path[len("/api/quotes/"):]
            if quote_id:
                self._api_delete_quote(quote_id)
                return True
```

In `do_POST`, add the quote auth branch before returning 405 for non-API requests.

```python
        if self._is_quote_path():
            if self._handle_quote_auth_post():
                return
```

- [ ] **Step 6: Run quote password flow tests**

Run:

```powershell
python -m unittest tests.test_quote_auth -v
```

Expected: all quote auth tests pass.

- [ ] **Step 7: Commit quote API and auth implementation**

```powershell
git add server.py tests/test_quote_auth.py
git commit -m "實作提案密碼與管理 API"
```

## Task 5: Admin UI Red Test

**Files:**
- Create: `tests/test_admin_quote_ui.py`

- [ ] **Step 1: Add static admin UI regression tests**

Create `tests/test_admin_quote_ui.py`.

```python
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AdminQuoteUiTest(unittest.TestCase):
    def read(self, rel_path):
        with open(os.path.join(ROOT, rel_path), "r", encoding="utf-8") as fh:
            return fh.read()

    def test_admin_html_has_quote_management_hooks(self):
        html = self.read("admin/index.html")
        self.assertIn('id="quotes-btn"', html)
        self.assertIn('id="quotes-modal"', html)
        self.assertIn('id="quotes-list"', html)
        self.assertIn('value="quotes.manage"', html)

    def test_admin_js_has_quote_management_api_calls(self):
        js = self.read("admin/app.js")
        self.assertIn("'quotes.manage'", js)
        self.assertIn("function openQuotesModal()", js)
        self.assertIn("function loadQuotes()", js)
        self.assertIn("function saveQuote()", js)
        self.assertIn("function deleteSelectedQuote()", js)
        self.assertIn("'/api/quotes'", js)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the red UI test**

Run:

```powershell
python -m unittest tests.test_admin_quote_ui -v
```

Expected: FAIL because the admin UI does not have quote management hooks yet.

- [ ] **Step 3: Commit UI red test**

```powershell
git add tests/test_admin_quote_ui.py
git commit -m "新增提案管理後台介面測試"
```

## Task 6: Admin UI Implementation

**Files:**
- Modify: `admin/index.html`
- Modify: `admin/app.js`
- Test: `tests/test_admin_quote_ui.py`

- [ ] **Step 1: Add quote management entry and modal markup**

In `admin/index.html`, add the button next to the account button.

```html
<button class="btn btn-secondary btn-sm" id="quotes-btn" onclick="openQuotesModal()">提案管理</button>
```

Add this modal before the confirm dialog.

```html
<div class="modal-overlay" id="quotes-modal">
  <div class="modal modal-wide">
    <div class="accounts-head">
      <div>
        <h2>提案管理</h2>
        <div class="muted" id="quotes-summary">讀取中...</div>
      </div>
      <button class="btn btn-secondary" onclick="loadQuotes()">重新整理</button>
    </div>
    <div class="accounts-layout">
      <div class="accounts-panel">
        <table class="accounts-table">
          <thead>
            <tr>
              <th>提案</th>
              <th>狀態</th>
              <th>密碼</th>
              <th>網址</th>
            </tr>
          </thead>
          <tbody id="quotes-list"></tbody>
        </table>
      </div>
      <div class="accounts-panel">
        <h3 id="quote-form-title" style="margin-top:0">選擇提案</h3>
        <input type="hidden" id="quote-id">
        <div class="field">
          <label>提案 ID</label>
          <input type="text" id="quote-id-display" disabled>
        </div>
        <div class="field">
          <label>標題</label>
          <input type="text" id="quote-title" placeholder="預設使用資料夾名稱">
        </div>
        <div class="field">
          <label>狀態</label>
          <select id="quote-status">
            <option value="hidden">隱藏 / 暫停開放</option>
            <option value="active">啟用 / 需要密碼</option>
          </select>
        </div>
        <div class="field">
          <label>設定新密碼</label>
          <input type="password" id="quote-password" autocomplete="new-password" placeholder="至少 6 碼，留空代表不變更">
          <div class="form-help">新提案必須先設定密碼，才能切換成啟用。</div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" onclick="closeQuotesModal()">關閉</button>
          <button class="btn btn-danger" id="quote-delete-btn" onclick="deleteSelectedQuote()" style="display:none">刪除此提案</button>
          <button class="btn btn-primary" onclick="saveQuote()">儲存提案</button>
        </div>
      </div>
    </div>
  </div>
</div>
```

Add the permission checkbox in the account permissions grid.

```html
<label class="permission-item"><input type="checkbox" name="acc-permission" value="quotes.manage">提案管理</label>
```

Bump the admin JS URL.

```html
<script src="/admin/app.js?v=20260517a"></script>
```

- [ ] **Step 2: Add admin JS state and permission labels**

At the top of `admin/app.js`, add:

```javascript
var quotesCache = [];
var selectedQuoteId = '';
```

Update `ROLE_PRESETS.admin`.

```javascript
admin: ['articles.read', 'articles.write', 'articles.delete', 'uploads.write', 'accounts.manage', 'quotes.manage'],
```

Update `PERMISSION_LABELS`.

```javascript
'quotes.manage': '提案管理'
```

- [ ] **Step 3: Wire permissions in `applyPermissions()`**

Add:

```javascript
var quotesBtn = document.getElementById('quotes-btn');
```

Then:

```javascript
quotesBtn.style.display = hasPermission('quotes.manage') ? '' : 'none';
```

- [ ] **Step 4: Add quote UI functions before `toast()`**

```javascript
function findQuote(id) {
  for (var i = 0; i < quotesCache.length; i++) {
    if (quotesCache[i].id === id) {
      return quotesCache[i];
    }
  }
  return null;
}

function quoteStatusLabel(status, hasPassword) {
  if (!hasPassword) {
    return '未設定密碼';
  }
  if (status === 'active') {
    return '啟用';
  }
  if (status === 'deleted') {
    return '已刪除';
  }
  return '隱藏';
}

function updateQuotesSummary() {
  var active = 0;
  var hidden = 0;
  var noPassword = 0;
  for (var i = 0; i < quotesCache.length; i++) {
    if (!quotesCache[i].hasPassword) {
      noPassword += 1;
    } else if (quotesCache[i].status === 'active') {
      active += 1;
    } else {
      hidden += 1;
    }
  }
  document.getElementById('quotes-summary').textContent =
    '共 ' + quotesCache.length + ' 份提案，啟用 ' + active + '，隱藏 ' + hidden + '，未設定密碼 ' + noPassword;
}

function renderQuotesList() {
  var tbody = document.getElementById('quotes-list');
  if (!quotesCache.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty-state">quote 資料夾內目前沒有提案</td></tr>';
    return;
  }

  var rows = [];
  for (var i = 0; i < quotesCache.length; i++) {
    var quote = quotesCache[i];
    var classes = quote.id === selectedQuoteId ? 'is-selected' : '';
    rows.push(
      '<tr class="' + classes + '" onclick="openQuoteForm(\'' + esc(quote.id) + '\')">' +
        '<td><strong>' + esc(quote.title || quote.id) + '</strong><div class="muted">' + esc(quote.id) + '</div></td>' +
        '<td><span class="status-chip ' + (quote.status === 'active' && quote.hasPassword ? 'is-enabled' : 'is-disabled') + '">' +
          esc(quoteStatusLabel(quote.status, quote.hasPassword)) + '</span></td>' +
        '<td>' + (quote.hasPassword ? '已設定' : '<span class="muted">未設定</span>') + '</td>' +
        '<td><a href="' + esc(quote.url) + '" target="_blank">' + esc(quote.url) + '</a></td>' +
      '</tr>'
    );
  }
  tbody.innerHTML = rows.join('');
}

function openQuoteForm(id) {
  var quote = id ? findQuote(id) : null;
  selectedQuoteId = quote ? quote.id : '';
  renderQuotesList();
  document.getElementById('quote-password').value = '';

  if (!quote) {
    document.getElementById('quote-form-title').textContent = '選擇提案';
    document.getElementById('quote-id').value = '';
    document.getElementById('quote-id-display').value = '';
    document.getElementById('quote-title').value = '';
    document.getElementById('quote-status').value = 'hidden';
    document.getElementById('quote-delete-btn').style.display = 'none';
    return;
  }

  document.getElementById('quote-form-title').textContent = '編輯提案';
  document.getElementById('quote-id').value = quote.id;
  document.getElementById('quote-id-display').value = quote.id;
  document.getElementById('quote-title').value = quote.title || quote.id;
  document.getElementById('quote-status').value = quote.status === 'active' ? 'active' : 'hidden';
  document.getElementById('quote-delete-btn').style.display = '';
}

function loadQuotes(preselectId) {
  if (!hasPermission('quotes.manage')) {
    return Promise.resolve();
  }
  return api('GET', '/api/quotes').then(function(data) {
    quotesCache = (data && data.quotes) || [];
    updateQuotesSummary();
    renderQuotesList();
    var nextId = preselectId || selectedQuoteId;
    if (!nextId || !findQuote(nextId)) {
      nextId = quotesCache.length ? quotesCache[0].id : '';
    }
    openQuoteForm(nextId);
  }).catch(function(error) {
    toast('載入提案失敗：' + error.message, true);
  });
}

function openQuotesModal() {
  if (!requirePermission('quotes.manage', '只有管理員可以管理提案')) {
    return;
  }
  document.getElementById('quotes-modal').classList.add('is-open');
  loadQuotes();
}

function closeQuotesModal() {
  document.getElementById('quotes-modal').classList.remove('is-open');
}

function saveQuote() {
  if (!requirePermission('quotes.manage', '只有管理員可以管理提案')) {
    return;
  }
  var id = document.getElementById('quote-id').value;
  if (!id) {
    toast('請先選擇提案', true);
    return;
  }
  var payload = {
    title: document.getElementById('quote-title').value.replace(/^\s+|\s+$/g, '') || id,
    status: document.getElementById('quote-status').value
  };
  var password = document.getElementById('quote-password').value;
  if (password) {
    if (password.length < 6) {
      toast('提案密碼至少需要 6 碼', true);
      return;
    }
    payload.password = password;
  }
  api('PUT', '/api/quotes/' + encodeURIComponent(id), payload).then(function(response) {
    toast('提案已儲存');
    document.getElementById('quote-password').value = '';
    var quote = response && response.quote ? response.quote : null;
    return loadQuotes(quote ? quote.id : id);
  }).catch(function(error) {
    toast('儲存提案失敗：' + error.message, true);
  });
}

function deleteSelectedQuote() {
  if (!requirePermission('quotes.manage', '只有管理員可以管理提案')) {
    return;
  }
  var id = document.getElementById('quote-id').value;
  if (!id) {
    toast('請先選擇提案', true);
    return;
  }
  openConfirm('確定要刪除提案「' + id + '」？資料夾會移到 quote/_deleted。', function() {
    api('DELETE', '/api/quotes/' + encodeURIComponent(id)).then(function() {
      closeConfirm();
      selectedQuoteId = '';
      toast('提案已移到 _deleted');
      return loadQuotes();
    }).catch(function(error) {
      toast('刪除提案失敗：' + error.message, true);
    });
  });
}
```

- [ ] **Step 5: Close quote modal on logout and unauthorized**

Call `closeQuotesModal()` in `handleUnauthorized()` and `doLogout()` beside `closeAccountsModal()`.

```javascript
closeQuotesModal();
```

- [ ] **Step 6: Run UI and quote tests**

Run:

```powershell
python -m unittest tests.test_admin_quote_ui tests.test_quote_auth -v
```

Expected: PASS.

- [ ] **Step 7: Commit admin UI**

```powershell
git add admin/index.html admin/app.js tests/test_admin_quote_ui.py
git commit -m "加入提案管理後台介面"
```

## Task 7: Final Verification

**Files:**
- Verify: `server.py`
- Verify: `admin/index.html`
- Verify: `admin/app.js`
- Verify: `tests/test_quote_auth.py`
- Verify: `tests/test_admin_quote_ui.py`

- [ ] **Step 1: Run the full available test suite**

```powershell
python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 2: Run a local smoke server**

```powershell
$env:GOODJOB_ALLOW_SQLITE='1'
python server.py --bind 127.0.0.1 --port 10814
```

Expected: server starts and prints `Murayama server running on http://127.0.0.1:10814/`.

- [ ] **Step 3: Browser smoke check**

Open `http://127.0.0.1:10814/admin/`, log in with an account that has `quotes.manage`, and verify:

- 「提案管理」 button appears.
- Existing `quote/` folders appear in the modal.
- A proposal cannot be activated without a password.
- Setting a password and activating a proposal makes `/quote/{id}/` show a password page.
- Hiding the proposal makes `/quote/{id}/` show 「此提案暫停開放」.

- [ ] **Step 4: Confirm no unrelated files changed**

```powershell
git status --short
```

Expected: clean working tree after all commits, or only intentional uncommitted local runtime files ignored by `.gitignore`.
