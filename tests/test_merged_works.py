import unittest
from unittest import mock

import server


class MergedWorksRedirectTest(unittest.TestCase):
    def _call(self, url_key, path, head_only=False):
        h = server.MurayamaHandler.__new__(server.MurayamaHandler)
        h.path = path
        sent = {"status": None, "headers": {}}
        h.send_response = lambda code, *a: sent.__setitem__("status", code)
        h.send_header = lambda k, v: sent["headers"].__setitem__(k, v)
        h.end_headers = lambda: None
        # 判斷要在查 DB 之前：一旦查 DB 就讓測試失敗
        with mock.patch.object(server, "_load_articles", side_effect=AssertionError("不該查 DB")):
            h._serve_works_page(url_key, head_only=head_only)
        return sent

    def test_old_id_and_slug_redirect(self):
        for key in ("81bf85d4", "auto-brand-new-year-showroom"):
            for head_only in (False, True):
                sent = self._call(key, f"/works/{key}", head_only)
                self.assertEqual(sent["status"], 301)
                self.assertEqual(sent["headers"]["Location"],
                                 "/works/benz-taichung-lunar-new-year-decor")

    def test_query_string_kept(self):
        sent = self._call("81bf85d4", "/works/81bf85d4?utm=x&a=1")
        self.assertEqual(sent["headers"]["Location"],
                         "/works/benz-taichung-lunar-new-year-decor?utm=x&a=1")


if __name__ == "__main__":
    unittest.main()
