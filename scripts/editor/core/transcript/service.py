"""What the Transcript page talks to. Owned by app.EditorState as `transcript`.

  * the three editable JSON inputs as lossless documents with per-file drafts
    (autosaved), review (change list + unified diff per file) and save
    (backup, atomic write, changed-on-disk refusal);
  * transcript-data.json read-only, for the course-title join and the GPA;
  * the raw TU PDFs in references/transcripts/ and the parse job;
  * the build job (make_transcript.py, docx → scripts/transcript/output/, PDFs →
    staging/transcript-out/) with its output streamed live and summarized;
  * the publish plan / apply into assets/pdfs/transcript/.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .. import validate
from ..backups import Backups, atomic_write
from ..jobs import JobRunner, python_exe, run_subprocess
from ..jsonfile import JsonFile, changes, delete_path, set_path
from ..review import unified_diff
from ..cv import publish as publish_mod
from ..cv import scans
from ..cv.masters import BLOCKLIST_PATH
from . import paths
from .profile import POINTS, validate_adjustments, validate_profile
from .titles import keys_sorted, rows, set_field, validate_titles

log = logging.getLogger("editor.transcript")

_UNVERIFIED_RE = re.compile(r"^unverified title: (.*)$")
_ADJUST_RE = re.compile(r"^ADJUSTMENT: (.*)$")
_WROTE_RE = re.compile(r"^wrote (.*)$")
_BUILT_RE = re.compile(r"^(en|es) Gideon Ong Transcript (\d{8})\.pdf$")


class TranscriptService:
    def __init__(self, repo_root: Path, local_dir: Path, backups: Backups, runner: Optional[JobRunner] = None):
        self.repo_root = Path(repo_root)
        self.local_dir = Path(local_dir)
        self.backups = backups
        self.runner = runner or JobRunner()
        self.docs: dict[str, Optional[JsonFile]] = {}
        self.load_errors: dict[str, str] = {}
        self.drafts: dict[str, Any] = {}  # file id → whole draft object
        self.autosave_path = self.local_dir / "drafts" / "transcript.json"
        self.pending_autosave: Optional[dict] = self._read_autosave()
        self.opener: Callable[[str], object] = getattr(os, "startfile", lambda p: None)
        self.script_dir = self.repo_root / paths.SCRIPT_DIR
        self.load()

    # ------------------------------------------------------------- loading
    def load(self) -> None:
        old = {n: d.obj for n, d in self.docs.items() if d is not None}
        for name in paths.FILES:
            try:
                self.docs[name] = JsonFile(self.repo_root, paths.rel(name))
                self.load_errors.pop(name, None)
            except (OSError, ValueError) as e:
                self.docs[name] = None
                self.load_errors[name] = f"{paths.rel(name)}: {e}"
                log.error("cannot load %s: %s", name, e)
        # Drafts are re-applied edit by edit onto the freshly read file, so a change
        # somebody else made on disk meanwhile survives (as on the Site text tab).
        for name in list(self.drafts):
            d = self.docs.get(name)
            if d is None:
                self.drafts.pop(name)
                continue
            if name in old:
                rebased = d.fresh_copy()
                for c in changes(old[name], self.drafts[name]):
                    try:
                        if c["kind"] == "removed":
                            delete_path(rebased, c["path"])
                        else:
                            set_path(rebased, c["path"], c["new"])
                    except (KeyError, IndexError, ValueError, TypeError):
                        log.warning("draft edit at %s no longer applies to %s", c["path"], name)
                self.drafts[name] = rebased
            if self.drafts[name] == d.obj:
                self.drafts.pop(name)
        self._write_autosave()

    def obj(self, name: str) -> Any:
        """The live object for a file: its draft when one exists, else what is on disk."""
        if name in self.drafts:
            return self.drafts[name]
        d = self.docs.get(name)
        return d.obj if d else None

    def draft_count(self) -> int:
        return sum(len(changes(self.docs[n].obj, self.drafts[n])) for n in self.drafts if self.docs.get(n))

    # ------------------------------------------------------------- drafts
    def set_draft(self, name: str, path: list, value: Any = None, delete: bool = False) -> None:
        if name not in paths.EDITABLE:
            raise KeyError(name)
        d = self.docs.get(name)
        if d is None:
            raise RuntimeError(self.load_errors.get(name, "file not loaded"))
        if d.read_only:
            raise RuntimeError(d.read_only)
        draft = self.drafts.get(name)
        if draft is None:
            draft = d.fresh_copy()
        if delete:
            delete_path(draft, path)
        else:
            set_path(draft, path, value)
        if name == "titles" and keys_sorted(d.obj) and list(draft) != sorted(draft):
            items = sorted(draft.items())
            draft.clear()
            draft.update(items)
        if draft == d.obj:
            self.drafts.pop(name, None)
        else:
            self.drafts[name] = draft
        self._write_autosave()

    def set_title(self, code: str, section: str, field: str, value: Any) -> None:
        d = self.docs.get("titles")
        if d is None:
            raise RuntimeError(self.load_errors.get("titles", "file not loaded"))
        if d.read_only:
            raise RuntimeError(d.read_only)
        draft = self.drafts.get("titles") or d.fresh_copy()
        set_field(draft, code, section, field, value, keep_sorted=keys_sorted(d.obj))
        if draft == d.obj:
            self.drafts.pop("titles", None)
        else:
            self.drafts["titles"] = draft
        self._write_autosave()

    def discard_drafts(self) -> None:
        self.drafts.clear()
        self._write_autosave()

    # ------------------------------------------------------------- autosave
    def _read_autosave(self) -> Optional[dict]:
        try:
            if self.autosave_path.is_file():
                j = json.loads(self.autosave_path.read_text(encoding="utf-8"))
                if isinstance(j, dict) and j.get("drafts"):
                    return j
        except (OSError, ValueError) as e:
            log.warning("transcript autosave unreadable: %s", e)
        return None

    def _write_autosave(self) -> None:
        try:
            if not self.drafts:
                if self.autosave_path.exists():
                    self.autosave_path.unlink()
                return
            self.autosave_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "saved": datetime.now().isoformat(timespec="seconds"),
                "baseSha256": {n: self.docs[n].sha256 for n in self.drafts if self.docs.get(n)},
                "drafts": self.drafts,
            }
            atomic_write(self.autosave_path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
        except OSError as e:
            log.warning("transcript autosave failed: %s", e)

    def restore_autosave(self) -> dict:
        pend, self.pending_autosave = self.pending_autosave, None
        if not pend:
            return {"applied": 0, "fileChanged": False}
        applied, changed = 0, False
        for name, draft in pend.get("drafts", {}).items():
            d = self.docs.get(name)
            if d is None or name not in paths.EDITABLE or d.read_only:
                continue
            if pend.get("baseSha256", {}).get(name) not in (None, d.sha256):
                changed = True
            if draft != d.obj:
                self.drafts[name] = draft
                applied += 1
        self._write_autosave()
        return {"applied": applied, "fileChanged": changed}

    def discard_autosave(self) -> None:
        self.pending_autosave = None
        if not self.drafts and self.autosave_path.exists():
            try:
                self.autosave_path.unlink()
            except OSError:
                pass

    # ------------------------------------------------------------- validation
    def _issues(self, objs: dict) -> dict[str, list[validate.Issue]]:
        data = objs.get("data")
        return {
            "titles": validate_titles(objs["titles"], data, objs.get("adjustments")) if objs.get("titles") is not None else [],
            "profile": validate_profile(objs["profile"]) if objs.get("profile") is not None else [],
            "adjustments": validate_adjustments(objs["adjustments"], data) if objs.get("adjustments") is not None else [],
        }

    def baseline_issues(self) -> dict:
        return self._issues({n: (self.docs[n].obj if self.docs.get(n) else None) for n in paths.FILES})

    def draft_issues(self) -> dict:
        return self._issues({n: self.obj(n) for n in paths.FILES})

    def gates(self) -> dict[str, validate.SaveGate]:
        base, draft = self.baseline_issues(), self.draft_issues()
        out = {}
        for name in paths.EDITABLE:
            touched = {self._issue_key(name, c["path"]) for c in self._changes(name)}
            out[name] = validate.blocking(base[name], draft[name], touched | self._touched_ids(name))
        return out

    def _touched_ids(self, name: str) -> set:
        """Issue keys that a draft touches: title row ids, profile fields, adjustment indexes."""
        keys = set()
        for c in self._changes(name):
            p = c["path"]
            if name == "titles" and p:
                code = p[0]
                keys.add(f"{code}|{p[2]}" if len(p) > 2 and p[1] == "sections" else code)
            elif name == "profile" and p:
                keys.add(".".join(str(x) for x in p[:2]) if p[0] in ("en", "es") else str(p[0]))
            elif name == "adjustments" and len(p) >= 2 and p[0] == "add":
                keys.add(f"add[{p[1]}]")
        return keys

    @staticmethod
    def _issue_key(name: str, path: list) -> str:
        return ".".join(str(x) for x in path)

    def _changes(self, name: str) -> list[dict]:
        d = self.docs.get(name)
        if d is None or name not in self.drafts:
            return []
        return changes(d.obj, self.drafts[name])

    # ------------------------------------------------------------- review / save
    def review(self) -> dict:
        files = []
        any_blocked, disk_changed = False, False
        gates = self.gates()
        for name in paths.EDITABLE:
            d = self.docs.get(name)
            if d is None or name not in self.drafts:
                continue
            g = gates[name]
            any_blocked = any_blocked or not g.ok()
            dc = d.disk_changed()
            disk_changed = disk_changed or dc
            files.append(
                {
                    "file": name,
                    "path": d.rel_path,
                    "changes": [dict(c, text=self._change_text(name, c)) for c in self._changes(name)],
                    "diff": d.diff(self.drafts[name]),
                    "gate": g.to_json(),
                    "diskChanged": dc,
                }
            )
        return {"files": files, "ok": not any_blocked and not disk_changed, "noop": not files}

    def _change_text(self, name: str, c: dict) -> str:
        where = " › ".join(str(p) for p in c["path"])
        label = {"titles": "Course titles", "profile": "Profile", "adjustments": "Adjustments"}[name]
        if c["kind"] == "added":
            return f"{label} › {where}: added {_q(c['new'])}"
        if c["kind"] == "removed":
            return f"{label} › {where}: removed {_q(c['old'])}"
        return f"{label} › {where}: {_q(c['old'])} → {_q(c['new'])}"

    def save(self) -> dict:
        if not self.drafts:
            return {"ok": True, "noop": True, "message": "Nothing to save."}
        for name in self.drafts:
            d = self.docs.get(name)
            if d is None:
                return {"ok": False, "error": "read-only", "message": self.load_errors.get(name, "file not loaded")}
            if d.disk_changed():
                return {"ok": False, "error": "changed-on-disk", "message": f"{d.rel_path} changed on disk since it was loaded. Reload and re-apply your edits."}
        gates = self.gates()
        blocked = {n: g for n, g in gates.items() if n in self.drafts and not g.ok()}
        if blocked:
            return {"ok": False, "error": "blocked", "message": "Fix the blocking errors first.", "gates": {n: g.to_json() for n, g in blocked.items()}}
        rels = [self.docs[n].rel_path for n in self.drafts]
        bset = self.backups.create(rels, "before saving transcript inputs")
        written = []
        for name in list(self.drafts):
            d = self.docs[name]
            try:
                atomic_write(d.path, d.render(self.drafts[name]))
            except OSError as e:
                log.warning("write failed for %s: %s", d.rel_path, e)
                return {
                    "ok": False,
                    "error": "write-failed",
                    "message": f"{d.rel_path} could not be written — it is probably open in another program. Close it and retry. Files already written: {', '.join(written) or 'none'}.",
                    "backup": bset.id,
                }
            written.append(d.rel_path)
            self.drafts.pop(name)
        self._write_autosave()
        self.load()
        log.info("saved %s (backup %s)", written, bset.id)
        return {"ok": True, "backup": bset.id, "written": written, "message": f"Saved {', '.join(written)}. Backup set {bset.id}."}

    # ------------------------------------------------------------- raw PDFs + jobs
    def raw_dir(self) -> Path:
        d = self.repo_root / paths.RAW_DIR
        d.mkdir(parents=True, exist_ok=True)
        return d

    def raw_pdfs(self) -> list[dict]:
        out = []
        for p in sorted(self.raw_dir().glob("*.pdf")):
            st = p.stat()
            out.append({"name": p.name, "mtime": st.st_mtime, "size": st.st_size})
        return out

    def busy(self) -> bool:
        return self.runner.busy()

    def job_json(self) -> Optional[dict]:
        return self.runner.json()

    def start_parse(self, pdf_name: str) -> dict:
        if not pdf_name or "/" in pdf_name or "\\" in pdf_name or not pdf_name.lower().endswith(".pdf"):
            raise ValueError("pick a PDF from references/transcripts/")
        pdf = (self.raw_dir() / pdf_name).resolve()
        if not pdf.is_file() or not pdf.is_relative_to(self.raw_dir().resolve()):
            raise ValueError(f"{pdf_name} is not in {paths.RAW_DIR}/")
        if "data" in self.drafts:
            raise RuntimeError("discard the transcript-data draft first")
        rel = paths.rel("data")
        before = self.docs["data"].raw if self.docs.get("data") else b""

        def run(runner: JobRunner):
            bset = self.backups.create([rel], f"before parsing {pdf_name}")
            runner.log_line(f"backed up {rel} (set {bset.id})")
            code = run_subprocess([python_exe(), paths.PARSER, str(pdf), "-o", paths.FILES["data"]], self.script_dir, runner.log_line)
            self.load()
            after = self.docs["data"].raw if self.docs.get("data") else b""
            diff = unified_diff(before, after, rel) if after != before else ""
            return {"exit": code, "backup": bset.id, "diff": diff, "changed": after != before}

        return self.runner.start("parse", run, pdf=pdf_name)

    def start_build(self, strict: bool = False, stamp: Optional[str] = None, pdf: bool = False) -> dict:
        if self.drafts:
            raise RuntimeError("save or discard the drafts first — the build reads the files on disk")
        if stamp and not publish_mod.valid_date(stamp):
            raise ValueError(f"“{stamp}” is not a date (YYYYMMDD)")
        cmd = [python_exe(), paths.BUILDER, "--docx-dir", str(self.repo_root / paths.OUTPUT_DIR)]
        if strict:
            cmd.append("--strict")
        if stamp:
            cmd += ["--date", stamp]
        if pdf:
            cmd += ["--pdf", "--pdf-dir", str(self.repo_root / paths.BUILT_DIR)]

        def run(runner: JobRunner):
            code = run_subprocess(cmd, self.script_dir, runner.log_line, timeout=900)
            summary = summarize_build(runner.json()["log"])
            summary["exit"] = code
            summary["ok"] = code == 0
            return summary

        return self.runner.start("build", run, strict=strict, date=stamp, pdf=pdf)

    # ------------------------------------------------------------- status / publish
    def inputs_mtime(self) -> float:
        latest = 0.0
        for rel in [paths.rel(n) for n in paths.FILES] + [f"{paths.SCRIPT_DIR}/{paths.BUILDER}"]:
            try:
                latest = max(latest, os.stat(self.repo_root / rel).st_mtime)
            except OSError:
                pass
        return latest

    def built(self) -> dict:
        """The newest built PDF per language in staging/transcript-out/."""
        d = self.repo_root / paths.BUILT_DIR
        out = {"en": None, "es": None}
        if d.is_dir():
            for p in d.iterdir():
                m = _BUILT_RE.match(p.name)
                if not m:
                    continue
                lang, stamp = m.group(1), m.group(2)
                cur = out[lang]
                if cur is None or stamp > cur["stamp"]:
                    st = p.stat()
                    out[lang] = {"name": p.name, "stamp": stamp, "mtime": st.st_mtime, "size": st.st_size, "path": str(p)}
        return out

    def docx_outputs(self) -> list[dict]:
        d = self.repo_root / paths.OUTPUT_DIR
        if not d.is_dir():
            return []
        return [{"name": p.name, "mtime": p.stat().st_mtime} for p in sorted(d.glob("*.docx"))]

    def publish_docs(self) -> list[dict]:
        built = self.built()
        inputs = self.inputs_mtime()
        terms, bl_warning = scans.load_blocklist(self.repo_root / BLOCKLIST_PATH)
        cv_gpa = self.cv_gpa_warning()
        docs = []
        for lang in ("en", "es"):
            b = built[lang]
            errors, warnings = [], []
            if b is not None:
                if b["mtime"] < inputs:
                    errors.append({"code": "stale", "message": "built before the last change to the transcript inputs — build again (with PDFs)"})
                try:
                    from ..cv import pdfcheck

                    pdf = pdfcheck.read_pdf(Path(b["path"]))
                    b["pages"] = pdf.pages
                    for h in scans.blocklist_hits(pdf.text, terms, scans.ALLOWED_IN_PUBLISHED_PDFS):
                        errors.append({"code": "blocklist", "message": f"blocked term “{h['term']}” ({h['reason'] or 'no reason given'}): {h['context']}"})
                except Exception as e:  # unreadable PDF
                    errors.append({"code": "pdf", "message": f"could not read the PDF: {e}"})
                if bl_warning:
                    warnings.append({"code": "no-blocklist", "message": bl_warning})
                if cv_gpa:
                    warnings.append({"code": "gpa", "message": cv_gpa})
            docs.append(
                {
                    "id": f"transcript-{lang}",
                    "title": f"Transcript ({lang.upper()})",
                    "source": Path(b["path"]) if b else None,
                    "type": paths.PUB_TYPE,
                    "lang": lang,
                    "label": paths.LABEL,
                    "stamp": b["stamp"] if b else None,
                    "errors": errors,
                    "warnings": warnings,
                }
            )
        stamps = {d["stamp"] for d in docs if d["stamp"]}
        if len(stamps) > 1:
            for d in docs:
                d["errors"].append({"code": "stamps", "message": "EN and ES were built with different dates — build both again"})
        return docs

    def publish_plan(self) -> dict:
        docs = self.publish_docs()
        stamp = next((d["stamp"] for d in docs if d["stamp"]), None)
        p = publish_mod.plan_docs(self.repo_root, docs, stamp)
        for e in p["errors"]:
            if e.get("code") == "no-pdf":
                e["message"] = e["message"].replace("no PDF to publish yet", "not built yet — Build with PDFs first")
        return p

    def publish_apply(self) -> dict:
        if self.busy():
            return {"ok": False, "error": "busy", "message": "wait for the running job to finish"}
        p = self.publish_plan()
        if not p["ok"]:
            return {"ok": False, "error": "blocked", "message": "Fix the blocking errors first.", "plan": p}
        sources = {d["id"]: d["source"] for d in self.publish_docs()}
        try:
            result = publish_mod.apply_docs(self.repo_root, self.backups, p, sources, f"before publishing transcript PDFs ({p['date']})")
        except OSError as e:
            log.warning("transcript publish failed: %s", e)
            return {"ok": False, "error": "write-failed", "message": f"Publishing stopped: {e}. Files already copied stay; see the backup set."}
        log.info("published transcript %s (backup %s)", result["added"] + result["overwritten"], result["backup"])
        return {"ok": True, "plan": p, **result}

    # ------------------------------------------------------------- GPA cross-check
    def computed_gpa(self) -> Optional[str]:
        """Cumulative GPA the record prints (transcript-data + adjustments, as make_transcript.py totals it)."""
        data = self.obj("data")
        if not data:
            return None
        pts = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        hours = points = 0.0
        courses = [c for b in data.get("blocks", []) for c in b.get("courses", [])]
        for a in (self.obj("adjustments") or {}).get("add", []):
            if isinstance(a, dict) and isinstance(a.get("course"), dict):
                courses.append(a["course"])
        for c in courses:
            g = c.get("grade")
            if g in pts:
                hours += c.get("credits", 0)
                points += pts[g] * c.get("credits", 0)
        return f"{points / hours:.2f}" if hours else None

    def cv_gpa_warning(self) -> Optional[str]:
        """The CV masters say 'GPA: x'; warn when the record's cumulative GPA disagrees."""
        mine = self.computed_gpa()
        if mine is None:
            return None
        try:
            from ..cv import docxread, masters
        except ImportError:  # pragma: no cover
            return None
        found = []
        for m in masters.MASTERS:
            p = masters.docx_path(self.repo_root, m)
            if not p.is_file():
                continue
            try:
                doc = docxread.read(p)
            except Exception:
                continue
            for para in doc.paragraphs:
                mm = re.search(r"GPA\)?:\s*(\d(?:[.,]\d+)?)", para.text)
                if mm:
                    found.append((m.title, mm.group(1).replace(",", ".")))
                    break
        off = [f"{title} says {val}" for title, val in found if abs(float(val) - float(mine)) > 0.005]
        if off:
            return f"the record's cumulative GPA is {mine} but " + "; ".join(off)
        return None

    def open_folder(self, which: str) -> str:
        d = {"raw": self.raw_dir(), "output": self.repo_root / paths.OUTPUT_DIR, "built": self.repo_root / paths.BUILT_DIR}.get(which)
        if d is None:
            raise ValueError("which must be raw, output or built")
        d.mkdir(parents=True, exist_ok=True)
        self.opener(str(d))
        return str(d)

    # ------------------------------------------------------------- state
    def state_json(self) -> dict:
        data = self.obj("data")
        titles = self.obj("titles")
        gates = self.gates()
        issues = self.draft_issues()
        files = {}
        for name in paths.FILES:
            d = self.docs.get(name)
            files[name] = {
                "path": paths.rel(name),
                "loaded": d is not None,
                "readOnly": d.read_only if d else self.load_errors.get(name),
                "sha256": d.sha256 if d else None,
                "hasDraft": name in self.drafts,
                "diskChanged": d.disk_changed() if d else False,
            }
        built = self.built()
        return {
            "files": files,
            "titles": rows(titles, data or {"blocks": []}, self.obj("adjustments")) if titles is not None else [],
            "titlesSorted": keys_sorted(self.docs["titles"].obj) if self.docs.get("titles") else True,
            "profile": self.obj("profile"),
            "adjustments": self.obj("adjustments"),
            "data": {
                "printed": (data or {}).get("transcript_printed"),
                "parsedOn": (data or {}).get("parsed_on"),
                "blocks": [
                    {"label": b.get("source") or f"{b.get('season')} {b.get('year')}", "kind": b.get("kind"), "codes": [c["code"] for c in b.get("courses", [])]}
                    for b in (data or {}).get("blocks", [])
                ],
                "gpa": self.computed_gpa(),
            },
            "issues": {n: [i.to_json() for i in v] for n, v in issues.items()},
            "gates": {n: g.to_json() for n, g in gates.items()},
            "draftCount": self.draft_count(),
            "autosave": (
                {"saved": self.pending_autosave.get("saved"), "files": list(self.pending_autosave.get("drafts", {}))}
                if self.pending_autosave
                else None
            ),
            "rawDir": paths.RAW_DIR,
            "rawPdfs": self.raw_pdfs(),
            "outputDir": paths.OUTPUT_DIR,
            "docx": self.docx_outputs(),
            "builtDir": paths.BUILT_DIR,
            "built": built,
            "rebuildNeeded": any(b and b["mtime"] < self.inputs_mtime() for b in built.values()),
            "job": self.job_json(),
            "cvGpaWarning": self.cv_gpa_warning(),
        }


def summarize_build(log_lines: list[str]) -> dict:
    """Pull the builder's own messages out of the streamed log."""
    unverified, adjustments, wrote, stopped = [], [], [], []
    in_stop = False
    for raw in log_lines:
        line = raw.split("  ", 1)[1] if "  " in raw else raw  # drop the timestamp
        m = _UNVERIFIED_RE.match(line)
        if m:
            unverified.append(m.group(1))
            continue
        m = _ADJUST_RE.match(line)
        if m:
            adjustments.append(m.group(1))
            continue
        m = _WROTE_RE.match(line)
        if m:
            wrote.append(m.group(1))
            continue
        if line.startswith("STOPPED"):
            in_stop = True
            rest = line.partition(":")[2].strip()
            if rest:
                stopped.append(rest)
            continue
        if in_stop and line.startswith("  "):
            stopped.append(line.strip())
        elif in_stop and not line.startswith("  "):
            in_stop = False
    return {"unverified": unverified, "adjustments": adjustments, "wrote": wrote, "stopped": [s for s in stopped if s]}


def _q(v: Any) -> str:
    if v is None:
        return "(missing)"
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", "⏎")
    return "“" + (s if len(s) <= 120 else s[:117] + "…") + "”"
