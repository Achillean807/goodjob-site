"""密碼雜湊升級（PBKDF2）測試：格式、舊格式相容、登入自動升級、格式錯誤不 500。"""
import base64
import hashlib
import http.client
import http.cookiejar
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

import server


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = 15  # PBKDF2 一次約 0.5 秒，伺服器單執行緒，留寬一點


def legacy_hash(salt, password):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def pbkdf2_hash(salt, password, iterations):
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()
    return f"pbkdf2_sha256${iterations}${digest}"


# 不測預算的伺服器測試類別都關掉全網 PBKDF2 預算（100% = 不限），避免連續登入被 429。
NO_BUDGET_ENV = {"GOODJOB_PBKDF2_BUDGET_PERCENT": "100"}


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def basic_auth(username, password):
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


class PasswordHashUnitTest(unittest.TestCase):
    def test_new_format_roundtrip(self):
        stored = server._make_password_hash("0123abcd", "s3cret-密碼")
        algo, iterations, digest = stored.split("$")
        self.assertEqual(algo, "pbkdf2_sha256")
        self.assertEqual(iterations, "600000")
        self.assertEqual(len(digest), 64)
        self.assertTrue(server._verify_password("0123abcd", "s3cret-密碼", stored))
        self.assertFalse(server._verify_password("0123abcd", "wrong", stored))
        self.assertFalse(server._verify_password("othersalt", "s3cret-密碼", stored))
        self.assertFalse(server._password_needs_upgrade(stored))

    def test_iterations_read_from_hash_string(self):
        stored = pbkdf2_hash("salt", "pw", 100000)
        self.assertTrue(server._verify_password("salt", "pw", stored))
        self.assertFalse(server._verify_password("salt", "pw2", stored))
        self.assertTrue(server._password_needs_upgrade(stored))

    def test_iterations_outside_100k_to_1_2m_are_malformed(self):
        # 只看格式、不跑 PBKDF2：邊界內回 (次數, 摘要)，邊界外一律 None
        digest = "0" * 64
        self.assertEqual(server._pbkdf2_parts(f"pbkdf2_sha256$100000${digest}"), (100000, digest))
        self.assertEqual(server._pbkdf2_parts(f"pbkdf2_sha256$1200000${digest}"), (1200000, digest))
        for iterations in (1, 99999, 1200001, 10000000):
            with self.subTest(iterations=iterations):
                self.assertIsNone(server._pbkdf2_parts(f"pbkdf2_sha256${iterations}${digest}"))
        # 次數 1 的雜湊即使摘要正確也不再接受（舊版會通過）
        self.assertFalse(server._verify_password("salt", "pw", pbkdf2_hash("salt", "pw", 1)))

    def test_legacy_format_still_verifies(self):
        stored = legacy_hash("adminsalt", "adminpass")
        self.assertTrue(server._verify_password("adminsalt", "adminpass", stored))
        self.assertTrue(server._verify_password("adminsalt", "adminpass", stored.upper()))
        self.assertFalse(server._verify_password("adminsalt", "wrong", stored))
        self.assertTrue(server._password_needs_upgrade(stored))

    def test_malformed_hashes_return_false_without_raising(self):
        bad = [
            "pbkdf2_sha256$abc$zz",
            "pbkdf2_sha256$$",
            "pbkdf2_sha256$600000",
            "pbkdf2_sha256$600000$zz$extra",
            "pbkdf2_sha256$0$aa",
            "pbkdf2_sha256$99999999$aa",
            "pbkdf2_sha256$+5$aa",
            "pbkdf2_sha256$１$aa",
            "pbkdf2_sha256$1$é",
            "zz" * 32,
            "a" * 63,
            "",
            None,
            123,
        ]
        for stored in bad:
            with self.subTest(stored=stored):
                self.assertFalse(server._verify_password("salt", "pw", stored))
        self.assertFalse(server._verify_password(None, None, legacy_hash("", "")))
        self.assertTrue(server._verify_password(None, "", legacy_hash("", "")))

    def test_cached_verify_only_caches_success(self):
        stored = pbkdf2_hash("s", "pw", 100000)
        self.assertFalse(server._verify_password_cached("s", "nope", stored))
        self.assertTrue(server._verify_password_cached("s", "pw", stored))
        with mock.patch.object(server, "_verify_password", side_effect=AssertionError("should hit cache")):
            self.assertTrue(server._verify_password_cached("s", "pw", stored))
        self.assertFalse(server._verify_password_cached("s", "nope", stored))

    def test_quote_upgrade_write_failure_keeps_old_record(self):
        record = {"passwordSalt": "qs", "passwordHash": legacy_hash("qs", "pw"), "status": "active"}
        manifest = {"quotes": {"260701": dict(record)}}
        with mock.patch.object(server, "_load_quote_manifest", return_value=manifest), \
                mock.patch.object(server, "_save_quote_manifest", side_effect=OSError("disk full")):
            result = server._upgrade_quote_password_hash("260701", record, "pw")
        self.assertIs(result, record)
        self.assertEqual(result["passwordHash"], legacy_hash("qs", "pw"))

    def test_account_upgrade_db_failure_does_not_raise(self):
        account = {"username": "admin", "salt": "s", "passwordHash": legacy_hash("s", "pw")}
        with mock.patch.object(server, "_using_postgres", return_value=False), \
                mock.patch.object(server, "_db_connect", side_effect=sqlite3.OperationalError("locked")):
            server._upgrade_account_password_hash(account, "pw")

    def test_non_ascii_quote_cookie_is_rejected_without_raising(self):
        record = {"passwordSalt": "s", "passwordHash": legacy_hash("s", "pw")}
        # 第一個是審查探針重現 TypeError 的寫法（引號包住的非 ASCII 值）
        for raw in ('quote_auth_260701="1:\xe9"', "quote_auth_260701=1:\xe9", 'quote_auth_260701="\xe9:abc"'):
            with self.subTest(raw=ascii(raw)):
                self.assertFalse(server._valid_quote_cookie("260701", record, raw))
        good = "quote_auth_260701=" + server._make_quote_cookie_value("260701", record)
        self.assertTrue(server._valid_quote_cookie("260701", record, good))

    def test_save_quote_manifest_strips_plaintext_from_every_record(self):
        tmpdir = tempfile.mkdtemp(prefix="goodjob-manifest-test-")
        self.addCleanup(shutil.rmtree, tmpdir, True)
        path = os.path.join(tmpdir, "quote_manifest.json")
        manifest = {"quotes": {
            "260701": {"title": "A", "passwordHash": "h", "passwordPlain": "secret-a"},
            "260702": {"title": "B", "passwordPlain": "secret-b"},
            "260703": "not-a-dict",
        }}
        with mock.patch.object(server, "QUOTE_MANIFEST_PATH", path):
            server._save_quote_manifest(manifest)
        with open(path, encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertNotIn("passwordPlain", json.dumps(saved))
        self.assertNotIn("secret-", json.dumps(saved))
        self.assertEqual(saved["quotes"]["260701"], {"title": "A", "passwordHash": "h"})

    def test_update_quote_hashes_password_before_reading_manifest(self):
        tmpdir = tempfile.mkdtemp(prefix="goodjob-quote-order-test-")
        self.addCleanup(shutil.rmtree, tmpdir, True)
        os.makedirs(os.path.join(tmpdir, "260701"))
        calls, sent = [], []
        handler = fake_handler({})
        handler._check_auth = lambda: True
        handler._require_permission = lambda permission: True
        handler._read_json_body = lambda: {"password": "newclientpass"}
        handler._send_json = lambda data, status=200: sent.append(status)
        handler._send_error_json = lambda status, message: sent.append((status, message))
        fake_hash = "pbkdf2_sha256$600000$" + "0" * 64

        def make_hash(salt, password):
            calls.append("hash")
            return fake_hash

        def load(strict=False):
            calls.append("load")
            return {"quotes": {"260701": {"title": "T", "status": "active", "passwordPlain": "old"}}}

        saved = []
        with mock.patch.object(server, "QUOTE_DIR", tmpdir), \
                mock.patch.object(server, "_make_password_hash", side_effect=make_hash), \
                mock.patch.object(server, "_load_quote_manifest", side_effect=load), \
                mock.patch.object(server, "_save_quote_manifest", side_effect=lambda m: (calls.append("save"), saved.append(m))):
            handler._api_update_quote("260701")
        self.assertEqual(sent, [200])
        self.assertEqual(calls, ["hash", "load", "save"])
        self.assertEqual(saved[0]["quotes"]["260701"]["passwordHash"], fake_hash)


class _ServerTestBase(unittest.TestCase):
    """自己起臨時伺服器（SQLite）。啟動探測打 /api/session，收到任何 HTTP 回應（含 401）就算起來；
    不打 /，因為快照裡沒有 index.html，/ 會回 500。"""

    extra_env = {}  # 子類別要調的環境變數（例如縮短限制時間窗）

    @classmethod
    def seed(cls, data_dir, quote_dir):
        raise NotImplementedError

    @classmethod
    def setUpClass(cls):
        cls.proc = None
        cls.tmpdir = tempfile.mkdtemp(prefix="goodjob-pwhash-test-")
        cls.data_dir = os.path.join(cls.tmpdir, "data")
        cls.quote_dir = os.path.join(cls.tmpdir, "quote")
        cls.manifest_path = os.path.join(cls.data_dir, "quote_manifest.json")
        cls.db_path = os.path.join(cls.data_dir, "goodjob.sqlite3")
        os.makedirs(cls.data_dir)
        os.makedirs(cls.quote_dir)
        cls.seed(cls.data_dir, cls.quote_dir)
        cls.port = free_port()
        env = os.environ.copy()
        env.pop("GOODJOB_DATABASE_URL", None)
        env.update({
            "GOODJOB_ALLOW_SQLITE": "1",
            "GOODJOB_ALLOW_JSON_SEED": "1",
            "GOODJOB_DATA_DIR": cls.data_dir,
            "GOODJOB_DB_PATH": cls.db_path,
            "GOODJOB_QUOTE_DIR": cls.quote_dir,
            "GOODJOB_QUOTE_MANIFEST_PATH": cls.manifest_path,
            "RESEND_API_KEY": "",  # 詢問單測試不寄信
        })
        env.update(NO_BUDGET_ENV)
        env.update(cls.extra_env)
        cls.proc = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "server.py"), "--bind", "127.0.0.1", "--port", str(cls.port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/api/session", timeout=1).close()
                return
            except urllib.error.HTTPError:
                return
            except OSError:
                if cls.proc.poll() is not None:
                    break
                time.sleep(0.1)
        err = cls._stop()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)
        raise RuntimeError(f"test server did not start: {err[-2000:]}")

    @classmethod
    def tearDownClass(cls):
        cls._stop()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    @classmethod
    def _stop(cls):
        if cls.proc is None:
            return ""
        if cls.proc.poll() is None:
            cls.proc.terminate()
        try:
            _, stderr = cls.proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
            _, stderr = cls.proc.communicate(timeout=5)
        cls.proc = None
        return stderr or ""

    def request(self, path, method=None, data=None, auth=None, opener=None, form=None, headers=None):
        # method=None：有 body 時 urllib 自動用 POST
        headers = dict(headers or {})
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if form is not None:
            body = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if auth:
            headers["Authorization"] = basic_auth(*auth)
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", data=body, headers=headers, method=method)
        open_url = opener.open if opener else urllib.request.urlopen
        try:
            with open_url(req, timeout=TIMEOUT) as resp:
                return resp.status, resp.headers, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8", errors="replace")

    def read_manifest(self):
        with open(self.manifest_path, encoding="utf-8") as fh:
            return json.load(fh)

    def write_manifest(self, quotes):
        with open(self.manifest_path, "w", encoding="utf-8") as fh:
            json.dump({"quotes": quotes}, fh)

    def db_password_hash(self, username):
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("SELECT password_hash FROM accounts WHERE username = ?", (username,)).fetchone()
        finally:
            conn.close()
        return row[0] if row else None


