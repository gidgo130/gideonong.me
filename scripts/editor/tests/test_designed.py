"""The Designed CV (core/cv/designed/): content.json version 2 and its migration, the Designed
variant's operations (checklist, per-output text, section placement, sort), what an "Import
masters" carries over, that no master path sees the variant, the page render, the export
through a real headless browser (skipped where neither Edge nor Chrome is installed) with
its checks, the stale-age flag, and that nothing can publish it.

Everything runs on synthetic masters with made-up text (test_cvtext.make_master) in a temp
folder; the real masters are only read, on a temp copy, when they are on this machine."""

import copy
import hashlib
import json
import shutil
import unittest
from datetime import date
from pathlib import Path

from _helpers import EDITOR_DIR, REPO_ROOT, TempRepo
from app import EditorState, create_app
from core.backups import Backups
from core.cv import content as C
from core.cv import cvcheck, importer, masters, renderer, scans
from core.cv import export as word_export
from core.cv.designed import checks, export, model, render, schema
from core.cv.designed.service import OUT_DIR, PERSONAL_FILE, DesignedService, pdf_name
from core.cv.textservice import CONTENT_FILE, CvTextService
from core.jobs import JobRunner
from test_cvtext import MASTERS_PRESENT, import_six, make_master, mini_content

D = C.DESIGNED
BROWSER = export.find_browser()
BIRTH = date(2001, 2, 3)  # made up
TODAY = date(2021, 6, 15)  # → age 20
STAGING_ICONS = REPO_ROOT / "staging" / "cv-design" / "icons"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def master_hashes(root: Path) -> dict:
    return {m.file: sha(root / masters.MASTERS_DIR / m.file) for m in masters.MASTERS}


def designed_service(t: TempRepo, svc: CvTextService, today: date = TODAY, photo: bool = True) -> DesignedService:
    settings: dict = {}
    (t.root / "staging/editor-private").mkdir(parents=True, exist_ok=True)
    (t.root / PERSONAL_FILE).write_text(json.dumps({"birth_date": BIRTH.isoformat()}), encoding="utf-8")
    if photo:
        from PIL import Image

        p = t.root / render.PHOTO_REL
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (600, 750), (120, 140, 160)).save(p, "JPEG")
    ds = DesignedService(t.root, svc, JobRunner(), t.local, settings=lambda: settings, update_settings=lambda **kw: settings.update(kw) or settings, today=lambda: today)
    ds.set_view(browser="chrome")  # Chrome first where both are installed (Edge as the fallback)
    return ds


def fill(ds: DesignedService, contact: bool = True) -> None:
    """A small Designed CV on the synthetic set: the education entry, the engineer entry with
    its two bullets, a profile, a GPA line and a row in each sidebar group. `contact` also gives
    the SHARED contact line a phone and a LinkedIn address (a change the masters would take).
    (import_six writes the same English words into the EN and the ES masters.)"""
    svc = ds.cvtext
    if contact:
        svc.set_text(["header", "contact", "en"], "test@example.com | +1 (918) 555-0100 | example.com | linkedin.com/in/test-person")
        svc.set_text(["header", "contact", "es"], "test@example.com | +1 (918) 555-0100 | example.com | linkedin.com/in/test-person")
    for iid in ("test-university", "engineer"):
        ds.op({"op": "tick", "id": iid, "on": True})
    for cid in ("test-university-1", "engineer-1", "engineer-2"):
        ds.op({"op": "tick", "id": cid, "on": True})
    for lang, text in (("en", "A made-up profile line."), ("es", "Una línea de perfil inventada.")):
        ds.op({"op": "single-text", "key": "profile", "lang": lang, "value": text})
        ds.op({"op": "single-text", "key": "gpa", "lang": lang, "value": "GPA: 3.9 / 4.0" if lang == "en" else "Promedio (GPA): 3.9 / 4.0"})
    ds.op({"op": "single-include", "key": "profile", "on": True})
    ds.op({"op": "single-include", "key": "gpa", "on": True})
    rows = {
        "languages": ({"en": "English", "es": "Inglés"}, {"en": "Fluent", "es": "Fluido"}),
        "skills": ({"en": "Tools", "es": "Herramientas"}, {"en": "Hammer, wrench", "es": "Martillo, llave"}),
        "certs": ({"en": "Made-up Certificate", "es": "Certificado inventado"}, {"en": "Some Board", "es": "Alguna Junta"}),
        "honors": ({"en": "Made-up Prize", "es": "Premio inventado"}, {"en": "2020", "es": "2020"}),
    }
    for group, (a, b) in rows.items():
        rid = ds.op({"op": "row-add", "group": group})["id"]
        fa, fb = schema.GROUPS[group]
        for lang in ("en", "es"):
            ds.op({"op": "row-set", "group": group, "id": rid, "field": fa, "lang": lang, "value": a[lang]})
            ds.op({"op": "row-set", "group": group, "id": rid, "field": fb, "lang": lang, "value": b[lang]})


def wait(ds: DesignedService, timeout: float = 240) -> dict:
    import time

    end = time.time() + timeout
    while ds.runner.busy() and time.time() < end:
        time.sleep(0.2)
    j = ds.job_json()
    assert j and not j["running"], "the export job did not finish"
    return j


# ----------------------------------------------------------------- schema / migration


class SchemaTests(unittest.TestCase):
    def test_migrate_adds_only_and_strip_gives_the_file_back(self):
        v1 = mini_content()
        v2 = schema.migrate(v1)
        self.assertEqual(v1, mini_content())  # the input is not modified
        self.assertEqual(v2["version"], 2)
        self.assertEqual(list(v2), ["version", "masters", "header", "sections", "items", "design", "hashes"])
        self.assertEqual(v2["masters"], v1["masters"])  # no "designed" master
        self.assertEqual(v2["items"], v1["items"])  # include flags untouched: a missing key means "not in it"
        self.assertEqual(v2["sections"], v1["sections"])
        self.assertIsNone(v2["header"]["title"][D])  # no Professional title line to start from
        self.assertEqual(v2["design"]["main"], [{"section": "education"}, {"section": "experience"}])
        self.assertEqual(v2["design"]["copies"], {D: {}})
        self.assertEqual(schema.strip_designed(v2), v1)
        self.assertIs(schema.migrate(v2), v2)  # already current: untouched
        with_title = mini_content()
        with_title["header"]["title"]["professional"] = {"en": "Student", "es": "Estudiante"}
        self.assertEqual(schema.migrate(with_title)["header"]["title"][D], {"en": "Student", "es": "Estudiante"})

    def test_only_the_editor_migrates_the_file_and_backs_it_up_first(self):
        with TempRepo() as t:
            p = t.root / CONTENT_FILE
            p.parent.mkdir(parents=True)
            old = json.dumps(mini_content(), indent=2, ensure_ascii=False).encode("utf-8")
            p.write_bytes(old)
            backups = Backups(t.root, t.local / "backups")
            reader = CvTextService(t.root, backups, t.local)  # a test, a script: opening is not a write
            self.assertEqual((p.read_bytes(), reader.migrated, backups.list()), (old, None, []))
            self.assertEqual(reader.state()["variants"][-1], {"id": D, "label": "Designed"})
            svc = CvTextService(t.root, backups, t.local, migrate=True)  # what app.EditorState does
            self.assertEqual((svc.migrated["from"], svc.migrated["to"]), (1, 2))
            self.assertEqual(backups.read_file(svc.migrated["backup"], CONTENT_FILE), old)
            now = json.loads(p.read_bytes().decode("utf-8"))
            self.assertEqual(now["version"], 2)
            self.assertEqual(json.dumps(schema.strip_designed(now), indent=2, ensure_ascii=False).encode("utf-8"), old)
            self.assertIsNone(svc.doc.read_only)
            self.assertEqual(svc.draft_count(), 0)
            again = CvTextService(t.root, backups, t.local, migrate=True)
            self.assertIsNone(again.migrated)
            self.assertEqual(len(backups.list()), 1)

    def test_an_autosaved_version_1_draft_is_migrated_with_the_file(self):
        with TempRepo() as t:
            p = t.root / CONTENT_FILE
            p.parent.mkdir(parents=True)
            p.write_bytes(json.dumps(mini_content(), indent=2, ensure_ascii=False).encode("utf-8"))
            draft = mini_content()
            draft["items"]["job"]["role"]["en"] = "Senior Engineer"
            (t.local / "drafts").mkdir()
            (t.local / "drafts" / "cvtext.json").write_text(json.dumps({"saved": "2026-01-01T00:00:00", "baseSha256": "x", "draft": draft}), encoding="utf-8")
            svc = CvTextService(t.root, Backups(t.root, t.local / "backups"), t.local, migrate=True)
            self.assertEqual(svc.restore_autosave()["applied"], 1)
            self.assertEqual(svc.obj()["items"]["job"]["role"]["en"], "Senior Engineer")
            self.assertEqual(svc.obj()["version"], 2)


