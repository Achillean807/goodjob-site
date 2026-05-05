import base64
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class QuoteAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = free_port()
        env = os.environ.copy()
        env["GOODJOB_QUOTE_USER"] = "client"
        env["GOODJOB_QUOTE_PASSWORD"] = "secret"
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

    def request(self, path, username=None, password=None):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method="HEAD")
        if username is not None and password is not None:
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
            req.add_header("Authorization", f"Basic {token}")
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, response.headers
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers

    def test_quote_pages_are_public_and_keep_noindex(self):
        status, headers = self.request("/quote/260606/")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

        status, headers = self.request("/quote/260606/", "client", "secret")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

    def test_quote_assets_are_public_and_keep_noindex(self):
        status, headers = self.request("/quote/260606/images/003.jpg")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

        status, headers = self.request("/quote/260606/images/003.jpg", "client", "secret")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

    def test_public_quote_260613_does_not_require_basic_auth(self):
        status, headers = self.request("/quote/260613/")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))

    def test_public_home_does_not_require_basic_auth(self):
        status, headers = self.request("/")
        self.assertEqual(status, 200)
        self.assertNotIn("WWW-Authenticate", headers)

    def test_robots_is_not_cached_by_origin(self):
        status, headers = self.request("/robots.txt")
        self.assertEqual(status, 200)
        self.assertIn("no-store", headers.get("Cache-Control", ""))


if __name__ == "__main__":
    unittest.main()