ADMIN_PERMS = ["accounts.manage", "articles.delete", "articles.read",
               "articles.write", "quotes.manage", "uploads.write"]


class PasswordUpgradeServerTest(_ServerTestBase):
    @classmethod
    def seed(cls, data_dir, quote_dir):
        for quote_id in ("260701", "260702", "260703"):
            root = os.path.join(quote_dir, quote_id)
            os.makedirs(root)
            with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(f"<!doctype html><h1>proposal {quote_id}</h1>")
        accounts = [
            {"username": "admin", "name": "Admin", "role": "admin", "enabled": True,
             "permissions": ADMIN_PERMS, "salt": "adminsalt",
             "passwordHash": legacy_hash("adminsalt", "adminpass")},
            {"username": "viewer", "name": "Viewer", "role": "viewer", "enabled": True,
             "permissions": ["articles.read"], "salt": "viewersalt",
             "passwordHash": legacy_hash("viewersalt", "viewerpass")},
        ]
        with open(os.path.join(data_dir, "accounts.json"), "w", encoding="utf-8") as fh:
            json.dump({"accounts": accounts}, fh)

    def quote_opener(self):
        jar = http.cookiejar.CookieJar()
        return (urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)),
                urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirectHandler))

    def test_legacy_quote_login_upgrades_manifest_and_new_cookie_works(self):
        old = legacy_hash("qsalt", "clientpass")
        self.write_manifest({"260701": {
            "title": "Legacy", "status": "active", "passwordSalt": "qsalt",
            "passwordHash": old, "updatedAt": "2026-01-01T00:00:00",
            "passwordPlain": "clientpass",  # 舊版留下的明碼：升級寫回時要一起清掉
        }})
        opener, no_redirect = self.quote_opener()

        status, _, body = self.request("/quote/260701/auth", form={"password": "wrong"}, opener=no_redirect)
        self.assertEqual(status, 200, body)
        self.assertEqual(self.read_manifest()["quotes"]["260701"]["passwordHash"], old)

        status, headers, body = self.request("/quote/260701/auth", form={"password": "clientpass"}, opener=no_redirect)
        self.assertEqual(status, 303, body)
        rec = self.read_manifest()["quotes"]["260701"]
        self.assertTrue(rec["passwordHash"].startswith("pbkdf2_sha256$600000$"), rec["passwordHash"])
        self.assertTrue(server._verify_password("qsalt", "clientpass", rec["passwordHash"]))
        self.assertEqual(rec["passwordSalt"], "qsalt")
        self.assertEqual(rec["updatedAt"], "2026-01-01T00:00:00")
        self.assertNotIn("passwordPlain", rec)

        status, _, body = self.request("/quote/260701/", opener=opener)
        self.assertEqual(status, 200)
        self.assertIn("proposal 260701", body)

        # 升級後用新格式再登入一次也要過
        _, no_redirect2 = self.quote_opener()
        status, _, body = self.request("/quote/260701/auth", form={"password": "clientpass"}, opener=no_redirect2)
        self.assertEqual(status, 303, body)

    def test_malformed_quote_hash_is_rejected_not_500(self):
        self.write_manifest({"260702": {
            "title": "Broken", "status": "active", "passwordSalt": "qsalt",
            "passwordHash": "pbkdf2_sha256$abc$zz",
        }})
        status, _, body = self.request("/quote/260702/auth", form={"password": "anything"})
        self.assertEqual(status, 200, body)
        self.assertIn("密碼錯誤", body)

    def test_legacy_account_login_upgrades_only_that_row(self):
        # 不靠測試執行順序：先把 admin 強制改回舊格式
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute("UPDATE accounts SET password_hash = ? WHERE username = 'admin'",
                             (legacy_hash("adminsalt", "adminpass"),))
        finally:
            conn.close()
        self.assertEqual(self.db_password_hash("admin"), legacy_hash("adminsalt", "adminpass"))

        status, _, body = self.request("/api/session", auth=("admin", "adminpass"))
        self.assertEqual(status, 200, body)
        self.assertEqual(sorted(json.loads(body)["account"]["permissions"]), ADMIN_PERMS)
        new_hash = self.db_password_hash("admin")
        self.assertTrue(new_hash.startswith("pbkdf2_sha256$600000$"), new_hash)
        self.assertTrue(server._verify_password("adminsalt", "adminpass", new_hash))
        # 沒登入的帳號不受影響
        self.assertEqual(self.db_password_hash("viewer"), legacy_hash("viewersalt", "viewerpass"))

        status, _, body = self.request("/api/session", auth=("admin", "adminpass"))
        self.assertEqual(status, 200, body)
        self.assertEqual(sorted(json.loads(body)["account"]["permissions"]), ADMIN_PERMS)
        status, _, _ = self.request("/api/session", auth=("admin", "wrong"))
        self.assertEqual(status, 401)

    def test_new_passwords_are_written_in_new_format(self):
        self.write_manifest({})
        status, _, body = self.request(
            "/api/quotes/260703", method="PUT", auth=("admin", "adminpass"),
            data={"title": "New", "status": "active", "password": "newclientpass"})
        self.assertEqual(status, 200, body)
        rec = self.read_manifest()["quotes"]["260703"]
        self.assertTrue(rec["passwordHash"].startswith("pbkdf2_sha256$600000$"))
        opener, no_redirect = self.quote_opener()
        status, _, body = self.request("/quote/260703/auth", form={"password": "newclientpass"}, opener=no_redirect)
        self.assertEqual(status, 303, body)
        status, _, body = self.request("/quote/260703/", opener=opener)
        self.assertIn("proposal 260703", body)

        status, _, body = self.request(
            "/api/accounts", method="POST", auth=("admin", "adminpass"),
            data={"username": "editor1", "password": "editorpass", "role": "viewer",
                  "permissions": ["articles.read"]})
        self.assertEqual(status, 201, body)
        self.assertTrue(self.db_password_hash("editor1").startswith("pbkdf2_sha256$600000$"))
        status, _, _ = self.request("/api/session", auth=("editor1", "editorpass"))
        self.assertEqual(status, 200)

    def legacy_plain_manifest(self):
        # 舊版後台會把明碼存在 passwordPlain
        self.write_manifest({"260703": {
            "title": "Legacy", "status": "active", "passwordSalt": "qsalt",
            "passwordHash": legacy_hash("qsalt", "oldclientpass"), "passwordPlain": "oldclientpass",
        }})

    def test_setting_quote_password_does_not_store_or_return_plaintext(self):
        self.write_manifest({})
        status, _, body = self.request(
            "/api/quotes/260703", method="PUT", auth=("admin", "adminpass"),
            data={"title": "New", "status": "active", "password": "freshclientpass"})
        self.assertEqual(status, 200, body)
        quote = json.loads(body)["quote"]
        self.assertTrue(quote["hasPassword"])
        self.assertNotIn("password", quote)
        self.assertNotIn("freshclientpass", body)
        rec = self.read_manifest()["quotes"]["260703"]
        self.assertNotIn("passwordPlain", rec)
        self.assertNotIn("freshclientpass", json.dumps(rec))

    def test_resetting_quote_password_drops_legacy_plaintext(self):
        self.legacy_plain_manifest()
        status, _, body = self.request(
            "/api/quotes/260703", method="PUT", auth=("admin", "adminpass"),
            data={"title": "Legacy", "status": "active", "password": "newclientpass"})
        self.assertEqual(status, 200, body)
        self.assertNotIn("oldclientpass", body)
        rec = self.read_manifest()["quotes"]["260703"]
        self.assertNotIn("passwordPlain", rec)
        self.assertTrue(server._verify_password(rec["passwordSalt"], "newclientpass", rec["passwordHash"]))

    def test_any_manifest_write_drops_plaintext_of_every_quote(self):
        # 只改標題（不重設密碼），整份 manifest 的 passwordPlain 都要清掉
        self.write_manifest({
            "260702": {"title": "Other", "status": "hidden", "passwordSalt": "s2",
                       "passwordHash": legacy_hash("s2", "otherpass"), "passwordPlain": "otherpass"},
            "260703": {"title": "Legacy", "status": "active", "passwordSalt": "qsalt",
                       "passwordHash": legacy_hash("qsalt", "oldclientpass"), "passwordPlain": "oldclientpass"},
        })
        status, _, body = self.request(
            "/api/quotes/260703", method="PUT", auth=("admin", "adminpass"), data={"title": "Renamed"})
        self.assertEqual(status, 200, body)
        manifest = self.read_manifest()
        self.assertNotIn("passwordPlain", json.dumps(manifest))
        self.assertEqual(manifest["quotes"]["260703"]["title"], "Renamed")
        # 密碼沒變：舊密碼照樣能登入
        _, no_redirect = self.quote_opener()
        status, _, body = self.request("/quote/260703/auth", form={"password": "oldclientpass"}, opener=no_redirect)
        self.assertEqual(status, 303, body)

    def test_quotes_list_api_never_returns_password(self):
        self.legacy_plain_manifest()
        status, _, body = self.request("/api/quotes", auth=("admin", "adminpass"))
        self.assertEqual(status, 200, body)
        quotes = json.loads(body)["quotes"]
        self.assertTrue(quotes)
        for quote in quotes:
            self.assertNotIn("password", quote)
        self.assertTrue(next(q for q in quotes if q["id"] == "260703")["hasPassword"])
        self.assertNotIn("oldclientpass", body)


