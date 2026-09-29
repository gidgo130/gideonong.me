"""Phase 2: data files, key naming, rendered order, the dev-check port and the
content service (add / edit / hide / delete, shells, tags, review, save)."""

import json
import unittest

from _helpers import REPO_ROOT, TempRepo
from app import EditorState
from core.site import datacheck, keys, order
from core.site.datafiles import DataFile
from test_spans import changed_lines


def make(t):
    return EditorState(t.root, t.local, "tok", 5510, 5501)


class DataFileTests(unittest.TestCase):
    def test_round_trip_and_minimal_diffs(self):
        with TempRepo() as t:
            for name in ("projects", "experience", "tags"):
                f = DataFile(t.root, name)
                self.assertEqual(f.render({}, []), f.raw, name)
                self.assertEqual(f.render({e[f.id_field]: dict(e) for e in f.entries()}, []), f.raw, name)  # identical drafts → no change
            f = DataFile(t.root, "projects")
            e = {x["slug"]: x for x in f.entries()}
            d = dict(e["velora"], pinned=True, tags=e["velora"]["tags"] + ["cad"])
            out = f.render({"velora": d}, [])
            self.assertEqual(sorted(changed_lines(f.raw.decode("utf-8"), out.decode("utf-8"))), sorted(["-    pinned: false,", "+    pinned: true,", '-    tags: ["python", "automation", "data-analysis"],', '+    tags: ["python", "automation", "data-analysis", "cad"],']))
            d = dict(e["velora"])
            d["homeLayout"] = "collage"
            d["gallery"] = [{"src": "a.jpg", "altKey": "k1"}, {"src": "b.jpg", "altKey": "k2"}]
            del d["longDescKey"]
            out = f.render({"velora": d}, [])
            lines = changed_lines(f.raw.decode("utf-8"), out.decode("utf-8"))
            self.assertIn('-    longDescKey: "",', lines)
            self.assertIn('+    homeLayout: "collage",', lines)
            self.assertIn('+      { src: "a.jpg", altKey: "k1" },', lines)
            DataFile.__init__  # the render re-parsed already; write and reload to be sure
            f.path.write_bytes(out)
            self.assertEqual(DataFile(t.root, "projects").entries()[[x["slug"] for x in f.entries()].index("velora")]["gallery"], d["gallery"])
            f = DataFile(t.root, "projects")
            out = f.render({"velora": None}, [{"slug": "zz", "titleKey": "projZzTitle", "listing": "hidden"}])
            ids = DataFile.__new__(DataFile)
            self.assertNotIn(b'slug: "velora"', out)
            self.assertTrue(out.rstrip().endswith(b'  {\n    slug: "zz",\n    titleKey: "projZzTitle",\n    listing: "hidden"\n  }\n];'))
            self.assertIn(b"/* ---- Index", out)


