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


class AboutTests(unittest.TestCase):
    def test_about_file_round_trip_edits_reorder_and_shown(self):
        from core.site import about

        with TempRepo() as t:
            f = about.AboutFile(t.root)
            self.assertEqual(f.render({}, []), f.raw)
            self.assertEqual([e["_list"] for e in f.entries()][:6], ["books"] * 5 + ["faq"])
            site = next(e for e in f.entries() if e["_list"] == "sites")
            edited = dict(site, descEN="Edited.")
            out = f.render({site["id"]: edited}, [])
            self.assertEqual(len(changed_lines(f.raw.decode("utf-8"), out.decode("utf-8"))), 2)  # one line out, one in
            out = f.render({"book-3": None}, [about.new_entry("faq", "faq-new", "Q?", "¿P?")])
            text = out.decode("utf-8")
            self.assertNotIn('"book-3"', text)
            self.assertIn('{ id: "faq-new", questionEN: "Q?", questionES: "¿P?", answerEN: "", answerES: "", visible: false }', text)
            out = f.render({}, [], {"books": ["book-5", "book-4", "book-3", "book-2", "book-1"]})
            f2 = about.AboutFile.__new__(about.AboutFile)
            (t.root / "js/about-data.js").write_bytes(out)
            f2 = about.AboutFile(t.root)
            self.assertEqual([e["id"] for e in f2.list_entries("books")], ["book-5", "book-4", "book-3", "book-2", "book-1"])
            self.assertEqual(f2.render({}, [], {"books": ["book-1", "book-2", "book-3", "book-4", "book-5"]}), f.raw)  # a reorder back is byte-identical
            html = (t.root / "about.html").read_text(encoding="utf-8")
            self.assertEqual(about.read_shown(html), {"about-reading": False, "about-faq": False, "about-sites": True})
            h2 = about.render_shown(html, {"about-faq": True, "about-sites": False})
            self.assertEqual(about.read_shown(h2), {"about-reading": False, "about-faq": True, "about-sites": False})
            self.assertEqual(len(changed_lines(html, h2)), 4)
            self.assertEqual(about.render_shown(h2, about.read_shown(html)), html)
            # the checks
            issues = about.check(f.entries(), t.root)
            self.assertEqual([i.level for i in issues if i.key == "about:atomic-rockets"], [])
            bad = [dict(site, url="#", visible=True), dict(about.new_entry("books", "b", "Some Title", "Some Title"), visible=True), dict(about.new_entry("sites", "s", "<b>x</b>", "TODO"), url="https://x.example", visible=False)]
            codes = sorted((i.level, i.code, i.key) for i in about.check(bad, t.root, shown={"about-reading": True, "about-sites": True}))
            self.assertEqual([c for c in sorted((i.level, i.code, i.key) for i in about.check(bad, t.root, shown={"about-reading": False, "about-sites": True})) if c[2] == "about:b" and c[0] == "error"], [])  # a hidden block: warnings only
            self.assertIn(("error", "url", "about:atomic-rockets"), codes)
            self.assertIn(("error", "missing-file", "about:b"), codes)  # no cover on a visible book
            self.assertIn(("error", "missing-key", "about:b"), codes)  # empty description
            self.assertIn(("warning", "same", "about:b"), codes)
            self.assertIn(("error", "html", "about:s"), codes)
            self.assertIn(("warning", "todo", "about:s"), codes)  # hidden entry

    def test_about_service_flow(self):
        with TempRepo() as t:
            state = make(t)
            svc = state.content
            self.assertIsNone(svc.read_only)
            before_data = (t.root / "js/about-data.js").read_bytes()
            before_page = (t.root / "about.html").read_bytes()
            svc.set_field("about", "atomic-rockets", ["descEN"], "Edited.")
            st = svc.state_json()
            self.assertEqual(st["about"]["lists"]["sites"][0]["descEN"], "Edited.")
            self.assertTrue(st["about"]["lists"]["sites"][0]["_draft"])
            e = svc.add_about_entry("sites", "new-site", "New", "Nuevo")
            self.assertEqual((e["_list"], e["visible"]), ("sites", False))
            with self.assertRaises(ValueError):
                svc.add_about_entry("sites", "new-site", "x", "y")
            with self.assertRaises(ValueError):
                svc.add_about_entry("nope", "x", "x", "y")
            self.assertTrue(svc.gate().ok())  # a hidden entry with no url is a warning
            svc.set_field("about", "new-site", ["visible"], True)
            self.assertFalse(svc.gate().ok())  # visible: the url and the empty description block
            svc.set_field("about", "new-site", ["url"], "https://example.com/")
            svc.set_field("about", "new-site", ["descEN"], "An example.")
            svc.set_field("about", "new-site", ["descES"], "Un ejemplo.")
            self.assertTrue(svc.gate().ok(), svc.gate().to_json())
            svc.set_about_order("books", ["book-2", "book-1", "book-3", "book-4", "book-5"])
            self.assertEqual([e["id"] for e in svc.live_entries("about") if e["_list"] == "books"][:2], ["book-2", "book-1"])
            with self.assertRaises(ValueError):
                svc.set_about_order("books", ["book-1"])
            svc.set_about_shown("about-faq", True)
            svc.set_about_shown("about-sites", True)  # already shown on disk → no draft
            self.assertEqual(svc.drafts["aboutShown"], {"about-faq": True})
            self.assertEqual(svc.about_shown()["about-faq"], True)
            r = svc.review()
            texts = [c["text"] for c in r["changes"]]
            self.assertTrue(any("About › Books: order changed" in x for x in texts), texts)
            self.assertTrue(any("About › FAQ: shown on the site" in x for x in texts), texts)
            self.assertTrue(any("About › new-site: added" in x for x in texts), texts)
            self.assertEqual({f["path"] for f in r["files"]}, {"js/about-data.js", "about.html"})
            self.assertIn("about.html", svc.preview_overrides())
            self.assertIn("js/about-data.js", svc.preview_overrides())
            self.assertGreaterEqual(svc.draft_count(), 4)
            s = svc.save()
            self.assertTrue(s["ok"], s)
            self.assertEqual(svc.draft_count(), 0)
            page = (t.root / "about.html").read_bytes()
            self.assertEqual(len(changed_lines(before_page.decode("utf-8"), page.decode("utf-8"))), 2)
            self.assertIn(b'<section class="section-faq" id="about-faq">', page)
            data = (t.root / "js/about-data.js").read_text(encoding="utf-8")
            self.assertIn('descEN: "Edited."', data)
            self.assertIn('id: "new-site", url: "https://example.com/"', data)
            self.assertLess(data.index('"book-2"'), data.index('"book-1"'))
            # delete, then everything back: the data file is byte-identical again
            svc.delete_entry("about", "new-site")
            svc.set_field("about", "atomic-rockets", ["descEN"], "Winchell Chung's encyclopedic guide to the physics and engineering of spaceflight, written for science-fiction authors who want to get it right.")
            svc.set_about_order("books", ["book-1", "book-2", "book-3", "book-4", "book-5"])
            svc.set_about_shown("about-faq", False)
            self.assertTrue(svc.save()["ok"])
            self.assertEqual((t.root / "js/about-data.js").read_bytes(), before_data)
            self.assertEqual((t.root / "about.html").read_bytes(), before_page)


