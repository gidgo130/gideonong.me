"""Phase 3: transcript inputs (lossless JSON), course-title rows, validation,
drafts / review / save, parse and build jobs, publish.

Runs on a temp copy of the real scripts/transcript/*.json files (they hold
nothing private). The real builder is run once (docx only, into a temp dir);
the real parser needs a TU PDF, so the parse job is exercised with a stand-in.
"""

import json
import os
import shutil
import time
import unittest
from pathlib import Path

from _helpers import REPO_ROOT, TempRepo
from core import validate
from core.backups import Backups
from core.jobs import JobRunner
from core.jsonfile import JsonFile, changes, flatten
from core.transcript import paths
from core.transcript.profile import validate_adjustments, validate_profile
from core.transcript.service import TranscriptService, summarize_build
from core.transcript.titles import rows, set_field, validate_titles

SCRIPT_SRC = REPO_ROOT / paths.SCRIPT_DIR
INPUTS_PRESENT = all((SCRIPT_SRC / f).is_file() for f in paths.FILES.values())


def wait(svc: TranscriptService, seconds: float = 120.0) -> dict:
    deadline = time.monotonic() + seconds
    while svc.busy() and time.monotonic() < deadline:
        time.sleep(0.05)
    return svc.job_json()


class TranscriptRepo:
    """TempRepo + a copy of scripts/transcript/ (JSON files and scripts), no output."""

    def __init__(self, t: TempRepo):
        self.t = t
        self.root = t.root
        dst = self.root / paths.SCRIPT_DIR
        dst.mkdir(parents=True, exist_ok=True)
        for f in list(paths.FILES.values()) + [paths.PARSER, paths.BUILDER]:
            src = SCRIPT_SRC / f
            if src.is_file():
                shutil.copy2(src, dst / f)
        self.backups = Backups(self.root, t.local / "backups")
        self.svc = TranscriptService(self.root, t.local, self.backups, JobRunner())

    def path(self, name: str) -> Path:
        return self.root / paths.rel(name)

    def built(self, lang: str, stamp: str, text: str = "Unofficial Academic Record") -> Path:
        from test_cv import make_pdf

        p = make_pdf(self.root / paths.BUILT_DIR / f"{lang} Gideon Ong Transcript {stamp}.pdf", [[text]])
        later = self.svc.inputs_mtime() + 5
        os.utime(p, (later, later))
        return p


