import unittest

import server


class MetaSummaryTest(unittest.TestCase):
    def test_short_text_untouched(self):
        self.assertEqual(server._meta_summary("第一段。\n\n第二段。"), "第一段。 第二段。")

    def test_cuts_at_last_sentence_end_within_limit(self):
        text = "甲" * 150 + "。" + "乙" * 50
        self.assertEqual(server._meta_summary(text), "甲" * 150 + "。")

    def test_keeps_closing_quote_after_sentence_end(self):
        text = "甲" * 150 + "？」" + "乙" * 50
        self.assertEqual(server._meta_summary(text), "甲" * 150 + "？」")

    def test_falls_back_to_comma_with_ellipsis(self):
        text = "甲" * 100 + "，" + "乙" * 100
        self.assertEqual(server._meta_summary(text), "甲" * 100 + "…")

    def test_never_exceeds_limit_or_uses_three_dots(self):
        out = server._meta_summary("甲" * 300)
        self.assertLessEqual(len(out), 160)
        self.assertFalse(out.endswith("..."))


if __name__ == "__main__":
    unittest.main()