class KeysAndOrderTests(unittest.TestCase):
    def test_key_naming_and_paths(self):
        self.assertEqual(keys.key_for("projects", "g-view", "title"), "projGViewTitle")
        self.assertEqual(keys.key_for("projects", "pump-cylinder-failure", "page.facts.2.value"), "projPumpCylinderFailureFact2Value")
        self.assertEqual(keys.key_for("projects", "eagle-pathway", "gallery.3.alt"), "projEaglePathwayGallery3Alt")
        self.assertEqual(keys.key_for("experience", "baker-hughes", "bullets.5"), "expBakerHughesBullet5")
        self.assertEqual(keys.key_for("experience", "turc", "imageAlt"), "expTurcImageAlt")
        self.assertEqual(keys.key_for("tags", "machine-learning", "label"), "tagMachineLearning")
        self.assertEqual(keys.data_path("projects", "page.sections.3.body"), ["page", "sections", 2, "bodyKey"])
        self.assertEqual(keys.data_path("experience", "bullets.1"), ["bulletKeys", 0])
        with self.assertRaises(KeyError):
            keys.key_for("projects", "x", "bogus")
        self.assertIsNone(keys.valid_slug("pump-cylinder-failure"))
        self.assertIsNotNone(keys.valid_slug("Pump Cylinder"))
        self.assertIsNotNone(keys.valid_slug("a--b"))

    def test_referenced_keys(self):
        with TempRepo() as t:
            f = DataFile(t.root, "projects")
            eagle = next(e for e in f.entries() if e["slug"] == "eagle-pathway")
            refs = keys.referenced_keys("projects", eagle)
            self.assertIn("projEaglePathwayGallery3Alt", refs)  # also its thumbAltKey
            self.assertIn("projEaglePathwayCredit", refs)
            self.assertIn("projEaglePathwayFact6Value", refs)
            self.assertNotIn("", refs)

    def test_rendered_order_matches_the_site(self):
        with TempRepo() as t:
            p = DataFile(t.root, "projects").entries()
            self.assertEqual([e["slug"] for e in order.projects_featured(p)], ["pump-cylinder-failure", "eagle-pathway", "g-view"])
            idx = [e["slug"] for e in order.projects_index(p)]
            self.assertEqual(idx[0], "uk-crash-hotspots")  # pinned
            self.assertEqual(idx[1], "dynamics-pdf-unifier")  # newest sortDate
            disp = order.projects_display(p)
            self.assertEqual([e["_tier"] for e in disp[:4]], ["featured", "featured", "featured", "index"])
            self.assertEqual(len(disp), len(p))
            x = DataFile(t.root, "experience").entries()
            disp = order.experience_display(x)
            self.assertEqual(disp[0]["slug"], "baker-hughes")
            self.assertEqual([e["_tier"] for e in disp][-3:], ["hidden"] * 3)
            self.assertEqual(order.suggested_sort_date({"from": {"season": "summer", "year": 2026}}), "2026-08")
            self.assertEqual(order.suggested_sort_date({"from": {"month": 7, "year": 2022}}), "2022-07")
            self.assertEqual(order.suggested_sort_date({"from": {"season": "fall", "year": 2025}, "to": {"month": 3, "year": 2026}}), "2026-03")
            self.assertEqual(order.format_dates({"from": {"season": "spring", "year": 2026}, "to": "present"}, "en", {"dateSpring": "Spring", "datePresent": "present", "dateRange": "{from} – {to}", "dateSeasonYear": "{season} {year}"}, {}), "Spring 2026 – present")


class DataCheckTests(unittest.TestCase):
    def test_no_errors_on_the_real_files_and_each_seeded_problem_is_caught(self):
        with TempRepo() as t:
            st = make(t)
            c = st.content
            base = [i for i in c.baseline_issues() if i.level == "error"]
            self.assertEqual(base, [], [(i.key, i.message) for i in base])
            en, es = st.site.as_dicts()
            P, X, T = c.files["projects"].entries(), c.files["experience"].entries(), c.files["tags"].entries()

            def errs(**kw):
                pj = kw.get("projects", P)
                return sorted({(i.key, i.code) for i in datacheck.check(t.root, kw.get("en", en), kw.get("es", es), pj, kw.get("experience", X), kw.get("tags", T)) if i.level == "error"})

            bad = json.loads(json.dumps(P))
            bad[3]["tags"].append("nope")
            bad[3]["experience"] = "ghost"
            bad[3]["sortDate"] = "2026-13"
            bad[4]["listing"] = "nested"
            bad[5]["featured"] = True  # index → 4 featured
            bad[6]["dates"] = "Fall 2025"
            bad[7]["context"] = "hobby"
            bad[8]["homeLayout"] = "spiral"
            bad[9]["imageSrc"] = "assets/images/missing.jpg"
            bad[10]["slug"] = bad[11]["slug"]
            bad[12]["page"] = {"sections": [{"headingKey": "x"}]}  # mechanical-fuse: no sub-page, key missing
            got = errs(projects=bad)
            for expect in [("projects:velora", "unknown-tag"), ("projects:velora", "experience"), ("projects:velora", "sortDate"), ("projects:autoscan", "listing"),
                           ("projects:", "featured"), ("projects:dynamics-pdf-unifier", "empty-key"), ("projects:keplinger-heating", "dates"),
                           ("projects:music-notes-matlab", "context"), ("projects:gender-employment-cs", "homeLayout"),
                           ("projects:chilled-water-pipeline", "missing-file"), ("projects:diesel-dual-cycle", "duplicate"),
                           ("projects:mechanical-fuse", "page"), ("projects:mechanical-fuse", "missing-key")]:
                self.assertIn(expect, got)
            en2 = dict(en)
            en2["projGViewDesc"] = "TODO write"
            en2["projVeloraTitle"] = "<b>Velora</b>"
            del en2["projAutoscanAlt"]
            got = errs(en=en2)
            self.assertIn(("projects:g-view", "todo"), got)
            self.assertIn(("projects:velora", "html"), got)
            self.assertIn(("projects:autoscan", "missing-key"), got)
            X2 = json.loads(json.dumps(X))
            X2[0]["status"] = "current"  # machine-shop is current too
            X2[1]["layout"] = "banner"
            issues = datacheck.check(t.root, en, es, P, X2, T)
            self.assertIn(("experience:", "current"), {(i.key, i.code) for i in issues if i.level == "warning"})
            self.assertIn(("experience:machine-shop", "layout"), {(i.key, i.code) for i in issues if i.level == "error"})
            P2 = json.loads(json.dumps(P))
            P2[2]["experience"] = "esl-tutor"  # hidden role
            self.assertIn(("projects:g-view", "experience"), errs(projects=P2))
            # unused key → warning only
            en3, es3 = dict(en), dict(es)
            en3["projGhostTitle"] = es3["projGhostTitle"] = "x"
            self.assertIn(("keys:projGhostTitle", "unused-key"), {(i.key, i.code) for i in datacheck.check(t.root, en3, es3, P, X, T) if i.level == "warning"})


