import unittest

import server


class SectionGalleryClassTest(unittest.TestCase):
    def test_column_rule(self):
        # 2 的倍數、不是 3 的倍數 → 每排 2 張；其餘維持預設
        expect = {1: "works-gallery", 2: "works-gallery works-gallery--2col",
                  3: "works-gallery", 4: "works-gallery works-gallery--2col",
                  6: "works-gallery", 8: "works-gallery works-gallery--2col",
                  9: "works-gallery", 12: "works-gallery"}
        for n, cls in expect.items():
            self.assertEqual(server._section_gallery_class(n), cls, n)

    def test_wide_wins(self):
        self.assertEqual(server._section_gallery_class(4, True), "works-gallery works-gallery--wide")
        self.assertEqual(server._section_gallery_class(1, True), "works-gallery works-gallery--wide")


if __name__ == "__main__":
    unittest.main()
