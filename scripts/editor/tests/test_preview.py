"""Preview server: Vercel-like 404s for ignored paths, draft overlay, read-only."""

import threading
import unittest
import urllib.error
import urllib.request

from _helpers import TempRepo
from core.preview import IgnoreRules, make_server


class IgnoreRuleTests(unittest.TestCase):
    def test_rules_from_repo_vercelignore(self):
        with TempRepo() as t:
            rules = IgnoreRules.from_repo(t.root)
            for p in ("scripts/editor/app.py", "scripts/x.js", "staging/cv-masters/a.docx", "references/x.pdf",
                      "README.md", "docs/notes.md", ".githooks/pre-commit", ".gitattributes", ".git/config",
                      ".vercelignore", ".env", ".env.local", "js/__pycache__/x.pyc"):
                self.assertTrue(rules.ignored(p), p)
            for p in ("index.html", "js/translations.js", "css/style.css", "assets/pdfs/resume/x.pdf",
                      "projects/eagle-pathway.html", "assets/images/experience/hero/a.jpg"):
                self.assertFalse(rules.ignored(p), p)

    def test_gitignore_semantics(self):
        r = IgnoreRules(["*.md", "build/", "/top.txt", "docs/private", "!keep.md"])
        self.assertTrue(r.ignored("a/b/c.md"))
        self.assertTrue(r.ignored("build/x.js"))
        self.assertFalse(r.ignored("build"))  # dir-only pattern; a file named build is fine
        self.assertTrue(r.ignored("top.txt"))
        self.assertFalse(r.ignored("sub/top.txt"))
        self.assertTrue(r.ignored("docs/private/x.txt"))
        self.assertFalse(r.ignored("keep.md"))


class PreviewServerTests(unittest.TestCase):
    def setUp(self):
        self.t = TempRepo().__enter__()
        self.overrides = {}
        self.server = make_server(self.t.root, 0, lambda: self.overrides)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.t.__exit__(None, None, None)

    def get(self, path, method="GET"):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read(), r.headers
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers

    def test_serves_site_files_and_root_index(self):
        self.assertEqual(self.get("/")[0], 200)
        code, body, headers = self.get("/js/translations.js")
        self.assertEqual(code, 200)
        self.assertEqual(body, self.t.translations.read_bytes())
        self.assertIn("javascript", headers.get("Content-Type", ""))
        self.assertEqual(headers.get("Cache-Control"), "no-store")

    def test_ignored_paths_404_like_vercel(self):
        for p in ("/scripts/x.js", "/staging/secret.txt", "/README.md", "/.vercelignore", "/scripts/", "/staging"):
            self.assertEqual(self.get(p)[0], 404, p)

    def test_no_directory_listing_and_no_traversal(self):
        self.assertEqual(self.get("/js/")[0], 404)
        code, body, _ = self.get("/../")  # normalises to / → the site index, never a parent folder
        self.assertEqual((code, body), (200, (self.t.root / "index.html").read_bytes()))
        self.assertEqual(self.get("/js/..%2f..%2fstaging/secret.txt")[0], 404)

    def test_read_only_methods(self):
        code, _, _ = self.get("/js/translations.js", method="POST")
        self.assertEqual(code, 501)
        self.assertEqual(self.get("/js/translations.js", method="HEAD")[0], 200)

    def test_draft_overlay(self):
        self.overrides["js/translations.js"] = b"// draft version\r\n"
        code, body, headers = self.get("/js/translations.js")
        self.assertEqual(code, 200)
        self.assertEqual(body, b"// draft version\r\n")
        self.assertEqual(headers.get("X-Editor-Draft"), "1")
        self.overrides.clear()
        self.assertEqual(self.get("/js/translations.js")[1], self.t.translations.read_bytes())


if __name__ == "__main__":
    unittest.main()
