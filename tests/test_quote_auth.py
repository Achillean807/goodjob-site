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
        cls.proc = None
        cls.tmpdir = tempfile.mkdtemp(prefix="goodjob-quote-test-")
        try:
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
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
            raise RuntimeError(cls._server_startup_error())
        except Exception:
            cls._stop_server()
            shutil.rmtree(cls.tmpdir, ignore_errors=True)
            raise

    @classmethod
    def tearDownClass(cls):
        cls._stop_server()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    @classmethod
    def _stop_server(cls):
        if cls.proc is None:
            return "", ""
        if cls.proc.poll() is None:
            cls.proc.terminate()
        try:
            stdout, stderr = cls.proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
            stdout, stderr = cls.proc.communicate(timeout=5)
        cls.proc = None
        return stdout or "", stderr or ""

    @classmethod
    def _server_startup_error(cls):
        returncode = cls.proc.poll() if cls.proc is not None else None
        stdout, stderr = cls._stop_server()
        return (
            f"test server did not start on 127.0.0.1:{cls.port}; "
            f"exit code: {returncode}\n"
            f"stdout:\n{stdout[-4000:] or '<empty>'}\n"
            f"stderr:\n{stderr[-4000:] or '<empty>'}"
        )

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
                },
            ]
        }
        with open(os.path.join(cls.data_dir, "accounts.json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def basic_auth(self, username="admin", password="adminpass"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def set_quote(self, quote_id, payload):
        status, headers, body = self.request(
            f"/api/quotes/{quote_id}",
            method="PUT",
            data=payload,
            auth=True,
        )
        self.assertIn(status, (200, 201), body)
        return json.loads(body)

    def request(self, path, method="GET", data=None, auth=False, opener=None, headers=None, raw=False):
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
                response_body = response.read()
                if raw:
                    return response.status, response.headers, response_body
                return response.status, response.headers, response_body.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            response_body = exc.read()
            if raw:
                return exc.code, exc.headers, response_body
            return exc.code, exc.headers, response_body.decode("utf-8", errors="replace")

    def assert_quote_private_headers(self, headers):
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

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
        deleted_rel_path = payload["quote"]["deletedPath"]
        deleted_fs_path = os.path.join(
            self.quote_dir,
            *deleted_rel_path.replace("\\", "/").split("/")[1:],
        )
        self.assertTrue(os.path.isdir(deleted_fs_path))
        self.assertTrue(
            os.path.exists(os.path.join(deleted_fs_path, "index.html"))
            or os.path.exists(os.path.join(deleted_fs_path, "images", "003.jpg"))
        )
        with open(self.manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        self.assertEqual(manifest["quotes"]["260613"]["status"], "deleted")
        self.assertEqual(manifest["quotes"]["260613"]["deletedPath"], deleted_rel_path)

        status, headers, body = self.request("/quote/260613/")
        self.assertEqual(status, 200)
        self.assertIn("此提案暫停開放", body)

    def test_unconfigured_quote_shows_paused_page(self):
        status, headers, body = self.request("/quote/260606/")
        self.assertEqual(status, 200)
        self.assertIn("此提案暫停開放", body)
        self.assertNotIn("proposal 260606", body)
        self.assert_quote_private_headers(headers)

    def test_unconfigured_quote_asset_is_not_public(self):
        status, headers, body = self.request("/quote/260606/images/003.jpg")
        self.assertEqual(status, 200)
        self.assertIn("此提案暫停開放", body)
        self.assertNotIn("fake-jpg", body)
        self.assert_quote_private_headers(headers)

    def test_unconfigured_quote_asset_head_has_no_body(self):
        status, headers, body = self.request(
            "/quote/260606/images/003.jpg",
            method="HEAD",
            raw=True,
        )
        self.assertEqual(status, 200)
        self.assert_quote_private_headers(headers)
        self.assertEqual(body, b"")

    def test_quote_traversal_attempts_do_not_leak_content(self):
        paths = [
            "/quote/260606/../260606/index.html",
            "/quote/260606/%2e%2e/260606/index.html",
            "/quote%2F260606/",
        ]
        for path in paths:
            with self.subTest(path=path):
                status, headers, body = self.request(path)
                self.assertIn(status, (200, 404))
                self.assertNotIn("proposal 260606", body)
                self.assertNotIn("fake-jpg", body)
                self.assert_quote_private_headers(headers)

    def test_public_home_does_not_require_quote_password(self):
        status, headers, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)

    def test_robots_is_not_cached_by_origin(self):
        status, headers, body = self.request("/robots.txt")
        self.assertEqual(status, 200)
        self.assertIn("no-store", headers.get("Cache-Control", ""))


if __name__ == "__main__":
    unittest.main()