class ContentServiceTests(unittest.TestCase):
    def test_add_edit_hide_delete_round_trip(self):
        with TempRepo() as t:
            before = {rel: (t.root / rel).read_bytes() for rel in ("js/projects-data.js", "js/translations.js")}
            st = make(t)
            c = st.content
            self.assertIsNone(c.read_only)
            with self.assertRaises(ValueError):
                c.add_entry("projects", "Bad Slug")
            with self.assertRaises(ValueError):
                c.add_entry("projects", "g-view")
            c.add_entry("projects", "test-editor", "Test project", "Proyecto de prueba")
            for fld, en, es in (("desc", "A test.", "Una prueba."), ("search", "test", "prueba")):
                c.set_text("projects", "test-editor", fld, "en", en)
                c.set_text("projects", "test-editor", fld, "es", es)
            c.set_field("projects", "test-editor", ["tags"], ["python"])
            with self.assertRaises(ValueError):
                c.set_field("projects", "test-editor", ["slug"], "other")
            self.assertTrue(c.gate().ok(), c.gate().to_json())
            e = c.entry("projects", "test-editor")
            self.assertEqual((e["listing"], e["titleKey"], e["descKey"]), ("hidden", "projTestEditorTitle", "projTestEditorDesc"))
            self.assertEqual(c.text("projTestEditorTitle", "es"), "Proyecto de prueba")
            # hidden entries render on the preview: the overlay carries the data file, the keys and (after create) the shell
            self.assertEqual(set(c.preview_overrides()), {"js/projects-data.js", "js/translations.js"})
            self.assertEqual(c.create_shell("test-editor"), "/projects/test-editor.html")
            self.assertIn("projects/test-editor.html", c.preview_overrides())
            self.assertIn(b'data-slug="test-editor"', c.shell_html("test-editor"))
            self.assertIn(b"<title>Test project", c.shell_html("test-editor"))
            c.set_field("projects", "test-editor", ["listing"], "index")
            self.assertIn("test-editor", [p["slug"] for p in order.projects_index(c.live_entries("projects"))])
            rev = c.review()
            self.assertEqual([f["path"] for f in rev["files"]], ["js/projects-data.js", "js/translations.js"])
            self.assertEqual(rev["shells"], [{"slug": "test-editor", "action": "create", "path": "projects/test-editor.html"}])
            self.assertTrue(any("added" in x["text"] for x in rev["changes"]))
            res = c.save()
            self.assertTrue(res["ok"], res)
            self.assertTrue((t.root / "projects" / "test-editor.html").is_file())
            self.assertIn(b"projTestEditorSearch", t.translations.read_bytes())
            self.assertEqual(c.draft_count(), 0)
            self.assertEqual(st.drafts, {})
            # the site sees it: a fresh load lists it in the index
            st2 = make(t)
            self.assertIn("test-editor", [p["slug"] for p in st2.content.state_json()["projects"] if p["_tier"] == "index"])
            # edit existing text (goes through the site-text drafts) + a flag
            c = st2.content
            original_es = st2.site.value("es", "projGViewDesc")
            c.set_text("projects", "g-view", "desc", "es", "Nueva descripción")
            c.set_field("projects", "g-view", ["pinned"], True)
            self.assertEqual(st2.drafts, {"es.projGViewDesc": "Nueva descripción"})
            rev = c.review()
            self.assertEqual([f["path"] for f in rev["files"]], ["js/projects-data.js", "js/translations.js"])
            self.assertTrue(c.save()["ok"])
            self.assertIn('projGViewDesc: "Nueva descripción"'.encode("utf-8"), t.translations.read_bytes())
            # delete: keys nothing else uses go, the shell moves to the backup
            d = c.delete_entry("projects", "test-editor")
            self.assertEqual(d["removedKeys"], ["projTestEditorDesc", "projTestEditorSearch", "projTestEditorTitle"])
            self.assertEqual(d["shell"], "projects/test-editor.html")
            c.set_field("projects", "g-view", ["pinned"], False)
            c.set_text("projects", "g-view", "desc", "es", original_es)
            res = c.save()
            self.assertTrue(res["ok"], res)
            self.assertEqual((t.root / "js/projects-data.js").read_bytes(), before["js/projects-data.js"])
            self.assertEqual(t.translations.read_bytes(), before["js/translations.js"])
            self.assertFalse((t.root / "projects" / "test-editor.html").exists())
            self.assertIsNotNone(st2.backups.read_file(res["backup"], "projects/test-editor.html"))

    def test_experience_bullets_current_and_tags(self):
        with TempRepo() as t:
            st = make(t)
            c = st.content
            e = c.entry("experience", "baker-hughes")
            bk = e["bulletKeys"]
            c.set_field("experience", "baker-hughes", ["bulletKeys"], [bk[1], bk[0]] + bk[2:])
            rev = c.review()
            lines = [l for l in rev["files"][0]["diff"].splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
            self.assertEqual(sorted(lines), sorted(['+      "expBakerHughesBullet2",', '-      "expBakerHughesBullet2",']))
            c.set_text("experience", "baker-hughes", "bullets.6", "en", "New bullet")
            c.set_text("experience", "baker-hughes", "bullets.6", "es", "Nuevo punto")
            self.assertEqual(c.entry("experience", "baker-hughes")["bulletKeys"][-1], "expBakerHughesBullet6")
            self.assertEqual(c.drafts["newKeys"]["expBakerHughesBullet6"], {"en": "New bullet", "es": "Nuevo punto"})
            c.set_field("experience", "baker-hughes", ["status"], "current")
            self.assertIn("current", [i.code for i in c.draft_issues() if i.level == "warning"])
            c.set_field("experience", "machine-shop", ["status"], None)
            self.assertNotIn("current", [i.code for i in c.draft_issues()])
            self.assertTrue(c.save()["ok"])
            self.assertIn(b'expBakerHughesBullet6: "Nuevo punto"', t.translations.read_bytes())
            # tags: add, use, refuse delete while used, delete when free
            c.add_tag("robotics", "Robotics", "Robótica")
            with self.assertRaises(ValueError):
                c.add_tag("robotics", "x", "y")
            c.set_field("projects", "g-view", ["tags"], ["python", "robotics"])
            self.assertTrue(c.gate().ok(), c.gate().to_json())
            with self.assertRaises(ValueError):
                c.delete_tag("robotics")
            self.assertTrue(c.save()["ok"])
            self.assertIn(b'{ id: "robotics", key: "tagRobotics" }', (t.root / "js/tags-data.js").read_bytes())
            c.set_field("projects", "g-view", ["tags"], ["python"])
            self.assertEqual(c.delete_tag("robotics")["removedKeys"], ["tagRobotics"])
            self.assertTrue(c.save()["ok"])
            self.assertNotIn(b"robotics", (t.root / "js/tags-data.js").read_bytes())
            self.assertNotIn(b"tagRobotics", t.translations.read_bytes())

    def test_gate_blocks_and_conflicts_refuse(self):
        with TempRepo() as t:
            st = make(t)
            c = st.content
            c.set_field("projects", "velora", ["tags"], ["nope"])
            res = c.save()
            self.assertEqual(res["error"], "blocked")
            self.assertEqual([i["code"] for i in res["gate"]["blocking"]], ["unknown-tag"])
            c.set_field("projects", "velora", ["tags"], ["python"])
            (t.root / "js/projects-data.js").write_bytes((t.root / "js/projects-data.js").read_bytes() + b"\n// touched\n")
            self.assertEqual(c.save()["error"], "changed-on-disk")
            c.load()
            self.assertEqual(c.draft_count(), 1)  # the draft survived the reload
            self.assertTrue(c.save()["ok"])
            # autosave offered on the next start
            c.set_field("projects", "velora", ["pinned"], True)
            st2 = make(t)
            self.assertIsNotNone(st2.content.state_json()["autosave"])
            self.assertEqual(st2.content.restore_autosave()["applied"], 1)
            self.assertTrue(st2.content.entry("projects", "velora")["pinned"])


if __name__ == "__main__":
    unittest.main()
