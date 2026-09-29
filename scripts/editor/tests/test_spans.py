"""core.spans + core.emit: structural edits that touch only what they must, and
site_text key add / delete. Run on temp copies of the real data files."""

import difflib
import unittest

from _helpers import TempRepo
from core import emit, spans
from core.jsdata import Document, JsDataError
from core.site_text import SiteText, entry_prefix, family


def changed_lines(a: str, b: str) -> list[str]:
    return [l for l in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]


class SpanEditTests(unittest.TestCase):
    def setUp(self):
        self.t = TempRepo().__enter__()
        self.doc = Document.load(self.t.root / "js" / "projects-data.js")
        self.arr = self.doc.const("projectsData")

    def tearDown(self):
        self.t.__exit__(None, None, None)

    def test_no_edits_is_identity_and_python_view(self):
        self.assertIs(spans.apply(self.doc, []), self.doc)
        py = spans.to_python(self.arr.items[0])
        self.assertEqual(py["slug"], "pump-cylinder-failure")
        self.assertEqual(py["dates"], {"from": {"season": "spring", "year": 2026}})
        self.assertIsInstance(py["featured"], bool)

    def test_replace_scalar_string_array(self):
        e0 = self.arr.items[0]
        out = spans.apply(self.doc, [spans.replace_value(self.doc, e0.value("pinned"), "true")])
        self.assertEqual(changed_lines(self.doc.text, out.text), ["-    pinned: false,", "+    pinned: true,"])
        out = spans.apply(self.doc, [spans.replace_string(self.doc, e0.value("context"), "research")])
        self.assertEqual(changed_lines(self.doc.text, out.text), ['-    context: "coursework",', '+    context: "research",'])
        tags = spans.to_python(e0.value("tags")) + ["python"]
        out = spans.apply(self.doc, [spans.replace_value(self.doc, e0.value("tags"), emit.value(tags, "tags", "    "))])
        self.assertEqual(len(changed_lines(self.doc.text, out.text)), 2)
        self.assertIn('+    tags: ["solid-mechanics", "fabrication", "cad", "leadership", "python"],', changed_lines(self.doc.text, out.text))

    def test_delete_and_insert_props(self):
        velora = next(i for i in self.arr.items if spans.to_python(i)["slug"] == "velora")
        out = spans.apply(self.doc, [spans.delete_prop(self.doc, velora, "experience")])  # last prop: previous comma goes too
        self.assertEqual(changed_lines(self.doc.text, out.text), ['-    listing: "index",', '-    experience: "baker-hughes"', '+    listing: "index"'])
        out = spans.apply(self.doc, [spans.delete_prop(self.doc, velora, "slug")])  # first prop
        self.assertEqual(changed_lines(self.doc.text, out.text), ['-    slug: "velora",'])
        out = spans.apply(self.doc, [spans.insert_prop_after(self.doc, velora, "pinned", "homeLayout", '"stacked"')])
        self.assertEqual(changed_lines(self.doc.text, out.text), ['+    homeLayout: "stacked",'])
        out = spans.apply(self.doc, [spans.insert_props_after(self.doc, velora, "experience", [("homeLayout", '"stacked"'), ("gallery", "[]")])])
        self.assertEqual(changed_lines(self.doc.text, out.text), ['-    experience: "baker-hughes"', '+    experience: "baker-hughes",', '+    homeLayout: "stacked",', '+    gallery: []'])
        out = spans.apply(self.doc, [spans.insert_props_after(self.doc, velora, None, [("first", "1")])])
        self.assertEqual(changed_lines(self.doc.text, out.text), ["+    first: 1,"])
        # a property with a comment line above it: the comment stays
        eagle = self.arr.items[1]
        out = spans.apply(self.doc, [spans.delete_prop(self.doc, eagle, "homeLayout")])
        self.assertEqual(changed_lines(self.doc.text, out.text), ['-    homeLayout: "collage",'])
        self.assertIn("// Home collage = exactly these three cells", out.text)

    def test_delete_and_append_entries_keep_comments_between(self):
        n = len(self.arr.items)
        out = spans.apply(self.doc, [spans.delete_item(self.doc, self.arr, 3)])  # velora, right after the Index banner
        self.assertEqual(len(out.const("projectsData").items), n - 1)
        self.assertIn("/* ---- Index", out.text)
        self.assertNotIn('slug: "velora"', out.text)
        out = spans.apply(self.doc, [spans.delete_item(self.doc, self.arr, n - 1)])  # last entry
        self.assertEqual(len(out.const("projectsData").items), n - 1)
        self.assertTrue(out.text.rstrip().endswith("}\n];"))
        new = {"slug": "zz", "titleKey": "projZzTitle", "tags": [], "page": {"sections": [{"headingKey": "a", "bodyKey": "b"}], "photos": []}}
        out = spans.apply(self.doc, [spans.append_item(self.doc, self.arr, emit.entry(new, "  "))])
        self.assertEqual(len(out.const("projectsData").items), n + 1)
        self.assertIn('  },\n  {\n    slug: "zz",\n    titleKey: "projZzTitle",\n    tags: [],\n    page: {\n      sections: [\n        { headingKey: "a", bodyKey: "b" }\n      ],\n      photos: []\n    }\n  }\n];', out.text)

    def test_overlap_and_bad_output_are_refused(self):
        e0 = self.arr.items[0]
        a = spans.replace_value(self.doc, e0, "{}")
        b = spans.replace_value(self.doc, e0.value("pinned"), "true")
        with self.assertRaises(JsDataError):
            spans.apply(self.doc, [a, b])
        with self.assertRaises(JsDataError):
            spans.apply(self.doc, [spans.replace_value(self.doc, e0.value("pinned"), "`x`")])

    def test_emitter_reproduces_the_files_own_style(self):
        e0 = self.arr.items[0]
        page = e0.value("page")
        s, e = spans.span(self.doc, page)
        self.assertEqual(emit.value(spans.to_python(page), "page", "    "), self.doc.text[s:e])
        gallery = self.arr.items[1].value("gallery")
        s, e = spans.span(self.doc, gallery)
        self.assertEqual(emit.value(spans.to_python(gallery), "gallery", "    "), self.doc.text[s:e])
        dates = e0.value("dates")
        s, e = spans.span(self.doc, dates)
        self.assertEqual(emit.value(spans.to_python(dates), "dates", "    "), self.doc.text[s:e])
        exp = Document.load(self.t.root / "js" / "experience-data.js").const("experienceData").items[0]
        self.assertEqual(emit.inline(spans.to_python(exp.value("bulletKeys"))[:2]), '["expBakerHughesBullet1", "expBakerHughesBullet2"]')
        self.assertEqual(emit.scalar(True), "true")
        self.assertEqual(emit.scalar(None), "null")
        self.assertEqual(emit.scalar('a "q"'), '"a \\"q\\""')


