"""CV text (Phase 4). Owned by app.EditorState as `cvtext`.

4a: import the six masters into staging/cv-content/ once the losslessness proof
passes on every one of them.
4b: the editor over that content set — one draft (a whole-object copy of
content.json, like the transcript tab), autosaved to .local/drafts/cvtext.json;
text edits and structural operations (core/cv/content.py); validation and the
fit meter (core/cv/cvcheck.py); review = change list in words + content.json
diff + what rendering would do to each master (renderer.plan_master); save =
backup + atomic write of content.json only.
4c: drift — paragraphs edited in Word since the last import / apply (their text
hash differs from content.hashes), each to be pulled into the content or
discarded — and apply: render every master in memory (renderer.render_master),
self-check each, then back up content.json + the six masters, write the
changed masters atomically, rebuild the slot maps and hashes from the files as
written, and save content.json. A master open in Word blocks the apply.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .. import validate
from ..backups import Backups, atomic_write
from ..jsonfile import JsonFile, changes, delete_path, set_path
from ..transcript import paths as tpaths
from . import content as C
from . import cvcheck, docxread, fit, importer, masters, renderer, scans, wordroute

log = logging.getLogger("editor.cvtext")

CONTENT_DIR = "staging/cv-content"
CONTENT_FILE = f"{CONTENT_DIR}/content.json"
SLOTS_DIR = f"{CONTENT_DIR}/slots"
REPORT_FILE = f"{CONTENT_DIR}/import-report.json"
PROFILE_FILE = tpaths.rel("profile")
ROUTES = ("python", "word")
ROUTE_LABELS = {"python": "python", "word": "Word"}


def _dump(obj) -> bytes:
    return json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")


class CvTextService:
    def __init__(self, repo_root: Path, backups: Backups, local_dir: Optional[Path] = None, gpa: Optional[Callable[[], Optional[str]]] = None):
        self.repo_root = Path(repo_root)
        self.backups = backups
        self.local_dir = Path(local_dir) if local_dir else None
        self.gpa = gpa or (lambda: None)
        self.doc: Optional[JsonFile] = None
        self.load_error: Optional[str] = None
        self.slots: dict[str, list] = {}
        self.draft: Optional[dict] = None
        self.discarded: set = set()  # (master file, slot id) Word edits the next apply may overwrite
        self._docs: dict[str, tuple[float, docxread.DocInfo]] = {}
        self._profile: tuple[float, Optional[dict]] = (0.0, None)
        self.autosave_path = (self.local_dir / "drafts" / "cvtext.json") if self.local_dir else None
        self.last_apply_path = (self.local_dir / "cvtext-last-apply.json") if self.local_dir else None
        self.pending_autosave: Optional[dict] = self._read_autosave()
        self.load()

    # ------------------------------------------------------------- last apply record
    def last_apply(self) -> Optional[dict]:
        if not self.last_apply_path or not self.last_apply_path.is_file():
            return None
        try:
            j = json.loads(self.last_apply_path.read_text(encoding="utf-8"))
            return j if isinstance(j, dict) and j.get("route") in ROUTES else None
        except (OSError, ValueError):
            return None

    def _record_apply(self, rec: dict) -> None:
        if not self.last_apply_path:
            return
        try:
            self.last_apply_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(self.last_apply_path, _dump(rec))
        except OSError as e:
            log.warning("could not record the apply: %s", e)

    # ------------------------------------------------------------- paths / loading
    def content_path(self) -> Path:
        return self.repo_root / CONTENT_FILE

    def load(self) -> None:
        """Read content.json and the slot maps; re-apply an existing draft edit by edit."""
        old = self.doc.obj if self.doc else None
        try:
            self.doc = JsonFile(self.repo_root, CONTENT_FILE) if self.content_path().is_file() else None
            self.load_error = None
        except (OSError, ValueError) as e:
            self.doc = None
            self.load_error = f"{CONTENT_FILE}: {e}"
            log.error("content.json unreadable: %s", e)
        self.slots = {}
        d = self.repo_root / SLOTS_DIR
        if d.is_dir():
            for p in sorted(d.glob("*.json")):
                try:
                    self.slots[p.name[: -len(".json")]] = json.loads(p.read_text(encoding="utf-8"))
                except (OSError, ValueError) as e:
                    log.error("slot map %s unreadable: %s", p.name, e)
        if self.draft is not None:
            if self.doc is None:
                self.draft = None
            elif old is not None:
                rebased = self.doc.fresh_copy()
                for c in changes(old, self.draft):
                    try:
                        if c["kind"] == "removed":
                            delete_path(rebased, c["path"])
                        else:
                            set_path(rebased, c["path"], c["new"])
                    except (KeyError, IndexError, ValueError, TypeError):
                        log.warning("draft edit at %s no longer applies", c["path"])
                self.draft = rebased
            if self.draft is not None and self.draft == self.doc.obj:
                self.draft = None
        self._write_autosave()

    def load_content(self) -> Optional[dict]:
        return self.doc.obj if self.doc else None

    def load_report(self) -> Optional[dict]:
        p = self.repo_root / REPORT_FILE
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return None

    def obj(self) -> Optional[dict]:
        """The live content: the draft when one exists, else the file."""
        if self.draft is not None:
            return self.draft
        return self.doc.obj if self.doc else None

    def _doc_info(self, master_file: str) -> Optional[docxread.DocInfo]:
        path = self.repo_root / masters.MASTERS_DIR / master_file
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            self._docs.pop(master_file, None)
            return None
        cached = self._docs.get(master_file)
        if cached and cached[0] == mtime:
            return cached[1]
        try:
            info = docxread.read(path)
        except Exception as e:  # a corrupt master must not take the page down
            log.warning("cannot read %s for the fit meter: %s", master_file, e)
            return None
        self._docs[master_file] = (mtime, info)
        return info

    def profile(self) -> Optional[dict]:
        p = self.repo_root / PROFILE_FILE
        try:
            mtime = os.stat(p).st_mtime
        except OSError:
            return None
        if self._profile[0] != mtime:
            try:
                self._profile = (mtime, json.loads(p.read_text(encoding="utf-8")))
            except (OSError, ValueError) as e:
                log.warning("profile.json unreadable: %s", e)
                self._profile = (mtime, None)
        return self._profile[1]

    # ------------------------------------------------------------- drafts
    def draft_count(self) -> int:
        if self.draft is None or self.doc is None:
            return 0
        return len(changes(self.doc.obj, self.draft))

    def _working(self) -> dict:
        if self.doc is None:
            raise RuntimeError(self.load_error or "no content set — import the masters first")
        if self.doc.read_only:
            raise RuntimeError(self.doc.read_only)
        return self.draft if self.draft is not None else self.doc.fresh_copy()

    def _commit(self, draft: dict) -> None:
        self.draft = None if draft == self.doc.obj else draft
        self._write_autosave()

    def set_text(self, path: list, value: Any) -> None:
        d = self._working()
        C.set_text(d, path, value)
        self._commit(d)

    def include(self, id: str, variant: str, on: bool, current: Optional[str] = None) -> None:
        d = self._working()
        C.set_include(d, id, variant, on, current)
        self._commit(d)

    def move(self, id: str, variant: str, delta: int) -> None:
        d = self._working()
        C.move(d, id, variant, delta)
        self._commit(d)

    def add_item(self, section_id: str, kind: str, en_text: str, variant: str) -> str:
        d = self._working()
        iid = C.add_item(d, section_id, kind, en_text, variant)
        self._commit(d)
        return iid

    def add_child(self, item_id: str, kind: str, variant: str) -> str:
        d = self._working()
        cid = C.add_child(d, item_id, kind, variant)
        self._commit(d)
        return cid

    def delete(self, id: str) -> None:
        d = self._working()
        C.delete(d, id)
        self._commit(d)

    def duplicate(self, id: str, variant: str) -> str:
        d = self._working()
        new_id = C.duplicate(d, id, variant)
        self._commit(d)
        return new_id

    def add_section(self, en: str, es: str, variant: str) -> str:
        d = self._working()
        sid = C.add_section(d, en, es, variant)
        self._commit(d)
        return sid

    def delete_section(self, section_id: str) -> None:
        d = self._working()
        C.delete_section(d, section_id)
        self._commit(d)

    def discard_drafts(self) -> None:
        self.draft = None
        self.discarded.clear()
        self._write_autosave()

    # ------------------------------------------------------------- autosave
    def _read_autosave(self) -> Optional[dict]:
        if not self.autosave_path:
            return None
        try:
            if self.autosave_path.is_file():
                j = json.loads(self.autosave_path.read_text(encoding="utf-8"))
                if isinstance(j, dict) and isinstance(j.get("draft"), dict):
                    return j
        except (OSError, ValueError) as e:
            log.warning("cvtext autosave unreadable: %s", e)
        return None

    def _write_autosave(self) -> None:
        if not self.autosave_path:
            return
        try:
            if self.draft is None:
                if self.autosave_path.exists() and not self.pending_autosave:
                    self.autosave_path.unlink()
                return
            self.autosave_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"saved": datetime.now().isoformat(timespec="seconds"), "baseSha256": self.doc.sha256 if self.doc else None, "draft": self.draft}
            atomic_write(self.autosave_path, _dump(data))
        except OSError as e:
            log.warning("cvtext autosave failed: %s", e)

    def restore_autosave(self) -> dict:
        pend, self.pending_autosave = self.pending_autosave, None
        if not pend or self.doc is None or self.doc.read_only:
            self._write_autosave()
            return {"applied": 0, "fileChanged": False}
        draft = pend.get("draft")
        changed = pend.get("baseSha256") not in (None, self.doc.sha256)
        applied = 0
        if isinstance(draft, dict) and draft.get("version") == self.doc.obj.get("version") and draft != self.doc.obj:
            self.draft = draft
            applied = 1
        self._write_autosave()
        return {"applied": applied, "fileChanged": changed}

    def discard_autosave(self) -> None:
        self.pending_autosave = None
        if self.draft is None and self.autosave_path and self.autosave_path.exists():
            try:
                self.autosave_path.unlink()
            except OSError:
                pass

    # ------------------------------------------------------------- checks
    def _terms(self) -> list[scans.Term]:
        return scans.load_blocklist(self.repo_root / masters.BLOCKLIST_PATH)[0]

    def fits(self, content: dict) -> dict:
        if fit.fonts_available():
            return {}
        docs = {name: self._doc_info(name) for langs in content["masters"].values() for name in langs.values()}
        return cvcheck.all_fits(content, self.slots, docs)

    def fit_warning(self, content: Optional[dict]) -> Optional[str]:
        problem = fit.fonts_available()
        if problem:
            return problem + " — the fit meter is off"
        if content:
            missing = [name for langs in content["masters"].values() for name in langs.values() if self._doc_info(name) is None]
            if missing:
                return "no fit meter for " + ", ".join(missing) + " (master missing or unreadable)"
        return None

    def _issues(self, content: Optional[dict], fits: Optional[dict] = None) -> list[validate.Issue]:
        if content is None:
            return []
        return cvcheck.check(content, self.profile(), self.gpa(), self._terms(), fits if fits is not None else self.fits(content))

    def touched(self) -> set:
        """Issue keys the draft touches (item / child ids, header parts, section ids)."""
        if self.draft is None or self.doc is None:
            return set()
        keys = set()
        for c in changes(self.doc.obj, self.draft):
            keys.add(_issue_key(self.doc.obj, self.draft, c["path"]))
        return {k for k in keys if k}

    def gate(self, live: Optional[list[validate.Issue]] = None) -> validate.SaveGate:
        """Only errors the draft introduces or touches block (validate.blocking)."""
        if live is None:
            live = self._issues(self.obj())
        base = live if self.draft is None else self._issues(self.doc.obj)
        return validate.blocking(base, live, self.touched())

    def _issue_json(self, content: Optional[dict], issue: validate.Issue) -> dict:
        """Issue + a human label for its key (ids never show on the page)."""
        j = issue.to_json()
        j["label"] = C.label_of(content, issue.key) if content else issue.key
        return j

    def _gate_json(self, content: Optional[dict], gate: validate.SaveGate) -> dict:
        return {
            "ok": gate.ok(),
            "blocking": [self._issue_json(content, i) for i in gate.blocking],
            "preexisting": [self._issue_json(content, i) for i in gate.preexisting],
            "warnings": [self._issue_json(content, i) for i in gate.warnings],
        }

    # ------------------------------------------------------------- review / save
    def review(self) -> dict:
        if self.doc is None:
            return {"readOnly": True, "error": self.load_error or "no content set", "noop": True}
        live = self.obj()
        gate = self.gate()
        dc = self.doc.disk_changed()
        drift = self.drift(live)
        out = {
            "readOnly": False,
            "file": CONTENT_FILE,
            "changes": change_lines(self.doc.obj, live) if self.draft is not None else [],
            "diff": self.doc.diff(live) if self.draft is not None else "",
            "gate": self._gate_json(live, gate),
            "diskChanged": dc,
            "noop": self.draft is None,
            "masters": self.master_plans(live),
            "drift": drift,
            "applyBlocked": self.apply_blockers(live, drift),
            "lastApply": self.last_apply(),
            "wordAvailable": wordroute.word_available(),
        }
        out["ok"] = gate.ok() and not dc and not out["noop"]
        return out

    def master_plans(self, content: dict) -> list[dict]:
        plans = []
        for m in masters.MASTERS:
            slots = self.slots.get(m.file)
            if slots is None or m.file not in {n for langs in content["masters"].values() for n in langs.values()}:
                continue
            p = renderer.plan_master(content, slots, m.file)
            p["title"] = m.title
            plans.append(p)
        return plans

    def save(self) -> dict:
        if self.doc is None:
            return {"ok": False, "error": "read-only", "message": self.load_error or "no content set"}
        if self.draft is None:
            return {"ok": True, "noop": True, "message": "Nothing to save."}
        if self.doc.read_only:
            return {"ok": False, "error": "read-only", "message": self.doc.read_only}
        if self.doc.disk_changed():
            return {"ok": False, "error": "changed-on-disk", "message": f"{CONTENT_FILE} changed on disk since it was loaded. Reload and re-apply your edits."}
        gate = self.gate()
        if not gate.ok():
            return {"ok": False, "error": "blocked", "message": "Fix the blocking errors first.", "gate": self._gate_json(self.draft, gate)}
        new = self.doc.render(self.draft)
        bset = self.backups.create([CONTENT_FILE], "before saving the CV content set")
        try:
            atomic_write(self.doc.path, new)
        except OSError as e:
            log.warning("write failed for %s: %s", CONTENT_FILE, e)
            return {"ok": False, "error": "write-failed", "message": f"{CONTENT_FILE} could not be written — it is probably open in another program. Close it and retry. Nothing was changed and your draft is kept.", "backup": bset.id}
        self.draft = None
        self._write_autosave()
        self.load()
        log.info("saved %s (backup %s)", CONTENT_FILE, bset.id)
        return {"ok": True, "backup": bset.id, "message": f"Saved {CONTENT_FILE}. Backup set {bset.id}. The masters are rewritten by Apply (4c)."}

    # ------------------------------------------------------------- 4c: drift
    def _master_docs(self) -> dict[str, tuple[masters.Master, Path]]:
        return {m.file: (m, masters.docx_path(self.repo_root, m)) for m in masters.MASTERS}

    def drift(self, content: Optional[dict] = None) -> dict:
        """Paragraphs edited in Word since the last import / apply, per master, with their
        resolution; `blocked` lists what stops an apply (structure drift, unresolved paragraphs)."""
        content = content if content is not None else self.obj()
        out: dict = {"masters": [], "blocked": [], "unresolved": 0}
        if content is None:
            out["blocked"].append("no content set — import the masters first")
            return out
        for m, path in self._master_docs().values():
            entry = {"file": m.file, "title": m.title, "structure": None, "paragraphs": []}
            out["masters"].append(entry)
            if not path.is_file():
                entry["structure"] = f"{m.file} is missing from {masters.MASTERS_DIR}/"
                out["blocked"].append(entry["structure"])
                continue
            slot_map = self.slots.get(m.file)
            if slot_map is None:
                entry["structure"] = "no slot map for this master — Import masters again"
                out["blocked"].append(f"{m.title}: {entry['structure']}")
                continue
            try:
                doc = importer.read_master(path)
                live = renderer.live_slots(doc, slot_map)
            except (importer.ImportError_, renderer.StructureDrift) as e:
                entry["structure"] = f"changed in Word beyond text ({e}) — Import masters again to pick it up"
                out["blocked"].append(f"{m.title}: {entry['structure']}")
                continue
            except Exception as e:  # unreadable file
                entry["structure"] = f"cannot be read ({e})"
                out["blocked"].append(f"{m.title}: {entry['structure']}")
                continue
            nodes = importer.structure(doc)
            variant, lang = renderer.master_of(content, m.file)
            hashes = content.get("hashes", {}).get(m.file, {})
            for sl in live:
                if sl["kind"] == "empty":
                    continue
                node = nodes[sl["para"]]
                is_entry = sl["kind"] == "entry"
                word_s = importer.text_string(node.parts, is_entry)
                stored = hashes.get(sl["id"])
                if stored is None or importer.hash_text(word_s) == stored:
                    continue
                content_s = renderer._expected_text(content, sl["id"], variant, lang)
                if content_s == word_s:
                    continue  # pulled, or typed the same thing
                resolved = "discard" if (m.file, sl["id"]) in self.discarded else None
                entry["paragraphs"].append(
                    {
                        "id": sl["id"],
                        "label": C.label_of(content, sl["id"], lang),
                        "kind": sl["kind"],
                        "lang": lang,
                        "wordText": word_s.replace("\t", " ⇥ "),
                        "contentText": content_s.replace("\t", " ⇥ ") if content_s is not None else None,
                        "resolved": resolved,
                    }
                )
                if not resolved:
                    out["unresolved"] += 1
        if out["unresolved"]:
            out["blocked"].append(f"{out['unresolved']} paragraph(s) were edited in Word since the last apply — pull each into the content or discard it")
        return out

    def _word_parts(self, master_file: str, sid: str) -> tuple[dict, bool]:
        """(parts, is_entry) of a slot's paragraph as it is in the master now."""
        m, path = self._master_docs()[master_file]
        slot_map = self.slots.get(master_file)
        if slot_map is None:
            raise KeyError(master_file)
        doc = importer.read_master(path)
        live = renderer.live_slots(doc, slot_map)
        sl = next((s for s in live if s["id"] == sid), None)
        if sl is None:
            raise KeyError(sid)
        node = importer.structure(doc)[sl["para"]]
        return node.parts, sl["kind"] == "entry"

    def pull_drift(self, master_file: str, sid: str) -> None:
        """The content takes the paragraph's text as it is in Word (a normal draft edit)."""
        content = self.obj()
        if content is None:
            raise RuntimeError("no content set")
        variant, lang = renderer.master_of(content, master_file)
        parts, is_entry = self._word_parts(master_file, sid)
        d = self._working()
        if sid.startswith("header."):
            part = sid.split(".", 1)[1]
            path = ["header", "name"] if part == "name" else ["header", "title", variant, lang] if part == "title" else ["header", "contact", lang]
            C.set_text(d, path, parts.get("text", ""))
        elif sid.startswith("section."):
            idx = next((i for i, s in enumerate(d["sections"]) if s["id"] == sid.split(".", 1)[1]), None)
            if idx is None:
                raise KeyError(sid)
            C.set_text(d, ["sections", idx, "heading", lang], parts.get("text", ""))
        else:
            kind, *rest = C.find(d, sid)
            if kind == "item" and is_entry:
                for k in ("role", "org", "date"):
                    C.set_text(d, ["items", sid, k, lang], parts.get(k, ""))
            elif kind == "item":
                C.set_text(d, ["items", sid, "text", lang], parts.get("text", ""))
            else:
                C.set_text(d, ["items", rest[0], "children", sid, "text", lang], parts.get("text", ""))
        self.discarded.discard((master_file, sid))
        self._commit(d)

    def discard_drift(self, master_file: str, sid: str) -> None:
        """Let the next apply overwrite the paragraph as edited in Word."""
        if master_file not in self._master_docs():
            raise KeyError(master_file)
        self.discarded.add((master_file, sid))

    def resolve_all(self, master_file: str, how: str) -> int:
        """pull or discard every unresolved paragraph of one master; returns how many."""
        n = 0
        for entry in self.drift()["masters"]:
            if entry["file"] != master_file:
                continue
            for p in entry["paragraphs"]:
                if p["resolved"]:
                    continue
                if how == "pull":
                    self.pull_drift(master_file, p["id"])
                else:
                    self.discard_drift(master_file, p["id"])
                n += 1
        return n

    # ------------------------------------------------------------- 4c: apply
    def apply_blockers(self, content: dict, drift: Optional[dict] = None) -> list[str]:
        """Everything that stops an apply right now (nothing is rendered here)."""
        reasons: list[str] = []
        if self.doc is None:
            return [self.load_error or "no content set"]
        if self.doc.read_only:
            reasons.append(self.doc.read_only)
        if self.doc.disk_changed():
            reasons.append(f"{CONTENT_FILE} changed on disk since it was loaded — reload first")
        # every error counts here, pre-existing ones too: an empty, TODO or overflowing paragraph
        # must never reach a master (saving content.json is gated more leniently)
        errors = [i for i in self._issues(content) if i.level == "error"]
        if errors:
            first = errors[0]
            reasons.append(f"{len(errors)} error(s) in the content — fix them first (e.g. {C.label_of(content, first.key)}: {first.message})")
        d = drift if drift is not None else self.drift(content)
        reasons += d["blocked"]
        for p in self.master_plans(content):
            if p["changed"] or p["added"] or p["removed"]:
                m, path = self._master_docs()[p["file"]]
                if masters.word_lock_file(path) is not None:
                    reasons.append(f"{m.file} is open in Word — close it in Word first")
        return reasons

    def _render_with(self, route: str, content: dict, m: masters.Master, path: Path, log_line) -> renderer.RenderResult:
        if route == "word":
            return wordroute.render_master(content, self.slots[m.file], path, log_line)
        return renderer.render_master(content, self.slots[m.file], path)

    def apply(self, route: str = "python", log_line=lambda s: None) -> dict:
        """Write the content into the masters (see the module docstring). Nothing is written
        unless every master renders and passes its self-check. `route`: "python" (the renderer)
        or "word" (the same edits through a private Word instance, wordroute.py)."""
        if route not in ROUTES:
            return {"ok": False, "error": "route", "message": f"unknown route {route!r}"}
        if route == "word":
            problem = wordroute.word_available()
            if problem:
                return {"ok": False, "error": "route", "message": f"Apply with Word cannot run: {problem}"}
        other = "Word" if route == "python" else "python"
        content = self.obj()
        if self.doc is None or content is None:
            return {"ok": False, "error": "read-only", "message": self.load_error or "no content set"}
        drift = self.drift(content)
        blockers = self.apply_blockers(content, drift)
        if blockers:
            return {"ok": False, "error": "blocked", "message": "Apply is blocked: " + "; ".join(blockers), "blockers": blockers, "drift": drift}
        content = copy.deepcopy(content)
        results: list[tuple[masters.Master, renderer.RenderResult]] = []
        for m, path in self._master_docs().values():
            try:
                r = self._render_with(route, content, m, path, log_line)
            except renderer.RenderError as e:
                return {"ok": False, "error": "render", "master": m.file, "route": route, "message": f"{m.title} could not be rendered with {ROUTE_LABELS[route]}: {e}. Nothing was written; try Apply with {other}."}
            except Exception as e:  # never half-write
                log.exception("render crashed for %s", m.file)
                return {"ok": False, "error": "render", "master": m.file, "route": route, "message": f"{m.title} could not be rendered with {ROUTE_LABELS[route]}: {type(e).__name__}: {e}. Nothing was written; try Apply with {other}."}
            problems = renderer.self_check(content, m.file, r.data, path, relaxed=(route == "word")) if r.changed else []
            if route == "word" and r.changed:
                tmpf = Path(tempfile.mkdtemp(prefix="cv-parts-")) / m.file
                try:
                    tmpf.write_bytes(r.data)
                    r.report["notes"] = [f"Word re-saved {n}" for n in renderer.parts_changed(path, tmpf)]
                finally:
                    shutil.rmtree(tmpf.parent, ignore_errors=True)
            if problems:
                return {
                    "ok": False,
                    "error": "self-check",
                    "master": m.file,
                    "route": route,
                    "problems": problems,
                    "message": f"{m.title}: the file {ROUTE_LABELS[route]} produced does not read back as the content ({problems[0]}). Nothing was written; try Apply with {other}.",
                }
            results.append((m, r))
        changed = [(m, r) for m, r in results if r.changed]
        if not changed and self.draft is None:
            return {"ok": True, "noop": True, "route": route, "message": "Nothing to apply — every master already matches the content.", "masters": [dict(r.report, file=m.file, title=m.title, written=False) for m, r in results]}
        locks = [m.file for m, r in changed if masters.word_lock_file(masters.docx_path(self.repo_root, m)) is not None]
        if locks:
            return {"ok": False, "error": "open-in-word", "message": "close in Word first: " + ", ".join(locks)}
        rels = [CONTENT_FILE] + [f"{masters.MASTERS_DIR}/{m.file}" for m in masters.MASTERS] + [f"{SLOTS_DIR}/{m.file}.json" for m in masters.MASTERS]
        bset = self.backups.create(rels, "before applying the CV text to the masters")
        written = []
        for m, r in changed:
            try:
                atomic_write(masters.docx_path(self.repo_root, m), r.data)
            except OSError as e:
                log.warning("write failed for %s: %s", m.file, e)
                return {
                    "ok": False,
                    "error": "write-failed",
                    "message": f"{m.file} could not be written ({e}). Already written: {', '.join(written) or 'none'}; content.json not updated. Backup set {bset.id} holds everything as it was.",
                    "backup": bset.id,
                    "written": written,
                }
            written.append(m.file)
        content["hashes"] = {}
        new_slots = {}
        for m, path in self._master_docs().values():
            try:
                sl, hs = renderer.rebuild_slots(content, path)
            except Exception as e:  # the file was just checked; this is a bug, not a user error
                log.exception("slot rebuild failed for %s", m.file)
                return {"ok": False, "error": "rebuild", "message": f"{m.file} was written but its slot map could not be rebuilt ({e}); restore backup set {bset.id} or Import masters again.", "backup": bset.id, "written": written}
            new_slots[m.file] = sl
            content["hashes"][m.file] = hs
        (self.repo_root / SLOTS_DIR).mkdir(parents=True, exist_ok=True)
        for name, sl in new_slots.items():
            atomic_write(self.repo_root / SLOTS_DIR / (name + ".json"), _dump(sl))
        atomic_write(self.doc.path, self.doc.render(content))
        self.draft = None
        self.discarded.clear()
        self._write_autosave()
        self.load()
        summary = [dict(r.report, file=m.file, title=m.title, written=r.changed) for m, r in results]
        rec = {"route": route, "when": datetime.now().isoformat(timespec="seconds"), "backup": bset.id, "written": written, "masters": summary}
        self._record_apply(rec)
        log.info("applied CV text with %s: wrote %s (backup %s)", route, written, bset.id)
        return {"ok": True, "route": route, "backup": bset.id, "written": written, "masters": summary, "message": f"Applied with {ROUTE_LABELS[route]}: {len(written)} master(s) rewritten, content.json saved. Backup set {bset.id}. Next: Export & check."}

    # ------------------------------------------------------------- 4d: cross-check
    def crosscheck(self, log_line=lambda s: None) -> dict:
        """Rerun the last apply through the OTHER route, from the backup set's copies of the
        masters and slot maps against the current content, and compare with the masters on
        disk. Nothing is written."""
        rec = self.last_apply()
        if not rec:
            return {"ok": False, "error": "no-apply", "message": "no apply recorded yet — apply first"}
        other = "word" if rec["route"] == "python" else "python"
        if other == "word":
            problem = wordroute.word_available()
            if problem:
                return {"ok": False, "error": "route", "message": f"the cross-check needs Word: {problem}"}
        bset = self.backups.get(rec["backup"])
        if bset is None:
            return {"ok": False, "error": "no-backup", "message": f"backup set {rec['backup']} of that apply no longer exists — nothing to rerun from"}
        content = self.obj()
        if content is None:
            return {"ok": False, "error": "read-only", "message": self.load_error or "no content set"}
        if self.draft is not None:
            return {"ok": False, "error": "drafts", "message": "save or discard the drafts first — the cross-check compares the content as applied"}
        out = {"ok": True, "route": other, "applied": rec["route"], "backup": rec["backup"], "masters": [], "agree": True}
        tmp = Path(tempfile.mkdtemp(prefix="cv-cross-"))
        try:
            for m, path in self._master_docs().values():
                if m.file not in rec.get("written", []):
                    continue
                entry = {"file": m.file, "title": m.title, "problems": [], "notes": []}
                out["masters"].append(entry)
                master_bytes = self.backups.read_file(rec["backup"], f"{masters.MASTERS_DIR}/{m.file}")
                slots_bytes = self.backups.read_file(rec["backup"], f"{SLOTS_DIR}/{m.file}.json")
                if master_bytes is None or slots_bytes is None:
                    entry["problems"].append("the backup set holds no copy of this master or its slot map")
                    out["agree"] = False
                    continue
                src = tmp / m.file
                src.write_bytes(master_bytes)
                try:
                    slot_map = json.loads(slots_bytes.decode("utf-8"))
                    r = wordroute.render_master(content, slot_map, src, log_line) if other == "word" else renderer.render_master(content, slot_map, src)
                except (renderer.RenderError, ValueError) as e:
                    entry["problems"].append(f"the {ROUTE_LABELS[other]} route could not render it: {e}")
                    out["agree"] = False
                    continue
                rendered = tmp / ("rendered-" + m.file)
                rendered.write_bytes(r.data)
                entry["problems"] = renderer.compare_layout(rendered, path)
                entry["notes"] = [f"package part {n} differs" for n in renderer.parts_changed(rendered, path)]
                if entry["problems"]:
                    out["agree"] = False
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        out["message"] = (
            f"The {ROUTE_LABELS[other]} route produces the same text and formatting as the {ROUTE_LABELS[rec['route']]} apply on every master."
            if out["agree"]
            else f"The {ROUTE_LABELS[other]} route differs from the {ROUTE_LABELS[rec['route']]} apply — see the paragraphs listed."
        )
        return out

    # ------------------------------------------------------------- state
    def state(self) -> dict:
        content = self.obj()
        p = self.content_path()
        summary = None
        if self.doc is not None:
            items = self.doc.obj.get("items", {})
            summary = {
                "items": len(items),
                "entries": sum(1 for i in items.values() if i.get("kind") == "entry"),
                "children": sum(len(i.get("children", {})) for i in items.values()),
                "sections": len(self.doc.obj.get("sections", [])),
                "shared": sum(1 for i in items.values() if sum(i.get("include", {}).values()) > 1),
                "modified": os.stat(p).st_mtime,
            }
        fits = self.fits(content) if content else {}
        issues = self._issues(content, fits)
        gate = self.gate(issues) if self.doc else None
        return {
            "contentPath": CONTENT_FILE,
            "content": summary,
            "masters": masters.all_info(self.repo_root),
            "lastImport": self.load_report(),
            "loaded": self.doc is not None,
            "loadError": self.load_error,
            "readOnly": self.doc.read_only if self.doc else (self.load_error or "no content set"),
            "diskChanged": self.doc.disk_changed() if self.doc else False,
            "data": content,
            "listing": {v: C.listing(content, v) for v in importer.VARIANTS} if content else None,
            "issues": [self._issue_json(content, i) for i in issues],
            "gate": self._gate_json(content, gate) if gate else None,
            "draftCount": self.draft_count(),
            "touched": sorted(self.touched()),
            "fits": fits,
            "fitWarning": self.fit_warning(content),
            "variants": [{"id": v, "label": C.VARIANT_LABELS[v]} for v in importer.VARIANTS],
            "profileLoaded": self.profile() is not None,
            "gpa": self.gpa(),
            "autosave": {"saved": self.pending_autosave.get("saved")} if self.pending_autosave else None,
            "lastApply": self.last_apply(),
            "wordAvailable": wordroute.word_available(),
        }

    # ------------------------------------------------------------- import (4a)
    def run_import(self) -> dict:
        """Read the six masters, merge, prove every one re-renders losslessly, then write the content set."""
        if self.draft is not None:
            return {"ok": False, "error": "drafts", "message": "save or discard the CV text drafts first — the import replaces the content set"}
        missing = [m.file for m in masters.MASTERS if not masters.docx_path(self.repo_root, m).is_file()]
        if missing:
            return {"ok": False, "error": "missing-masters", "message": "missing masters: " + ", ".join(missing)}
        started = time.time()
        docs: dict[str, dict] = {}
        try:
            for v in importer.VARIANTS:
                docs[v] = {}
                for lang in ("en", "es"):
                    m = masters.BY_ID[f"{v}-{lang}"]
                    docs[v][lang] = importer.read_master(masters.docx_path(self.repo_root, m))
        except importer.ImportError_ as e:
            return {"ok": False, "error": "unsupported", "message": str(e)}
        content, slots, report = importer.merge(docs)
        proof = {}
        tmp = Path(tempfile.mkdtemp(prefix="cv-proof-"))
        try:
            for v, langs in docs.items():
                for lang, doc in langs.items():
                    out = renderer.force_render(doc, slots[doc.path.name], content, tmp / doc.path.name)
                    proof[doc.path.name] = importer.compare(doc.path, out)
        except Exception as e:  # a render crash is a failed proof, not a server error
            log.exception("proof render failed")
            proof["(render)"] = [f"render failed: {e}"]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        ok = all(not v for v in proof.values())
        result = {
            "ok": ok,
            "ran": datetime.now().isoformat(timespec="seconds"),
            "seconds": round(time.time() - started, 1),
            "proof": proof,
            "report": report,
            "written": False,
        }
        if not ok:
            result["error"] = "not-lossless"
            result["message"] = "The round trip is not lossless for every master; nothing was written."
            return result
        existing = [CONTENT_FILE] + [f"{SLOTS_DIR}/{p.name}" for p in (self.repo_root / SLOTS_DIR).glob("*.json")] if self.content_path().is_file() else []
        if existing:
            result["backup"] = self.backups.create(existing, "before re-importing the CV masters").id
        (self.repo_root / SLOTS_DIR).mkdir(parents=True, exist_ok=True)
        atomic_write(self.content_path(), _dump(content))
        for name, sl in slots.items():
            atomic_write(self.repo_root / SLOTS_DIR / (name + ".json"), _dump(sl))
        atomic_write(self.repo_root / REPORT_FILE, _dump({k: v for k, v in result.items() if k != "written"}))
        result["written"] = True
        self.load()
        log.info("imported CV masters: %d items, proof lossless", len(content["items"]))
        return result


