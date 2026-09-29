"""Flask app for the local content editor (Phase 1: site text, EN/ES).

Run through launch.pyw normally. `python app.py --no-edge` starts the two
servers without opening Edge and prints the URL (for tests and Playwright).

Security model (all local):
  * a random token is generated per launch and put in the app URL; every
    /api/* request except /api/ping must carry it (X-Editor-Token header or
    ?token= on GET);
  * the Host header must be 127.0.0.1:<port> or localhost:<port>;
  * an Origin header, when present, must be one of those two origins.
No CORS headers are ever sent.
"""

from __future__ import annotations

import argparse
import hmac
import json
import logging
import os
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from flask import Flask, Response, jsonify, request, send_from_directory

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from core import preview as preview_mod  # noqa: E402
from core import review as review_mod  # noqa: E402
from core import validate as validate_mod  # noqa: E402
from core.backups import Backups, atomic_write  # noqa: E402
from core.cv.service import CvService  # noqa: E402
from core.cv.textservice import CvTextService  # noqa: E402
from core.jobs import JobRunner  # noqa: E402
from core.jsdata import JsDataError, sha256_bytes  # noqa: E402
from core.site.service import ContentService  # noqa: E402
from core.site_text import SiteText, hidden_key_prefixes  # noqa: E402
from core.transcript.service import TranscriptService  # noqa: E402

log = logging.getLogger("editor.app")

EDITOR_PORT = 5510
PREVIEW_PORT = 5501
HEARTBEAT_TIMEOUT = 10 * 60  # seconds of silence before the crash fallback may exit
VERSION = "0.3 (phase 3)"


