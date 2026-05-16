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