# ----------------------------------------------------------------- operations


class OperationTests(unittest.TestCase):
    def test_checklist_keeps_places_and_the_cv_text_tab_shows_the_same_flags(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            self.assertEqual(svc.obj()["version"], 2)
            ds.op({"op": "tick", "id": "engineer", "on": True})
            ds.op({"op": "tick", "id": "engineer-1", "on": True})
            ds.op({"op": "tick", "id": "engineer-2", "on": True})
            c = svc.obj()
            eng = c["items"]["engineer"]
            self.assertEqual((eng["include"][D], eng["order"][D]), (True, ["engineer-1", "engineer-2"]))
            # unticking a bullet, then the entry: both keep their place, the other bullet keeps its tick
            ds.op({"op": "tick", "id": "engineer-1", "on": False})
            ds.op({"op": "tick", "id": "engineer", "on": False})
            eng = svc.obj()["items"]["engineer"]
            self.assertEqual(eng["order"][D], ["engineer-1", "engineer-2"])
            self.assertEqual((eng["include"][D], eng["children"]["engineer-1"]["include"][D], eng["children"]["engineer-2"]["include"][D]), (False, False, True))
            sec = next(s for s in svc.obj()["sections"] if s["id"] == "experience")
            self.assertEqual(sec["order"][D], ["engineer"])
            # the CV text tab reads the same flags: its Designed list shows ticked items only
            lst = next(s for s in svc.state()["listing"][D] if s["id"] == "experience")
            self.assertEqual((lst["items"], lst["others"]), ([], ["engineer"]))
            svc.include("engineer", D, True, current=D)  # ticked in the CV text tab …
            row = ds.state()["checklist"]["main"][1]["rows"][0]
            self.assertEqual((row["id"], row["on"], [k["on"] for k in row["children"]]), ("engineer", True, [False, True]))  # … shows in this tab
            lst = next(s for s in svc.state()["listing"][D] if s["id"] == "experience")
            self.assertEqual((lst["items"], lst["variants"]), (["engineer"], ["full", "professional", "resume", D]))
            # the other three documents never moved
            self.assertEqual(schema.strip_designed(svc.obj()), schema.strip_designed(svc.doc.obj))
            self.assertEqual([p for p in svc.master_plans(svc.obj()) if p["changed"] or p["added"] or p["removed"]], [])
            # taking it off the checklist altogether
            ds.op({"op": "remove", "id": "engineer"})
            self.assertFalse(C.on_shelf(svc.obj(), "engineer"))
            self.assertNotIn(D, svc.obj()["items"]["engineer"]["include"])
            self.assertEqual(svc.draft_count(), 0)  # back to the file exactly
            with self.assertRaises(ValueError):
                ds.op({"op": "tick", "id": "engineer-1", "on": True})  # its entry is not on the list

    def test_text_for_this_output_only_and_reset(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            for i in ("engineer", "engineer-1", "engineer-2"):
                ds.op({"op": "tick", "id": i, "on": True})
            before = copy.deepcopy(svc.obj())
            masters_before = master_hashes(t.root)
            # a bullet: the first edit separates it for this output
            nid = ds.op({"op": "text", "id": "engineer-1", "field": "text", "lang": "es", "value": "Hice algo, en corto."})["id"]
            self.assertEqual(nid, "engineer-1-designed")
            c = svc.obj()
            eng = c["items"]["engineer"]
            self.assertEqual(eng["children"][nid]["text"], {"en": "Did a thing.", "es": "Hice algo, en corto."})
            self.assertEqual(eng["children"][nid]["include"], {"full": False, "professional": False, "resume": False, D: True})
            self.assertEqual(eng["children"]["engineer-1"]["text"]["es"], "Did a thing.")  # the shared wording
            self.assertNotIn(D, eng["children"]["engineer-1"]["include"])
            self.assertEqual(eng["order"][D], [nid, "engineer-2"])
            self.assertEqual(C.copy_records(c)[nid], {"of": "engineer-1", "base": {"text": {"en": "Did a thing.", "es": "Did a thing."}}})
            st = model.status(c, nid)
            self.assertEqual((st["copy"], st["edited"], st["sharedChanged"]), (True, True, False))
            self.assertEqual(ds.op({"op": "text", "id": nid, "field": "text", "lang": "en", "value": "Did a thing, briefly."})["id"], nid)  # already a copy
            # Full, Professional, Résumé and the six masters do not know
            self.assertEqual(schema.strip_designed(svc.obj()), schema.strip_designed(before))
            self.assertEqual([p for p in svc.master_plans(svc.obj()) if p["changed"] or p["added"] or p["removed"]], [])
            for v in importer.VARIANTS:
                self.assertEqual(C.listing(svc.obj(), v), C.listing(before, v))
            lines = [l["text"] for l in svc.review()["changes"]]
            self.assertTrue(any("duplicated into Designed" in l for l in lines), lines)
            # the page prints the copy
            html_es = render.render(svc.obj(), render.Options("c", "blue", "es"), age=20, base_href="x/", photo_src="")
            self.assertIn("Hice algo, en corto.", html_es)
            self.assertNotIn("Did a thing.", html_es)
            # the shared text changes afterwards: the copy says so, with the shared text beside it
            svc.set_text(["items", "engineer", "children", "engineer-1", "text", "es"], "Hice algo nuevo.")
            st = model.status(svc.obj(), nid)
            self.assertEqual((st["sharedChanged"], st["sharedText"]["text"]["es"], st["base"]["text"]["es"]), (True, "Hice algo nuevo.", "Did a thing."))
            ds.op({"op": "keep", "id": nid})
            self.assertFalse(model.status(svc.obj(), nid)["sharedChanged"])
            svc.set_text(["items", "engineer", "children", "engineer-1", "text", "es"], "Did a thing.")
            # reset: the shared wording is back and the copy is folded into the shared bullet
            self.assertEqual(ds.op({"op": "reset", "id": nid})["id"], "engineer-1")
            self.assertEqual(svc.obj(), before)
            self.assertEqual(master_hashes(t.root), masters_before)

    def test_an_entry_line_edit_copies_the_entry_with_a_base_per_bullet(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            for i in ("engineer", "engineer-1", "engineer-2"):
                ds.op({"op": "tick", "id": i, "on": True})
            ds.op({"op": "tick", "id": "engineer-2", "on": False})  # an unticked bullet travels with the copy
            before = copy.deepcopy(svc.obj())
            eid = ds.op({"op": "text", "id": "engineer", "field": "role", "lang": "es", "value": "Ingeniero de Pruebas"})["id"]
            self.assertEqual(eid, "engineer-designed")
            c = svc.obj()
            e = c["items"][eid]
            self.assertEqual((e["role"], e["org"], e["include"][D]), ({"en": "Engineer", "es": "Ingeniero de Pruebas"}, c["items"]["engineer"]["org"], True))
            self.assertEqual(c["items"]["engineer"]["role"]["es"], "Engineer")  # the shared wording
            self.assertEqual(e["order"], {D: [f"{eid}-1", f"{eid}-2"]})
            self.assertEqual([e["children"][k]["include"][D] for k in e["order"][D]], [True, False])
            rec = C.copy_records(c)
            self.assertEqual(rec[eid]["of"], "engineer")
            self.assertEqual(rec[eid]["base"]["role"], {"en": "Engineer", "es": "Engineer"})
            self.assertEqual({k: rec[k]["of"] for k in e["order"][D]}, {f"{eid}-1": "engineer-1", f"{eid}-2": "engineer-2"})  # a base per bullet
            self.assertEqual(rec[f"{eid}-1"]["base"], {"text": {"en": "Did a thing.", "es": "Did a thing."}})
            self.assertFalse(C.on_shelf(c, "engineer"))
            sec = next(s for s in c["sections"] if s["id"] == "experience")
            self.assertEqual(sec["order"][D], [eid])
            self.assertEqual(schema.strip_designed(c), schema.strip_designed(before))
            # a bullet of the copy edited, then reset on its own: bullet by bullet
            ds.op({"op": "text", "id": f"{eid}-1", "field": "text", "lang": "en", "value": "Did it."})
            self.assertTrue(model.status(svc.obj(), f"{eid}-1")["edited"])
            self.assertFalse(model.status(svc.obj(), f"{eid}-2")["edited"])
            self.assertEqual(ds.op({"op": "reset", "id": f"{eid}-1"})["id"], f"{eid}-1")  # the entry line still differs: it stays a copy
            self.assertEqual(svc.obj()["items"][eid]["children"][f"{eid}-1"]["text"]["en"], "Did a thing.")
            # resetting the entry line too folds the whole copy back
            self.assertEqual(ds.op({"op": "reset", "id": eid})["id"], "engineer")
            self.assertEqual(svc.obj(), before)
            # resetting the entry line keeps what the bullets say for this output: an edited bullet
            # and one written for this output go back under the shared entry, still Designed-only
            eid = ds.op({"op": "text", "id": "engineer", "field": "role", "lang": "es", "value": "Otro"})["id"]
            ds.op({"op": "text", "id": f"{eid}-1", "field": "text", "lang": "en", "value": "Did it."})
            own = ds.op({"op": "add-bullet", "id": eid})["id"]
            self.assertEqual(ds.op({"op": "reset", "id": eid})["id"], "engineer")
            eng = svc.obj()["items"]["engineer"]
            self.assertNotIn(eid, svc.obj()["items"])
            self.assertEqual((eng["role"]["es"], eng["include"][D]), ("Engineer", True))
            self.assertEqual(eng["order"][D], ["engineer-1-designed", "engineer-2", own])
            self.assertEqual(eng["children"]["engineer-1-designed"]["text"]["en"], "Did it.")
            self.assertEqual(C.copy_records(svc.obj()), {"engineer-1-designed": {"of": "engineer-1", "base": {"text": {"en": "Did a thing.", "es": "Did a thing."}}}})
            self.assertEqual((eng["children"]["engineer-2"]["include"][D], eng["children"][own]["include"]), (False, {"full": False, "professional": False, "resume": False, D: True}))
            self.assertEqual(schema.strip_designed(svc.obj()), schema.strip_designed(before))
            with self.assertRaises(ValueError):
                ds.op({"op": "reset", "id": own})  # not a copy of anything
            self.assertEqual(ds.op({"op": "reset", "id": "engineer-1-designed"})["id"], "engineer-1")  # bullet by bullet

    def test_section_placement_is_for_this_output_only(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            ds.op({"op": "tick", "id": "engineer", "on": True})
            before = copy.deepcopy(svc.obj())
            ds.op({"op": "place", "id": "engineer", "section": "education"})
            c = svc.obj()
            by = {s["id"]: s for s in c["sections"]}
            self.assertEqual((by["education"]["order"][D], by["experience"]["order"].get(D)), (["engineer"], None))
            for v in importer.VARIANTS:
                self.assertEqual([s["order"].get(v) for s in c["sections"]], [s["order"].get(v) for s in before["sections"]])
                self.assertEqual(C.section_of(c, "engineer", v)["id"], "experience")
            self.assertEqual(C.section_of(c, "engineer", D)["id"], "education")
            self.assertEqual(C.section_of(c, "engineer")["id"], "experience")  # a master never follows the Designed placement
            self.assertEqual([p for p in svc.master_plans(c) if p["changed"] or p["added"] or p["removed"]], [])
            html_en = render.render(c, render.Options("e", "bronze", "en"), age=20, base_href="x/", photo_src="")
            self.assertLess(html_en.index('data-sec="education"'), html_en.index('data-id="engineer"'))
            self.assertNotIn('data-sec="experience"', html_en)  # nothing ticked there any more
            with self.assertRaises(ValueError):
                ds.op({"op": "place", "id": "engineer", "section": "nowhere"})
            # ↑ ↓ work in the section it sits in for this output
            ds.op({"op": "tick", "id": "test-university", "on": True})
            ds.op({"op": "move", "id": "engineer", "delta": 1})
            self.assertEqual({s["id"]: s for s in svc.obj()["sections"]}["education"]["order"][D], ["test-university", "engineer"])

    def test_sort_newest_first(self):
        today = date(2026, 11, 25)
        self.assertEqual(model.date_key("Spring 2026", today), (2026, 5))
        self.assertEqual(model.date_key("Primavera 2026 – presente", today), (2026, 11))
        self.assertEqual(model.date_key("Fall 2025", today), (2025, 12))
        self.assertEqual(model.date_key("Otoño 2024", today), (2024, 12))
        self.assertEqual(model.date_key("Summer 2025", today), (2025, 8))
        self.assertEqual(model.date_key("2023–2024", today), (2024, 12))
        self.assertEqual(model.date_key("2023, 2024", today), (2024, 12))
        self.assertEqual(model.date_key("October 2025", today), (2025, 10))
        self.assertEqual(model.date_key("Spring 2020 – Summer 2021", today), (2021, 8))
        self.assertIsNone(model.date_key("someday", today))
        self.assertIsNone(model.date_key("", today))
        # the D16 shape: seven projects in the order they were first listed → newest first, ties as they were
        c = schema.migrate(mini_content())
        terms = [("pump", "Spring 2026"), ("beam", "Fall 2025"), ("hot", "Spring 2025"), ("pipe", "Fall 2025"), ("kep", "Spring 2026"), ("bike", "Spring 2025"), ("ard", "Fall 2024"), ("odd", "sometime")]
        c["sections"].append({"id": "projects", "heading": {"en": "Projects", "es": "Proyectos"}, "order": {D: [n for n, _ in terms]}})
        c["design"]["main"].append({"section": "projects"})
        for n, d in terms:
            c["items"][n] = {"kind": "entry", "role": {"en": n, "es": n}, "org": {"en": "", "es": ""}, "date": {"en": d, "es": d}, "sep": " · ", "include": {"full": True, D: n in ("pump", "beam", "hot")}, "order": {D: []}, "children": {}}
        c["sections"][-1]["order"][D].insert(2, "odd")
        c["sections"][-1]["order"][D].pop()
        undated = model.sort_newest(c, "projects", today)
        self.assertEqual(c["sections"][-1]["order"][D], ["pump", "kep", "odd", "beam", "pipe", "hot", "bike", "ard"])  # "odd" did not move
        self.assertEqual(undated, ["odd"])
        # "present" is today: a current role sorts above one that ended last summer
        c["items"]["ard"]["date"] = {"en": "Fall 2024 – present", "es": "Otoño 2024 – presente"}
        model.sort_newest(c, "projects", today)
        self.assertEqual(c["sections"][-1]["order"][D][0], "ard")
        # honors by their years
        for name, years in (("Eagle", "2023"), ("Merit", "2024"), ("Prize", "2026"), ("Silver", "2023, 2024")):
            rid = model.row_add(c, "honors")
            model.row_set(c, "honors", rid, "name", "en", name)
            model.row_set(c, "honors", rid, "years", "en", years)
        self.assertEqual(model.rows_sort(c, "honors", today), [])
        self.assertEqual([r["name"]["en"] for r in c["design"]["honors"]], ["Prize", "Merit", "Silver", "Eagle"])

    def test_age(self):
        self.assertEqual(model.age_on(BIRTH, date(2021, 2, 2)), 19)
        self.assertEqual(model.age_on(BIRTH, date(2021, 2, 3)), 20)  # on the birthday
        self.assertEqual(model.age_on(BIRTH, date(2022, 2, 2)), 20)
        self.assertEqual(model.next_birthday(BIRTH, date(2021, 6, 15)), date(2022, 2, 3))
        self.assertEqual((render.age_text("es", 20), render.age_text("en", 20)), ("Edad: 20 años", "Age: 20"))

    def test_validation_and_the_apply_gate(self):
        with TempRepo() as t:
            svc = import_six(t, gpa=lambda: "3.50")
            ds = designed_service(t, svc)
            fill(ds)
            self.assertEqual([i for i in ds.state()["issues"] if i["level"] == "error"], [])
            self.assertIn(("gpa", "design.gpa"), [(i["code"], i["key"]) for i in ds.state()["issues"]])  # 3.9 printed, 3.50 on the transcript
            svc.save()
            ds.op({"op": "single-text", "key": "profile", "lang": "es", "value": ""})
            own = ds.op({"op": "add-bullet", "id": "engineer"})["id"]  # empty in both languages
            ds.op({"op": "single-text", "key": "gpa", "lang": "en", "value": "TODO"})
            codes = {(i["code"], i["key"], i["lang"]) for i in ds.state()["issues"] if i["level"] == "error"}
            self.assertEqual(codes, {("empty", "design.profile", "es"), ("todo", "design.gpa", "en")})
            # the new bullet has no text yet: it is left out of both pages, which is a warning
            self.assertEqual({(i["code"], i["lang"]) for i in ds.state()["issues"] if i["key"] == own}, {("left-out", "en"), ("left-out", "es")})
            self.assertFalse(svc.gate().ok())  # the same save gate as the CV text tab
            self.assertEqual(svc.save()["error"], "blocked")
            # … but none of it can reach a master, so it does not block an Apply
            self.assertTrue(all(cvcheck.designed_only_key(svc.obj(), k) for _, k, _ in codes))
            self.assertEqual([b for b in svc.apply_blockers(svc.obj()) if "error(s) in the content" in b], [])
            self.assertFalse(cvcheck.designed_only_key(svc.obj(), "engineer-1"))
            # blocklist and voice words apply to the Designed text too
            issues = cvcheck.check(schema.migrate(mini_content()) | {"design": dict(schema.empty_design(mini_content()), profile={"include": True, "text": {"en": "Leveraged SECRETWORD.", "es": "Usé SECRETWORD."}})}, terms=[scans.Term("secretword", "test", 1)])
            got = {(i.level, i.code, i.lang) for i in issues if i.key == "design.profile"}
            self.assertEqual(got, {("error", "blocklist", "en"), ("error", "blocklist", "es"), ("warning", "voice", "en")})

    def test_no_master_path_sees_the_variant(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            fill(ds, contact=False)  # Designed-only changes: nothing a master would take
            ds.op({"op": "text", "id": "engineer-1", "field": "text", "lang": "en", "value": "Did a thing, briefly."})
            ds.op({"op": "title", "lang": "en", "value": "Tester"})
            before = master_hashes(t.root)
            c = svc.obj()
            self.assertNotIn(D, c["masters"])
            self.assertEqual(set(svc.fits(c).get("engineer", {})), set(importer.VARIANTS))  # the fit meter is the masters'
            with self.assertRaises(renderer.RenderError):
                renderer.wanted_ids(c, D)
            for m in masters.MASTERS:
                self.assertNotIn("engineer-1-designed", renderer.wanted_ids(c, m.variant))
                r = renderer.render_master(c, svc.slots[m.file], t.root / masters.MASTERS_DIR / m.file)
                self.assertFalse(r.changed, m.file)
            self.assertEqual(svc.drift()["blocked"], [])
            r = svc.apply()  # Designed-only drafts: content.json is saved, no master is rewritten
            self.assertTrue(r["ok"], r)
            self.assertEqual(r["written"], [])
            self.assertEqual(master_hashes(t.root), before)
            self.assertTrue(svc.apply()["noop"])
            self.assertEqual(svc.obj()["items"]["engineer"]["children"]["engineer-1-designed"]["text"]["en"], "Did a thing, briefly.")
            self.assertEqual(svc.draft_count(), 0)


# ----------------------------------------------------------------- Import masters keeps the Designed CV


class ImportCarryOverTests(unittest.TestCase):
    def test_import_masters_keeps_flags_orders_copies_and_the_design_block(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            fill(ds, contact=False)
            copy_id = ds.op({"op": "text", "id": "engineer-2", "field": "text", "lang": "es", "value": "Otra cosa, en corto."})["id"]
            own = ds.op({"op": "add-bullet", "id": "engineer"})["id"]
            for lang in ("en", "es"):
                ds.op({"op": "text", "id": own, "field": "text", "lang": lang, "value": "Only here." if lang == "en" else "Solo aquí."})
            ds.op({"op": "tick", "id": "engineer-1", "on": False})
            ds.op({"op": "move", "id": own, "delta": -1})
            ds.op({"op": "move", "id": own, "delta": -1})
            ds.op({"op": "place", "id": "test-university", "section": "experience"})
            ds.op({"op": "title", "lang": "en", "value": "Tester"})
            ds.op({"op": "title", "lang": "es", "value": "Probador"})
            ds.op({"op": "heading", "key": "main:education", "lang": "es", "value": "Estudios"})
            self.assertTrue(svc.save()["ok"])
            was = copy.deepcopy(svc.obj())
            r = svc.run_import()
            self.assertTrue(r["ok"], r)
            self.assertEqual((r["report"]["designed"]["dropped"], r["report"]["designed"]["moved"]), ([], []))
            self.assertEqual(r["report"]["designed"]["kept"], 6)
            now = svc.obj()
            self.assertEqual(now["version"], 2)
            self.assertEqual(now["design"], was["design"])  # the block, the copy records, the rows, the headings
            self.assertEqual(now["header"]["title"][D], {"en": "Tester", "es": "Probador"})
            self.assertEqual([s["order"].get(D) for s in now["sections"]], [s["order"].get(D) for s in was["sections"]])
            self.assertEqual(now["items"]["engineer"], was["items"]["engineer"])  # flags, order, the copy and the Designed-only bullet
            self.assertEqual(now["items"]["engineer"]["order"][D], [own, "engineer-1", copy_id])
            self.assertEqual(C.copy_records(now)[copy_id]["of"], "engineer-2")
            self.assertEqual(schema.strip_designed(now), schema.strip_designed(was))
            self.assertEqual(ds.state()["checklist"], model.checklist(was, TODAY))

    def test_what_cannot_be_re_attached_is_reported(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            fill(ds, contact=False)
            copy_id = ds.op({"op": "text", "id": "engineer-1", "field": "text", "lang": "es", "value": "Hice algo, en corto."})["id"]
            self.assertTrue(svc.save()["ok"])
            # in Word: the second bullet is reworded and the first one deleted, in every master
            from docx import Document

            for m in masters.MASTERS:
                p = t.root / masters.MASTERS_DIR / m.file
                doc = Document(str(p))
                for para in list(doc.paragraphs):
                    if para.text == "Did a thing.":
                        para._element.getparent().remove(para._element)
                    elif para.text == "Did another.":
                        for run in para.runs:
                            run.text = ""
                        para.runs[0].text = "Did something else."
                doc.save(str(p))
            r = svc.run_import()
            self.assertTrue(r["ok"], r)
            rep = r["report"]["designed"]
            self.assertEqual(len(rep["dropped"]), 1, rep)  # the ticked shared bullet whose words are gone
            self.assertIn("Did another.", rep["dropped"][0])
            self.assertEqual(len(rep["moved"]), 1, rep)  # the copy stays, without its shared original
            self.assertIn("Did a thing.", rep["moved"][0])
            now = svc.obj()
            eng = now["items"]["engineer"]
            self.assertIn(copy_id, eng["children"])
            self.assertEqual(eng["children"][copy_id]["text"]["es"], "Hice algo, en corto.")
            self.assertEqual(eng["order"][D], [copy_id])
            self.assertNotIn(copy_id, C.copy_records(now))
            self.assertEqual(model.status(now, copy_id), {"shared": False, "copy": False})
            self.assertEqual(now["design"]["profile"]["text"]["en"], "A made-up profile line.")


# ----------------------------------------------------------------- the page


class RenderTests(unittest.TestCase):
    def _content(self, t):
        svc = import_six(t)
        ds = designed_service(t, svc)
        fill(ds)
        return svc, ds

    def test_page_holds_what_is_ticked_and_nothing_else(self):
        with TempRepo() as t:
            svc, ds = self._content(t)
            ds.op({"op": "tick", "id": "engineer-2", "on": False})
            ds.op({"op": "text", "id": "engineer-1", "field": "text", "lang": "en", "value": "Cut <b>costs</b> & time."})
            c = svc.obj()
            for layout in render.LAYOUTS:
                for lang in render.LANGS:
                    h = render.render(c, render.Options(layout, "blue", lang), age=ds.age(), base_href="/static/designed/", photo_src="/designed/photo", key="7")
                    self.assertIn(f'<div class="pg l-{layout}" id="pg">', h)
                    self.assertIn('class="pal-blue"', h)
                    self.assertIn(f'<html lang="{lang}"', h)
                    self.assertIn("Edad: 20 años" if lang == "es" else "Age: 20", h)
                    self.assertIn("Test Person", h)
                    self.assertIn("+1 (918) 555-0100", h)  # read from the shared contact line
                    self.assertIn("linkedin.com/in/test-person", h)
                    self.assertNotIn("design.contact", json.dumps(c["design"]))  # the phone is stored once, in the header
                    self.assertIn("Promedio (GPA): 3.9 / 4.0" if lang == "es" else "GPA: 3.9 / 4.0", h)
                    self.assertIn("Una línea de perfil inventada." if lang == "es" else "A made-up profile line.", h)
                    self.assertNotIn("Did another.", h)
                    self.assertNotIn(BIRTH.isoformat(), h)
                    self.assertNotIn("{{", h)
                    self.assertIn('href="/static/designed/designed.css"', h)
                    self.assertIn('src="/designed/photo"', h)
                    self.assertEqual(h.count('class="ic"'), 5)  # age, phone, mail, site, LinkedIn — no location line
            en = render.render(c, render.Options("c", "blue", "en"), age=20, base_href="x/", photo_src="")
            self.assertIn("Cut &lt;b&gt;costs&lt;/b&gt; &amp; time.", en)  # text is escaped
            self.assertNotIn('class="photo"', en)
            # C puts the sidebar first, E the main column; the same blocks in both
            c_html = render.render(c, render.Options("c", "blue", "es"), age=20, base_href="x/", photo_src="p")
            e_html = render.render(c, render.Options("e", "blue", "es"), age=20, base_href="x/", photo_src="p")
            self.assertLess(c_html.index('<aside class="side">'), c_html.index('<main class="main">'))
            self.assertLess(e_html.index('<main class="main">'), e_html.index('<aside class="side">'))
            for key in ("profile", "education", "experience", "contact", "languages", "skills", "certs", "honors"):
                self.assertIn(f'data-sec="{key}"', c_html)
                self.assertIn(f'data-sec="{key}"', e_html)
            self.assertLess(c_html.index('data-sec="profile"'), c_html.index('data-sec="education"'))
            self.assertLess(c_html.index('data-sec="education"'), c_html.index('data-sec="experience"'))
            # the website icon is a setting; the angular G draws larger
            self.assertIn('<svg viewBox="0 0 24 24" class="big"', c_html)
            globe = render.render(c, render.Options("c", "blue", "es", "web"), age=20, base_href="x/", photo_src="p")
            self.assertNotIn('class="big"', globe)
            with self.assertRaises(ValueError):
                render.Options("z").checked()

    def test_contact_line_and_linkedin_fallback(self):
        self.assertEqual(
            render.contact_parts("a@b.com | +1 (918) 555-0100 | example.com | linkedin.com/in/x | Somewhere"),
            [("tel", "+1 (918) 555-0100"), ("mail", "a@b.com"), ("web", "example.com"), ("linkedin", "linkedin.com/in/x"), ("link", "Somewhere")],
        )
        with TempRepo() as t:
            svc, ds = self._content(t)
            real, render.LINKEDIN_MASK = render.LINKEDIN_MASK, "icons/not-there.png"
            try:
                h = render.render(svc.obj(), render.Options(), age=20, base_href="x/", photo_src="")
            finally:
                render.LINKEDIN_MASK = real
            self.assertNotIn("li-mask", h)
            self.assertIn('data-ic="link"', h)  # the generic link icon on a machine without LinkedIn's files
            if (render.TEMPLATE_DIR / render.LINKEDIN_MASK).is_file():
                h = render.render(svc.obj(), render.Options(), age=20, base_href="x/", photo_src="")
                self.assertIn('class="li-mask" style="--li:url(data:image/png;base64,', h)

    def test_template_holds_no_personal_text_and_the_fonts_are_vendored(self):
        for name in ("page.html", "parts.html", "designed.css"):
            text = (render.TEMPLATE_DIR / name).read_text(encoding="utf-8")
            for private in ("@", "918", "linkedin.com/in/", "Tulsa"):
                if name == "designed.css" and private == "@":
                    continue  # @page, @font-face
                self.assertNotIn(private, text.replace("@page", "").replace("@font-face", ""), f"{name} holds {private!r}")
        fonts = render.TEMPLATE_DIR / "fonts"
        css = (fonts / "fonts.css").read_text(encoding="utf-8")
        self.assertNotIn("http", css)  # nothing is fetched from the network
        for fam in ("Archivo", "Archivo Narrow", "Figtree", "Lora", "DM Sans"):
            self.assertIn(f"font-family: '{fam}'", css)
            self.assertIn("SIL OPEN FONT LICENSE", (fonts / f"OFL-{fam.replace(' ', '')}.txt").read_text(encoding="utf-8").upper())
        import re

        for f in re.findall(r"url\(([^)]+)\)", css):
            self.assertTrue((fonts / f).is_file(), f)

    @unittest.skipUnless(STAGING_ICONS.is_dir() and (render.TEMPLATE_DIR / "icons" / "InBug-White-noR.png").is_file(), "LinkedIn's files are not on this machine")
    def test_linkedin_files_are_copied_unchanged(self):
        for p in sorted(STAGING_ICONS.glob("*.png")):
            self.assertEqual(sha(render.TEMPLATE_DIR / "icons" / p.name), sha(p), p.name)


# ----------------------------------------------------------------- checks (pure parts)


class CheckTests(unittest.TestCase):
    def test_birth_date_forms(self):
        forms = checks.birth_forms(BIRTH)  # a made-up date
        self.assertEqual(forms, ["2001-02-03", "03/02/2001", "02/03/2001", "3/2/2001", "2/3/2001", "3 de febrero de 2001", "3 de febrero", "February 3, 2001", "February 3"])
        for form in forms:
            self.assertIn(form, checks.birth_hits(f"born {form}.", BIRTH), form)
        self.assertEqual(checks.birth_hits("Edad: 20 años · Age: 20 · February 2026 · 13 de febrero · February 30 · 2012/3/2/2001", BIRTH), [])
        self.assertEqual(checks.birth_hits("NACIDO EL 3 DE FEBRERO", BIRTH), ["3 de febrero"])
        self.assertEqual(len(checks.birth_forms(date(1999, 11, 12))), 7)  # no leading zeros to drop: the two slash forms appear once each

    def test_missing_text_and_photo_resolution(self):
        text = "EXPERIENCE Engineer Summer 2026 Did a thing, with a line break in the PDF."
        self.assertEqual(checks.missing_texts([("a", "Did a thing, with a line  break in the PDF."), ("h", "Experience"), ("b", "Clipped words")], text), [("b", "Clipped words")])
        self.assertAlmostEqual(checks.photo_dpi((1000, 1250), render.PHOTO_PX["c"]), 685.7, places=1)
        self.assertAlmostEqual(checks.photo_dpi((1000, 1250), render.PHOTO_PX["e"]), 1116.3, places=1)
        self.assertLess(checks.photo_dpi((300, 300), render.PHOTO_PX["c"]), checks.MIN_DPI)

    def test_file_names(self):
        self.assertEqual(pdf_name("es", "c", "blue", "20261125"), "es Gideon Ong CV Diseño C 20261125.pdf")
        self.assertEqual(pdf_name("en", "e", "blue", "20261125"), "en Gideon Ong CV Designed E 20261125.pdf")
        self.assertEqual(pdf_name("en", "c", "bronze", "20261125"), "en Gideon Ong CV Designed C bronze 20261125.pdf")


# ----------------------------------------------------------------- export (a real headless browser)


@unittest.skipUnless(BROWSER, "neither Edge nor Chrome is installed")
class ExportTests(unittest.TestCase):
    def setUp(self):
        self._word = word_export.export_pdf
        word_export.export_pdf = lambda *a, **k: self.fail("the Designed CV export started Word")

    def tearDown(self):
        word_export.export_pdf = self._word

    def _ready(self, t, today=TODAY):
        svc = import_six(t)
        ds = designed_service(t, svc, today)
        (t.root / masters.BLOCKLIST_PATH).write_text("secretword | a test term\n", encoding="utf-8")
        fill(ds)
        self.assertTrue(svc.save()["ok"])
        return svc, ds

    def test_both_layouts_and_languages_export_to_one_checked_page_each(self):
        with TempRepo() as t:
            svc, ds = self._ready(t)
            assets_before = sorted(str(p.relative_to(t.root)) for p in (t.root / "assets").rglob("*"))
            masters_before = master_hashes(t.root)
            self.assertEqual(ds.export_blockers(), [])
            ds.start_export(["c", "e"], ["es", "en"])
            j = wait(ds)
            self.assertEqual(j["failed"], {}, "\n".join(j["log"]))
            names = sorted(d["file"] for d in j["done"])
            self.assertEqual(names, ["en Gideon Ong CV Designed C 20210615.pdf", "en Gideon Ong CV Designed E 20210615.pdf", "es Gideon Ong CV Diseño C 20210615.pdf", "es Gideon Ong CV Diseño E 20210615.pdf"])
            self.assertEqual(sorted(p.name for p in (t.root / OUT_DIR).iterdir()), names)
            for name in names:
                pages, text = checks.read_pdf(t.root / OUT_DIR / name)
                lang = name[:2]
                self.assertEqual(pages, 1, name)
                self.assertIn("Edad: 20 años" if lang == "es" else "Age: 20", text)
                self.assertEqual(checks.birth_hits(text, BIRTH), [])
                self.assertEqual(checks.missing_texts(model.ticked_texts(svc.obj(), lang), text), [], name)
                self.assertIn("+1 (918) 555-0100", text)
                self.assertNotIn("secretword", text.lower())
            ex = ds.exports()
            self.assertEqual(([e["age"] for e in ex], [e["stale"] for e in ex]), ([20] * 4, [False] * 4))
            # private: nothing under assets/, nothing in the masters, no leftovers of the job
            self.assertEqual(sorted(str(p.relative_to(t.root)) for p in (t.root / "assets").rglob("*")), assets_before)
            self.assertEqual(master_hashes(t.root), masters_before)
            self.assertEqual(list((t.local / "designed").iterdir()), [])
            self.assertFalse(any("WINWORD" in line.upper() or "Word " in line for line in j["log"]))
            # the measure the page reports is in the log, per column
            self.assertTrue(any("space left — main column" in line for line in j["log"]))
            # the palette is in the name only when it is not the default
            ds.start_export(["c"], ["es"], "bronze")
            j = wait(ds)
            self.assertEqual([d["file"] for d in j["done"]], ["es Gideon Ong CV Diseño C bronze 20210615.pdf"], "\n".join(j["log"]))

    def test_overflow_blocks_the_export_and_names_the_column(self):
        with TempRepo() as t:
            svc, ds = self._ready(t)
            for n in range(45):
                cid = ds.op({"op": "add-bullet", "id": "engineer"})["id"]
                for lang in ("en", "es"):
                    ds.op({"op": "text", "id": cid, "field": "text", "lang": lang, "value": f"Made-up bullet number {n} that runs long enough to take most of a line on the page, in {lang}."})
            self.assertTrue(svc.save()["ok"])
            ds.start_export(["c"], ["es"])
            j = wait(ds)
            self.assertEqual(j["done"], [])
            why = j["failed"]["C · blue · ES"]
            self.assertEqual(len(why), 1, why)
            self.assertRegex(why[0], r"^the main column is over by \d+ px \(about \d+\.\d cm\)")
            self.assertFalse((t.root / OUT_DIR).exists() and any((t.root / OUT_DIR).iterdir()))
            # the sidebar is named when it is the one that overflows
            for cid in list(svc.obj()["items"]["engineer"]["children"]):
                if cid not in ("engineer-1", "engineer-2"):
                    ds.op({"op": "remove", "id": cid})
            for n in range(40):
                rid = ds.op({"op": "row-add", "group": "skills"})["id"]
                for lang in ("en", "es"):
                    ds.op({"op": "row-set", "group": "skills", "id": rid, "field": "label", "lang": lang, "value": f"Skill {n} {lang}"})
                    ds.op({"op": "row-set", "group": "skills", "id": rid, "field": "list", "lang": lang, "value": "one, two, three, four, five"})
            self.assertTrue(svc.save()["ok"])
            ds.start_export(["c"], ["en"])
            j = wait(ds)
            self.assertRegex(j["failed"]["C · blue · EN"][0], r"^the sidebar is over by \d+ px")

    def test_checks_on_the_printed_pdf_fail_the_export(self):
        with TempRepo() as t:
            svc, ds = self._ready(t)
            # the birth date typed into the profile (the content validation has no rule for it — the PDF check does)
            ds.op({"op": "single-text", "key": "profile", "lang": "es", "value": "Nací el 3 de febrero de 2001 y busco trabajo."})
            self.assertTrue(svc.save()["ok"])
            ds.start_export(["e"], ["es", "en"])
            j = wait(ds)
            self.assertEqual([d["tag"] for d in j["done"]], ["E · blue · EN"], "\n".join(j["log"]))
            why = j["failed"]["E · blue · ES"]
            self.assertTrue(all("birth date" in w for w in why), why)
            self.assertEqual({w.split("“")[1].split("”")[0] for w in why}, {"3 de febrero de 2001", "3 de febrero"})
            self.assertEqual([p.name for p in (t.root / OUT_DIR).iterdir()], ["en Gideon Ong CV Designed E 20210615.pdf"])
            # a blocklist term that reaches the PDF (the term is added after the text was saved)
            (t.root / masters.BLOCKLIST_PATH).write_text("made-up profile | a test term\n", encoding="utf-8")
            ds.op({"op": "single-text", "key": "profile", "lang": "es", "value": "Una línea de perfil inventada."})
            svc.draft = svc.obj()  # keep the draft through the gate of this test only
            content = svc.obj()
            page = t.local / "p.html"
            page.write_text(render.render(content, render.Options("c", "blue", "en"), age=20, base_href=render.TEMPLATE_DIR.as_uri() + "/", photo_src=""), encoding="utf-8")
            pdf = export.print_pdf(BROWSER[1], page, t.local / "p.pdf", t.local / "w")
            r = checks.check_pdf(pdf, content, "en", age_line="Age: 20", birth=BIRTH, terms=scans.load_blocklist(t.root / masters.BLOCKLIST_PATH)[0], photo=((200, 200), 140))
            self.assertEqual([e["code"] for e in r["errors"]], ["blocklist"])
            self.assertIn("photo-dpi", [w["code"] for w in r["warnings"]])
            self.assertEqual((r["pages"], r["age"]), (1, 20))
            # a ticked text that is not on the page is an error (here: asked for, never rendered)
            r = checks.check_pdf(pdf, content, "en", age_line="Age: 21", birth=BIRTH)
            self.assertEqual([e["code"] for e in r["errors"]], ["missing-text"])

    def test_stale_age_flag(self):
        with TempRepo() as t:
            svc, ds = self._ready(t, today=date(2022, 2, 2))  # the day before the 21st birthday
            self.assertEqual(ds.state()["age"]["value"], 20)
            self.assertEqual(ds.state()["age"]["nextBirthday"], "2022-02-03")
            ds.start_export(["c"], ["es"])
            j = wait(ds)
            self.assertEqual(j["failed"], {}, "\n".join(j["log"]))
            self.assertEqual([(e["age"], e["stale"]) for e in ds.exports()], [(20, False)])
            ds.today = lambda: date(2022, 2, 3)  # the birthday
            self.assertEqual(ds.state()["age"]["value"], 21)
            ex = ds.state()["exports"]
            self.assertEqual([(e["age"], e["stale"], e["note"]) for e in ex], [(20, True, "rendered at 20, you're now 21: re-render")])
            ds.start_export(["c"], ["es"])
            j = wait(ds)
            names = {e["name"]: (e["age"], e["stale"]) for e in ds.exports()}
            self.assertEqual(names, {"es Gideon Ong CV Diseño C 20220202.pdf": (20, True), "es Gideon Ong CV Diseño C 20220203.pdf": (21, False)})


# ----------------------------------------------------------------- service gates, privacy, endpoints


class ServiceTests(unittest.TestCase):
    def test_export_is_refused_before_any_browser_starts(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            started = []
            ds.measure = lambda *a, **k: started.append("measure") or {}
            ds.print_pdf = lambda *a, **k: started.append("print")
            fill(ds)
            with self.assertRaises(RuntimeError) as e:
                ds.start_export()
            self.assertIn("save or discard the drafts first", str(e.exception))
            self.assertTrue(svc.save()["ok"])
            (t.root / PERSONAL_FILE).unlink()
            self.assertIn("no birth date", "; ".join(ds.export_blockers()))
            self.assertIsNone(ds.state()["age"]["value"])
            (t.root / PERSONAL_FILE).write_text(json.dumps({"birth_date": BIRTH.isoformat()}), encoding="utf-8")
            # the browser is a per-machine setting: Edge or Chrome first, or the path of another Chromium
            if BROWSER:
                ds.set_view(browser=str(BROWSER[1]))
                self.assertEqual(ds.find_browser(), (BROWSER[1].stem, BROWSER[1]))
                ds.settings()["designedView"]["browser"] = str(t.root / "gone" / "browser.exe")  # it moved away since
                self.assertEqual(ds.find_browser()[1], BROWSER[1])  # back to Edge, else Chrome
            with self.assertRaises(ValueError):
                ds.set_view(browser=str(t.root / "nothing-here.exe"))
            ds.find_browser = lambda: None
            self.assertIn("neither Microsoft Edge nor Google Chrome", "; ".join(ds.export_blockers()))
            self.assertEqual(started, [])

    def test_a_failed_measure_or_missing_fonts_writes_nothing(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            fill(ds)
            self.assertTrue(svc.save()["ok"])
            printed = []
            ds.find_browser = lambda: ("Fake", Path("fake.exe"))
            ds.print_pdf = lambda *a, **k: printed.append(1)
            ds.measure = lambda *a, **k: {"main": 12, "side": -30, "fonts": "missing: Figtree"}
            ds.start_export(["e"], ["en"])
            j = wait(ds)
            self.assertEqual(j["failed"]["E · blue · EN"], ["the sidebar is over by 30 px (about 0.8 cm) — untick something", "the page's fonts did not load (missing: Figtree) — the PDF would print in a fallback font"])
            self.assertEqual((printed, (t.root / OUT_DIR).exists()), ([], False))

            def boom(*a, **k):
                raise export.ExportError("fake.exe exited with code 1")

            ds.measure = boom
            ds.start_export(["c"], ["es"])
            self.assertEqual(wait(ds)["failed"]["C · blue · ES"], ["fake.exe exited with code 1"])

    def test_private_by_default_nothing_publishes_it(self):
        with TempRepo() as t:
            svc = import_six(t)
            ds = designed_service(t, svc)
            st = ds.state()
            self.assertEqual(st["publish"]["enabled"], False)
            self.assertFalse(ds.publish_enabled())
            self.assertFalse(hasattr(ds, "publish") or hasattr(ds, "publish_apply") or hasattr(ds, "publish_plan"))
        # no code path from staging/cv-design-out/ into assets/: the Designed modules never name
        # the served folders, and the CV / transcript publish code never names the Designed output
        designed_dir = EDITOR_DIR / "core" / "cv" / "designed"
        for p in sorted(designed_dir.glob("*.py")):
            code = p.read_text(encoding="utf-8")
            for word in ("assets/pdfs", "PDF_DIR", "publish.plan", "publish.apply", "build-docs-manifest", "shutil.copy"):
                self.assertNotIn(word, code, f"{p.name} mentions {word}")
        for rel in ("core/cv/publish.py", "core/cv/service.py", "core/transcript/service.py", "core/preview.py"):
            self.assertNotIn("cv-design", (EDITOR_DIR / rel).read_text(encoding="utf-8"), rel)
        self.assertNotIn("designedPublish", (EDITOR_DIR / "app.py").read_text(encoding="utf-8"))  # no endpoint can set the flag
        routes = (EDITOR_DIR / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("/api/designed/publish", routes)

    def test_endpoints(self):
        with TempRepo() as t:
            import_six(t)
            state = EditorState(t.root, t.local, "tok", 5510, 5501)
            designed_service(t, state.cvtext)  # writes personal.json and the photo
            client = create_app(state).test_client()
            h = {"X-Editor-Token": "tok", "Host": "127.0.0.1:5510"}
            self.assertEqual(client.get("/api/designed/state", headers={"Host": "127.0.0.1:5510"}).status_code, 403)
            self.assertEqual(client.post("/api/designed/op", headers={"Host": "127.0.0.1:5510"}, json={"op": "tick", "id": "engineer", "on": True}).status_code, 403)
            self.assertEqual(client.post("/api/designed/export", headers={"Host": "127.0.0.1:5510"}, json={}).status_code, 403)
            self.assertEqual(client.get("/designed", headers={"Host": "evil.example"}).status_code, 403)
            r = client.get("/designed", headers={"Host": "127.0.0.1:5510"})
            self.assertEqual(r.status_code, 200)
            self.assertIn(b"Designed CV", r.data)
            r.close()
            st = client.get("/api/designed/state", headers=h).get_json()
            self.assertEqual((st["hasDesign"], st["seeded"], st["seedAvailable"], st["view"]["layout"], st["view"]["lang"]), (True, False, False, "c", "es"))
            r = client.post("/api/designed/op", headers=h, json={"op": "tick", "id": "engineer", "on": True}).get_json()
            self.assertTrue(r["ok"])
            self.assertEqual(r["checklist"]["main"][1]["rows"][0]["id"], "engineer")
            self.assertEqual(r["draftCount"], state.cvtext.draft_count())
            self.assertEqual(client.post("/api/designed/op", headers=h, json={"op": "tick", "id": "nope", "on": True}).status_code, 404)
            self.assertEqual(client.post("/api/designed/op", headers=h, json={"op": "bogus"}).status_code, 400)
            self.assertEqual(client.post("/api/designed/op", headers=h, json={"op": "seed"}).status_code, 409)  # no seed file here
            page = client.get("/api/designed/page?layout=e&palette=bronze&lang=en&key=3", headers=h).get_json()
            self.assertIn('<div class="pg l-e" id="pg">', page["html"])
            self.assertIn("Engineer", page["html"])
            self.assertEqual(client.get("/api/designed/page?layout=q", headers=h).status_code, 400)
            v = client.post("/api/designed/view", headers=h, json={"layout": "e", "webIcon": "code"}).get_json()
            self.assertEqual((v["view"]["layout"], v["view"]["webIcon"]), ("e", "code"))
            self.assertEqual(json.loads((t.local / "settings.json").read_text(encoding="utf-8"))["designedView"]["layout"], "e")
            self.assertEqual(client.post("/api/designed/view", headers=h, json={"palette": "pink"}).status_code, 400)
            self.assertEqual(client.post("/api/designed/export", headers=h, json={}).status_code, 409)  # drafts
            self.assertEqual(client.post("/api/settings", headers=h, json={"designedPublish": True}).status_code, 400)
            photo = client.get("/designed/photo", headers={"Host": "127.0.0.1:5510"})
            self.assertEqual((photo.status_code, photo.mimetype), (200, "image/jpeg"))
            photo.close()
            self.assertIsNone(client.get("/api/designed/job", headers=h).get_json()["job"])
            # the CV text tab's own endpoints carry the same draft, and its review words the change
            rv = client.get("/api/cvtext/review", headers=h).get_json()
            self.assertTrue(any("now in Designed" in c["text"] for c in rv["changes"]), rv["changes"])
            self.assertEqual(client.post("/api/cvtext/op", headers=h, json={"op": "include", "id": "engineer", "variant": D, "on": False, "current": D}).status_code, 200)
            self.assertFalse(client.get("/api/designed/state", headers=h).get_json()["checklist"]["main"][1]["rows"][0]["on"])


# ----------------------------------------------------------------- the real masters (read on a temp copy)


@unittest.skipUnless(MASTERS_PRESENT and (REPO_ROOT / CONTENT_FILE).is_file(), "the CV masters and content set are not on this machine")
class RealMastersTests(unittest.TestCase):
    def test_import_proof_and_a_no_edit_apply_leave_the_six_masters_byte_identical(self):
        with TempRepo() as t:
            for rel in ("staging/cv-masters", "staging/cv-content"):
                shutil.copytree(REPO_ROOT / rel, t.root / rel)
            before = master_hashes(t.root)
            self.assertEqual(before, {m.file: sha(masters.docx_path(REPO_ROOT, m)) for m in masters.MASTERS})
            content_before = (t.root / CONTENT_FILE).read_bytes()
            svc = CvTextService(t.root, Backups(t.root, t.local / "backups"), t.local, migrate=True)
            self.assertEqual(svc.obj()["version"], 2)
            self.assertIsNone(svc.doc.read_only)
            was = copy.deepcopy(svc.obj())
            # What an Apply would do is exactly what it would do without the Designed variant: the
            # plan per master from the content as the masters see it (version 1, nothing Designed)
            # equals the plan from the file. Where that plan is empty an Apply with no edits writes
            # nothing. (A plan can be non-empty on its own: content saved but never applied.)
            plain = schema.strip_designed(svc.obj())
            pending = set()
            for m in masters.MASTERS:
                p1, p2 = renderer.plan_master(plain, svc.slots[m.file], m.file), renderer.plan_master(svc.obj(), svc.slots[m.file], m.file)
                self.assertEqual(p1, p2, m.file)
                self.assertEqual((p2["changed"], p2["removed"]), ([], []), m.file)
                if p2["added"]:
                    pending.add(m.file)
            if not svc.apply_blockers(svc.obj()):
                r = svc.apply()
                self.assertTrue(r["ok"], r)
                self.assertEqual(set(r.get("written", [])), pending, r)
                if not pending:
                    self.assertTrue(r.get("noop"), r)
                    self.assertEqual((t.root / CONTENT_FILE).read_bytes(), content_before)
                after = master_hashes(t.root)
                self.assertEqual({f for f in before if before[f] != after[f]}, pending)
                for f in pending:  # put the pending master back: the import below reads the six as they are
                    shutil.copy2(masters.MASTERS_DIR and REPO_ROOT / masters.MASTERS_DIR / f, t.root / masters.MASTERS_DIR / f)
                shutil.rmtree(t.root / "staging/cv-content")
                shutil.copytree(REPO_ROOT / "staging/cv-content", t.root / "staging/cv-content")
                svc.load()
                was = copy.deepcopy(svc.obj())
            self.assertEqual(master_hashes(t.root), before)
            # the import proof passes on all six and the Designed variant comes through it whole
            r = svc.run_import()
            self.assertTrue(r["ok"], r)
            self.assertEqual(r["proof"], {m.file: [] for m in masters.MASTERS})
            self.assertEqual(master_hashes(t.root), before)
            now = svc.obj()
            self.assertEqual(now["version"], 2)
            if was.get("design"):
                self.assertEqual(r["report"]["designed"]["dropped"], [])
                self.assertEqual(now["design"], was["design"])
                self.assertEqual([s["order"].get(D) for s in now["sections"]], [s["order"].get(D) for s in was["sections"]])
                self.assertEqual(model.checklist(now, TODAY), model.checklist(was, TODAY))
            self.assertEqual(schema.strip_designed(now)["items"].keys(), schema.strip_designed(was)["items"].keys())


if __name__ == "__main__":
    unittest.main()