class EditorState:
    """Everything the endpoints share: the loaded file, drafts, heartbeat, backups."""

    def __init__(self, repo_root: Path, local_dir: Path, token: str, editor_port: int, preview_port: int):
        self.repo_root = Path(repo_root)
        self.local_dir = Path(local_dir)
        self.token = token
        self.editor_port = editor_port
        self.preview_port = preview_port
        self.lock = threading.RLock()
        self.drafts: dict[str, str] = {}
        self.site: Optional[SiteText] = None
        self.load_error: Optional[str] = None
        self.hidden_prefixes: list[str] = []
        self.started = time.monotonic()
        self.last_heartbeat = time.monotonic()
        self.heartbeat_seen = False
        self.shutdown_requested = threading.Event()
        # set by the launcher: bring the window to the front (returns False when no window)
        self.focus_callback: Optional[Callable[[], bool]] = None
        # how "Preview" opens the preview URL in the normal browser (tests replace it)
        self.opener: Callable[[str], object] = webbrowser.open
        self.backups = Backups(self.repo_root, self.local_dir / "backups")
        self.autosave_path = self.local_dir / "drafts" / "translations.json"
        self.pending_autosave: Optional[dict] = self._read_autosave()
        # One background job at a time across the tools (Word export, transcript parse / build).
        self.jobs = JobRunner()
        # Phase 1b: CV / résumé check & publish (its own module; shares the backups)
        self.cv = CvService(self.repo_root, self.backups, self.jobs)
        # Phase 3: transcript inputs, parse / build jobs, publish
        self.transcript = TranscriptService(self.repo_root, self.local_dir, self.backups, self.jobs)
        self.load()
        # Phase 2: projects / experience / tags (needs self.site loaded first)
        self.content = ContentService(self)
        # Phase 4: CV text (import of the masters into staging/cv-content/, then the editor over it)
        self.cvtext = CvTextService(self.repo_root, self.backups, self.local_dir, gpa=self.transcript.computed_gpa)

    def busy(self) -> bool:
        """True while a background job (a Word export, a transcript parse or build) is running."""
        return self.jobs.busy()

    def draft_count(self) -> int:
        """Unsaved edits across the tools (the close prompt)."""
        return len(self.drafts) + self.transcript.draft_count() + self.content.draft_count() + self.cvtext.draft_count()

    # ------------------------------------------------------------- loading
    def load(self) -> None:
        with self.lock:
            try:
                self.site = SiteText(self.repo_root)
                self.load_error = None
            except (JsDataError, OSError) as e:
                self.site = None
                self.load_error = str(e)
                log.error("cannot load translations.js: %s", e)
            self.hidden_prefixes = hidden_key_prefixes(self.repo_root)
            if self.site is not None and self.drafts:
                self.drafts = self.site.normalize_edits(self.drafts)

    @property
    def read_only(self) -> bool:
        return self.site is None

    # ------------------------------------------------------------- drafts
    def set_draft(self, lang: str, key: str, value: str) -> None:
        with self.lock:
            if self.site is None:
                raise RuntimeError("file is read-only")
            if lang not in ("en", "es") or self.site.value(lang, key) is None:
                raise KeyError(f"{lang}.{key}")
            k = f"{lang}.{key}"
            if self.site.value(lang, key) == value:
                self.drafts.pop(k, None)
            else:
                self.drafts[k] = value
            self._write_autosave()

    def discard_drafts(self) -> None:
        with self.lock:
            self.drafts.clear()
            self._write_autosave()

    def touched_keys(self) -> set:
        return {k.partition(".")[2] for k in self.drafts}

    def draft_bytes(self) -> Optional[bytes]:
        with self.lock:
            if self.site is None:
                return None
            return self.site.render(self.drafts)

    def preview_overrides(self) -> dict:
        with self.lock:
            if self.site is None:
                return {}
            out = {}
            if self.drafts:
                out[SiteText.REL_PATH] = self.site.render(self.drafts)
            content = getattr(self, "content", None)
            if content is not None:
                out.update(content.preview_overrides())  # data files, new keys, shells
            return out

    # ------------------------------------------------------------- autosave
    def _read_autosave(self) -> Optional[dict]:
        try:
            if self.autosave_path.is_file():
                j = json.loads(self.autosave_path.read_text(encoding="utf-8"))
                if isinstance(j, dict) and j.get("edits"):
                    return j
        except (OSError, ValueError) as e:
            log.warning("autosave file unreadable: %s", e)
        return None

    def _write_autosave(self) -> None:
        try:
            if not self.drafts:
                if self.autosave_path.exists():
                    self.autosave_path.unlink()
                return
            self.autosave_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "file": SiteText.REL_PATH,
                "baseSha256": self.site.sha256 if self.site else None,
                "saved": datetime.now().isoformat(timespec="seconds"),
                "edits": self.drafts,
            }
            atomic_write(self.autosave_path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
        except OSError as e:
            log.warning("autosave failed: %s", e)

    def restore_autosave(self) -> dict:
        with self.lock:
            pend = self.pending_autosave
            self.pending_autosave = None
            if not pend or self.site is None:
                return {"applied": 0, "skipped": 0, "fileChanged": False}
            edits = {k: v for k, v in pend.get("edits", {}).items() if isinstance(v, str)}
            applied = self.site.normalize_edits(edits)
            self.drafts.update(applied)
            self._write_autosave()
            return {
                "applied": len(applied),
                "skipped": len(edits) - len(applied),
                "fileChanged": pend.get("baseSha256") not in (None, self.site.sha256),
            }

    def discard_autosave(self) -> None:
        with self.lock:
            self.pending_autosave = None
            if not self.drafts and self.autosave_path.exists():
                try:
                    self.autosave_path.unlink()
                except OSError:
                    pass

    # ------------------------------------------------------------- validation
    def baseline_issues(self) -> list:
        if self.site is None:
            return []
        en, es = self.site.as_dicts()
        return validate_mod.validate(en, es, self.hidden_prefixes)

    def draft_issues(self) -> list:
        if self.site is None:
            return []
        en, es = self.site.apply(self.drafts)
        return validate_mod.validate(en, es, self.hidden_prefixes)

    def gate(self) -> validate_mod.SaveGate:
        return validate_mod.blocking(self.baseline_issues(), self.draft_issues(), self.touched_keys())

    # ------------------------------------------------------------- review/save
    def review(self) -> dict:
        with self.lock:
            if self.site is None:
                return {"readOnly": True, "error": self.load_error}
            new = self.site.render(self.drafts)
            diff = review_mod.unified_diff(self.site.raw, new, SiteText.REL_PATH)
            j = self.site.to_json()
            return {
                "readOnly": False,
                "file": SiteText.REL_PATH,
                "changes": review_mod.change_list(self.drafts, j["entries"], j["sections"]),
                "diff": diff,
                "diffStats": review_mod.count_changed_lines(diff),
                "gate": self.gate().to_json(),
                "diskChanged": self.site.disk_changed(),
                "noop": new == self.site.raw,
            }

    def save(self) -> dict:
        with self.lock:
            if self.site is None:
                return {"ok": False, "error": "read-only", "message": self.load_error}
            if self.site.disk_changed():
                return {
                    "ok": False,
                    "error": "changed-on-disk",
                    "message": "js/translations.js changed on disk since it was loaded. Reload and re-apply your edits.",
                }
            gate = self.gate()
            if not gate.ok():
                return {"ok": False, "error": "blocked", "message": "Fix the blocking errors first.", "gate": gate.to_json()}
            new = self.site.render(self.drafts)
            if new == self.site.raw:
                self.drafts.clear()
                self._write_autosave()
                return {"ok": True, "noop": True, "message": "Nothing to save — the file is unchanged."}
            bset = self.backups.create([SiteText.REL_PATH], "before saving site text")
            try:
                atomic_write(self.site.path, new)
            except OSError as e:
                # Windows: os.replace fails while another program holds the file
                # open. Nothing was written; drafts and the autosave stay as they are.
                log.warning("write failed for %s: %s", SiteText.REL_PATH, e)
                return {
                    "ok": False,
                    "error": "write-failed",
                    "message": "js/translations.js could not be written — it is probably open in another program. "
                    "Close it and retry. Nothing was changed and your drafts are kept.",
                    "detail": str(e),
                    "backup": bset.id,
                }
            written_sha = sha256_bytes(new)
            self.drafts.clear()
            self._write_autosave()
            self.load()
            ok = self.site is not None and self.site.sha256 == written_sha
            log.info("saved %s (backup %s)", SiteText.REL_PATH, bset.id)
            return {"ok": ok, "backup": bset.id, "sha256": written_sha, "message": f"Saved. Backup set {bset.id}."}

    # ------------------------------------------------------------- misc
    def git_info(self) -> Optional[dict]:
        def run(args):
            try:
                r = subprocess.run(
                    ["git", *args],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                return r.stdout.strip() if r.returncode == 0 else None
            except (OSError, subprocess.SubprocessError):
                return None

        status = run(["status", "--porcelain", "--", SiteText.REL_PATH])
        if status is None:
            return None
        return {"status": status, "diffStat": run(["diff", "--stat", "--", SiteText.REL_PATH]) or ""}

    def heartbeat(self) -> None:
        self.last_heartbeat = time.monotonic()
        self.heartbeat_seen = True

    def heartbeat_silence(self) -> float:
        return time.monotonic() - self.last_heartbeat

    def state_json(self) -> dict:
        with self.lock:
            out = {
                "version": VERSION,
                "pid": os.getpid(),
                "repoRoot": str(self.repo_root),
                "previewUrl": f"http://127.0.0.1:{self.preview_port}/",
                "readOnly": self.read_only,
                "loadError": self.load_error,
                "drafts": dict(self.drafts),
                "autosave": (
                    {
                        "saved": self.pending_autosave.get("saved"),
                        "count": len(self.pending_autosave.get("edits", {})),
                        "fileChanged": self.pending_autosave.get("baseSha256")
                        not in (None, self.site.sha256 if self.site else None),
                    }
                    if self.pending_autosave
                    else None
                ),
                "git": self.git_info(),
            }
            if self.site is not None:
                out["file"] = self.site.to_json()
                out["issues"] = [i.to_json() for i in self.draft_issues()]
                out["gate"] = self.gate().to_json()
            else:
                out["file"] = None
                out["issues"] = []
                out["gate"] = None
            return out


# ------------------------------------------------------------------- Flask


def create_app(state: EditorState) -> Flask:
    app = Flask("gideonong_editor", static_folder=str(HERE / "static"), static_url_path="/static")
    app.config["JSON_AS_ASCII"] = False
    app.config["MAX_CONTENT_LENGTH"] = 26 * 1024 * 1024  # image imports (25 MB cap + form fields)
    allowed_hosts = {f"127.0.0.1:{state.editor_port}", f"localhost:{state.editor_port}"}
    allowed_origins = {"http://" + h for h in allowed_hosts}

    def deny(code: int, msg: str) -> Response:
        return Response(json.dumps({"ok": False, "error": msg}), status=code, mimetype="application/json")

    def token_ok() -> bool:
        supplied = request.headers.get("X-Editor-Token") or request.args.get("token") or ""
        return hmac.compare_digest(supplied, state.token)

    @app.before_request
    def guard():
        if request.host not in allowed_hosts:
            log.warning("rejected request with Host %r", request.host)
            return deny(403, "bad host")
        origin = request.headers.get("Origin")
        if origin and origin not in allowed_origins:
            log.warning("rejected request with Origin %r", origin)
            return deny(403, "foreign origin")
        if request.path.startswith("/api/") and request.path != "/api/ping":
            if not token_ok():
                return deny(403, "missing or bad token")
            if request.method not in ("GET", "HEAD") and request.headers.get("X-Editor-Token") is None:
                return deny(403, "state-changing requests need the X-Editor-Token header")
        return None

    @app.after_request
    def headers(resp: Response):
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    @app.get("/")
    def index():
        return send_from_directory(HERE / "static", "index.html")

    @app.get("/cv")
    def cv_page():
        return send_from_directory(HERE / "static", "cv.html")

    # ---------------------------------------------------------- CV / résumé
    @app.get("/api/cv/state")
    def cv_state():
        return jsonify(state.cv.state())

    @app.post("/api/cv/check")
    def cv_check():
        body = request.get_json(silent=True) or {}
        ids = body.get("ids")
        if ids is not None and not (isinstance(ids, list) and all(isinstance(i, str) for i in ids)):
            return deny(400, "ids must be a list of master ids")
        return jsonify(ok=True, checks=state.cv.check(ids, force=bool(body.get("force"))), masters=state.cv.state()["masters"])

    @app.post("/api/cv/export")
    def cv_export():
        body = request.get_json(silent=True) or {}
        ids = body.get("ids")
        if ids is not None and not (isinstance(ids, list) and all(isinstance(i, str) for i in ids)):
            return deny(400, "ids must be a list of master ids")
        try:
            job = state.cv.start_export(ids)
        except RuntimeError as e:
            return deny(409, str(e))
        return jsonify(ok=True, job=job)

    @app.get("/api/cv/job")
    def cv_job():
        return jsonify(job=state.cv.job_json())

    @app.get("/api/cv/publish-plan")
    def cv_publish_plan():
        return jsonify(state.cv.publish_plan(request.args.get("date") or None))

    @app.post("/api/cv/publish")
    def cv_publish():
        body = request.get_json(silent=True) or {}
        result = state.cv.publish_apply(body.get("date") or None)
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.post("/api/cv/open-out")
    def cv_open_out():
        try:
            path = state.cv.open_out()
        except OSError as e:  # pragma: no cover
            return deny(500, f"could not open the folder: {e}")
        return jsonify(ok=True, path=path)

    # ---------------------------------------------------------- content (projects / experience / tags)
    @app.get("/content")
    def content_page():
        return send_from_directory(HERE / "static", "content.html")

    @app.get("/api/content/state")
    def content_state():
        with state.lock:
            return jsonify(state.content.state_json())

    @app.post("/api/content/reload")
    def content_reload():
        with state.lock:
            state.load()
            state.content.load()
            return jsonify(state.content.state_json())

    def _content_call(fn, *args, **kw):
        try:
            with state.lock:
                result = fn(*args, **kw)
                return jsonify(ok=True, result=result, **state.content.state_json())
        except KeyError as e:
            return deny(404, f"unknown entry {e}")
        except ValueError as e:
            return deny(400, str(e))
        except RuntimeError as e:
            return deny(409, str(e))

    @app.post("/api/content/field")
    def content_field():
        b = request.get_json(silent=True) or {}
        path = b.get("path")
        if not isinstance(b.get("file"), str) or not isinstance(b.get("slug"), str) or not isinstance(path, list) or not path:
            return deny(400, "file, slug and a path list are required")
        if not all(isinstance(p, (str, int)) and not isinstance(p, bool) for p in path):
            return deny(400, "path parts must be strings or integers")
        return _content_call(state.content.set_field, b["file"], b["slug"], path, b.get("value"), bool(b.get("delete")))

    @app.post("/api/content/text")
    def content_text():
        b = request.get_json(silent=True) or {}
        if not all(isinstance(b.get(k), str) for k in ("file", "slug", "field", "lang", "value")):
            return deny(400, "file, slug, field, lang and value (strings) are required")
        return _content_call(state.content.set_text, b["file"], b["slug"], b["field"], b["lang"], b["value"])

    @app.post("/api/content/add")
    def content_add():
        b = request.get_json(silent=True) or {}
        if not isinstance(b.get("file"), str) or not isinstance(b.get("slug"), str):
            return deny(400, "file and slug are required")
        return _content_call(state.content.add_entry, b["file"], b["slug"].strip(), str(b.get("titleEn") or ""), str(b.get("titleEs") or ""))

    @app.post("/api/content/delete")
    def content_delete():
        b = request.get_json(silent=True) or {}
        if not isinstance(b.get("file"), str) or not isinstance(b.get("slug"), str):
            return deny(400, "file and slug are required")
        return _content_call(state.content.delete_entry, b["file"], b["slug"])

    @app.post("/api/content/shell")
    def content_shell():
        b = request.get_json(silent=True) or {}
        if not isinstance(b.get("slug"), str):
            return deny(400, "slug is required")
        return _content_call(state.content.create_shell, b["slug"])

    @app.post("/api/content/tag")
    def content_tag():
        b = request.get_json(silent=True) or {}
        if not isinstance(b.get("id"), str):
            return deny(400, "id is required")
        return _content_call(state.content.add_tag, b["id"].strip(), str(b.get("en") or ""), str(b.get("es") or ""))

    @app.post("/api/content/tag/delete")
    def content_tag_delete():
        b = request.get_json(silent=True) or {}
        if not isinstance(b.get("id"), str):
            return deny(400, "id is required")
        return _content_call(state.content.delete_tag, b["id"])

    @app.post("/api/content/images/import")
    def content_image_import():
        f = request.files.get("image")
        form = request.form
        if f is None or not f.filename:
            return deny(400, "no image file in the request")
        for k in ("file", "slug", "field", "preset", "altEn", "altEs"):
            if not isinstance(form.get(k), str):
                return deny(400, f"{k} is required")
        data = f.read()
        try:
            with state.lock:
                result = state.content.import_image(
                    data, f.filename, form["file"], form["slug"], form["field"], form["preset"], form["altEn"], form["altEs"],
                    new_name=form.get("name", ""), replace=form.get("replace") in ("1", "true", "on"),
                )
                return jsonify(ok=True, result=result, **state.content.state_json())
        except KeyError as e:
            return deny(404, f"unknown entry {e}")
        except ValueError as e:
            return deny(400, str(e))
        except RuntimeError as e:
            return deny(409, str(e))

    @app.post("/api/content/images/delete")
    def content_image_delete():
        b = request.get_json(silent=True) or {}
        if not isinstance(b.get("path"), str):
            return deny(400, "path is required")
        return _content_call(state.content.delete_image, b["path"])

    @app.get("/api/content/images")
    def content_images():
        with state.lock:
            return jsonify(state.content.images_state())

    @app.post("/api/content/drafts/discard")
    def content_discard():
        with state.lock:
            state.content.discard_drafts()
        return jsonify(ok=True, draftCount=0)

    @app.get("/api/content/review")
    def content_review():
        with state.lock:
            return jsonify(state.content.review())

    @app.post("/api/content/save")
    def content_save():
        with state.lock:
            result = state.content.save()
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.post("/api/content/autosave/restore")
    def content_autosave_restore():
        with state.lock:
            return jsonify(ok=True, **state.content.restore_autosave())

    @app.post("/api/content/autosave/discard")
    def content_autosave_discard():
        with state.lock:
            state.content.discard_autosave()
        return jsonify(ok=True)

    # ---------------------------------------------------------- CV text (Phase 4)
    @app.get("/cvtext")
    def cvtext_page():
        return send_from_directory(HERE / "static", "cvtext.html")

    @app.get("/api/cvtext/state")
    def cvtext_state():
        with state.lock:
            return jsonify(state.cvtext.state())

    @app.post("/api/cvtext/import")
    def cvtext_import():
        if state.busy():
            return deny(409, "wait for the running job to finish")
        with state.lock:
            result = state.cvtext.run_import()
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.post("/api/cvtext/reload")
    def cvtext_reload():
        with state.lock:
            state.cvtext.load()
            return jsonify(state.cvtext.state())

    @app.post("/api/cvtext/op")
    def cvtext_op():
        b = request.get_json(silent=True) or {}
        op = b.get("op")
        svc = state.cvtext

        def s(key, required=True):
            v = b.get(key)
            if v is None and not required:
                return None
            if not isinstance(v, str):
                raise ValueError(f"{key} must be a string")
            return v

        try:
            with state.lock:
                if op == "set":
                    path = b.get("path")
                    if not isinstance(path, list) or not path or not all(isinstance(p, (str, int)) and not isinstance(p, bool) for p in path):
                        return deny(400, "path must be a non-empty list of strings and integers")
                    svc.set_text(path, b.get("value"))
                    result = None
                elif op == "include":
                    svc.include(s("id"), s("variant"), bool(b.get("on")), s("current", False))
                    result = None
                elif op == "move":
                    delta = b.get("delta")
                    if not isinstance(delta, int) or isinstance(delta, bool):
                        return deny(400, "delta must be an integer")
                    svc.move(s("id"), s("variant"), delta)
                    result = None
                elif op == "add-item":
                    result = {"id": svc.add_item(s("section"), s("kind"), s("en"), s("variant"))}
                elif op == "add-child":
                    result = {"id": svc.add_child(s("item"), s("kind"), s("variant"))}
                elif op == "delete":
                    svc.delete(s("id"))
                    result = None
                elif op == "add-section":
                    result = {"id": svc.add_section(s("en"), s("es", False) or "", s("variant"))}
                elif op == "delete-section":
                    svc.delete_section(s("id"))
                    result = None
                elif op == "pull-drift":
                    svc.pull_drift(s("master"), s("id"))
                    result = None
                elif op == "discard-drift":
                    svc.discard_drift(s("master"), s("id"))
                    result = None
                elif op in ("pull-all", "discard-all"):
                    result = {"count": svc.resolve_all(s("master"), "pull" if op == "pull-all" else "discard")}
                else:
                    return deny(400, "unknown op")
                return jsonify(ok=True, result=result, **svc.state())
        except KeyError as e:
            return deny(404, f"unknown id {e}")
        except ValueError as e:
            return deny(400, str(e))
        except RuntimeError as e:
            return deny(409, str(e))

    @app.post("/api/cvtext/drafts/discard")
    def cvtext_discard():
        with state.lock:
            state.cvtext.discard_drafts()
        return jsonify(ok=True, draftCount=0)

    @app.get("/api/cvtext/review")
    def cvtext_review():
        with state.lock:
            return jsonify(state.cvtext.review())

    @app.post("/api/cvtext/save")
    def cvtext_save():
        with state.lock:
            result = state.cvtext.save()
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.get("/api/cvtext/drift")
    def cvtext_drift():
        with state.lock:
            return jsonify(state.cvtext.drift())

    @app.post("/api/cvtext/apply")
    def cvtext_apply():
        if state.busy():
            return deny(409, "wait for the running job to finish")
        body = request.get_json(silent=True) or {}
        with state.lock:
            result = state.cvtext.apply(str(body.get("route") or "python"))
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.post("/api/cvtext/crosscheck")
    def cvtext_crosscheck():
        if state.busy():
            return deny(409, "wait for the running job to finish")
        with state.lock:
            result = state.cvtext.crosscheck()
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.post("/api/cvtext/autosave/restore")
    def cvtext_autosave_restore():
        with state.lock:
            return jsonify(ok=True, **state.cvtext.restore_autosave())

    @app.post("/api/cvtext/autosave/discard")
    def cvtext_autosave_discard():
        with state.lock:
            state.cvtext.discard_autosave()
        return jsonify(ok=True)

    # ---------------------------------------------------------- transcript
    @app.get("/transcript")
    def transcript_page():
        return send_from_directory(HERE / "static", "transcript.html")

    @app.get("/api/transcript/state")
    def transcript_state():
        return jsonify(state.transcript.state_json())

    @app.post("/api/transcript/reload")
    def transcript_reload():
        state.transcript.load()
        return jsonify(state.transcript.state_json())

    @app.post("/api/transcript/draft")
    def transcript_draft():
        body = request.get_json(silent=True) or {}
        name, path = body.get("file"), body.get("path")
        if not isinstance(name, str) or not isinstance(path, list) or not path:
            return deny(400, "file and a non-empty path list are required")
        if not all(isinstance(p, (str, int)) and not isinstance(p, bool) for p in path):
            return deny(400, "path parts must be strings or integers")
        try:
            state.transcript.set_draft(name, path, body.get("value"), delete=bool(body.get("delete")))
        except KeyError:
            return deny(404, f"unknown file {name}")
        except (RuntimeError, ValueError, IndexError, TypeError) as e:
            return deny(409, str(e))
        return jsonify(ok=True, **_transcript_draft_reply())

    @app.post("/api/transcript/title")
    def transcript_title():
        body = request.get_json(silent=True) or {}
        code, section, field = body.get("code"), body.get("section") or "", body.get("field")
        if not isinstance(code, str) or not code.strip() or not isinstance(field, str):
            return deny(400, "code and field are required")
        try:
            state.transcript.set_title(code.strip(), section, field, body.get("value"))
        except KeyError:
            return deny(400, f"unknown field {field}")
        except (RuntimeError, ValueError) as e:
            return deny(409, str(e))
        return jsonify(ok=True, **_transcript_draft_reply())

    def _transcript_draft_reply() -> dict:
        t = state.transcript
        return {
            "draftCount": t.draft_count(),
            "issues": {n: [i.to_json() for i in v] for n, v in t.draft_issues().items()},
            "gates": {n: g.to_json() for n, g in t.gates().items()},
            "titles": t.state_json()["titles"],
        }

    @app.post("/api/transcript/drafts/discard")
    def transcript_discard():
        state.transcript.discard_drafts()
        return jsonify(ok=True, draftCount=0)

    @app.get("/api/transcript/review")
    def transcript_review():
        return jsonify(state.transcript.review())

    @app.post("/api/transcript/save")
    def transcript_save():
        result = state.transcript.save()
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.post("/api/transcript/autosave/restore")
    def transcript_autosave_restore():
        return jsonify(ok=True, **state.transcript.restore_autosave())

    @app.post("/api/transcript/autosave/discard")
    def transcript_autosave_discard():
        state.transcript.discard_autosave()
        return jsonify(ok=True)

    @app.post("/api/transcript/parse")
    def transcript_parse():
        body = request.get_json(silent=True) or {}
        try:
            job = state.transcript.start_parse(str(body.get("pdf") or ""))
        except ValueError as e:
            return deny(400, str(e))
        except RuntimeError as e:
            return deny(409, str(e))
        return jsonify(ok=True, job=job)

    @app.post("/api/transcript/build")
    def transcript_build():
        body = request.get_json(silent=True) or {}
        try:
            job = state.transcript.start_build(bool(body.get("strict")), (body.get("date") or None), bool(body.get("pdf")))
        except ValueError as e:
            return deny(400, str(e))
        except RuntimeError as e:
            return deny(409, str(e))
        return jsonify(ok=True, job=job)

    @app.get("/api/transcript/job")
    def transcript_job():
        return jsonify(job=state.transcript.job_json())

    @app.get("/api/transcript/publish-plan")
    def transcript_publish_plan():
        return jsonify(state.transcript.publish_plan())

    @app.post("/api/transcript/publish")
    def transcript_publish():
        result = state.transcript.publish_apply()
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.post("/api/transcript/open-folder")
    def transcript_open_folder():
        body = request.get_json(silent=True) or {}
        try:
            path = state.transcript.open_folder(str(body.get("which") or ""))
        except ValueError as e:
            return deny(400, str(e))
        except OSError as e:  # pragma: no cover
            return deny(500, f"could not open the folder: {e}")
        return jsonify(ok=True, path=path)

    @app.get("/api/ping")
    def ping():
        return jsonify(ok=True, app="gideonong-editor", pid=os.getpid(), version=VERSION)

    @app.post("/api/heartbeat")
    def heartbeat():
        state.heartbeat()
        changed = state.site.disk_changed() if state.site else False
        return jsonify(ok=True, drafts=len(state.drafts), diskChanged=changed)

    @app.get("/api/state")
    def get_state():
        return jsonify(state.state_json())

    @app.post("/api/reload")
    def reload():
        state.load()
        state.content.load()
        return jsonify(state.state_json())

    @app.post("/api/draft")
    def draft():
        body = request.get_json(silent=True) or {}
        lang, key, value = body.get("lang"), body.get("key"), body.get("value")
        if not isinstance(lang, str) or not isinstance(key, str) or not isinstance(value, str):
            return deny(400, "lang, key and value (strings) are required")
        try:
            state.set_draft(lang, key, value)
        except KeyError:
            return deny(404, f"unknown key {lang}.{key}")
        except RuntimeError as e:
            return deny(409, str(e))
        e = state.site.entries[key]
        en = state.drafts.get(f"en.{key}", e.en)
        es = state.drafts.get(f"es.{key}", e.es)
        from core.site_text import parity_status

        return jsonify(
            ok=True,
            drafts=len(state.drafts),
            status=parity_status(key, en, es),
            issues=[i.to_json() for i in state.draft_issues() if i.key == key],
            gate=state.gate().to_json(),
        )

    @app.post("/api/drafts/discard")
    def discard():
        state.discard_drafts()
        return jsonify(ok=True, drafts=0)

    @app.get("/api/review")
    def review():
        return jsonify(state.review())

    @app.post("/api/save")
    def save():
        result = state.save()
        return jsonify(result), (200 if result.get("ok") else 409)

    @app.get("/api/backups")
    def backups():
        return jsonify(sets=[s.to_json() for s in state.backups.list()])

    @app.get("/api/backups/<set_id>/file")
    def backup_file(set_id: str):
        rel = request.args.get("path", "")
        data = state.backups.read_file(set_id, rel)
        if data is None:
            return deny(404, "no such backup file")
        current = state.site.raw if state.site else b""
        return jsonify(
            path=rel,
            diff=review_mod.unified_diff(current, data, rel),
            sameAsCurrent=data == current,
        )

    @app.post("/api/restore")
    def restore():
        body = request.get_json(silent=True) or {}
        set_id = body.get("set", "")
        try:
            result = state.backups.restore(set_id)
        except FileNotFoundError as e:
            return deny(404, str(e))
        except OSError as e:
            log.warning("restore of %s failed: %s", set_id, e)
            return deny(409, "js/translations.js could not be written — it is probably open in another program. Close it and retry.")
        state.load()
        state.transcript.load()  # a set may hold transcript inputs; drafts there are re-applied
        state.content.load()
        state.cvtext.load()  # or the CV content set
        log.info("restored %s (backup %s)", set_id, result["backup"])
        return jsonify(ok=True, **result)

    @app.post("/api/autosave/restore")
    def autosave_restore():
        return jsonify(ok=True, **state.restore_autosave(), drafts=len(state.drafts))

    @app.post("/api/autosave/discard")
    def autosave_discard():
        state.discard_autosave()
        return jsonify(ok=True)

    @app.get("/api/git")
    def git():
        return jsonify(git=state.git_info())

    @app.post("/api/focus")
    def focus():
        """Second launch: bring the existing window to the front. focused=False → no window."""
        cb = state.focus_callback
        focused = bool(cb()) if cb else False
        return jsonify(ok=True, focused=focused)

    @app.post("/api/open-preview")
    def open_preview():
        """Open the preview in the normal default browser, not inside the editor window."""
        url = f"http://127.0.0.1:{state.preview_port}/"
        try:
            state.opener(url)
        except Exception as e:  # pragma: no cover
            log.warning("could not open the browser: %s", e)
            return deny(500, "could not open the browser")
        return jsonify(ok=True, url=url)

    return app


# ------------------------------------------------------------------- servers


class Servers:
    """The editor (Flask/werkzeug) and preview servers, each on its own thread."""

    def __init__(self, state: EditorState):
        from werkzeug.serving import make_server

        self.state = state
        self.app = create_app(state)
        self.editor = make_server("127.0.0.1", state.editor_port, self.app, threaded=True)
        self.preview = preview_mod.make_server(state.repo_root, state.preview_port, state.preview_overrides)
        self.threads: list[threading.Thread] = []

    def start(self) -> None:
        t = threading.Thread(target=self.editor.serve_forever, name="editor", daemon=True)
        t.start()
        self.threads = [t, preview_mod.serve_in_thread(self.preview)]

    def stop(self) -> None:
        for s in (self.editor, self.preview):
            try:
                s.shutdown()
                s.server_close()
            except Exception:  # pragma: no cover
                pass


def default_paths() -> tuple[Path, Path]:
    repo_root = HERE.parent.parent
    return repo_root, HERE / ".local"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Local content editor server")
    ap.add_argument("--no-edge", action="store_true", help="start the servers only; print the URL")
    ap.add_argument("--token", default=None)
    ap.add_argument("--editor-port", type=int, default=EDITOR_PORT)
    ap.add_argument("--preview-port", type=int, default=PREVIEW_PORT)
    ap.add_argument("--repo", default=None)
    ap.add_argument("--local", default=None)
    args = ap.parse_args(argv)
    import secrets

    repo_root, local_dir = default_paths()
    repo_root = Path(args.repo) if args.repo else repo_root
    local_dir = Path(args.local) if args.local else local_dir
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    token = args.token or secrets.token_urlsafe(32)
    state = EditorState(repo_root, local_dir, token, args.editor_port, args.preview_port)
    servers = Servers(state)
    servers.start()
    url = f"http://127.0.0.1:{args.editor_port}/?token={token}"
    print(url, flush=True)
    try:
        while not state.shutdown_requested.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    servers.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
