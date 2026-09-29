"""Preview server: Vercel-like 404s for ignored paths, draft overlay, read-only,
Host/Origin allow-list, and no way around the ignore rules by letter case, 8.3
short names or traversal."""

import http.client
import os
import threading
import unittest
import urllib.error
import urllib.request

from _helpers import TempRepo
from core.preview import IgnoreRules, make_server


def short_path(path: str):
    """The 8.3 short form of an existing path on Windows, or None."""
    if os.name != "nt":
        return None
    import ctypes

    buf = ctypes.create_unicode_buffer(1024)
    n = ctypes.windll.kernel32.GetShortPathNameW(path, buf, 1024)
    return buf.value if 0 < n < 1024 else None


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

    def test_matching_ignores_letter_case(self):
        r = IgnoreRules(["*.md", "staging/", ".env.*", "Docs/Private"])
        for p in ("NOTES.MD", "notes.Md", "STAGING/x.txt", "Staging/Sub/y", ".ENV.local", ".env.LOCAL", "docs/private/z"):
            self.assertTrue(r.ignored(p), p)
        self.assertFalse(r.ignored("index.html"))


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

    def raw(self, path, host=None, origin=None):
        """GET with an explicit Host (and optional Origin) header; returns (status, body)."""
        headers = {"Host": host if host is not None else f"127.0.0.1:{self.port}"}
        if origin is not None:
            headers["Origin"] = origin
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.request("GET", path, headers=headers)
            r = conn.getresponse()
            return r.status, r.read()
        finally:
            conn.close()

    def test_serves_site_files_and_root_index(self):
        self.assertEqual(self.get("/")[0], 200)
        code, body, headers = self.get("/js/translations.js")
        self.assertEqual(code, 200)
        self.assertEqual(body, self.t.translations.read_bytes())
        self.assertIn("javascript", headers.get("Content-Type", ""))
        self.assertEqual(headers.get("Cache-Control"), "no-store")

    def test_ignored_paths_404_like_vercel(self):
        for p in ("/scripts/x.js", "/staging/secret.txt", "/README.md", "/.vercelignore", "/scripts/", "/staging",
                  "/scripts/editor/.local/editor.lock", "/.env.local", "/notes.md"):
            self.assertEqual(self.get(p)[0], 404, p)

    def test_letter_case_cannot_reach_an_ignored_file(self):
        # On Windows the file system would open these; the rules must still hide them.
        for p in ("/STAGING/secret.txt", "/Staging/Secret.txt", "/.ENV.local", "/.env.LOCAL", "/notes.MD", "/NOTES.md",
                  "/SCRIPTS/editor/.local/editor.lock", "/scripts/EDITOR/.LOCAL/editor.lock", "/README.MD"):
            code, body, _ = self.get(p)
            self.assertEqual(code, 404, p)
            self.assertNotIn(b"secret", body.lower(), p)
            self.assertNotIn(b"TOKEN", body, p)
        # a public file is still served whatever the case (the OS decides if it exists)
        self.assertEqual(self.get("/index.html")[0], 200)

    def test_short_names_cannot_reach_an_ignored_file(self):
        short = short_path(str(self.t.root / "staging"))
        if not short or os.path.basename(short).lower() == "staging":
            self.skipTest("8.3 short names not available here")
        p = "/" + os.path.basename(short) + "/secret.txt"
        code, body, _ = self.get(p)
        self.assertEqual(code, 404, p)
        self.assertNotIn(b"private", body)

    def test_foreign_host_or_origin_is_refused(self):
        for host in ("evil.example", f"127.0.0.1.nip.io:{self.port}", "127.0.0.1:5500", "localhost", ""):
            code, body = self.raw("/index.html", host=host)
            self.assertEqual(code, 403, host)
            self.assertNotIn(b"<title>t</title>", body)
        for origin in ("http://evil.example", "null", f"https://127.0.0.1:{self.port}", "http://localhost:5500"):
            self.assertEqual(self.raw("/index.html", origin=origin)[0], 403, origin)
        # the two allowed spellings, with and without a matching Origin
        self.assertEqual(self.raw("/index.html", host=f"localhost:{self.port}")[0], 200)
        self.assertEqual(self.raw("/index.html", host=f"127.0.0.1:{self.port}", origin=f"http://127.0.0.1:{self.port}")[0], 200)
        self.assertEqual(self.raw("/index.html", host=f"LOCALHOST:{self.port}")[0], 200)  # host names are case-insensitive

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
