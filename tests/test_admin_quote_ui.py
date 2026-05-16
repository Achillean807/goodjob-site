import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AdminQuoteUiTest(unittest.TestCase):
    def read(self, rel_path):
        with open(os.path.join(ROOT, rel_path), "r", encoding="utf-8") as fh:
            return fh.read()

    def js_function_body(self, js, function_name):
        signature = f"function {function_name}("
        start = js.find(signature)
        self.assertNotEqual(start, -1, f"{function_name} function not found")
        brace_start = js.find("{", start)
        self.assertNotEqual(brace_start, -1, f"{function_name} opening brace not found")

        depth = 0
        in_string = None
        escape = False
        for index in range(brace_start, len(js)):
            char = js[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == in_string:
                    in_string = None
                continue

            if char in ("'", '"', "`"):
                in_string = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return js[brace_start + 1:index]

        self.fail(f"{function_name} closing brace not found")

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

    def test_apply_permissions_wires_quote_management_button(self):
        js = self.read("admin/app.js")
        body = self.js_function_body(js, "applyPermissions")
        self.assertIn("var quotesBtn = document.getElementById('quotes-btn');", body)
        self.assertIn("quotesBtn.style.display = hasPermission('quotes.manage') ? '' : 'none';", body)

    def test_logout_paths_clear_quote_modal_state(self):
        js = self.read("admin/app.js")
        for function_name in ("handleUnauthorized", "doLogout"):
            body = self.js_function_body(js, function_name)
            with self.subTest(function_name=function_name):
                self.assertIn("quotesCache = [];", body)
                self.assertIn("selectedQuoteId = '';", body)
                self.assertIn("closeQuotesModal();", body)

    def test_render_quotes_list_escapes_fields_and_hardens_preview_link(self):
        js = self.read("admin/app.js")
        body = self.js_function_body(js, "renderQuotesList")
        self.assertIn("esc(quote.title || quote.id)", body)
        self.assertIn("esc(quote.id)", body)
        self.assertIn("esc(quote.url)", body)
        self.assertIn('target="_blank" rel="noopener noreferrer"', body)

    def test_load_quotes_checks_permission_and_fetches_quotes_api(self):
        js = self.read("admin/app.js")
        body = self.js_function_body(js, "loadQuotes")
        self.assertIn("hasPermission('quotes.manage')", body)
        self.assertIn("api('GET', '/api/quotes')", body)

    def test_save_quote_requires_permission_preflights_password_and_updates_api(self):
        js = self.read("admin/app.js")
        body = self.js_function_body(js, "saveQuote")
        self.assertIn("requirePermission('quotes.manage'", body)
        self.assertIn("var selectedQuote = findQuote(id);", body)
        self.assertIn("payload.status === 'active'", body)
        self.assertIn("selectedQuote && !selectedQuote.hasPassword", body)
        self.assertIn("!password", body)
        self.assertIn("api('PUT', '/api/quotes/' + encodeURIComponent(id), payload)", body)

    def test_delete_selected_quote_requires_permission_and_deletes_api(self):
        js = self.read("admin/app.js")
        body = self.js_function_body(js, "deleteSelectedQuote")
        self.assertIn("requirePermission('quotes.manage'", body)
        self.assertIn("api('DELETE', '/api/quotes/' + encodeURIComponent(id))", body)


if __name__ == "__main__":
    unittest.main()