class SiteTextKeyTests(unittest.TestCase):
    def test_families_and_prefixes(self):
        self.assertEqual(entry_prefix("projGViewFact4Label"), "projGView")
        self.assertEqual(entry_prefix("expBakerHughesBullet12"), "expBakerHughes")
        self.assertEqual(entry_prefix("tagRobotics"), "tagRobotics")
        self.assertIsNone(entry_prefix("projSearchBtn"))
        self.assertEqual(family("projSearchBtn"), "proj")
        self.assertIsNone(family("navAbout"))

    def test_add_and_remove_keys_round_trip(self):
        with TempRepo() as t:
            st = SiteText(t.root)
            out = st.render({}, adds={"projGViewFact4Label": {"en": "L", "es": "E"}, "projTestEditorTitle": {"en": "T", "es": "P"}, "projTestEditorDesc": {"en": "d", "es": "de"}, "tagRobotics": {"en": "Robotics", "es": "Robótica"}}, removes=["projLandmineClassificationSearch"])
            lines = changed_lines(st.raw.decode("utf-8"), out.decode("utf-8"))
            self.assertEqual(lines.count('+    projGViewFact4Label: "L",'), 1)
            self.assertEqual(lines.count('+    tagRobotics: "Robótica",'), 1)
            self.assertEqual(sum(1 for l in lines if l.startswith("-    projLandmineClassificationSearch")), 2)
            self.assertEqual(sum(1 for l in lines if l.startswith("+    projTestEditor")), 4)
            t.translations.write_bytes(out)
            st2 = SiteText(t.root)  # still lossless, keys in the right blocks
            i = st2.keys.index("projGViewFact4Label")
            self.assertTrue(st2.keys[i - 1].startswith("projGView"))
            self.assertEqual(st2.entries["tagRobotics"].section, st2.entries["tagLeadership"].section)
            self.assertNotIn("projLandmineClassificationSearch", st2.keys)
            j = st2.keys.index("projTestEditorTitle")
            self.assertEqual(st2.keys[j + 1], "projTestEditorDesc")
            self.assertEqual(st2.value("es", "projTestEditorTitle"), "P")
            # adding a key that exists is a no-op; removing one that doesn't is fine
            self.assertEqual(st2.render({}, adds={"navAbout": {"en": "x", "es": "y"}}, removes=["nope"]), st2.raw)


if __name__ == "__main__":
    unittest.main()
