import unittest

from _helpers import TempRepo
from core import validate
from core.site_text import SiteText, hidden_key_prefixes, parity_status, slug_camel


class SiteTextTests(unittest.TestCase):
    def test_loads_real_file_with_sections_and_keys(self):
        with TempRepo() as t:
            st = SiteText(t.root)
            self.assertGreater(len(st.keys), 200)
            self.assertGreater(len(st.sections), 10)
            self.assertEqual(sum(len(s.keys) for s in st.sections), len(st.keys))
            self.assertIn("navAbout", st.keys)
            first = st.sections[0]
            self.assertIn("nav", first.title.lower())
            self.assertEqual(first.keys[:3], ["navProjects", "navExperience", "navAbout"])
            # decorative dashes are trimmed from titles
            self.assertFalse(any(s.title.startswith("-") for s in st.sections))

    def test_trailing_comment_becomes_a_note_not_a_section(self):
        with TempRepo() as t:
            st = SiteText(t.root)
            e = st.entries["projPartClear"]
            self.assertIn("aria-label", e.en_note)
            # the key after it is in the same section as the key before it
            i = st.keys.index("projPartClear")
            self.assertEqual(st.entries[st.keys[i - 1]].section, st.entries[st.keys[i + 1]].section)

    def test_render_no_edits_is_identical_and_one_edit_is_one_line(self):
        with TempRepo() as t:
            st = SiteText(t.root)
            self.assertEqual(st.render({}), st.raw)
            self.assertEqual(st.render({"es.navAbout": st.value("es", "navAbout")}), st.raw)  # same value → no edit
            new = st.render({"es.navAbout": "Sobre mí!"})
            diff = [a for a, b in zip(st.raw.split(b"\n"), new.split(b"\n")) if a != b]
            self.assertEqual(len(diff), 1)
            self.assertEqual(st.render({"es.doesNotExist": "x", "fr.navAbout": "y"}), st.raw)

    def test_parity_status(self):
        self.assertEqual(parity_status("k", "a", None), "en-only")
        self.assertEqual(parity_status("k", None, "a"), "es-only")
        self.assertEqual(parity_status("k", "TODO x", "y"), "todo")
        self.assertEqual(parity_status("k", "Hello", "Hello"), "same")
        self.assertEqual(parity_status("tagPython", "Python", "Python"), "both")
        self.assertEqual(parity_status("dateSeasonYear", "{season} {year}", "{season} {year}"), "both")
        self.assertEqual(parity_status("k", "Hello", "Hola"), "both")

    def test_hidden_prefixes_from_experience_data(self):
        with TempRepo() as t:
            p = hidden_key_prefixes(t.root)
            self.assertIn("expEslTutor", p)
            self.assertNotIn("expBakerHughes", p)
        self.assertEqual(slug_camel("senior-patrol-leader"), "SeniorPatrolLeader")

    def test_disk_changed(self):
        with TempRepo() as t:
            st = SiteText(t.root)
            self.assertFalse(st.disk_changed())
            t.translations.write_bytes(st.raw + b"\r\n// touched\r\n")
            self.assertTrue(st.disk_changed())


class ValidateTests(unittest.TestCase):
    def test_real_file_has_no_errors_today(self):
        with TempRepo() as t:
            st = SiteText(t.root)
            en, es = st.as_dicts()
            issues = validate.validate(en, es, hidden_key_prefixes(t.root))
            errors = [i for i in issues if i.level == "error"]
            self.assertEqual(errors, [], [i.message + " " + i.key for i in errors])
            self.assertTrue(any(i.code == "todo-hidden" for i in issues))

    def test_rules(self):
        en = {"a": "Hi", "b": "TODO later", "c": "<b>bold</b>", "d": "We leveraged synergy", "e": "Same", "only": "x", "h": "TODO"}
        es = {"a": "Hola", "b": "Luego", "c": "negrita", "d": "Aprovechamos", "e": "Same", "esonly": "y", "h": "z"}
        issues = validate.validate(en, es, hidden_prefixes=["h"])
        codes = {(i.code, i.key, i.lang) for i in issues}
        self.assertIn(("todo", "b", "en"), codes)
        self.assertIn(("html", "c", "en"), codes)
        self.assertIn(("voice", "d", "en"), codes)
        self.assertIn(("same", "e", ""), codes)
        self.assertIn(("missing-key", "only", "es"), codes)
        self.assertIn(("missing-key", "esonly", "en"), codes)
        self.assertIn(("todo-hidden", "h", "en"), codes)
        self.assertNotIn(("todo", "h", "en"), codes)
        levels = {i.code: i.level for i in issues}
        self.assertEqual(levels["missing-key"], "error")
        self.assertEqual(levels["todo"], "error")
        self.assertEqual(levels["html"], "error")
        self.assertEqual(levels["same"], "warning")
        self.assertEqual(levels["voice"], "warning")
        self.assertEqual(levels["todo-hidden"], "warning")

    def test_blocking_only_for_introduced_or_touched(self):
        en = {"a": "Hi", "lonely": "x", "b": "fine"}
        es = {"a": "Hola", "b": "bien"}
        baseline = validate.validate(en, es)
        # draft touches only key b and introduces no new error → pre-existing missing-key not blocking
        en2 = dict(en, b="fine!")
        gate = validate.blocking(baseline, validate.validate(en2, es), touched_keys={"b"})
        self.assertTrue(gate.ok())
        self.assertEqual([i.key for i in gate.preexisting], ["lonely"])
        # draft introduces a TODO → blocking
        gate = validate.blocking(baseline, validate.validate(dict(en, b="TODO"), es), touched_keys={"b"})
        self.assertFalse(gate.ok())
        self.assertEqual(gate.blocking[0].code, "todo")
        # draft touches the key that already has the error → blocking
        gate = validate.blocking(baseline, validate.validate(dict(en, lonely="y"), es), touched_keys={"lonely"})
        self.assertFalse(gate.ok())

    def test_identical_allow_list(self):
        self.assertTrue(validate.identical_allowed("tagCad", "CAD"))
        self.assertTrue(validate.identical_allowed("footerContact", "a@b.edu"))
        self.assertTrue(validate.identical_allowed("k", "2026"))
        self.assertTrue(validate.identical_allowed("expFooOrg", "Baker Hughes Company"))
        self.assertFalse(validate.identical_allowed("k", "Welcome to my site"))


if __name__ == "__main__":
    unittest.main()
