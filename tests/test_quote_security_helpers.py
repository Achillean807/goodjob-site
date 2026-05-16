import unittest

import server


class QuoteSecurityHelperTest(unittest.TestCase):
    def setUp(self):
        self.original_cookie_secure = server.QUOTE_COOKIE_SECURE
        self.original_trust_proxy_headers = server.TRUST_PROXY_HEADERS

    def tearDown(self):
        server.QUOTE_COOKIE_SECURE = self.original_cookie_secure
        server.TRUST_PROXY_HEADERS = self.original_trust_proxy_headers

    def handler_with_headers(self, headers):
        handler = object.__new__(server.MurayamaHandler)
        handler.headers = headers
        return handler

    def test_forwarded_proto_requires_trusted_proxy_headers(self):
        server.QUOTE_COOKIE_SECURE = False
        server.TRUST_PROXY_HEADERS = False
        handler = self.handler_with_headers({"X-Forwarded-Proto": "https"})

        self.assertFalse(handler._should_set_secure_quote_cookie())

        server.TRUST_PROXY_HEADERS = True
        self.assertTrue(handler._should_set_secure_quote_cookie())

    def test_explicit_secure_cookie_env_overrides_proxy_detection(self):
        server.QUOTE_COOKIE_SECURE = True
        server.TRUST_PROXY_HEADERS = False
        handler = self.handler_with_headers({})

        self.assertTrue(handler._should_set_secure_quote_cookie())


if __name__ == "__main__":
    unittest.main()
