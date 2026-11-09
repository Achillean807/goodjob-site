import io
import unittest
from unittest import mock

import server

LUNAR = ("/services/lunar-new-year-decor/", "春節佈置")
XMAS = ("/services/christmas-decor/", "聖誕節佈置")
PARTY = ("/services/party-spring-banquet/", "春酒尾牙佈置")


def _article(aid, category, slug=None):
    return {"id": aid, "slug": slug, "title": f"作品 {aid}", "description": "文案第一句。",
            "category": category, "images": [f"https://x/{aid}-1.webp"],
            "heroImage": f"https://x/{aid}-1.webp", "caseBlocks": {}}


ARTICLES = [
    _article("2c4af1fc", "business", "christmas-series-decor"),
    _article("1c45c415", "party", "hotel-lunar-new-year-decor"),
    _article("tianyuequan-lunar-new-year-decor", "party"),
    _article("benz-taichung-lunar-new-year-decor", "party"),
    _article("corporate-lobby-lunar-new-year-decor", "party"),
    _article("kway-2025-year-end-party", "party"),
    _article("lanya-junior-high-50th-anniversary", "school"),
]


class PillarOverridesTest(unittest.TestCase):
    def _render(self, key):
        h = server.MurayamaHandler.__new__(server.MurayamaHandler)
        h.path = f"/works/{key}"
        h.wfile = io.BytesIO()
        h.send_response = lambda *a: None
        h.send_header = lambda *a: None
        h.end_headers = lambda: None
        with mock.patch.object(server, "_load_articles", return_value=ARTICLES):
            h._serve_works_page(key, head_only=False)
        return h.wfile.getvalue().decode("utf-8")

    def _assert_pillar(self, key, pillar):
        html = self._render(key)
        url, label = pillar
        # 麵包屑＋服務入口各一處
        self.assertEqual(html.count(f'<a href="{url}">{label}</a>'), 2, key)
        # BreadcrumbList JSON-LD 第 2 層
        self.assertIn(f'"name": "{label}", "item": "{server.SITE_URL}{url}"', html, key)

    def test_overrides(self):
        self.assertEqual(server.PILLAR_OVERRIDES["2c4af1fc"], XMAS)
        self._assert_pillar("christmas-series-decor", XMAS)
        for key in ("hotel-lunar-new-year-decor", "tianyuequan-lunar-new-year-decor",
                    "benz-taichung-lunar-new-year-decor", "corporate-lobby-lunar-new-year-decor"):
            self._assert_pillar(key, LUNAR)

    def test_others_follow_category(self):
        self._assert_pillar("kway-2025-year-end-party", PARTY)
        self._assert_pillar("lanya-junior-high-50th-anniversary", server.CLUSTER_PILLAR_MAP["school"])


if __name__ == "__main__":
    unittest.main()
