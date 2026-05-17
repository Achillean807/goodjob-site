import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ControlCenterRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = None
        cls.tmpdir = tempfile.mkdtemp(prefix="goodjob-controlcenter-test-")
        try:
            data_dir = os.path.join(cls.tmpdir, "data")
            os.makedirs(data_dir, exist_ok=True)
            cls.port = free_port()
            env = os.environ.copy()
            env["GOODJOB_ALLOW_SQLITE"] = "1"
            env["GOODJOB_ALLOW_JSON_SEED"] = "1"
            env["GOODJOB_DATA_DIR"] = data_dir
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

    def request(self, path):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}")
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, response.headers, response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8", errors="replace")

    def test_controlcenter_serves_admin_shell_and_app_js(self):
        status, headers, body = self.request("/controlcenter/")
        self.assertEqual(status, 200)
        self.assertIn("村山良作 CMS", body)
        self.assertIn("/controlcenter/app.js", body)
        self.assertNotIn("/admin/app.js", body)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))

        status, headers, body = self.request("/controlcenter/app.js?v=test")
        self.assertEqual(status, 200)
        self.assertIn("function doLogin()", body)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))

    def test_legacy_admin_url_is_not_served(self):
        status, headers, body = self.request("/admin/")
        self.assertIn(status, (404, 410))
        self.assertNotIn("村山良作 CMS", body)
        self.assertIn("noindex", headers.get("X-Robots-Tag", ""))


if __name__ == "__main__":
    unittest.main()
