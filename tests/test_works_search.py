import unittest

import server


def _article(id_, title, description, category, featured=False, created_at="2026-01-01T00:00:00"):
    return {
        "id": id_,
        "title": title,
        "description": description,
        "category": category,
        "featured": featured,
        "createdAt": created_at,
    }


ARTICLES = [
    _article(
        "c35fa390", "海運尾牙｜航向魔法學院",
        "當全球航運巨頭遇上魔法世界，一場跨越現實與奇幻的企業尾牙就此啟航，魔法學院世界觀深度融合。",
        "magic", created_at="2026-06-10T00:00:00",
    ),
    _article(
        "lativ-magic-platform", "Lativ 魔法月台派對",
        "Lativ 品牌年度派對，打造魔法月台主題場景，從入口拱門到舞台佈置。",
        "magic", created_at="2026-03-01T00:00:00",
    ),
    _article(
        "brand-launch-event", "品牌新品發表主題活動",
        "為新品上市打造主題化品牌活動場景，強化第一印象與記憶點。",
        "business", created_at="2026-05-01T00:00:00",
    ),
    _article(
        "spring-banquet", "科技業春酒尾牙佈置",
        "年度春酒尾牙宴會廳佈置，主視覺牆與舞台燈光設計。",
        "party", created_at="2026-02-01T00:00:00",
    ),
]


class WorksSearchTermsTest(unittest.TestCase):
    def test_cjk_bigram_and_dedup(self):
        self.assertEqual(server._works_search_terms("尾牙佈置"), ["尾牙", "牙佈", "佈置"])

    def test_alnum_whole_word(self):
        self.assertIn("lativ", server._works_search_terms("Lativ 派對"))

    def test_magic_synonym_added_as_whole_term(self):
        terms = server._works_search_terms("哈利波特")
        self.assertIn("哈利波特", terms)

    def test_cap_at_16_terms(self):
        long_q = "一二三四五六七八九十甲乙丙丁戊己庚辛壬癸子丑寅卯" * 2
        self.assertLessEqual(len(server._works_search_terms(long_q)), 16)

    def test_empty_query_returns_empty(self):
        self.assertEqual(server._works_search_terms(""), [])


class WorksSearchRankTest(unittest.TestCase):
    def test_harry_potter_hits_magic_and_ranks_first(self):
        terms = server._works_search_terms("哈利波特")
        ranked = server._works_search_rank(ARTICLES, terms, 5)
        self.assertTrue(ranked)
        self.assertEqual(ranked[0]["category"], "magic")

    def test_business_article_not_matched_by_unrelated_term(self):
        terms = server._works_search_terms("尾牙")
        ranked = server._works_search_rank(ARTICLES, terms, 5)
        ids = [a["id"] for a in ranked]
        self.assertNotIn("brand-launch-event", ids)
        self.assertIn("spring-banquet", ids)

    def test_business_article_matched_by_category_label_term(self):
        terms = server._works_search_terms("品牌活動")
        ranked = server._works_search_rank(ARTICLES, terms, 5)
        ids = [a["id"] for a in ranked]
        self.assertIn("brand-launch-event", ids)

    def test_limit_applies(self):
        terms = server._works_search_terms("魔法")
        ranked = server._works_search_rank(ARTICLES, terms, 1)
        self.assertEqual(len(ranked), 1)

    def test_no_hit_returns_empty(self):
        terms = server._works_search_terms("完全不相干的詞彙xyz999")
        ranked = server._works_search_rank(ARTICLES, terms, 5)
        self.assertEqual(ranked, [])

    def test_empty_terms_returns_empty(self):
        self.assertEqual(server._works_search_rank(ARTICLES, [], 5), [])


if __name__ == "__main__":
    unittest.main()