class LegacyConfigAdminTest(_ServerTestBase):
    @classmethod
    def seed(cls, data_dir, quote_dir):
        cfg = {"adminUser": "boss", "adminSalt": "cfgsalt",
               "adminPasswordHash": legacy_hash("cfgsalt", "bosspass")}
        with open(os.path.join(data_dir, "config.json"), "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)

    def test_legacy_config_admin_still_logs_in(self):
        status, _, body = self.request("/api/session", auth=("boss", "bosspass"))
        self.assertEqual(status, 200, body)
        status, _, _ = self.request("/api/session", auth=("boss", "wrong"))
        self.assertEqual(status, 401)


# ---------------------------------------------------------------------------
# 登入失敗限制、訪客 IP 判斷、帳號不存在的計時差
# ---------------------------------------------------------------------------


def fake_handler(headers, peer="127.0.0.1"):
    handler = object.__new__(server.MurayamaHandler)
    handler.headers = headers
    handler.client_address = (peer, 54321)
    return handler


class ClientIpUnitTest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(setattr, server, "TRUST_PROXY_HEADERS", server.TRUST_PROXY_HEADERS)

    def test_trusted_proxy_uses_cf_connecting_ip_never_xff(self):
        server.TRUST_PROXY_HEADERS = True
        handler = fake_handler({"CF-Connecting-IP": " 198.51.100.7 ",
                                "X-Forwarded-For": "6.6.6.6, 198.51.100.7"})
        self.assertEqual(handler._client_ip(), "198.51.100.7")
        # 只有 X-Forwarded-For：不採用，退回 TCP 來源
        self.assertEqual(fake_handler({"X-Forwarded-For": "6.6.6.6"})._client_ip(), "127.0.0.1")
        # 不合法、多值、過長、空字串：退回 TCP 來源
        for bad in ("not-an-ip", "1.2.3.4, 5.6.7.8", "1" * 100, ""):
            with self.subTest(bad=bad):
                self.assertEqual(fake_handler({"CF-Connecting-IP": bad})._client_ip(), "127.0.0.1")
        # IPv6 正規化：不同寫法算同一個 IP
        self.assertEqual(fake_handler({"CF-Connecting-IP": "2001:DB8:0:0::1"})._client_ip(), "2001:db8::1")

    def test_untrusted_ignores_proxy_headers(self):
        server.TRUST_PROXY_HEADERS = False
        handler = fake_handler({"CF-Connecting-IP": "198.51.100.7", "X-Forwarded-For": "6.6.6.6"},
                               peer="203.0.113.9")
        self.assertEqual(handler._client_ip(), "203.0.113.9")

    def test_client_ip_keeps_full_ipv6_address(self):
        # 詢問單記錄用 _client_ip：不能被 /64 限流鍵影響
        server.TRUST_PROXY_HEADERS = True
        self.assertEqual(fake_handler({"CF-Connecting-IP": "2001:db8:1:2:3:4:5:6"})._client_ip(),
                         "2001:db8:1:2:3:4:5:6")
        self.assertEqual(fake_handler({}, peer="::ffff:203.0.113.9")._client_ip(), "::ffff:203.0.113.9")


class IpLimitKeyUnitTest(unittest.TestCase):
    def test_ipv6_uses_slash_64_and_mapped_ipv4_folds_back(self):
        key = server._ip_limit_key
        self.assertEqual(key("2001:db8:1:2:3:4:5:6"), "2001:db8:1:2::/64")
        self.assertEqual(key("2001:db8:1:2:ffff::1"), key("2001:DB8:1:2::9"))
        self.assertNotEqual(key("2001:db8:1:2::1"), key("2001:db8:1:3::1"))
        self.assertEqual(key("::ffff:203.0.113.9"), "203.0.113.9")
        self.assertEqual(key("203.0.113.9"), "203.0.113.9")
        self.assertEqual(key("fe80::1%eth0"), "fe80::/64")
        self.assertEqual(key(""), "")
        self.assertEqual(server._quote_auth_state_key("2001:db8:1:2::5", "260801"), "2001:db8:1:2::/64:260801")
        self.assertEqual(server._quote_auth_state_key("::ffff:203.0.113.9", "260801"), "203.0.113.9:260801")


class Pbkdf2BudgetUnitTest(unittest.TestCase):
    """全網 PBKDF2 預算以「秒」計：用假時鐘驗回補、欠款、上限，以及攻擊下的佔用率。"""

    def run_with_clock(self, percent, burst_ms):
        clock = [1000.0]
        patches = [
            mock.patch.object(server.time, "monotonic", lambda: clock[0]),
            mock.patch.object(server, "PBKDF2_BUDGET_PERCENT", percent),
            mock.patch.object(server, "PBKDF2_BUDGET_BURST_MS", burst_ms),
            mock.patch.object(server, "_PBKDF2_BUDGET", {"balance": burst_ms / 1000, "updatedAt": clock[0]}),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        return clock

    def test_refill_debt_and_cap(self):
        clock = self.run_with_clock(25, 1000)
        self.assertTrue(server._pbkdf2_budget_available())
        server._spend_pbkdf2_budget(0.6)                   # 餘 0.4
        self.assertTrue(server._pbkdf2_budget_available())
        server._spend_pbkdf2_budget(0.6)                   # 欠 0.2
        self.assertFalse(server._pbkdf2_budget_available())
        clock[0] += 0.4                                    # 回補 0.1，還欠 0.1
        self.assertFalse(server._pbkdf2_budget_available())
        clock[0] += 0.8                                    # 再回補 0.2 → 餘 0.1
        self.assertTrue(server._pbkdf2_budget_available())
        clock[0] += 3600
        self.assertTrue(server._pbkdf2_budget_available())
        self.assertEqual(server._PBKDF2_BUDGET["balance"], 1.0)  # 最多存 burst

    def test_default_budget_leaves_at_least_half_the_time_under_attack(self):
        # 模擬攻擊者不停送需要 PBKDF2 的請求：被擋的 429 花 1 毫秒，准跑的花 cost 秒。
        # 不論單次 PBKDF2 多慢，PBKDF2 佔用都不超過 PERCENT% ＋ (burst＋單次耗時) / 總時間。
        for cost in (0.33, 0.6, 1.2):
            with self.subTest(cost=cost):
                clock = self.run_with_clock(server.PBKDF2_BUDGET_PERCENT, server.PBKDF2_BUDGET_BURST_MS)
                start, busy = clock[0], 0.0
                while clock[0] - start < 600:
                    if server._pbkdf2_budget_available():
                        server._spend_pbkdf2_budget(cost)
                        clock[0] += cost
                        busy += cost
                    else:
                        clock[0] += 0.005
                total = clock[0] - start
                bound = server.PBKDF2_BUDGET_PERCENT / 100 + (server.PBKDF2_BUDGET_BURST_MS / 1000 + cost) / total
                self.assertLessEqual(busy / total, bound)
                self.assertLessEqual(busy / total, 0.5)

    def test_default_values(self):
        self.assertEqual((server.PBKDF2_BUDGET_PERCENT, server.PBKDF2_BUDGET_BURST_MS), (30, 3000))


class AuthFailureStoreUnitTest(unittest.TestCase):
    def test_store_is_bounded_and_keeps_newest(self):
        store = {}
        with mock.patch.object(server, "AUTH_FAILURE_MAX_ENTRIES", 3):
            for i in range(10):
                server._record_auth_failure(store, f"ip{i}", 5, 60, 60)
        self.assertEqual(list(store), ["ip7", "ip8", "ip9"])

    def test_expired_entries_are_swept_before_live_ones(self):
        now = time.time()
        store = {
            "locked": {"failures": [now - 1000], "lockedUntil": now + 100},
            "live": {"failures": [now], "lockedUntil": 0},
            "expired": {"failures": [now - 1000], "lockedUntil": 0},
        }
        with mock.patch.object(server, "AUTH_FAILURE_MAX_ENTRIES", 3):
            server._record_auth_failure(store, "new", 5, 60, 60)
        self.assertEqual(list(store), ["locked", "live", "new"])

    def test_limit_locks_and_lock_is_reported(self):
        store = {}
        self.assertFalse(server._record_auth_failure(store, "k", 2, 60, 60))
        self.assertFalse(server._auth_failure_limited(store, "k", 60))
        self.assertTrue(server._record_auth_failure(store, "k", 2, 60, 60))
        self.assertTrue(server._auth_failure_limited(store, "k", 60))

    def test_flooding_new_keys_never_evicts_a_locked_entry(self):
        # 審查 P3-3 探針：先鎖住攻擊者，再灌大量新鍵；舊版會把鎖刪掉
        store = {}
        with mock.patch.object(server, "AUTH_FAILURE_MAX_ENTRIES", 5):
            for _ in range(2):
                server._record_auth_failure(store, "attacker", 2, 60, 60)
            self.assertTrue(server._auth_failure_limited(store, "attacker", 60))
            for i in range(100):
                server._record_auth_failure(store, f"flood{i}", 2, 60, 60)
            self.assertEqual(len(store), 5)
            self.assertIn("attacker", store)
            self.assertEqual(list(store)[-1], "flood99")  # 剛寫入的這筆也不刪
        self.assertTrue(server._auth_failure_limited(store, "attacker", 60))

    def test_eviction_trims_to_90_percent_so_full_store_is_not_rescanned_every_insert(self):
        store = {}
        with mock.patch.object(server, "AUTH_FAILURE_MAX_ENTRIES", 20):
            for i in range(21):
                server._record_auth_failure(store, f"ip{i}", 5, 60, 60)
            self.assertEqual(len(store), 18)  # 超過 20 才掃，一次刪到 18
            self.assertEqual(list(store)[-1], "ip20")
            for i in range(21, 23):            # 之後兩筆不用再掃
                server._record_auth_failure(store, f"ip{i}", 5, 60, 60)
            self.assertEqual(len(store), 20)

    def test_store_stays_bounded_even_when_every_entry_is_locked(self):
        store = {}
        with mock.patch.object(server, "AUTH_FAILURE_MAX_ENTRIES", 3):
            for i in range(10):
                server._record_auth_failure(store, f"ip{i}", 1, 60, 60)  # limit=1：一記就鎖
        self.assertEqual(list(store), ["ip7", "ip8", "ip9"])

    def test_recording_while_locked_never_shortens_the_lock(self):
        now = time.time()
        store = {"k": {"failures": [now - 1000], "lockedUntil": now + 500}}
        server._record_auth_failure(store, "k", 5, 60, 60)
        self.assertGreaterEqual(store["k"]["lockedUntil"], now + 500)


class AdminAuthTimingUnitTest(unittest.TestCase):
    """帳號不存在／停用時也要跑一次完整 PBKDF2（假雜湊）。用假 handler 直接呼叫 _check_auth。"""

    HASH = pbkdf2_hash("s", "pw", 100000)
    ACCOUNTS = [
        {"username": "admin", "enabled": True, "salt": "s", "passwordHash": HASH, "permissions": []},
        {"username": "off", "enabled": False, "salt": "s", "passwordHash": HASH, "permissions": []},
    ]
    IP = "192.0.2.50"

    def setUp(self):
        for name in ("ADMIN_AUTH_FAILURES", "ADMIN_AUTH_GLOBAL_FAILURES", "ADMIN_AUTH_BLOCKED"):
            patcher = mock.patch.object(server, name, {})
            patcher.start()
            self.addCleanup(patcher.stop)
        # 測試行程共用一份全網預算；這裡預設不限，測預算的案例再各自蓋掉。
        # 登入成功會觸發雜湊升級（HASH 是 10 萬次），換成 mock，免得寫到 repo 的 data/goodjob.sqlite3。
        for name, value in (("_pbkdf2_budget_available", True), ("_upgrade_account_password_hash", None)):
            patcher = mock.patch.object(server, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        server._AUTH_CACHE.clear()

    def run_auth(self, user, password, accounts, cfg=None):
        handler = fake_handler({"Authorization": basic_auth(user, password)}, peer=self.IP)
        sent = []
        handler._send_401 = lambda: sent.append(401)
        handler._send_429 = lambda: sent.append(429)
        verified = []
        real_verify = server._verify_password

        def spy(salt, pw, stored):
            verified.append(stored)
            return real_verify(salt, pw, stored)

        with mock.patch.object(server, "_load_accounts", return_value=accounts), \
                mock.patch.object(server, "_load_config", return_value=cfg or {}), \
                mock.patch.object(server, "_verify_password", side_effect=spy):
            ok = handler._check_auth()
        return ok, sent, verified

    def test_unknown_or_disabled_account_runs_dummy_pbkdf2(self):
        cfg = {"adminUser": "boss", "adminSalt": "s", "adminPasswordHash": self.HASH}
        cases = [
            ("帳號不存在", "ghost", "pw", self.ACCOUNTS, None),
            ("帳號停用（密碼正確）", "off", "pw", self.ACCOUNTS, None),
            ("舊 config 帳號名不符", "ghost", "pw", [], cfg),
        ]
        for label, user, password, accounts, config in cases:
            with self.subTest(label):
                ok, sent, verified = self.run_auth(user, password, accounts, config)
                self.assertFalse(ok)
                self.assertEqual(sent, [401])
                self.assertEqual(verified, [server._DUMMY_PASSWORD_HASH])

    def test_existing_account_verifies_its_own_hash(self):
        ok, sent, verified = self.run_auth("admin", "wrong", self.ACCOUNTS)
        self.assertEqual((ok, sent, verified), (False, [401], [self.HASH]))

    def test_legacy_hash_failure_pads_with_dummy_pbkdf2(self):
        # 舊格式 SHA-256 太快，不補的話「舊帳號存在」可從時間量出來
        old = legacy_hash("s", "pw")
        accounts = [{"username": "old", "enabled": True, "salt": "s", "passwordHash": old, "permissions": []}]
        ok, sent, verified = self.run_auth("old", "wrong", accounts)
        self.assertEqual((ok, sent, verified), (False, [401], [old, server._DUMMY_PASSWORD_HASH]))

    def test_unrecognized_hash_format_pads_with_dummy_pbkdf2(self):
        # 審查 P3-5：帳號存在但雜湊認不得（含次數超出範圍）也要補跑假 PBKDF2
        for bad in (pbkdf2_hash("s", "pw", 1), "garbage", "pbkdf2_sha256$600000"):
            with self.subTest(bad=bad):
                accounts = [{"username": "odd", "enabled": True, "salt": "s", "passwordHash": bad, "permissions": []}]
                ok, sent, verified = self.run_auth("odd", "pw", accounts)
                self.assertEqual((ok, sent, verified), (False, [401], [bad, server._DUMMY_PASSWORD_HASH]))

    def test_budget_and_breaker_429_are_not_counted_as_ip_failures(self):
        # 審查 P1-2：被全網預算或全域保險擋下的 429 沒跑 PBKDF2，不能算成這個 IP 的失敗
        with mock.patch.object(server, "_pbkdf2_budget_available", return_value=False):
            for _ in range(20):
                self.assertEqual(self.run_auth("admin", "pw", self.ACCOUNTS), (False, [429], []))
        now = time.time()
        server.ADMIN_AUTH_GLOBAL_FAILURES[server.ADMIN_AUTH_GLOBAL_KEY] = {"failures": [now], "lockedUntil": now + 60}
        for _ in range(20):
            self.assertEqual(self.run_auth("ghost", "pw", self.ACCOUNTS), (False, [429], []))
        self.assertEqual(server.ADMIN_AUTH_FAILURES, {})
        self.assertEqual(list(server.ADMIN_AUTH_GLOBAL_FAILURES), [server.ADMIN_AUTH_GLOBAL_KEY])
        self.assertEqual(len(server.ADMIN_AUTH_GLOBAL_FAILURES[server.ADMIN_AUTH_GLOBAL_KEY]["failures"]), 1)
        # 保險解除後，同一個 IP 第一次就能登入（舊版這時已被鎖 300 秒）
        server.ADMIN_AUTH_GLOBAL_FAILURES.clear()
        self.assertEqual(self.run_auth("admin", "pw", self.ACCOUNTS), (True, [], [self.HASH]))

    def test_success_does_not_clear_ip_failures(self):
        # 審查 P3-4：持有一個有效帳號的人，不能靠登入成功重置計數再猜別人
        self.assertEqual(self.run_auth("admin", "wrong", self.ACCOUNTS)[1], [401])
        self.assertTrue(self.run_auth("admin", "pw", self.ACCOUNTS)[0])
        self.assertEqual(len(server.ADMIN_AUTH_FAILURES[self.IP]["failures"]), 1)

    def test_cache_hit_is_refused_while_misses_are_cheap_and_ip_was_blocked_often(self):
        # 保險／預算期間「沒命中＝不花成本的 429、命中＝200」。同 IP 的人若被擋滿次數後還放行命中，
        # 就能高速猜「同 IP 已登入管理員」的密碼。
        self.assertTrue(self.run_auth("admin", "pw", self.ACCOUNTS)[0])  # 管理員登入，進快取
        with mock.patch.object(server, "ADMIN_AUTH_FAILURE_LIMIT", 3), \
                mock.patch.object(server, "_pbkdf2_budget_available", return_value=False):
            self.assertEqual(self.run_auth("admin", "pw", self.ACCOUNTS), (True, [], []))  # 還沒被擋過：命中照常放行
            for i in range(3):
                self.assertEqual(self.run_auth("admin", f"guess-{i}", self.ACCOUNTS), (False, [429], []))
            self.assertEqual(self.run_auth("admin", "pw", self.ACCOUNTS), (False, [429], []))  # 猜中也不放行
        self.assertEqual(server.ADMIN_AUTH_FAILURES, {})
        # 預算恢復後，快取命中照常放行，也不跑 PBKDF2
        self.assertEqual(self.run_auth("admin", "pw", self.ACCOUNTS), (True, [], []))


class _AdminAuthServerBase(_ServerTestBase):
    """後台帳號用真的 60 萬次 PBKDF2，這樣「回應 < 0.1 秒」才能證明沒跑 PBKDF2。"""

    @classmethod
    def seed(cls, data_dir, quote_dir):
        os.makedirs(os.path.join(quote_dir, "260801"))
        with open(os.path.join(quote_dir, "260801", "index.html"), "w", encoding="utf-8") as fh:
            fh.write("<!doctype html><h1>proposal 260801</h1>")
        accounts = [{"username": "admin", "name": "Admin", "role": "admin", "enabled": True,
                     "permissions": ADMIN_PERMS, "salt": "adminsalt",
                     "passwordHash": server._make_password_hash("adminsalt", "adminpass")}]
        with open(os.path.join(data_dir, "accounts.json"), "w", encoding="utf-8") as fh:
            json.dump({"accounts": accounts}, fh)

    def admin(self, ip, password, xff=None):
        headers = {"CF-Connecting-IP": ip}
        if xff:
            headers["X-Forwarded-For"] = xff
        start = time.perf_counter()
        status, _, _ = self.request("/api/session", auth=("admin", password), headers=headers)
        return status, time.perf_counter() - start


class AdminAuthLimitServerTest(_AdminAuthServerBase):
    """每 IP 上限：後台 3 次、提案 2 次。全域保險調高，避免和本類別互相干擾。每個測試用不同 IP。"""

    extra_env = {
        "GOODJOB_TRUST_PROXY_HEADERS": "1",
        "GOODJOB_ADMIN_AUTH_FAILURE_LIMIT": "3",
        "GOODJOB_ADMIN_AUTH_FAILURE_WINDOW_SECONDS": "60",
        "GOODJOB_ADMIN_AUTH_LOCK_SECONDS": "60",
        "GOODJOB_ADMIN_AUTH_GLOBAL_FAILURE_LIMIT": "1000",
        "GOODJOB_QUOTE_AUTH_FAILURE_LIMIT": "2",
        "GOODJOB_QUOTE_AUTH_FAILURE_WINDOW_SECONDS": "60",
        "GOODJOB_QUOTE_AUTH_LOCK_SECONDS": "60",
    }

    def test_lockout_returns_fast_429_even_for_cached_password(self):
        ip = "198.51.100.1"
        self.assertEqual(self.admin(ip, "adminpass")[0], 200)  # 先登入成功，密碼進快取
        status, wrong_elapsed = self.admin(ip, "wrong-1")
        self.assertEqual(status, 401)
        self.assertGreater(wrong_elapsed, 0.1)  # 對照組：沒鎖時錯密碼會跑 PBKDF2
        self.assertEqual([self.admin(ip, f"wrong-{i}")[0] for i in (2, 3)], [401, 429])

        status, elapsed = self.admin(ip, "wrong-4")  # 錯密碼才能證明沒跑 PBKDF2
        self.assertEqual(status, 429)
        self.assertLess(elapsed, 0.1)
        status, elapsed = self.admin(ip, "adminpass")  # 鎖定中連快取命中的正確密碼也擋
        self.assertEqual(status, 429)
        self.assertLess(elapsed, 0.1)
        self.assertEqual(self.admin("198.51.100.2", "adminpass")[0], 200)  # 別的 IP 不受影響

    def test_success_does_not_clear_failures(self):
        # 審查 P3-4（刻意改變舊行為）：成功登入不清計數，讓它自然過期
        ip = "198.51.100.10"
        self.assertEqual([self.admin(ip, "wrong")[0] for _ in range(2)], [401, 401])
        self.assertEqual(self.admin(ip, "adminpass")[0], 200)
        # 沒清：再錯 1 次就湊滿 3 次而鎖定
        self.assertEqual(self.admin(ip, "wrong")[0], 429)

    def test_changing_xff_first_value_cannot_bypass_lock(self):
        ip = "198.51.100.20"
        statuses = [self.admin(ip, "wrong", xff=f"203.0.113.{i}, {ip}")[0] for i in range(3)]
        self.assertEqual(statuses, [401, 401, 429])
        status, elapsed = self.admin(ip, "wrong", xff="203.0.113.99")
        self.assertEqual(status, 429)
        self.assertLess(elapsed, 0.1)
        # 鎖的是 CF-Connecting-IP：XFF 相同、CF 不同就是另一位訪客
        self.assertEqual(self.admin("198.51.100.21", "wrong", xff="203.0.113.99")[0], 401)

    def test_quote_login_limit_still_per_ip_with_cf_connecting_ip(self):
        self.write_manifest({"260801": {
            "title": "Q", "status": "active", "passwordSalt": "qsalt",
            "passwordHash": legacy_hash("qsalt", "clientpass"),
        }})
        no_redirect = urllib.request.build_opener(NoRedirectHandler)

        def quote(ip, password, xff=None):
            headers = {"CF-Connecting-IP": ip}
            if xff:
                headers["X-Forwarded-For"] = xff
            return self.request("/quote/260801/auth", form={"password": password},
                                headers=headers, opener=no_redirect)[0]

        ip = "198.51.100.30"
        self.assertEqual(quote(ip, "wrong", xff="203.0.113.1"), 200)
        self.assertEqual(quote(ip, "wrong", xff="203.0.113.2"), 429)
        self.assertEqual(quote(ip, "clientpass", xff="203.0.113.3"), 429)  # 換 XFF 也還是鎖住
        self.assertEqual(quote("198.51.100.31", "clientpass"), 303)  # 另一個 CF IP 正常登入


class AdminAuthGlobalBreakerServerTest(_AdminAuthServerBase):
    """全域保險：60 秒內 3 次失敗就鎖 60 秒。每 IP 上限調高，只測全域。整段狀態相依，放在同一個測試。"""

    extra_env = {
        "GOODJOB_TRUST_PROXY_HEADERS": "1",
        "GOODJOB_ADMIN_AUTH_FAILURE_LIMIT": "100",
        "GOODJOB_ADMIN_AUTH_GLOBAL_FAILURE_LIMIT": "3",
        "GOODJOB_ADMIN_AUTH_GLOBAL_WINDOW_SECONDS": "60",
        "GOODJOB_ADMIN_AUTH_GLOBAL_LOCK_SECONDS": "60",
    }

    def test_breaker_blocks_uncached_but_logged_in_user_keeps_working(self):
        home = "192.0.2.10"
        self.assertEqual(self.admin(home, "adminpass")[0], 200)  # 正常使用者先登入（進快取）
        # 分散 IP 的錯誤密碼，第 3 次觸發全域保險
        self.assertEqual([self.admin(f"203.0.113.{i}", "wrong")[0] for i in range(3)], [401, 401, 401])

        status, elapsed = self.admin("203.0.113.50", "wrong")
        self.assertEqual(status, 429)
        self.assertLess(elapsed, 0.1)
        # 快取綁 IP：換 IP 帶正確密碼也不能從快取通過（不能拿快取當快速猜密碼通道）
        status, elapsed = self.admin("203.0.113.51", "adminpass")
        self.assertEqual(status, 429)
        self.assertLess(elapsed, 0.1)

        for _ in range(3):  # 已登入（同 IP、同密碼、命中快取）照常可用
            status, elapsed = self.admin(home, "adminpass")
            self.assertEqual(status, 200)
            self.assertLess(elapsed, 0.1)
        self.assertEqual(self.admin(home, "wrong")[0], 429)  # 同 IP 但密碼不對：沒命中快取


class AdminBreakerRecoveryServerTest(_AdminAuthServerBase):
    """審查 P1-2：全域保險期間真管理員一直重試，保險解除後不能因此被鎖在門外。保險只鎖 2 秒。"""

    extra_env = {
        "GOODJOB_TRUST_PROXY_HEADERS": "1",
        "GOODJOB_ADMIN_AUTH_FAILURE_LIMIT": "3",
        "GOODJOB_ADMIN_AUTH_FAILURE_WINDOW_SECONDS": "60",
        "GOODJOB_ADMIN_AUTH_LOCK_SECONDS": "60",
        "GOODJOB_ADMIN_AUTH_GLOBAL_FAILURE_LIMIT": "3",
        "GOODJOB_ADMIN_AUTH_GLOBAL_WINDOW_SECONDS": "60",
        "GOODJOB_ADMIN_AUTH_GLOBAL_LOCK_SECONDS": "2",
    }

    def test_breaker_429_does_not_lock_out_the_real_admin(self):
        self.assertEqual([self.admin(f"203.0.113.{i}", "wrong")[0] for i in range(3)], [401, 401, 401])
        real = "192.0.2.77"
        for _ in range(6):  # 舊版：第 3 次起這個 IP 被記滿失敗、鎖 60 秒
            status, elapsed = self.admin(real, "adminpass")
            self.assertEqual(status, 429)
            self.assertLess(elapsed, 0.1)
        time.sleep(2.3)
        self.assertEqual(self.admin(real, "adminpass")[0], 200)
        self.assertEqual(self.admin(real, "adminpass")[0], 200)


class Pbkdf2BudgetServerTest(_AdminAuthServerBase):
    """全網 PBKDF2 預算：1% 回補、只存 1 毫秒 → 開機後只准跑 1 次 PBKDF2，之後約 60 秒內全擋。"""

    extra_env = {
        "GOODJOB_TRUST_PROXY_HEADERS": "1",
        "GOODJOB_PBKDF2_BUDGET_PERCENT": "1",
        "GOODJOB_PBKDF2_BUDGET_BURST_MS": "1",
        "GOODJOB_QUOTE_AUTH_FAILURE_LIMIT": "2",
    }

    @classmethod
    def seed(cls, data_dir, quote_dir):
        super().seed(data_dir, quote_dir)
        os.makedirs(os.path.join(quote_dir, "260802"))
        with open(os.path.join(quote_dir, "260802", "index.html"), "w", encoding="utf-8") as fh:
            fh.write("<!doctype html><h1>proposal 260802</h1>")

    def quote(self, quote_id, ip, password, opener=None):
        start = time.perf_counter()
        status, _, body = self.request(
            f"/quote/{quote_id}/auth", form={"password": password}, headers={"CF-Connecting-IP": ip},
            opener=opener or urllib.request.build_opener(NoRedirectHandler))
        return status, body, time.perf_counter() - start

    def test_shared_budget_blocks_uncached_logins_but_not_logged_in_users(self):
        self.write_manifest({
            "260801": {"title": "Q", "status": "active", "passwordSalt": "qsalt",
                       "passwordHash": server._make_password_hash("qsalt", "clientpass")},
            "260802": {"title": "L", "status": "active", "passwordSalt": "lsalt",
                       "passwordHash": legacy_hash("lsalt", "legacypass")},
        })
        # 管理員登入，用掉唯一一次 PBKDF2 額度
        self.assertEqual(self.admin("192.0.2.1", "adminpass")[0], 200)

        # 提案登入（PBKDF2 雜湊）：預算用完 → 429 加客人看得懂的訊息，不跑 PBKDF2、不洩漏內部細節
        for password in ("wrong", "clientpass"):
            status, body, elapsed = self.quote("260801", "198.51.100.1", password)
            self.assertEqual(status, 429, body)
            self.assertIn("目前登入人數較多，請稍後再試", body)
            self.assertLess(elapsed, 0.1)
            for secret in ("PBKDF2", "pbkdf2", "預算", "budget"):
                self.assertNotIn(secret, body)
        # 預算 429 不算失敗：同一組 IP×提案 超過上限（2 次）也不會變成「嘗試次數過多」
        for _ in range(3):
            status, body, _ = self.quote("260801", "198.51.100.1", "wrong")
            self.assertIn("目前登入人數較多", body)
            self.assertNotIn("嘗試次數過多", body)

        # 共用預算：沒命中快取的後台登入也 429
        status, elapsed = self.admin("192.0.2.2", "adminpass")
        self.assertEqual(status, 429)
        self.assertLess(elapsed, 0.1)
        # 已登入的管理員（同 IP、同密碼、命中快取）照常可用
        status, elapsed = self.admin("192.0.2.1", "adminpass")
        self.assertEqual(status, 200)
        self.assertLess(elapsed, 0.1)

        # 舊格式提案驗證不跑 PBKDF2，不受預算影響；登入成功後的 cookie 也照常可用
        status, body, _ = self.quote("260802", "198.51.100.2", "wrong")
        self.assertEqual(status, 200, body)
        self.assertIn("密碼錯誤", body)
        jar = http.cookiejar.CookieJar()
        no_redirect = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirectHandler)
        status, body, _ = self.quote("260802", "198.51.100.2", "legacypass", opener=no_redirect)
        self.assertEqual(status, 303, body)
        status, _, body = self.request("/quote/260802/", opener=no_redirect)
        self.assertEqual(status, 200)
        self.assertIn("proposal 260802", body)


class RequestHardeningServerTest(_AdminAuthServerBase):
    """IPv6 /64 限流鍵、詢問單保留完整 IP、非 ASCII cookie、request body 上限。"""

    extra_env = {
        "GOODJOB_TRUST_PROXY_HEADERS": "1",
        "GOODJOB_QUOTE_AUTH_FAILURE_LIMIT": "2",
        "GOODJOB_QUOTE_AUTH_FAILURE_WINDOW_SECONDS": "60",
        "GOODJOB_QUOTE_AUTH_LOCK_SECONDS": "60",
    }

    def setUp(self):
        self.write_manifest({"260801": {
            "title": "Q", "status": "active", "passwordSalt": "qsalt",
            "passwordHash": legacy_hash("qsalt", "clientpass"),
        }})

    def quote(self, ip, password):
        return self.request("/quote/260801/auth", form={"password": password}, headers={"CF-Connecting-IP": ip},
                            opener=urllib.request.build_opener(NoRedirectHandler))[0]

    def raw(self, method, path, headers, body=b""):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=TIMEOUT)
        try:
            conn.putrequest(method, path)
            for name, value in headers.items():
                conn.putheader(name, value)
            conn.endheaders()
            if body:
                conn.send(body)
            resp = conn.getresponse()
            return resp.status, resp.read().decode("utf-8", errors="replace")
        finally:
            conn.close()

    def test_ipv6_addresses_in_same_64_share_quote_limit(self):
        self.assertEqual(self.quote("2001:db8:a:b::1", "wrong"), 200)
        self.assertEqual(self.quote("2001:db8:a:b:ffff:1:2:3", "wrong"), 429)  # 同一段 /64 換位址也鎖住
        self.assertEqual(self.quote("2001:db8:a:c::1", "clientpass"), 303)     # 另一段 /64 不受影響
        # IPv4 對應的 IPv6 和 IPv4 算同一位訪客
        self.assertEqual(self.quote("::ffff:198.51.100.40", "wrong"), 200)
        self.assertEqual(self.quote("198.51.100.40", "wrong"), 429)

    def test_inquiry_keeps_full_ipv6_address(self):
        ip = "2001:db8:a:d:1:2:3:4"
        status, _, body = self.request("/api/inquiry", data={"nickname": "測試"}, headers={"CF-Connecting-IP": ip})
        self.assertEqual(status, 200, body)
        inquiry_dir = os.path.join(self.data_dir, "inquiries")
        records = []
        for name in os.listdir(inquiry_dir):
            with open(os.path.join(inquiry_dir, name), encoding="utf-8") as fh:
                records.append(json.load(fh))
        self.assertIn(ip, [r["remote_ip"] for r in records])

    def test_non_ascii_quote_cookie_gets_login_page_not_dropped_connection(self):
        cookie = {"Cookie": 'quote_auth_260801="1:\xe9"'}  # urllib 用 latin-1 送出 é
        status, _, body = self.request("/quote/260801/", headers=cookie)
        self.assertEqual(status, 200)
        self.assertIn("請輸入提案密碼", body)
        status, _, _ = self.request("/quote/260801/state", data={"a": 1}, headers=cookie)
        self.assertEqual(status, 403)

    def test_oversized_or_invalid_body_is_rejected_without_reading(self):
        auth = {"Authorization": basic_auth("admin", "adminpass"), "CF-Connecting-IP": "192.0.2.60"}
        self.assertEqual(self.request("/api/session", auth=("admin", "adminpass"),
                                      headers={"CF-Connecting-IP": "192.0.2.60"})[0], 200)
        too_big = str(server.MAX_REQUEST_BODY_BYTES + 1)
        # 只送標頭、不送 body：伺服器若真的去讀，這裡會卡到逾時
        status, body = self.raw("PUT", "/api/quotes/260801",
                                dict(auth, **{"Content-Type": "application/json", "Content-Length": too_big}))
        self.assertEqual(status, 413, body)
        status, body = self.raw("POST", "/api/accounts",
                                dict(auth, **{"Content-Type": "application/json", "Content-Length": too_big}))
        self.assertEqual(status, 413, body)
        status, body = self.raw("POST", "/quote/260801/auth",
                                {"Content-Type": "application/x-www-form-urlencoded", "Content-Length": too_big,
                                 "CF-Connecting-IP": "192.0.2.61"})
        self.assertEqual(status, 413, body)
        status, body = self.raw("PUT", "/api/quotes/260801",
                                dict(auth, **{"Content-Type": "application/json", "Content-Length": "abc"}))
        self.assertEqual(status, 400, body)
        # manifest 沒被動到
        self.assertEqual(self.read_manifest()["quotes"]["260801"]["title"], "Q")

    def test_upload_is_not_capped(self):
        # 上傳圖片維持原行為：超過 1 MB 的 multipart 照樣讀完、解析（文章不存在 → 404，不是 413）
        boundary = "goodjobtestboundary"
        payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.bin\"\r\n"
                   "Content-Type: application/octet-stream\r\n\r\n").encode("ascii")
        payload += b"\0" * (server.MAX_REQUEST_BODY_BYTES + 1024) + f"\r\n--{boundary}--\r\n".encode("ascii")
        headers = {"Authorization": basic_auth("admin", "adminpass"), "CF-Connecting-IP": "192.0.2.62",
                   "Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(payload))}
        status, body = self.raw("POST", "/api/upload/no-such-article", headers, payload)
        self.assertEqual(status, 404, body)
        self.assertIn("Article not found", body)


if __name__ == "__main__":
    unittest.main()
