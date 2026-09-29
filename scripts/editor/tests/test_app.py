"""Save / backup / conflict / security tests through the Flask test client."""

import json
import unittest

from _helpers import TempRepo
from app import EditorState, create_app

TOKEN = "test-token-123"
PORT = 5510
HOST = f"127.0.0.1:{PORT}"


def make(t, token=TOKEN):
    state = EditorState(t.root, t.local, token, PORT, 5501)
    app = create_app(state)
    app.testing = True
    return state, app.test_client()


def hdr(**extra):
    h = {"Host": HOST, "X-Editor-Token": TOKEN}
    h.update(extra)
    return h


class SaveTests(unittest.TestCase):
    def test_no_edit_save_leaves_file_identical(self):
        with TempRepo() as t:
            before = t.translations.read_bytes()
            state, c = make(t)
            r = c.post("/api/save", headers=hdr(), json={})
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.get_json()["noop"])
            self.assertEqual(t.translations.read_bytes(), before)
            self.assertEqual(state.backups.list(), [])

    def test_one_edit_gives_one_line_diff_and_saves_exactly_that(self):
        with TempRepo() as t:
            before = t.translations.read_bytes()
            state, c = make(t)
            r = c.post("/api/draft", headers=hdr(), json={"lang": "es", "key": "navAbout", "value": "Acerca de mí"})
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.get_json()["gate"]["ok"])
            rev = c.get("/api/review", headers=hdr()).get_json()
            self.assertEqual(len(rev["changes"]), 1)
            self.assertEqual(rev["diffStats"], {"added": 1, "removed": 1})
            self.assertIn('-    navAbout: "Sobre mí",', rev["diff"])
            self.assertIn('+    navAbout: "Acerca de mí",', rev["diff"])
            r = c.post("/api/save", headers=hdr(), json={})
            self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
            after = t.translations.read_bytes()
            self.assertNotEqual(after, before)
            a, b = before.split(b"\n"), after.split(b"\n")
            self.assertEqual(len(a), len(b))
            self.assertEqual(sum(1 for x, y in zip(a, b) if x != y), 1)
            # backup holds the previous bytes, drafts are gone, autosave file removed
            sets = state.backups.list()
            self.assertEqual(len(sets), 1)
            self.assertEqual(state.backups.read_file(sets[0].id, "js/translations.js"), before)
            self.assertEqual(state.drafts, {})
            self.assertFalse(state.autosave_path.exists())
            # no temp files left beside the target
            self.assertEqual([p.name for p in t.translations.parent.glob("*.tmp-*")], [])

    def test_changed_on_disk_is_refused(self):
        with TempRepo() as t:
            state, c = make(t)
            c.post("/api/draft", headers=hdr(), json={"lang": "es", "key": "navAbout", "value": "X"})
            t.translations.write_bytes(t.translations.read_bytes().replace(b'navProjects: "Proyectos"', b'navProjects: "Proyectos!"'))
            r = c.post("/api/save", headers=hdr(), json={})
            self.assertEqual(r.status_code, 409)
            self.assertEqual(r.get_json()["error"], "changed-on-disk")
            self.assertIn(b'navProjects: "Proyectos!"', t.translations.read_bytes())
            self.assertNotIn(b'navAbout: "X"', t.translations.read_bytes())
            # reload keeps the draft, then the save goes through
            c.post("/api/reload", headers=hdr(), json={})
            self.assertEqual(state.drafts, {"es.navAbout": "X"})
            r = c.post("/api/save", headers=hdr(), json={})
            self.assertEqual(r.status_code, 200)
            self.assertIn(b'navAbout: "X"', t.translations.read_bytes())

    def test_unsupported_syntax_makes_file_read_only_with_line(self):
        with TempRepo() as t:
            data = t.translations.read_bytes().replace('navAbout: "Sobre mí",'.encode("utf-8"), "navAbout: `Sobre mí`,".encode("utf-8"))
            t.translations.write_bytes(data)
            state, c = make(t)
            self.assertTrue(state.read_only)
            line = data.split(b"navAbout: `")[0].count(b"\n") + 1
            self.assertIn(f"line {line}:", state.load_error)
            self.assertIn("template literal", state.load_error)
            r = c.post("/api/draft", headers=hdr(), json={"lang": "es", "key": "navAbout", "value": "X"})
            self.assertEqual(r.status_code, 409)
            r = c.post("/api/save", headers=hdr(), json={})
            self.assertEqual(r.status_code, 409)
            self.assertEqual(t.translations.read_bytes(), data)

    def test_blocking_errors_refuse_save_but_preexisting_do_not(self):
        with TempRepo() as t:
            # create a pre-existing error: drop an ES key entirely
            data = t.translations.read_bytes().replace(b'    navProjects: "Proyectos",\n', b"")
            t.translations.write_bytes(data)
            state, c = make(t)
            st = c.get("/api/state", headers=hdr()).get_json()
            self.assertEqual([i["key"] for i in st["gate"]["preexisting"]], ["navProjects"])
            self.assertEqual(st["file"]["entries"]["navProjects"]["status"], "en-only")
            # untouched pre-existing error does not block a save elsewhere
            c.post("/api/draft", headers=hdr(), json={"lang": "es", "key": "navAbout", "value": "Acerca"})
            self.assertEqual(c.post("/api/save", headers=hdr(), json={}).status_code, 200)
            # an introduced error blocks
            c.post("/api/draft", headers=hdr(), json={"lang": "en", "key": "navAbout", "value": "<b>About</b>"})
            r = c.post("/api/save", headers=hdr(), json={})
            self.assertEqual(r.status_code, 409)
            self.assertEqual(r.get_json()["gate"]["blocking"][0]["code"], "html")

    def test_restore_backs_up_current_then_writes_old_bytes(self):
        with TempRepo() as t:
            before = t.translations.read_bytes()
            state, c = make(t)
            c.post("/api/draft", headers=hdr(), json={"lang": "es", "key": "navAbout", "value": "Y"})
            c.post("/api/save", headers=hdr(), json={})
            sets = c.get("/api/backups", headers=hdr()).get_json()["sets"]
            self.assertEqual(len(sets), 1)
            r = c.post("/api/restore", headers=hdr(), json={"set": sets[0]["id"]})
            self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
            self.assertEqual(t.translations.read_bytes(), before)
            self.assertEqual(len(state.backups.list()), 2)
            self.assertEqual(c.post("/api/restore", headers=hdr(), json={"set": "../../etc"}).status_code, 404)
            # a backup file path cannot wander into a sibling set or out of the backups folder
            newer, older = [s.id for s in state.backups.list()]
            self.assertIsNotNone(state.backups.read_file(older, "js/translations.js"))
            self.assertIsNone(state.backups.read_file(older, f"../{newer}/js/translations.js"))
            self.assertIsNone(state.backups.read_file(older, "../../../js/translations.js"))
            self.assertIsNone(state.backups.read_file(older, str(t.translations)))
            r = c.get(f"/api/backups/{older}/file?path=../{newer}/js/translations.js", headers=hdr())
            self.assertEqual(r.status_code, 404)

    def test_write_failure_returns_409_and_leaves_file_and_drafts_alone(self):
        import app as app_mod
        import core.backups as backups_mod

        def boom(path, data):
            raise PermissionError(13, "The process cannot access the file because it is being used by another process")

        with TempRepo() as t:
            before = t.translations.read_bytes()
            state, c = make(t)
            c.post("/api/draft", headers=hdr(), json={"lang": "es", "key": "navAbout", "value": "X"})
            orig = app_mod.atomic_write
            app_mod.atomic_write = boom
            try:
                r = c.post("/api/save", headers=hdr(), json={})
            finally:
                app_mod.atomic_write = orig
            self.assertEqual(r.status_code, 409)
            j = r.get_json()
            self.assertEqual(j["error"], "write-failed")
            self.assertIn("open in another program", j["message"])
            self.assertEqual(t.translations.read_bytes(), before)
            self.assertEqual(state.drafts, {"es.navAbout": "X"})
            self.assertTrue(state.autosave_path.is_file())
            self.assertEqual([p.name for p in t.translations.parent.glob("*.tmp-*")], [])
            # the same save works once the file is free
            self.assertEqual(c.post("/api/save", headers=hdr(), json={}).status_code, 200)
            after = t.translations.read_bytes()
            self.assertIn(b'navAbout: "X"', after)
            # restore: same failure, same answer, file untouched
            set_id = state.backups.list()[0].id
            orig = backups_mod.atomic_write
            backups_mod.atomic_write = boom
            try:
                r = c.post("/api/restore", headers=hdr(), json={"set": set_id})
            finally:
                backups_mod.atomic_write = orig
            self.assertEqual(r.status_code, 409)
            self.assertIn("open in another program", r.get_json()["error"])
            self.assertEqual(t.translations.read_bytes(), after)

    def test_autosave_written_and_offered_on_next_start(self):
        with TempRepo() as t:
            state, c = make(t)
            c.post("/api/draft", headers=hdr(), json={"lang": "es", "key": "navAbout", "value": "Borrador"})
            self.assertTrue(state.autosave_path.is_file())
            j = json.loads(state.autosave_path.read_text(encoding="utf-8"))
            self.assertEqual(j["edits"], {"es.navAbout": "Borrador"})
            # "next launch"
            state2, c2 = make(t)
            st = c2.get("/api/state", headers=hdr()).get_json()
            self.assertEqual(st["autosave"]["count"], 1)
            self.assertEqual(st["drafts"], {})
            r = c2.post("/api/autosave/restore", headers=hdr(), json={}).get_json()
            self.assertEqual(r["applied"], 1)
            self.assertEqual(state2.drafts, {"es.navAbout": "Borrador"})
            # preview overlay serves the draft
            self.assertIn('navAbout: "Borrador"'.encode("utf-8"), state2.preview_overrides()["js/translations.js"])