class RenameTests(unittest.TestCase):
    def test_rename_project_cascades_previews_saves_and_renames_back(self):
        with TempRepo() as t:
            files = ("js/projects-data.js", "js/experience-data.js", "js/translations.js")
            before = {rel: (t.root / rel).read_bytes() for rel in files}
            shell_before = (t.root / "projects/pump-cylinder-failure.html").read_bytes()
            folder = t.root / "assets/images/projects/pump-cylinder-failure"
            folder_files = sorted(p.name for p in folder.iterdir())
            self.assertTrue(folder_files)
            st = make(t)
            c = st.content
            orig_title = st.site.value("en", "projPumpCylinderFailureTitle")
            for bad in ("Bad Slug", "g-view", "pump-cylinder-failure"):
                with self.assertRaises(ValueError, msg=bad):
                    c.rename_entry("projects", "pump-cylinder-failure", bad)
            with self.assertRaises(KeyError):
                c.rename_entry("projects", "nobody", "x")
            s = c.rename_entry("projects", "pump-cylinder-failure", "pump-failure")
            self.assertEqual((s["from"], s["to"]), ("pump-cylinder-failure", "pump-failure"))
            self.assertIn(["projPumpCylinderFailureTitle", "projPumpFailureTitle"], s["keys"])
            self.assertEqual(s["keysKept"], [])
            self.assertGreaterEqual(s["paths"], 8)  # image, thumbnail, 5 photos, subpageUrl …
            self.assertEqual(s["references"], ["role machine-shop › image link", "role machine-shop › image path"])  # the band image sits in the project's folder
            self.assertEqual(s["files"], [["projects/pump-cylinder-failure.html", "projects/pump-failure.html"], ["assets/images/projects/pump-cylinder-failure/", "assets/images/projects/pump-failure/"]])
            # the live entry, its keys and paths, the role's link
            e = c.entry("projects", "pump-failure")
            self.assertIsNone(c.entry("projects", "pump-cylinder-failure"))
            self.assertEqual((e["titleKey"], e["subpageUrl"], e["imageSrc"].split("/")[3]), ("projPumpFailureTitle", "/projects/pump-failure.html", "pump-failure"))
            self.assertTrue(all(ph["src"].startswith("assets/images/projects/pump-failure/") for ph in e["page"]["photos"]))
            self.assertEqual(c.entry("experience", "machine-shop")["imageLink"], "projects/pump-failure.html")
            self.assertTrue(c.entry("experience", "machine-shop")["imageSrc"].startswith("assets/images/projects/pump-failure/"))
            en, es = c.texts()
            self.assertEqual(en["projPumpFailureTitle"], st.site.value("en", "projPumpCylinderFailureTitle"))
            self.assertNotIn("projPumpCylinderFailureTitle", en)
            self.assertEqual(c.text("projPumpFailureTitle", "es"), st.site.value("es", "projPumpCylinderFailureTitle"))
            # editing text on the renamed entry lands on the disk key as a site draft, not as a new key
            c.set_text("projects", "pump-failure", "title", "en", "Pump failure")
            self.assertEqual(st.drafts.get("en.projPumpCylinderFailureTitle"), "Pump failure")
            self.assertEqual(c.drafts["newKeys"], {})
            # preview: the new sub-page and image paths are served before anything is saved
            ov = c.preview_overrides()
            self.assertIn(b'data-slug="pump-failure"', ov["projects/pump-failure.html"])
            self.assertEqual(ov[f"assets/images/projects/pump-failure/{folder_files[0]}"], folder / folder_files[0])
            self.assertTrue(c.gate().ok(), c.gate().to_json())  # the dev check sees the moved files
            rev = c.review()
            self.assertTrue(rev["changes"][0]["text"].startswith("Rename project “pump-cylinder-failure” → “pump-failure”"), rev["changes"][0])
            self.assertEqual([m["kind"] for m in rev["renames"]], ["file", "folder"])
            self.assertEqual(sorted(f["path"] for f in rev["files"]), sorted(files))
            self.assertEqual(c.state_json()["renamed"], {"projects": {"pump-failure": "pump-cylinder-failure"}})
            self.assertIn("pump-failure", [p["slug"] for p in c.state_json()["projects"] if p["_draft"]])
            res = c.save()
            self.assertTrue(res["ok"], res)
            self.assertFalse((t.root / "projects/pump-cylinder-failure.html").exists())
            self.assertIn(b'data-slug="pump-failure"', (t.root / "projects/pump-failure.html").read_bytes())
            self.assertFalse(folder.exists())
            self.assertEqual(sorted(p.name for p in (t.root / "assets/images/projects/pump-failure").iterdir()), folder_files)
            tr = t.translations.read_text(encoding="utf-8")
            self.assertIn("projPumpFailureTitle: ", tr)
            self.assertNotIn("projPumpCylinderFailure", tr)
            self.assertIn('imageLink: "projects/pump-failure.html"', (t.root / "js/experience-data.js").read_text(encoding="utf-8"))
            self.assertEqual(c.draft_count(), 0)
            bset = st.backups.get(res["backup"])
            self.assertIn("projects/pump-cylinder-failure.html", [f["path"] for f in bset.files])
            self.assertTrue(all(f"assets/images/projects/pump-cylinder-failure/{n}" in [f["path"] for f in bset.files] for n in folder_files))
            en2, es2 = st.site.as_dicts()
            self.assertEqual([x for x in datacheck.check(t.root, en2, es2, c.files["projects"].entries(), c.files["experience"].entries(), c.files["tags"].entries()) if x.level == "error"], [])
            # rename back: everything byte-identical (keys were renamed in place)
            c.rename_entry("projects", "pump-failure", "pump-cylinder-failure")
            c.set_text("projects", "pump-cylinder-failure", "title", "en", orig_title)
            self.assertTrue(c.save()["ok"])
            for rel in files:
                self.assertEqual((t.root / rel).read_bytes(), before[rel], rel)
            self.assertEqual((t.root / "projects/pump-cylinder-failure.html").read_bytes(), shell_before)
            self.assertEqual(sorted(p.name for p in folder.iterdir()), folder_files)

    def test_rename_role_and_undo_by_delete(self):
        with TempRepo() as t:
            st = make(t)
            c = st.content
            projects_of = [p["slug"] for p in c.live_entries("projects") if p.get("experience") == "baker-hughes"]
            self.assertTrue(projects_of)
            s = c.rename_entry("experience", "baker-hughes", "bh")
            self.assertEqual(c.entry("experience", "bh")["roleKey"], "expBhRole")
            self.assertTrue(all(c.entry("projects", p)["experience"] == "bh" for p in projects_of))
            self.assertEqual(c.entry("experience", "bh")["imageLink"], "projects.html?part=bh")
            self.assertEqual(len(s["references"]), len(projects_of) + 1)
            self.assertTrue(c.gate().ok(), c.gate().to_json())
            # a rename of a rename maps to the disk slug once
            c.rename_entry("experience", "bh", "baker")
            self.assertEqual(c.state_json()["renamed"], {"experience": {"baker": "baker-hughes"}})
            self.assertEqual(c.drafts["renames"]["keys"]["expBakerRole"], "expBakerHughesRole")
            self.assertNotIn("expBhRole", c.drafts["renames"]["keys"])
            # deleting the renamed entry undoes the rename and deletes the disk entry
            c.delete_entry("experience", "baker")
            self.assertIsNone(c.drafts["entries"]["experience"]["baker-hughes"])
            self.assertEqual(c.drafts["renames"]["entries"], {"experience": {}})
            self.assertEqual(c.drafts["renames"]["keys"], {})
            self.assertIn("expBakerHughesRole", c.drafts["removedKeys"])
            c.discard_drafts()
            self.assertEqual(c.draft_count(), 0)
            # a new (unsaved) entry renamed before its first save just renames its pending keys and shell
            c.add_entry("projects", "brand-new", "New", "Nuevo")
            c.create_shell("brand-new")
            c.rename_entry("projects", "brand-new", "newer")
            self.assertIn("projNewerTitle", c.drafts["newKeys"])
            self.assertNotIn("projBrandNewTitle", c.drafts["newKeys"])
            self.assertEqual(c.drafts["shells"], {"newer": "create"})
            self.assertEqual(c.drafts["renames"]["files"], {})
            self.assertEqual(c.entry("projects", "newer")["subpageUrl"], "/projects/newer.html")


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
