"""Phase 4a: master import, pairing, sharing across variants, and the proof of
losslessness. Phase 4b: the editor over the content set — operations, validation,
the fit meter, review / save / autosave. Synthetic masters carry the same shapes
as Gideon's (name / title / contact, headings, entry lines with a right tab,
bullets, split runs with rsid attributes and spell-check markers). The real
masters are used when present."""

import copy
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from _helpers import REPO_ROOT, TempRepo
from app import EditorState, create_app
from core import validate
from core.backups import Backups
from core.cv import content as C
from core.cv import cvcheck, docxread, fit, importer, masters, renderer, scans
from core.cv.textservice import CvTextService, change_lines
from core.jsonfile import JsonFile

MASTERS_PRESENT = all(masters.docx_path(REPO_ROOT, m).is_file() for m in masters.MASTERS)
W = importer.W_NS


def make_master(path: Path, lang="en", title=True, entries=None, extra_bullet=True, split_runs=True):
    """A CV-shaped master: name, [title], contact, Education heading + entry + line, Experience + entries with bullets."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(0.32)
    doc.styles["Normal"].font.name = "Georgia"
    doc.styles["Normal"].font.size = Pt(11)

    def para(text="", size=None, bold=False, italic=False, center=False, style=None):
        p = doc.add_paragraph(style=style)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if text:
            r = p.add_run(text)
            if bold:
                r.bold = True
            if italic:
                r.italic = True
            if size:
                r.font.size = Pt(size)
        return p

    def entry(role, org, date):
        p = doc.add_paragraph()
        p.paragraph_format.tab_stops.add_tab_stop(Inches(7.86), WD_TAB_ALIGNMENT.RIGHT)
        r = p.add_run(role)
        r.bold = True
        if org:
            p.add_run(" · " + org)
        p.add_run("\t")
        r = p.add_run(date.replace(" ", "\xa0"))
        r.italic = r.underline = True
        return p

    para("Test Person", size=18, bold=True, center=True)
    if title:
        para("Engineer · Tester" if lang == "en" else "Ingeniero · Probador", italic=True, center=True)
    para("test@example.com  |  example.com", size=10, center=True)
    para("Education" if lang == "en" else "Formación", size=13, bold=True)
    entry("Test University" if lang == "en" else "Universidad de Prueba", "", "In progress" if lang == "en" else "En curso")
    para("Program line" if lang == "en" else "Línea del programa")
    para("Experience" if lang == "en" else "Experiencia", size=13, bold=True)
    for role, org, date, bullets in (entries or [("Engineer", "Org, Town", "Summer 2026", ["Did a thing.", "Did another."])]):
        entry(role, org, date)
        for b in bullets:
            para(b, style="List Bullet")
    if extra_bullet:
        pass
    doc.save(str(path))
    if split_runs:
        # split the first bullet's run in two (rsid-only difference) and add a spell-check marker between them
        import zipfile
        import re

        z = zipfile.ZipFile(path)
        xml = z.read("word/document.xml").decode("utf-8")
        parts = {n: z.read(n) for n in z.namelist()}
        z.close()
        target = "Did a thing." if lang == "en" else None
        if target and target in xml:
            xml = xml.replace(f"<w:t>{target}</w:t></w:r>", '<w:t>Did a</w:t></w:r><w:proofErr w:type="spellStart"/><w:r w:rsidRPr="00AB12CD"><w:t xml:space="preserve"> thing.</w:t></w:r>', 1)
        parts["word/document.xml"] = xml.encode("utf-8")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
            for n, data in parts.items():
                out.writestr(n, data)
    return path


class ReadAndStructureTests(unittest.TestCase):
    def test_read_merges_split_runs_and_classifies(self):
        with TempRepo() as t:
            p = make_master(t.root / "m.docx")
            d = importer.read_master(p)
            kinds = [x.kind for x in d.paragraphs]
            self.assertEqual(kinds, ["name", "title", "contact", "heading", "entry", "plain", "heading", "entry", "bullet", "bullet"])
            first_bullet = d.paragraphs[8]
            self.assertEqual([s.text for s in first_bullet.spans], ["Did a thing."])  # rsid split + proofErr merged away
            e = d.paragraphs[7]
            self.assertEqual([(importer.is_bold(s.key), s.text) for s in e.spans], [(True, "Engineer"), (False, " · Org, Town\t"), (False, "Summer\xa02026")])
            self.assertEqual(importer.split_entry(e.spans), {"role": "Engineer", "org": "Org, Town", "date": "Summer 2026", "sep": " · ", "notes": []})
            self.assertEqual(importer.split_entry(d.paragraphs[4].spans)["org"], "")
            nodes = importer.structure(d)
            self.assertEqual([n.kind for n in nodes], ["name", "title", "contact", "heading", "entry", "child-line", "heading", "entry", "child-bullet", "child-bullet"])

    def test_unsupported_constructs_are_refused(self):
        with TempRepo() as t:
            p = make_master(t.root / "m.docx", split_runs=False)
            from docx import Document

            doc = Document(str(p))
            doc.add_table(rows=1, cols=1)
            doc.save(str(p))
            with self.assertRaises(importer.ImportError_):
                importer.read_master(p)


class MergeAndProofTests(unittest.TestCase):
    def _docs(self, t):
        en = make_master(t.root / "Gideon Ong CV Full EN.docx", "en", entries=[("Engineer", "Org, Town", "Summer 2026", ["Did a thing.", "Did another."]), ("Tutor", "School", "Fall 2025", ["Taught."])])
        es = make_master(t.root / "Gideon Ong CV Completo ES.docx", "es", entries=[("Ingeniero", "Org, Pueblo", "Verano 2026", ["Hice algo.", "Hice otra cosa."]), ("Tutor", "Escuela", "Otoño 2025", ["Enseñé."])])
        pen = make_master(t.root / "Gideon Ong CV Professional EN.docx", "en", entries=[("Engineer", "Org, Town", "Summer 2026", ["Did a thing."])])
        pes = make_master(t.root / "Gideon Ong CV Profesional ES.docx", "es", entries=[("Ingeniero", "Org, Pueblo", "Verano 2026", ["Hice algo."])], split_runs=False)
        return {"full": {"en": importer.read_master(en), "es": importer.read_master(es)}, "professional": {"en": importer.read_master(pen), "es": importer.read_master(pes)}}

    def test_merge_shares_items_and_keeps_per_variant_order(self):
        with TempRepo() as t:
            content, slots, report = importer.merge(self._docs(t))
            items = content["items"]
            eng = items["engineer"]
            self.assertEqual(eng["include"], {"full": True, "professional": True, "resume": False})
            self.assertEqual(eng["role"], {"en": "Engineer", "es": "Ingeniero"})
            self.assertEqual(eng["org"], {"en": "Org, Town", "es": "Org, Pueblo"})
            self.assertEqual(eng["order"]["full"], ["engineer-1", "engineer-2"])
            self.assertEqual(eng["order"]["professional"], ["engineer-1"])
            self.assertEqual(eng["children"]["engineer-2"]["include"], {"full": True, "professional": False, "resume": False})
            self.assertEqual(items["tutor"]["include"]["professional"], False)
            exp = next(s for s in content["sections"] if s["id"] == "experience")
            self.assertEqual(exp["order"], {"full": ["engineer", "tutor"], "professional": ["engineer"]})
            self.assertEqual(content["header"]["title"]["full"], {"en": "Engineer · Tester", "es": "Ingeniero · Probador"})
            self.assertEqual(report["variants"]["professional"]["sharedWithEarlier"], 4)  # education entry, program line, engineer entry, its first bullet
            self.assertEqual(report["unpaired"], {"full": [], "professional": []})
            self.assertEqual(len(slots["Gideon Ong CV Full EN.docx"]), 12)  # one slot per paragraph
            self.assertIn("engineer", content["hashes"]["Gideon Ong CV Full EN.docx"])

    def test_pairing_gap_and_proof(self):
        with TempRepo() as t:
            en = make_master(t.root / "Gideon Ong Resume EN.docx", "en", title=False, entries=[("Engineer", "Org", "Summer 2026", ["One.", "Two."])])
            es = make_master(t.root / "Gideon Ong Resume ES.docx", "es", title=False, entries=[("Ingeniero", "Org", "Verano 2026", ["Uno."])], split_runs=False)
            docs = {"resume": {"en": importer.read_master(en), "es": importer.read_master(es)}}
            content, slots, report = importer.merge(docs)
            self.assertEqual(len(report["unpaired"]["resume"]), 1)
            self.assertIn("no ES twin", report["unpaired"]["resume"][0])
            self.assertEqual(content["items"]["engineer"]["children"]["engineer-2"]["text"], {"en": "Two.", "es": ""})
            self.assertIsNone(content["header"]["title"]["resume"])
            tmp = Path(tempfile.mkdtemp())
            for doc in (docs["resume"]["en"], docs["resume"]["es"]):
                out = renderer.force_render(doc, slots[doc.path.name], content, tmp / doc.path.name)
                self.assertEqual(importer.compare(doc.path, out), [], doc.path.name)
            # an edited render changes exactly that paragraph and re-imports to the new text
            c2 = copy.deepcopy(content)
            c2["items"]["engineer"]["children"]["engineer-1"]["text"]["en"] = "One, edited."
            c2["items"]["engineer"]["org"]["en"] = "New Org"
            doc = importer.read_master(en)
            out = renderer.force_render(doc, slots[en.name], c2, tmp / "edited.docx")
            problems = importer.compare(en, out)
            self.assertEqual(len(problems), 2, problems)
            nodes = importer.structure(importer.read_master(out))
            self.assertIn({"text": "One, edited."}, [n.parts for n in nodes])
            e = next(n.parts for n in nodes if n.kind == "entry" and n.parts["role"] == "Engineer")
            self.assertEqual((e["org"], e["date"], e["sep"]), ("New Org", "Summer 2026", " · "))
            self.assertEqual(importer.compare(en, en), [])

    def test_service_import_writes_only_when_lossless(self):
        with TempRepo() as t:
            (t.root / masters.MASTERS_DIR).mkdir(parents=True)
            for m in masters.MASTERS:
                make_master(t.root / masters.MASTERS_DIR / m.file, m.lang, title=m.variant != "resume", split_runs=(m.lang == "en"))
            svc = CvTextService(t.root, Backups(t.root, t.local / "backups"))
            self.assertIsNone(svc.state()["content"])
            r = svc.run_import()
            self.assertTrue(r["ok"], r)
            self.assertTrue(r["written"])
            self.assertEqual({k: v for k, v in r["proof"].items()}, {m.file: [] for m in masters.MASTERS})
            self.assertTrue(svc.content_path().is_file())
            self.assertEqual(len(list((t.root / "staging/cv-content/slots").glob("*.json"))), 6)
            st = svc.state()
            self.assertEqual(st["content"]["sections"], 2)
            self.assertTrue(st["lastImport"]["ok"])
            # re-import backs the previous set up
            r2 = svc.run_import()
            self.assertTrue(r2["ok"])
            self.assertIn("backup", r2)
            # a master with an unsupported construct blocks the import
            from docx import Document

            p = t.root / masters.MASTERS_DIR / "Gideon Ong Resume ES.docx"
            doc = Document(str(p))
            doc.add_table(rows=1, cols=1)
            doc.save(str(p))
            r3 = svc.run_import()
            self.assertEqual((r3["ok"], r3["error"]), (False, "unsupported"))
            p.unlink()
            self.assertEqual(svc.run_import()["error"], "missing-masters")


# ----------------------------------------------------------------- Phase 4b


def import_six(t: TempRepo, gpa=None) -> CvTextService:
    """Six synthetic masters imported into t.root/staging/cv-content/; the service over them."""
    (t.root / masters.MASTERS_DIR).mkdir(parents=True, exist_ok=True)
    for m in masters.MASTERS:
        make_master(t.root / masters.MASTERS_DIR / m.file, m.lang, title=m.variant != "resume", split_runs=(m.lang == "en"))
    svc = CvTextService(t.root, Backups(t.root, t.local / "backups"), t.local, gpa=gpa or (lambda: None))
    r = svc.run_import()
    assert r["ok"], r
    return svc


def mini_content() -> dict:
    """A hand-built content set for the rules (no masters needed)."""
    inc = {"full": True, "professional": False, "resume": False}

    def entry(role_en, role_es, org, date_en, date_es, children):
        return {"kind": "entry", "role": {"en": role_en, "es": role_es}, "org": {"en": org, "es": org}, "date": {"en": date_en, "es": date_es}, "sep": " · ", "include": dict(inc), "order": {"full": list(children)}, "children": {cid: {"kind": kind, "text": {"en": en, "es": es}, "include": dict(inc)} for cid, (kind, en, es) in children.items()}}

    return {
        "version": 1,
        "masters": {"full": {"en": "F EN.docx", "es": "F ES.docx"}},
        "header": {"name": "Test Person", "title": {"full": {"en": "Engineer", "es": "Ingeniero"}, "professional": None, "resume": None}, "contact": {"en": "a@b.com | +1 (918) 555-0100", "es": "a@b.com | +1 (918) 555-0100"}},
        "sections": [
            {"id": "education", "heading": {"en": "Education", "es": "Formación"}, "order": {"full": ["uni"]}},
            {"id": "experience", "heading": {"en": "Experience", "es": "Experiencia"}, "order": {"full": ["job", "spin"]}},
        ],
        "items": {
            "uni": entry("Test University", "Universidad de Prueba", "", "In progress", "En curso", {
                "uni-1": ("line", "Mechanical Engineering, B.S.M.E.; Spanish, B.A.", "Licenciatura en Ingeniería Mecánica (B.S.M.E.); Español (B.A.)"),
                "uni-2": ("line", "GPA: 4.0", "Promedio (GPA): 4.0"),
                "uni-3": ("line", "Minors: Economics, Basket Weaving", "Menciones: Economía y Cestería"),
            }),
            "job": entry("Engineer", "Ingeniero", "Org", "2026", "2026", {"job-1": ("bullet", "Leveraged a robust tool.", "Aproveché una herramienta.")}),
            "spin": entry("Translator, Spinelli essays", "Traductor, ensayos de Spinelli", "YWF", "2025", "2025", {"spin-1": ("bullet", "Leveraged translation memory.", "Aproveché la memoria de traducción.")}),
        },
        "hashes": {},
    }


PROFILE = {
    "en": {"majors": ["Mechanical Engineering, B.S.M.E.", "Spanish, B.A."], "minors": ["Economics"]},
    "es": {"majors": ["Ingeniería Mecánica (B.S.M.E.)", "Español (B.A.)"], "minors": ["Economía"]},
}


def codes(issues, key=None, level=None):
    return sorted((i.code, i.key, i.lang) for i in issues if (key is None or i.key == key) and (level is None or i.level == level))


class ContentOpsTests(unittest.TestCase):
    def test_set_include_move_add_delete(self):
        with TempRepo() as t:
            svc = import_six(t)
            self.assertEqual(svc.draft_count(), 0)
            svc.set_text(["items", "engineer", "role", "es"], "  Ingeniero  jefe ")
            self.assertEqual(svc.obj()["items"]["engineer"]["role"]["es"], "Ingeniero jefe")
            self.assertEqual(svc.draft_count(), 1)
            for bad in (["items", "engineer", "include", "full"], ["header", "title", "resume", "en"], ["items", "engineer", "kind"], ["hashes"]):
                with self.assertRaises((ValueError, KeyError), msg=bad):
                    svc.set_text(bad, "x")
            with self.assertRaises(KeyError):
                svc.set_text(["items", "nobody", "role", "en"], "x")
            # include off / on keeps the order lists in step and places the id after its neighbour
            eng = lambda: svc.obj()["items"]["engineer"]
            svc.include("engineer-2", "resume", False)
            self.assertEqual((eng()["children"]["engineer-2"]["include"]["resume"], eng()["order"]["resume"]), (False, ["engineer-1"]))
            svc.include("engineer-2", "resume", True, current="full")
            self.assertEqual(eng()["order"]["resume"], ["engineer-1", "engineer-2"])
            svc.include("engineer-1", "resume", False)
            svc.include("engineer-1", "resume", True, current="full")  # no included neighbour before it → at the start
            self.assertEqual(eng()["order"]["resume"], ["engineer-1", "engineer-2"])
            # taking the entry out of a variant takes its children out; a child cannot be in a variant its parent is not
            svc.include("engineer", "resume", False)
            sec = next(s for s in svc.obj()["sections"] if s["id"] == "experience")
            self.assertEqual(sec["order"]["resume"], [])
            self.assertEqual([c["include"]["resume"] for c in eng()["children"].values()], [False, False])
            with self.assertRaises(ValueError):
                svc.include("engineer-2", "resume", True)
            svc.include("engineer", "resume", True, current="full")
            self.assertEqual(sec["order"]["resume"], ["engineer"])
            self.assertEqual(eng()["order"]["resume"], [])
            # move within one variant only
            svc.move("engineer-1", "full", 1)
            self.assertEqual(eng()["order"]["full"], ["engineer-2", "engineer-1"])
            self.assertEqual(eng()["order"]["professional"], ["engineer-1", "engineer-2"])
            svc.move("engineer-1", "full", 1)  # already last: no-op
            self.assertEqual(eng()["order"]["full"], ["engineer-2", "engineer-1"])
            with self.assertRaises(ValueError):
                svc.move("engineer-1", "resume", -1)  # not in that variant
            # add item / child
            iid = svc.add_item("experience", "entry", "New Role", "resume")
            self.assertEqual(iid, "new-role")
            item = svc.obj()["items"][iid]
            self.assertEqual(item["include"], {"full": False, "professional": False, "resume": True})
            self.assertEqual(sec["order"]["resume"], ["engineer", "new-role"])
            self.assertEqual(svc.add_child(iid, "bullet", "resume"), "new-role-1")
            self.assertEqual(item["order"]["resume"], ["new-role-1"])
            with self.assertRaises(ValueError):
                svc.add_child(iid, "bullet", "full")  # the entry is not in Full
            self.assertEqual(svc.add_item("experience", "line", "Extra line", "full"), "experience-extra-line")
            with self.assertRaises(ValueError):
                svc.add_item("experience", "entry", "   ", "full")
            with self.assertRaises(KeyError):
                svc.add_item("nowhere", "entry", "x", "full")
            # delete
            svc.delete("new-role-1")
            self.assertEqual((item["children"], item["order"]["resume"]), ({}, []))
            svc.delete("engineer")
            self.assertNotIn("engineer", svc.obj()["items"])
            self.assertTrue(all("engineer" not in o for s in svc.obj()["sections"] for o in s["order"].values()))
            with self.assertRaises(KeyError):
                svc.delete("engineer")
            # listing: this variant's order first, the section's other items after
            lst = C.listing(svc.obj(), "resume")
            exp = next(s for s in lst if s["id"] == "experience")
            self.assertEqual((exp["items"], exp["others"]), (["new-role"], ["experience-extra-line"]))
            svc.discard_drafts()
            self.assertEqual(svc.draft_count(), 0)
            self.assertIn("engineer", svc.obj()["items"])


class CvCheckTests(unittest.TestCase):
    def test_rules(self):
        c = mini_content()
        base = cvcheck.check(c, PROFILE, "4.00", [])
        # the hand-built set has exactly the two bad minors and the voice words
        self.assertEqual(codes(base, level="error"), [("degree", "uni-3", "en"), ("degree", "uni-3", "es")])
        self.assertEqual(codes(base, level="warning"), [("voice", "job-1", "en")])
        self.assertIn("Basket Weaving", next(i.message for i in base if i.key == "uni-3" and i.lang == "en"))
        self.assertIn("Cestería", next(i.message for i in base if i.key == "uni-3" and i.lang == "es"))
        # empty text: an error only where the node is included somewhere
        c2 = copy.deepcopy(c)
        c2["items"]["job"]["role"]["es"] = ""
        c2["items"]["job"]["org"]["en"] = ""  # org may be empty
        c2["items"]["job"]["children"]["job-1"]["text"] = {"en": "", "es": ""}
        c2["items"]["job"]["children"]["job-1"]["include"] = {"full": False, "professional": False, "resume": False}
        self.assertEqual(codes(cvcheck.check(c2, PROFILE, "4.00", []), key="job"), [("empty", "job", "es")])
        self.assertEqual(codes(cvcheck.check(c2, PROFILE, "4.00", []), key="job-1"), [])
        # TODO / HTML
        c3 = copy.deepcopy(c)
        c3["items"]["job"]["role"]["en"] = "TODO engineer"
        c3["header"]["contact"]["es"] = "a@b.com <b>x</b>"
        got = cvcheck.check(c3, PROFILE, "4.00", [])
        self.assertIn(("todo", "job", "en"), codes(got))
        self.assertIn(("html", "header.contact", "es"), codes(got))
        # blocklist: the (918) phone is allowed, other terms are not
        terms = [scans.Term("555-0100", "phone", 1), scans.Term("org", "client name", 2)]
        got = cvcheck.check(c, PROFILE, "4.00", terms)
        self.assertEqual([i for i in codes(got) if i[0] == "blocklist"], [("blocklist", "job", "en"), ("blocklist", "job", "es")])
        # voice words: the Spinelli item keeps "leveraged"
        self.assertEqual(codes(base, key="spin-1"), [])
        self.assertIn("leveraged, robust", next(i.message for i in base if i.key == "job-1"))
        # degree line with a degree profile.json does not list
        c4 = copy.deepcopy(c)
        c4["items"]["uni"]["children"]["uni-1"]["text"]["en"] = "Mechanical Engineering, B.S.M.E.; Physics, B.S."
        msg = next(i.message for i in cvcheck.check(c4, PROFILE, "4.00", []) if i.key == "uni-1")
        self.assertIn("Physics, B.S.", msg)
        # no profile → unchecked warning, not an error
        got = cvcheck.check(c, None, "4.00", [])
        self.assertEqual([i.level for i in got if i.code == "degree-unchecked"], ["warning"] * 4)
        self.assertNotIn("degree", [i.code for i in got])
        # GPA
        self.assertEqual(codes(cvcheck.check(c, PROFILE, "3.95", []), key="uni-2"), [("gpa", "uni-2", "en"), ("gpa", "uni-2", "es")])
        self.assertEqual(codes(cvcheck.check(c, PROFILE, None, []), key="uni-2"), [])
        # fit results become issues per variant
        fits = {"job": {"full": {"en": {"status": "overflow", "left_pt": -3.0, "left_pct": -0.5, "text": "Engineer · Org"}, "es": {"status": "tight", "left_pt": 2.0, "left_pct": 0.4, "text": "Ingeniero · Org"}}}}
        got = cvcheck.check(c, PROFILE, "4.00", [], fits)
        self.assertEqual([(i.level, i.code, i.lang) for i in got if i.key == "job"], [("error", "fit-overflow-full", "en"), ("warning", "fit-tight-full", "es")])
        # the gate: pre-existing errors do not block until touched
        c5 = copy.deepcopy(c)
        c5["items"]["job"]["role"]["en"] = "TODO"
        gate = validate.blocking(base, cvcheck.check(c5, PROFILE, "4.00", []), {"job"})
        self.assertEqual(codes(gate.blocking), [("todo", "job", "en")])
        self.assertEqual(codes(gate.preexisting), [("degree", "uni-3", "en"), ("degree", "uni-3", "es")])
        c5["items"]["uni"]["children"]["uni-3"]["text"]["en"] = "Minors: Economics, Pottery"
        gate = validate.blocking(base, cvcheck.check(c5, PROFILE, "4.00", []), {"job", "uni-3"})
        self.assertIn(("degree", "uni-3", "en"), codes(gate.blocking))


class FitMeterTests(unittest.TestCase):
    def test_meter_matches_the_document_check_and_moves_with_the_text(self):
        with TempRepo() as t:
            svc = import_six(t)
            st = svc.state()
            self.assertIsNone(st["fitWarning"])
            full_en = masters.BY_ID["full-en"].file
            info = docxread.read(t.root / masters.MASTERS_DIR / full_en)
            slot = next(s for s in svc.slots[full_en] if s["id"] == "engineer")
            expected = fit.check_entry(info.paragraphs[slot["para"]], info)
            got = st["fits"]["engineer"]["full"]["en"]
            self.assertEqual(got["status"], "fits")
            self.assertAlmostEqual(got["left_pt"], expected.left_pt, delta=0.01)
            self.assertAlmostEqual(got["avail_pt"], expected.avail_pt, delta=0.01)
            # lengthen the role until it overflows: EN meters go red in every variant, ES stays
            svc.set_text(["items", "engineer", "role", "en"], "A role title that is far too long for one line " * 3)
            fits = svc.state()["fits"]["engineer"]
            self.assertEqual({v: d["en"]["status"] for v, d in fits.items()}, {"full": "overflow", "professional": "overflow", "resume": "overflow"})
            self.assertEqual({v: d["es"]["status"] for v, d in fits.items()}, {"full": "fits", "professional": "fits", "resume": "fits"})
            self.assertEqual(sorted(i.code for i in svc.gate().blocking), ["fit-overflow-full", "fit-overflow-professional", "fit-overflow-resume"])
            # a role that lands within 3 % → tight (a warning, not an error)
            fixed = fit.width_pt(" · Org, Town") + fit.width_pt(" ") + fit.width_pt("Summer 2026", italic=True)
            role = "a"
            while fit.width_pt(role, bold=True) + fixed < expected.avail_pt * 0.985:
                role += "a"
            svc.set_text(["items", "engineer", "role", "en"], role)
            self.assertEqual(svc.state()["fits"]["engineer"]["full"]["en"]["status"], "tight")
            self.assertEqual(svc.gate().blocking, [])
            self.assertIn("fit-tight-full", [i.code for i in svc.gate().warnings])
            # a new entry has no paragraph yet: it borrows its sibling's geometry
            iid = svc.add_item("experience", "entry", "Brand new role", "full")
            f = svc.state()["fits"][iid]
            self.assertEqual(list(f), ["full"])
            self.assertAlmostEqual(f["full"]["en"]["avail_pt"], expected.avail_pt, delta=0.01)
            self.assertEqual(f["full"]["en"]["status"], "fits")
            # a missing master → no meter for it, a warning, never an error
            (t.root / masters.MASTERS_DIR / full_en).unlink()
            st = svc.state()
            self.assertIsNone(st["fits"]["engineer"]["full"]["en"])
            self.assertIsNotNone(st["fits"]["engineer"]["full"]["es"])
            self.assertIn(full_en, st["fitWarning"])


class ReviewSaveTests(unittest.TestCase):
    def test_review_save_reload_and_refusals(self):
        with TempRepo() as t:
            svc = import_six(t)
            self.assertTrue(svc.review()["noop"])
            self.assertTrue(svc.save()["noop"])
            before = svc.content_path().read_bytes()
            svc.set_text(["items", "engineer", "role", "es"], "Ingeniero jefe")
            r = svc.review()
            self.assertFalse(r["noop"])
            self.assertTrue(r["ok"], r["gate"])
            self.assertEqual(len(r["changes"]), 1)
            self.assertIn("role (ES)", r["changes"][0]["text"])
            self.assertIn("Ingeniero jefe", r["changes"][0]["text"])
            touched = {m["file"] for m in r["masters"] if m["changed"]}
            self.assertEqual(touched, {masters.BY_ID[f"{v}-es"].file for v in importer.VARIANTS})
            self.assertTrue(all(m["changed"] == ["engineer"] and not m["added"] and not m["removed"] for m in r["masters"] if m["changed"]))
            self.assertIn('+        "es": "Ingeniero jefe"', r["diff"])
            s = svc.save()
            self.assertTrue(s["ok"], s)
            self.assertEqual(svc.draft_count(), 0)
            self.assertIsNone(JsonFile(t.root, "staging/cv-content/content.json").read_only)
            self.assertEqual(svc.obj()["items"]["engineer"]["role"]["es"], "Ingeniero jefe")
            bset = svc.backups.get(s["backup"])
            self.assertEqual([f["path"] for f in bset.files], ["staging/cv-content/content.json"])
            self.assertEqual(svc.backups.read_file(s["backup"], "staging/cv-content/content.json"), before)
            # structural edits show as one line each; a pure reorder shows as an order line
            svc.include("engineer-2", "resume", False)
            svc.move("engineer-1", "professional", 1)
            svc.add_child("engineer", "line", "full")
            texts = [c["text"] for c in svc.review()["changes"]]
            self.assertTrue(any("bullet 2: no longer in Résumé" in x for x in texts), texts)
            self.assertTrue(any("bullet order in Professional changed" in x for x in texts), texts)
            self.assertTrue(any("added line 3 in Full" in x for x in texts), texts)
            self.assertEqual(len(texts), 3, texts)  # membership changes (Résumé, Full) are not repeated as order lines
            plans = {m["file"]: m for m in svc.review()["masters"]}
            self.assertEqual(plans[masters.BY_ID["resume-en"].file]["removed"], ["engineer-2"])
            self.assertEqual(plans[masters.BY_ID["full-en"].file]["added"], ["engineer-3"])
            svc.discard_drafts()
            # blocked: an included item with empty text
            svc.set_text(["items", "engineer", "role", "en"], "")
            s = svc.save()
            self.assertEqual((s["ok"], s["error"]), (False, "blocked"))
            self.assertEqual([i["code"] for i in s["gate"]["blocking"]], ["empty"])
            svc.discard_drafts()
            # changed on disk: refused until reload; the draft is re-applied over the new file
            svc.set_text(["items", "engineer", "org", "en"], "New Org")
            raw = svc.content_path().read_bytes()
            time.sleep(0.05)
            svc.content_path().write_bytes(raw.replace(b'"Summer\\u00a02026"', b'"Summer 2026"').replace(b'"In progress"', b'"Still in progress"'))
            s = svc.save()
            self.assertEqual((s["ok"], s["error"]), (False, "changed-on-disk"))
            svc.load()
            self.assertEqual(svc.draft_count(), 1)
            self.assertEqual(svc.obj()["items"]["engineer"]["org"]["en"], "New Org")
            self.assertEqual(svc.obj()["items"]["test-university"]["date"]["en"], "Still in progress")
            self.assertTrue(svc.save()["ok"])
            # import is refused while a draft exists
            svc.set_text(["items", "engineer", "org", "en"], "Other Org")
            self.assertEqual(svc.run_import()["error"], "drafts")

    def test_autosave_and_editor_state(self):
        with TempRepo() as t:
            svc = import_six(t)
            svc.set_text(["items", "engineer", "date", "en"], "Fall 2026")
            auto = t.local / "drafts" / "cvtext.json"
            self.assertTrue(auto.is_file())
            again = CvTextService(t.root, svc.backups, t.local)
            self.assertIsNotNone(again.state()["autosave"])
            self.assertEqual(again.draft_count(), 0)
            r = again.restore_autosave()
            self.assertEqual((r["applied"], r["fileChanged"]), (1, False))
            self.assertEqual(again.obj()["items"]["engineer"]["date"]["en"], "Fall 2026")
            again.discard_drafts()
            self.assertFalse(auto.exists())
            # the Flask app: op / review / save, and the drafts count toward the close prompt
            state = EditorState(t.root, t.local, "tok", 5510, 5501)
            app = create_app(state)
            app.testing = True
            c = app.test_client()
            h = {"Host": "127.0.0.1:5510", "X-Editor-Token": "tok"}
            r = c.post("/api/cvtext/op", headers=h, json={"op": "set", "path": ["items", "engineer", "role", "es"], "value": "Ingeniera"})
            self.assertEqual(r.status_code, 200, r.get_json())
            j = r.get_json()
            self.assertEqual((j["ok"], j["draftCount"], j["touched"]), (True, 1, ["engineer"]))
            self.assertIn("engineer", j["fits"])
            self.assertEqual(state.draft_count(), 1)
            self.assertEqual(c.post("/api/cvtext/op", headers=h, json={"op": "set", "path": ["items", "engineer", "kind"], "value": "x"}).status_code, 400)
            self.assertEqual(c.post("/api/cvtext/op", headers=h, json={"op": "delete", "id": "nobody"}).status_code, 404)
            self.assertEqual(c.post("/api/cvtext/op", headers=h, json={"op": "bogus"}).status_code, 400)
            r = c.post("/api/cvtext/op", headers=h, json={"op": "add-item", "section": "experience", "kind": "line", "en": "A line", "variant": "resume"})
            self.assertEqual(r.get_json()["result"], {"id": "experience-a-line"})
            self.assertEqual(c.post("/api/cvtext/import", headers=h, json={}).status_code, 409)
            rv = c.get("/api/cvtext/review", headers=h).get_json()
            self.assertEqual(len(rv["changes"]), 2)
            self.assertFalse(rv["ok"])  # the new line has no Spanish text yet
            c.post("/api/cvtext/op", headers=h, json={"op": "delete", "id": "experience-a-line"})
            r = c.post("/api/cvtext/save", headers=h, json={})
            self.assertEqual(r.status_code, 200, r.get_json())
            self.assertEqual(state.draft_count(), 0)
            self.assertEqual(state.cvtext.obj()["items"]["engineer"]["role"]["es"], "Ingeniera")


@unittest.skipUnless(MASTERS_PRESENT, "CV masters are not on this machine")
class RealMastersTests(unittest.TestCase):
    def test_fit_meter_agrees_with_the_document_check(self):
        """Every entry slot of every real master: the meter (built from the content) measures what fit.check_doc measures on the file."""
        content_path = REPO_ROOT / "staging/cv-content/content.json"
        if not content_path.is_file():
            self.skipTest("no content set imported yet")
        tmp = Path(tempfile.mkdtemp())
        svc = CvTextService(REPO_ROOT, Backups(REPO_ROOT, tmp / "b"), tmp)
        fits = svc.state()["fits"]
        checked = 0
        for m in masters.MASTERS:
            info = docxread.read(masters.docx_path(REPO_ROOT, m))
            lines = {l.index: l for l in fit.check_doc(info)}
            for slot in svc.slots[m.file]:
                if slot["kind"] != "entry":
                    continue
                got = fits[slot["id"]][m.variant][m.lang]
                self.assertAlmostEqual(got["left_pt"], lines[slot["para"]].left_pt, delta=0.05, msg=f"{m.file} {slot['id']}")
                checked += 1
        self.assertGreater(checked, 60)
        self.assertEqual([p for p in svc.master_plans(svc.obj()) if p["changed"] or p["removed"]], [])

    def test_all_six_round_trip_losslessly(self):
        docs = {v: {lang: importer.read_master(masters.docx_path(REPO_ROOT, masters.BY_ID[f"{v}-{lang}"])) for lang in ("en", "es")} for v in importer.VARIANTS}
        content, slots, report = importer.merge(docs)
        self.assertGreater(len(content["items"]), 30)
        self.assertEqual(report["unpaired"]["full"], [])
        self.assertEqual(report["unpaired"]["professional"], [])
        self.assertEqual(len(report["unpaired"]["resume"]), 1)  # the ES résumé lacks the IEL line
        tmp = Path(tempfile.mkdtemp())
        for langs in docs.values():
            for doc in langs.values():
                out = renderer.force_render(doc, slots[doc.path.name], content, tmp / doc.path.name)
                self.assertEqual(importer.compare(doc.path, out), [], doc.path.name)
        self.assertEqual(report["formatting"], [])


if __name__ == "__main__":
    unittest.main()