class WindowEndpointTests(unittest.TestCase):
    def test_focus_reports_whether_a_window_exists(self):
        with TempRepo() as t:
            state, c = make(t)
            r = c.post("/api/focus", headers=hdr(), json={})
            self.assertEqual((r.status_code, r.get_json()["focused"]), (200, False))
            calls = []
            state.focus_callback = lambda: calls.append(1) or True
            r = c.post("/api/focus", headers=hdr(), json={})
            self.assertEqual((r.status_code, r.get_json()["focused"]), (200, True))
            self.assertEqual(calls, [1])

    def test_open_preview_uses_the_opener_with_the_preview_url(self):
        with TempRepo() as t:
            state, c = make(t)
            opened = []
            state.opener = opened.append
            r = c.post("/api/open-preview", headers=hdr(), json={})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(opened, ["http://127.0.0.1:5501/"])


class SecurityTests(unittest.TestCase):
    def test_missing_or_wrong_token_is_refused_on_state_changing_endpoints(self):
        with TempRepo() as t:
            before = t.translations.read_bytes()
            state, c = make(t)
            state.opener = lambda url: (_ for _ in ()).throw(AssertionError("opener must not run"))
            state.focus_callback = lambda: (_ for _ in ()).throw(AssertionError("focus must not run"))
            state.cv.opener = lambda p: (_ for _ in ()).throw(AssertionError("open-out must not run"))
            state.transcript.opener = state.cv.opener
            for path in ("/api/draft", "/api/save", "/api/restore", "/api/drafts/discard", "/api/heartbeat", "/api/focus", "/api/open-preview",
                         "/api/cv/check", "/api/cv/export", "/api/cv/publish", "/api/cv/open-out",
                         "/api/transcript/draft", "/api/transcript/title", "/api/transcript/save", "/api/transcript/parse", "/api/transcript/build",
                         "/api/transcript/publish", "/api/transcript/open-folder", "/api/transcript/drafts/discard", "/api/transcript/reload",
                         "/api/content/field", "/api/content/text", "/api/content/add", "/api/content/delete", "/api/content/shell",
                         "/api/content/tag", "/api/content/tag/delete", "/api/content/save", "/api/content/drafts/discard", "/api/content/reload",
                         "/api/content/images/delete"):
                r = c.post(path, headers={"Host": HOST}, json={"lang": "es", "key": "navAbout", "value": "X", "set": "x"})
                self.assertEqual(r.status_code, 403, path)
                r = c.post(path, headers={"Host": HOST, "X-Editor-Token": "wrong"}, json={"lang": "es", "key": "navAbout", "value": "X"})
                self.assertEqual(r.status_code, 403, path)
            # a token in the query string is not enough for a POST
            r = c.post("/api/draft?token=" + TOKEN, headers={"Host": HOST}, json={"lang": "es", "key": "navAbout", "value": "X"})
            self.assertEqual(r.status_code, 403)
            self.assertEqual(state.drafts, {})
            self.assertEqual(t.translations.read_bytes(), before)
            # reads need it too; ping does not
            self.assertEqual(c.get("/api/state", headers={"Host": HOST}).status_code, 403)
            self.assertEqual(c.get("/api/cv/state", headers={"Host": HOST}).status_code, 403)
            self.assertEqual(c.get("/api/cv/job", headers={"Host": HOST}).status_code, 403)
            self.assertEqual(c.get("/api/cv/publish-plan", headers={"Host": HOST}).status_code, 403)
            self.assertEqual(c.get("/cv", headers={"Host": HOST}).status_code, 200)
            for path in ("/api/transcript/state", "/api/transcript/review", "/api/transcript/job", "/api/transcript/publish-plan",
                         "/api/content/state", "/api/content/review"):
                self.assertEqual(c.get(path, headers={"Host": HOST}).status_code, 403, path)
            self.assertEqual(c.get("/transcript", headers={"Host": HOST}).status_code, 200)
            self.assertEqual(c.get("/content", headers={"Host": HOST}).status_code, 200)
            self.assertEqual(c.get("/api/ping", headers={"Host": HOST}).status_code, 200)
            self.assertEqual(c.get("/", headers={"Host": HOST}).status_code, 200)

    def test_bad_host_is_refused(self):
        with TempRepo() as t:
            state, c = make(t)
            for host in ("evil.example", "127.0.0.1:5500", "localhost", "127.0.0.1.nip.io:5510"):
                r = c.post("/api/draft", headers=hdr(Host=host), json={"lang": "es", "key": "navAbout", "value": "X"})
                self.assertEqual(r.status_code, 403, host)
                self.assertEqual(c.get("/api/ping", headers={"Host": host}).status_code, 403, host)
            self.assertEqual(c.get("/api/ping", headers={"Host": f"localhost:{PORT}"}).status_code, 200)
            self.assertEqual(state.drafts, {})

    def test_foreign_origin_is_refused(self):
        with TempRepo() as t:
            state, c = make(t)
            for origin in ("http://evil.example", "http://localhost:5500", "null", "https://127.0.0.1:5510"):
                r = c.post("/api/draft", headers=hdr(Origin=origin), json={"lang": "es", "key": "navAbout", "value": "X"})
                self.assertEqual(r.status_code, 403, origin)
            self.assertEqual(state.drafts, {})
            r = c.post("/api/draft", headers=hdr(Origin=f"http://127.0.0.1:{PORT}"), json={"lang": "es", "key": "navAbout", "value": "X"})
            self.assertEqual(r.status_code, 200)
            self.assertNotIn("Access-Control-Allow-Origin", r.headers)


if __name__ == "__main__":
    unittest.main()
