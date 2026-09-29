"""What the CV page talks to: master discovery, cached checks, the one
background export job, and publish. Owned by app.EditorState as `cv`.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from ..backups import Backups
from ..jobs import JobRunner
from . import docxread, export, fit, masters, pdfcheck, publish, scans

log = logging.getLogger("editor.cv")


class CvService:
    def __init__(self, repo_root: Path, backups: Backups, runner: Optional[JobRunner] = None):
        self.repo_root = Path(repo_root)
        self.backups = backups
        self.lock = threading.RLock()
        self.runner = runner or JobRunner()
        self._docs: dict[str, tuple[float, docxread.DocInfo]] = {}  # id → (docx mtime, parsed)
        self._checks: dict[str, tuple[tuple, dict]] = {}  # id → (cache key, result)
        # how "open the output folder" is done (tests replace it)
        self.opener: Callable[[str], object] = getattr(os, "startfile", lambda p: None)

    # ------------------------------------------------------------- reading
    def _doc(self, m: masters.Master) -> Optional[docxread.DocInfo]:
        path = masters.docx_path(self.repo_root, m)
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            self._docs.pop(m.id, None)
            return None
        cached = self._docs.get(m.id)
        if cached and cached[0] == mtime:
            return cached[1]
        doc = docxread.read(path)
        self._docs[m.id] = (mtime, doc)
        return doc

    def _blocklist_mtime(self) -> float:
        try:
            return os.stat(self.repo_root / masters.BLOCKLIST_PATH).st_mtime
        except OSError:
            return 0.0

    def _cache_key(self, info: dict, pair_info: dict) -> tuple:
        return (
            info["mtime"],
            info["size"],
            info["pdf"]["mtime"],
            info["pdf"]["size"],
            pair_info.get("mtime"),
            pair_info.get("size"),
            self._blocklist_mtime(),
        )

    # ------------------------------------------------------------- checks
    def check(self, ids: Optional[list[str]] = None, force: bool = False) -> dict:
        with self.lock:
            infos = {i["id"]: i for i in masters.all_info(self.repo_root)}
            terms, bl_warning = scans.load_blocklist(self.repo_root / masters.BLOCKLIST_PATH)
            font_problem = fit.fonts_available()
            out = {}
            for m in masters.MASTERS:
                if ids and m.id not in ids:
                    continue
                info = infos[m.id]
                key = self._cache_key(info, infos[m.pair_id])
                cached = self._checks.get(m.id)
                if cached and cached[0] == key and not force:
                    out[m.id] = cached[1]
                    continue
                try:
                    result = self._check_one(m, info, infos[m.pair_id], terms, bl_warning, font_problem)
                except Exception as e:  # a corrupt file must not take the page down
                    log.exception("check failed for %s", m.id)
                    result = {"id": m.id, "errors": [{"code": "check-failed", "message": f"check failed: {e}"}], "warnings": []}
                self._checks[m.id] = (key, result)
                out[m.id] = result
            return out

    def _check_one(self, m, info, pair_info, terms, bl_warning, font_problem) -> dict:
        errors: list[dict] = []
        warnings: list[dict] = []
        res: dict = {"id": m.id, "errors": errors, "warnings": warnings, "fit": None, "pdf": None, "parity": [], "voice": []}
        if not info["exists"]:
            errors.append({"code": "no-master", "message": f"{m.file} is missing from {masters.MASTERS_DIR}/"})
            return res
        doc = self._doc(m)
        # -- fit estimate on the docx
        if font_problem:
            warnings.append({"code": "fonts", "message": font_problem + " — the one-line estimate is off; the PDF check still runs"})
        else:
            lines = fit.check_doc(doc)
            res["fit"] = {"lines": [l.to_json() for l in lines], "summary": fit.summary(lines)}
            for l in lines:
                if l.status == "overflow":
                    warnings.append({"code": "fit-overflow", "message": f"“{l.text}” + date is {-l.left_pt:.1f} pt too wide for one line (estimate; the PDF decides)"})
                elif l.status == "tight":
                    warnings.append({"code": "fit-tight", "message": f"“{l.text}” has only {l.left_pt:.1f} pt ({l.left_pct:.1f}%) left before its date wraps"})
        odd_fonts = sorted({r.font for p in doc.paragraphs for r in p.runs if r.font and r.font.lower() != "georgia"})
        if odd_fonts:
            warnings.append({"code": "font", "message": "runs not in Georgia: " + ", ".join(odd_fonts)})
        res["voice"] = scans.voice_hits(doc)
        for v in res["voice"]:
            warnings.append({"code": "voice", "message": f"voice words ({', '.join(v['words'])}) in “{v['text'][:70]}…”"})
        # -- parity with the other language
        if pair_info["exists"]:
            pair = masters.BY_ID[m.pair_id]
            try:
                pair_doc = self._doc(pair)
                en_doc, es_doc = (doc, pair_doc) if m.lang == "en" else (pair_doc, doc)
                res["parity"] = scans.parity(en_doc, es_doc)
            except Exception as e:  # pragma: no cover
                res["parity"] = [f"parity check failed: {e}"]
            for n in res["parity"]:
                warnings.append({"code": "parity", "message": f"EN/ES: {n}"})
        # -- the exported PDF
        if not info["pdf"]["exists"]:
            res["pdf"] = {"exists": False}
            return res
        pdf = pdfcheck.read_pdf(masters.pdf_path(self.repo_root, m))
        entry_lines = pdfcheck.entry_lines_check([p.text for p in doc.entries()], pdf)
        missing = pdfcheck.coverage_check([p.text for p in doc.nonempty()], pdf)
        hits = scans.blocklist_hits(pdf.text, terms, scans.ALLOWED_IN_PUBLISHED_PDFS)
        res["pdf"] = {
            "exists": True,
            "stale": info["pdf"]["stale"],
            "pages": pdf.pages,
            "entryLines": entry_lines,
            "missing": missing,
            "blocklist": hits,
        }
        if info["pdf"]["stale"]:
            errors.append({"code": "stale", "message": "the PDF is older than the master — export again"})
        if missing:
            errors.append({"code": "stale-text", "message": f"{len(missing)} paragraph(s) of the master are not in the PDF — export again (first: “{missing[0][:60]}…”)"})
        for e in entry_lines:
            if not e["ok"]:
                errors.append({"code": "wrapped", "message": f"“{e['text']}” does not sit on one line in the PDF — shorten it in Word"})
        if m.one_page and pdf.pages != 1:
            errors.append({"code": "pages", "message": f"the résumé is {pdf.pages} pages; it must be exactly one"})
        for h in hits:
            errors.append({"code": "blocklist", "message": f"blocked term “{h['term']}” ({h['reason'] or 'no reason given'}): {h['context']}"})
        if bl_warning:
            warnings.append({"code": "no-blocklist", "message": bl_warning})
        return res

    # ------------------------------------------------------------- state
    def state(self) -> dict:
        with self.lock:
            infos = masters.all_info(self.repo_root)
            terms, bl_warning = scans.load_blocklist(self.repo_root / masters.BLOCKLIST_PATH)
            return {
                "mastersDir": masters.MASTERS_DIR,
                "outDir": masters.OUT_DIR,
                "blocklist": {"path": masters.BLOCKLIST_PATH, "terms": len(terms), "warning": bl_warning},
                "fonts": fit.fonts_available(),
                "masters": infos,
                "job": self.job_json(),
                "today": publish.today(),
            }

    # ------------------------------------------------------------- export job
    def job_json(self) -> Optional[dict]:
        return self.runner.json()

    def busy(self) -> bool:
        return self.runner.busy()

    def start_export(self, ids: Optional[list[str]] = None) -> dict:
        with self.lock:
            if self.busy():
                raise RuntimeError("a job is already running")
            wanted = [m for m in masters.MASTERS if (not ids or m.id in ids)]
            todo, refused = [], {}
            for m in wanted:
                reason = export.check_exportable(masters.docx_path(self.repo_root, m))
                if reason:
                    refused[m.id] = reason
                else:
                    todo.append(m)
            if not todo:
                raise RuntimeError("; ".join(refused.values()) or "nothing to export")
            return self.runner.start(
                "export",
                lambda runner: self._run_export(runner, todo),
                ids=[m.id for m in todo],
                refused=refused,
                done=[],
                failed={},
                current=None,
            )

    def _run_export(self, runner: JobRunner, todo: list[masters.Master]) -> dict:
        for m in todo:
            runner.update(current=m.id)
            runner.log_line(f"{m.title}: exporting {m.file}")
            try:
                export.export_pdf(masters.docx_path(self.repo_root, m), masters.pdf_path(self.repo_root, m), runner.log_line)
                with runner.lock:
                    runner.job["done"].append(m.id)
                with self.lock:
                    self._checks.pop(m.id, None)
                runner.log_line(f"{m.title}: done")
            except export.ExportError as e:
                with runner.lock:
                    runner.job["failed"][m.id] = str(e)
                runner.log_line(f"{m.title}: FAILED — {e}")
            except Exception as e:  # pragma: no cover
                log.exception("export crashed")
                with runner.lock:
                    runner.job["failed"][m.id] = f"unexpected error: {e}"
                runner.log_line(f"{m.title}: FAILED — unexpected error: {e}")
        runner.update(current=None)
        runner.log_line("export finished")
        return {"done": list(runner.json()["done"]), "failed": dict(runner.json()["failed"])}

    # ------------------------------------------------------------- publish
    def _check_summaries(self) -> dict:
        checks = self.check()
        return {mid: {"errors": c["errors"], "warnings": c["warnings"]} for mid, c in checks.items()}

    def publish_plan(self, stamp: Optional[str] = None) -> dict:
        with self.lock:
            return publish.plan(self.repo_root, self._check_summaries(), stamp)

    def publish_apply(self, stamp: Optional[str] = None) -> dict:
        with self.lock:
            if self.busy():
                return {"ok": False, "error": "busy", "message": "wait for the export to finish"}
            p = publish.plan(self.repo_root, self._check_summaries(), stamp)
            if not p["ok"]:
                return {"ok": False, "error": "blocked", "message": "Fix the blocking errors first.", "plan": p}
            try:
                result = publish.apply(self.repo_root, self.backups, p)
            except OSError as e:
                log.warning("publish failed: %s", e)
                return {"ok": False, "error": "write-failed", "message": f"Publishing stopped: {e}. Files already copied stay; see the backup set."}
            self._checks.clear()
            log.info("published %s (backup %s)", result["added"] + result["overwritten"], result["backup"])
            return {"ok": True, "plan": p, **result}

    def open_out(self) -> str:
        d = self.repo_root / masters.OUT_DIR
        d.mkdir(parents=True, exist_ok=True)
        self.opener(str(d))
        return str(d)