# ----------------------------------------------------------------- change descriptions


def _issue_key(base: dict, draft: dict, path: list) -> str:
    """The issue key a change path belongs to."""
    if not path:
        return ""
    if path[0] == "header":
        if len(path) > 2 and path[1] == "title":
            return f"header.title.{path[2]}"
        return f"header.{path[1]}" if len(path) > 1 else "header"
    if path[0] == "sections" and len(path) > 1:
        for src in (draft, base):
            secs = src.get("sections", [])
            if isinstance(path[1], int) and path[1] < len(secs):
                return f"section.{secs[path[1]]['id']}"
        return ""
    if path[0] == "items" and len(path) > 1:
        if len(path) > 3 and path[2] == "children":
            return str(path[3])
        return str(path[1])
    return ""


def _q(v: Any) -> str:
    if v is None:
        return "(missing)"
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", "⏎")
    return "“" + (s if len(s) <= 120 else s[:117] + "…") + "”"


def change_lines(base: dict, draft: dict) -> list[dict]:
    """Plain-language lines for the review: whole added / removed items and children and
    order changes collapse into one line each; text and include edits are listed one by one."""
    out: list[dict] = []
    seen_ids: set = set()
    base_items, draft_items = base.get("items", {}), draft.get("items", {})

    def where(content: dict, iid: str) -> str:
        sec = C.section_of(content, iid)
        return f"{sec['heading']['en'] or sec['id']} › " if sec else ""

    def child_label(item: dict, cid: str) -> str:
        child = item.get("children", {}).get(cid) or {}
        n = list(item.get("children", {})).index(cid) + 1 if cid in item.get("children", {}) else "?"
        return f"{'bullet' if child.get('kind') == 'bullet' else 'line'} {n}"

    def duplicated_from(container_base: dict, container_draft: dict, new_id: str) -> Optional[tuple[str, str]]:
        """(original id, variant) when `new_id` is a copy made by duplicate(): named <orig>-<variant>[-n],
        the original exists and has left that variant in the draft."""
        for v in C.VARIANTS:
            for suffix in (f"-{v}",) + tuple(f"-{v}-{n}" for n in range(2, 10)):
                if new_id.endswith(suffix):
                    orig = new_id[: -len(suffix)]
                    if orig in container_base and orig in container_draft and container_base[orig]["include"].get(v) and not container_draft[orig]["include"].get(v):
                        return orig, v
        return None

    for iid, item in draft_items.items():
        if iid not in base_items:
            seen_ids.add(iid)
            dup = duplicated_from(base_items, draft_items, iid)
            if dup:
                orig, v = dup
                seen_ids.add(orig)
                others = ", ".join(C.VARIANT_LABELS[x] for x, on in draft_items[orig]["include"].items() if on) or "no other document"
                out.append({"path": ["items", iid], "kind": "added", "text": f"{where(draft, iid)}{_q(C.label_of(draft, orig))}: duplicated into {C.VARIANT_LABELS[v]} (the original stays in {others})"})
                continue
            vs = ", ".join(C.VARIANT_LABELS[v] for v, on in item["include"].items() if on) or "no variant"
            out.append({"path": ["items", iid], "kind": "added", "text": f"{where(draft, iid)}added {item['kind']} {_q(C.label_of(draft, iid))} in {vs}"})
    for iid, item in base_items.items():
        if iid not in draft_items:
            seen_ids.add(iid)
            out.append({"path": ["items", iid], "kind": "removed", "text": f"{where(base, iid)}deleted {item['kind']} {_q(C.label_of(base, iid))}"})
            continue
        for cid in draft_items[iid].get("children", {}):
            if cid not in item.get("children", {}):
                seen_ids.add(cid)
                child = draft_items[iid]["children"][cid]
                dup = duplicated_from(item.get("children", {}), draft_items[iid]["children"], cid)
                if dup:
                    orig, v = dup
                    seen_ids.add(orig)
                    others = ", ".join(C.VARIANT_LABELS[x] for x, on in draft_items[iid]["children"][orig]["include"].items() if on) or "no other document"
                    out.append({"path": ["items", iid, "children", cid], "kind": "added", "text": f"{where(draft, iid)}{C.label_of(draft, iid)} › {child_label(item, orig)}: duplicated into {C.VARIANT_LABELS[v]} (the original stays in {others})"})
                    continue
                vs = ", ".join(C.VARIANT_LABELS[v] for v, on in child["include"].items() if on) or "no variant"
                out.append({"path": ["items", iid, "children", cid], "kind": "added", "text": f"{where(draft, iid)}{C.label_of(draft, iid)} › added {child_label(draft_items[iid], cid)} in {vs}"})
        for cid in item.get("children", {}):
            if cid not in draft_items[iid].get("children", {}):
                seen_ids.add(cid)
                out.append({"path": ["items", iid, "children", cid], "kind": "removed", "text": f"{where(base, iid)}{C.label_of(base, iid)} › deleted {child_label(item, cid)} {_q(C.label_of(base, cid))}"})
    orders_done: set = set()

    def pure_reorder(a: Optional[list], b: Optional[list]) -> bool:
        """An order list whose membership is unchanged — only then is "order changed" worth a line
        (adds, deletes and include changes already explain a membership change)."""
        return set(a or []) == set(b or [])

    for c in changes(base, draft):
        p = c["path"]
        if p[0] == "items" and len(p) > 1 and (p[1] in seen_ids or (len(p) > 3 and p[2] == "children" and p[3] in seen_ids)):
            continue
        text = None
        if p[0] == "header":
            part = p[1]
            if part == "title":
                text = f"Header › title ({C.VARIANT_LABELS.get(p[2], p[2])}, {str(p[3]).upper()}): {_q(c['old'])} → {_q(c['new'])}"
            elif part == "name":
                text = f"Header › name: {_q(c['old'])} → {_q(c['new'])}"
            else:
                text = f"Header › {part} ({str(p[-1]).upper()}): {_q(c['old'])} → {_q(c['new'])}"
        elif p[0] == "sections":
            sec = (draft.get("sections") or base.get("sections"))[p[1]] if len(p) > 1 and isinstance(p[1], int) else None
            name = sec["heading"]["en"] or sec["id"] if sec else "?"
            if len(p) > 2 and p[2] == "heading":
                text = f"Section {_q(name)} › heading ({str(p[3]).upper()}): {_q(c['old'])} → {_q(c['new'])}"
            elif len(p) > 3 and p[2] == "order":
                key = ("section", p[1], p[3])
                if key in orders_done:
                    continue
                orders_done.add(key)
                base_sec = base["sections"][p[1]] if p[1] < len(base.get("sections", [])) else {}
                if not pure_reorder(base_sec.get("order", {}).get(p[3]), sec["order"].get(p[3]) if sec else None):
                    continue
                text = f"Section {_q(name)} › order in {C.VARIANT_LABELS.get(p[3], p[3])} changed"
        elif p[0] == "items" and len(p) > 2:
            iid = p[1]
            src = base if iid in base_items else draft
            head = f"{where(src, iid)}{C.label_of(src, iid)}"
            if p[2] == "children" and len(p) > 4:
                cid = p[3]
                clabel = child_label(src["items"][iid], cid)
                if p[4] == "text":
                    text = f"{head} › {clabel} ({str(p[5]).upper()}): {_q(c['old'])} → {_q(c['new'])}"
                elif p[4] == "include":
                    text = f"{head} › {clabel}: {'now in' if c['new'] else 'no longer in'} {C.VARIANT_LABELS.get(p[5], p[5])}"
            elif p[2] in ("role", "org", "date", "text"):
                text = f"{head} › {p[2]} ({str(p[3]).upper()}): {_q(c['old'])} → {_q(c['new'])}"
            elif p[2] == "include":
                text = f"{head}: {'now in' if c['new'] else 'no longer in'} {C.VARIANT_LABELS.get(p[3], p[3])}"
            elif p[2] == "order" and len(p) > 3:
                key = ("item", iid, p[3])
                if key in orders_done:
                    continue
                orders_done.add(key)
                if not pure_reorder(base_items.get(iid, {}).get("order", {}).get(p[3]), draft_items.get(iid, {}).get("order", {}).get(p[3])):
                    continue
                text = f"{head} › bullet order in {C.VARIANT_LABELS.get(p[3], p[3])} changed"
        if text is None:
            text = " › ".join(str(x) for x in p) + f": {_q(c['old'])} → {_q(c['new'])}"
        out.append({"path": p, "kind": c["kind"], "text": text})
    return out