@unittest.skipUnless(INPUTS_PRESENT, "scripts/transcript/*.json not found")
class JsonFileTests(unittest.TestCase):
    def test_real_inputs_round_trip_byte_for_byte(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            for name in paths.FILES:
                d = JsonFile(r.root, paths.rel(name))
                self.assertIsNone(d.read_only, name)
                self.assertEqual(d.render(d.obj), d.raw)
                self.assertEqual((d.newline, d.trailing_newline, d.indent, d.bom), ("\n", False, 2, False), name)

    def test_other_layouts_are_detected_or_refused(self):
        with TempRepo() as t:
            p = t.root / "a.json"
            p.write_bytes(b'\xef\xbb\xbf{\r\n  "a": 1,\r\n  "b": [\r\n    "x"\r\n  ]\r\n}\r\n')
            d = JsonFile(t.root, "a.json")
            self.assertIsNone(d.read_only)
            self.assertEqual((d.newline, d.trailing_newline, d.bom), ("\r\n", True, True))
            d.obj["a"] = 2
            self.assertEqual(d.render(d.obj), b'\xef\xbb\xbf{\r\n  "a": 2,\r\n  "b": [\r\n    "x"\r\n  ]\r\n}\r\n')
            p.write_bytes(b'{"a": 1,\n    "b": 2}')  # not the dumps layout
            d = JsonFile(t.root, "a.json")
            self.assertIn("line 1", d.read_only)
            self.assertIn("read-only", d.read_only)

    def test_changes_and_one_line_diff(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            d = JsonFile(r.root, paths.rel("titles"))
            draft = d.fresh_copy()
            code = next(k for k, v in draft.items() if "sections" not in v)
            draft[code]["es"] = draft[code]["es"] + "!"
            ch = changes(d.obj, draft)
            self.assertEqual([(c["path"], c["kind"]) for c in ch], [([code, "es"], "changed")])
            diff = d.diff(draft)
            self.assertEqual(sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")), 1)
            self.assertEqual(sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")), 1)
            self.assertEqual(flatten({"a": [], "b": {"c": 1}}), {("a",): [], ("b", "c"): 1})


@unittest.skipUnless(INPUTS_PRESENT, "scripts/transcript/*.json not found")
class TitlesTests(unittest.TestCase):
    def test_rows_join_transcript_data(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            st = r.svc.state_json()
            rs = st["titles"]
            self.assertGreaterEqual(len(rs), 58)
            self.assertEqual([x for x in rs if x["missing"]], [])
            self.assertTrue(all(x["onTranscript"] for x in rs))
            sections = [x for x in rs if x["section"]]
            self.assertTrue(sections and all(x["code"] in ("ES 4863", "ME 4863") for x in sections))
            self.assertTrue(all(x["terms"] for x in rs))
            self.assertTrue(st["titlesSorted"])
            self.assertEqual(st["data"]["gpa"], "4.00")

    def test_missing_code_and_sorted_insert(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            data = json.loads(r.path("data").read_text(encoding="utf-8"))
            data["blocks"][-1]["courses"].append({"code": "ZZ 1001", "transcript_title": "Made Up", "credits": 3, "grade": "", "points": 0.0})
            data["blocks"][-1]["courses"].append({"code": "AA 1001", "transcript_title": "Also Made Up", "credits": 3, "grade": "", "points": 0.0})
            r.path("data").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            r.svc.load()
            missing = [x for x in r.svc.state_json()["titles"] if x["missing"]]
            self.assertEqual({x["code"] for x in missing}, {"ZZ 1001", "AA 1001"})
            self.assertEqual([i.code for i in r.svc.draft_issues()["titles"] if i.level == "error"], ["missing-title", "missing-title"])
            r.svc.set_title("AA 1001", "", "en", "Alpha")
            self.assertEqual(list(r.svc.drafts["titles"])[0], "AA 1001")  # inserted first, keys stay sorted
            r.svc.set_title("AA 1001", "", "es", "Alfa")
            r.svc.set_title("ZZ 1001", "", "en", "Zed")
            g = r.svc.gates()["titles"]
            self.assertFalse(g.ok())  # ZZ 1001 still has no ES title
            self.assertEqual([i.key for i in g.blocking], ["ZZ 1001"])
            r.svc.set_title("ZZ 1001", "", "es", "Zed")  # ES = EN → warning only
            g = r.svc.gates()["titles"]
            self.assertTrue(g.ok())
            self.assertIn("same", [i.code for i in g.warnings if i.key == "ZZ 1001"])
            self.assertIn("unverified", [i.code for i in g.warnings if i.key == "AA 1001"])
            res = r.svc.save()
            self.assertTrue(res["ok"], res)
            titles = json.loads(r.path("titles").read_text(encoding="utf-8"))
            self.assertEqual(list(titles)[0], "AA 1001")
            self.assertEqual(list(titles)[-1], "ZZ 1001")
            self.assertEqual(titles["AA 1001"], {"en": "Alpha", "es": "Alfa", "source": "", "verified": False})
            self.assertEqual(r.svc.draft_count(), 0)

    def test_set_field_rules(self):
        titles = {"ES 4863": {"sections": {"ST: A": {"en": "A", "es": "A", "source": "", "verified": False}}}, "ME 1": {"en": "x", "es": "y", "source": "", "verified": True}}
        with self.assertRaises(ValueError):
            set_field(titles, "ES 4863", "", "en", "plain")
        with self.assertRaises(ValueError):
            set_field(titles, "ME 1", "ST: B", "en", "section on a plain code")
        set_field(titles, "ES 4863", "ST: B", "en", "B")
        self.assertEqual(titles["ES 4863"]["sections"]["ST: B"]["en"], "B")
        set_field(titles, "ME 1", "", "verified", 0)
        self.assertIs(titles["ME 1"]["verified"], False)
        with self.assertRaises(KeyError):
            set_field(titles, "ME 1", "", "bogus", "x")
        data = {"blocks": [{"kind": "term", "season": "Fall", "year": 2026, "courses": [{"code": "ES 4863", "transcript_title": "ST: C"}]}]}
        rs = rows(titles, data)
        self.assertEqual([(x["code"], x["section"], x["missing"]) for x in rs if x["missing"]], [("ES 4863", "ST: C", True)])
        # ST: B has no ES title yet (empty), ST: C is on the transcript with no entry (missing)
        self.assertEqual([(i.code, i.key) for i in validate_titles(titles, data) if i.level == "error"], [("empty", "ES 4863|ST: B"), ("missing-title", "ES 4863|ST: C")])


class ValidationTests(unittest.TestCase):
    def test_profile(self):
        good = {"name": "N", "contact": "c", "en": {"university": "U", "program": "P", "majors": ["A"], "minors": ["B"], "expected_graduation": "May 2029"},
                "es": {"university": "U", "program": "P", "majors": ["A"], "minors": ["B"], "expected_graduation": "mayo de 2029"}}
        self.assertEqual(validate_profile(good), [])
        bad = json.loads(json.dumps(good))
        bad["name"] = " "
        bad["en"]["majors"] = []
        bad["es"]["minors"] = ["", "x"]
        bad["es"]["program"] = "TODO fix"
        codes = sorted((i.code, i.key) for i in validate_profile(bad) if i.level == "error")
        self.assertEqual(codes, [("empty", "en.majors"), ("empty", "es.minors"), ("empty", "name"), ("todo", "es.program")])
        self.assertEqual(sorted(i.key for i in validate_profile(bad) if i.level == "warning"), ["majors", "minors"])

    def test_adjustments(self):
        data = {"blocks": [{"kind": "exam", "source": "AP", "courses": [{"code": "PHYS 2053"}]}, {"kind": "term", "season": "Fall", "year": 2024, "courses": [{"code": "ME 1"}]}]}
        good = {"add": [{"block": "AP", "after": "PHYS 2053", "course": {"code": "PHYS 2051", "transcript_title": "", "credits": 1, "grade": "P", "points": 0.0}, "reason": "AP"}]}
        self.assertEqual(validate_adjustments(good, data), [])
        bad = {"add": [
            {"block": "Nope", "after": "ZZ", "course": {"code": "PHYS 2053", "credits": 7, "grade": "Z"}, "reason": ""},
            {"block": "Fall 2024", "after": "ZZ", "course": {"code": "X 1", "credits": 3, "grade": "A"}, "reason": "r"},
            {"block": "Fall 2024", "course": {"code": "X 1", "credits": True, "grade": ""}, "reason": "r"},
        ]}
        got = sorted((i.level, i.code, i.key) for i in validate_adjustments(bad, data))
        self.assertEqual(got, sorted([
            ("error", "on-transcript", "add[0] PHYS 2053"), ("error", "block", "add[0] PHYS 2053"), ("error", "credits", "add[0] PHYS 2053"),
            ("error", "grade", "add[0] PHYS 2053"), ("warning", "reason", "add[0] PHYS 2053"),
            ("warning", "after", "add[1] X 1"),
            ("error", "duplicate", "add[2] X 1"), ("error", "credits", "add[2] X 1"),
        ]))
        self.assertEqual(validate_adjustments({"_comment": "x"}, data), [])


@unittest.skipUnless(INPUTS_PRESENT, "scripts/transcript/*.json not found")
class ServiceTests(unittest.TestCase):
    def test_drafts_review_save_and_conflict(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            before = r.path("profile").read_bytes()
            r.svc.set_draft("profile", ["en", "expected_graduation"], "May 2030")
            self.assertEqual(r.svc.draft_count(), 1)
            self.assertTrue(r.svc.autosave_path.is_file())
            rev = r.svc.review()
            self.assertEqual([f["file"] for f in rev["files"]], ["profile"])
            self.assertIn("May 2029", rev["files"][0]["changes"][0]["text"])
            self.assertTrue(rev["ok"])
            # a draft equal to disk disappears
            r.svc.set_draft("profile", ["en", "expected_graduation"], "May 2029")
            self.assertEqual(r.svc.draft_count(), 0)
            self.assertFalse(r.svc.autosave_path.exists())
            r.svc.set_draft("profile", ["en", "expected_graduation"], "May 2030")
            # changed on disk → refused, draft kept; reload then save
            r.path("profile").write_bytes(before.replace(b'"name": "Gideon A. Ong"', b'"name": "Gideon Ong"'))
            res = r.svc.save()
            self.assertEqual(res["error"], "changed-on-disk")
            self.assertEqual(r.svc.draft_count(), 1)
            r.svc.load()
            self.assertEqual(r.svc.draft_count(), 1)  # the draft edit survived the reload …
            res = r.svc.save()
            self.assertTrue(res["ok"], res)
            after = r.path("profile").read_bytes()
            self.assertIn(b'"expected_graduation": "May 2030"', after)
            self.assertIn(b'"name": "Gideon Ong"', after)  # … and so did the change made on disk
            self.assertFalse(after.endswith(b"\n"))
            self.assertEqual(r.backups.read_file(res["backup"], paths.rel("profile")), before.replace(b'"name": "Gideon A. Ong"', b'"name": "Gideon Ong"'))
            # autosave offered on the next start
            r.svc.set_draft("profile", ["contact"], "x")
            svc2 = TranscriptService(r.root, t.local, r.backups, JobRunner())
            self.assertEqual(svc2.state_json()["autosave"]["files"], ["profile"])
            self.assertEqual(svc2.restore_autosave()["applied"], 1)
            self.assertEqual(svc2.draft_count(), 1)

    def test_blocking_errors_refuse_save(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            r.svc.set_draft("adjustments", ["add", 0, "course", "credits"], 9)
            res = r.svc.save()
            self.assertEqual(res["error"], "blocked")
            self.assertEqual([i["code"] for i in res["gates"]["adjustments"]["blocking"]], ["credits"])
            r.svc.set_draft("adjustments", ["add", 0], None, delete=True)
            self.assertTrue(r.svc.save()["ok"])
            self.assertEqual(len(json.loads(r.path("adjustments").read_text(encoding="utf-8"))["add"]), 1)

    def test_parse_is_restricted_and_backs_up(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            with self.assertRaises(ValueError):
                r.svc.start_parse("../secret.pdf")
            with self.assertRaises(ValueError):
                r.svc.start_parse("nope.pdf")
            raw = r.svc.raw_dir() / "Ong_Gideon_Transcript_20260914.pdf"
            raw.write_bytes(b"%PDF-fake")
            self.assertEqual([p["name"] for p in r.svc.raw_pdfs()], [raw.name])
            # stand-in parser: rewrites transcript-data.json with a marker
            (r.root / paths.SCRIPT_DIR / paths.PARSER).write_text(
                "import sys, json\nd = json.load(open('transcript-data.json', encoding='utf-8'))\nd['parsed_on'] = '2099-01-01'\n"
                "json.dump(d, open(sys.argv[3], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)\nprint('parsed', sys.argv[1])\n",
                encoding="utf-8",
            )
            before = r.path("data").read_bytes()
            r.svc.start_parse(raw.name)
            j = wait(r.svc, 60)
            self.assertFalse(j["running"], j)
            self.assertIsNone(j["error"], j)
            self.assertEqual(j["result"]["exit"], 0)
            self.assertTrue(j["result"]["changed"])
            self.assertIn('+  "parsed_on": "2099-01-01"', j["result"]["diff"])
            self.assertTrue(any(line.endswith("parsed " + str(raw)) for line in j["log"]))
            self.assertEqual(r.backups.read_file(j["result"]["backup"], paths.rel("data")), before)
            self.assertEqual(r.svc.state_json()["data"]["parsedOn"], "2099-01-01")

    def test_real_build_docx_only(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            # one unverified title on the temp copy, so the test does not depend on the real
            # file having any (all titles were verified on 2026-09-29)
            titles = json.loads(r.path("titles").read_text(encoding="utf-8"))
            data = json.loads(r.path("data").read_text(encoding="utf-8"))
            on_transcript = [c["code"] for b in data["blocks"] for c in b.get("courses", [])]
            first = next(k for k in on_transcript if isinstance(titles.get(k), dict) and "verified" in titles[k])
            titles[first]["verified"] = False
            r.path("titles").write_text(json.dumps(titles, indent=2, ensure_ascii=False), encoding="utf-8")
            r.svc.load()
            r.svc.start_build(strict=False, stamp=None, pdf=False)
            j = wait(r.svc, 180)
            self.assertFalse(j["running"])
            self.assertIsNone(j["error"], j)
            res = j["result"]
            self.assertTrue(res["ok"], j["log"][-5:])
            self.assertEqual(len(res["wrote"]), 2)
            self.assertEqual(sorted(p.name for p in (r.root / paths.OUTPUT_DIR).glob("*.docx")), ["en Gideon Ong Transcript 20260914.docx", "es Gideon Ong Transcript 20260914.docx"])
            self.assertGreater(len(res["unverified"]), 0)
            self.assertEqual(len(res["adjustments"]), 2)
            self.assertEqual(res["stopped"], [])
            self.assertEqual([d["name"] for d in r.svc.state_json()["docx"]][:1], ["en Gideon Ong Transcript 20260914.docx"])
            # --strict stops on the unverified titles
            r.svc.start_build(strict=True, stamp="20260101", pdf=False)
            j = wait(r.svc, 180)
            self.assertFalse(j["result"]["ok"])
            self.assertTrue(any("unverified" in s for s in j["result"]["stopped"]), j["result"])
            # a draft blocks the build (it reads the files on disk)
            r.svc.set_draft("profile", ["contact"], "x")
            with self.assertRaises(RuntimeError):
                r.svc.start_build()
            with self.assertRaises(ValueError):
                r.svc.discard_drafts() or r.svc.start_build(stamp="2026-01-01")

    def test_publish_plan_and_apply(self):
        with TempRepo() as t:
            r = TranscriptRepo(t)
            p = r.svc.publish_plan()
            self.assertFalse(p["ok"])
            self.assertEqual({e["code"] for e in p["errors"]}, {"no-pdf"})
            r.built("en", "20260914")
            p = r.svc.publish_plan()
            self.assertEqual([e["id"] for e in p["errors"]], ["transcript-es"])
            r.built("es", "20260914")
            old = r.root / "assets/pdfs/transcript/en Gideon Ong Transcript 20250101.pdf"
            old.write_bytes(b"%PDF-old")
            p = r.svc.publish_plan()
            self.assertTrue(p["ok"], p["errors"])
            self.assertEqual(p["date"], "20260914")
            by = {i["id"]: i for i in p["items"]}
            self.assertEqual(by["transcript-en"]["target"], "assets/pdfs/transcript/en Gideon Ong Transcript 20260914.pdf")
            self.assertEqual(by["transcript-en"]["moves"], ["assets/pdfs/transcript/en Gideon Ong Transcript 20250101.pdf"])
            self.assertTrue(any(w["code"] == "no-blocklist" for w in p["warnings"]))
            res = r.svc.publish_apply()
            self.assertTrue(res["ok"], res)
            self.assertEqual(sorted(res["added"]), ["assets/pdfs/transcript/en Gideon Ong Transcript 20260914.pdf", "assets/pdfs/transcript/es Gideon Ong Transcript 20260914.pdf"])
            self.assertEqual(res["moved"], [str(old.relative_to(r.root)).replace("\\", "/")])
            self.assertFalse(old.exists())
            self.assertEqual(r.backups.read_file(res["backup"], "assets/pdfs/transcript/en Gideon Ong Transcript 20250101.pdf"), b"%PDF-old")
            if res["manifest"]["ran"] and res["manifest"]["ok"]:
                text = (r.root / "js" / "docs-data.js").read_text(encoding="utf-8")
                self.assertIn('transcript: { en: "assets/pdfs/transcript/en Gideon Ong Transcript 20260914.pdf", es: "assets/pdfs/transcript/es Gideon Ong Transcript 20260914.pdf" }', text)
            # gates: stale build, mixed stamps, blocklist hit
            time.sleep(0.01)
            r.svc.set_draft("profile", ["contact"], "changed")
            self.assertTrue(r.svc.save()["ok"])
            later = os.stat(r.path("profile")).st_mtime + 5
            os.utime(r.path("profile"), (later, later))
            self.assertIn("stale", [e["code"] for e in r.svc.publish_plan()["errors"]])
            r.built("en", "20260915")
            r.built("es", "20260914")
            self.assertIn("stamps", [e["code"] for e in r.svc.publish_plan()["errors"]])
            r.built("es", "20260915", text="Record for student 123456")
            r.built("en", "20260915")
            bl = r.root / "staging" / "editor-private" / "blocklist.txt"
            bl.parent.mkdir(parents=True, exist_ok=True)
            bl.write_text("123456 | student id\n", encoding="utf-8")
            p = r.svc.publish_plan()
            self.assertEqual([(e["id"], e["code"]) for e in p["errors"]], [("transcript-es", "blocklist")])
            self.assertEqual(r.svc.publish_apply()["error"], "blocked")

    def test_summarize_build(self):
        s = summarize_build(["12:00:00  unverified title: ME 1123 X  [transcript]", "12:00:01  ADJUSTMENT: added PHYS 2051", "12:00:02  wrote C:/x.docx",
                             "12:00:03  STOPPED:", "12:00:03    no title for XX 1000", "12:00:03    Fall 2026 term_totals: TU vs computed", "12:00:04  exit code 1"])
        self.assertEqual(s, {"unverified": ["ME 1123 X  [transcript]"], "adjustments": ["added PHYS 2051"], "wrote": ["C:/x.docx"],
                             "stopped": ["no title for XX 1000", "Fall 2026 term_totals: TU vs computed"]})


if __name__ == "__main__":
    unittest.main()
