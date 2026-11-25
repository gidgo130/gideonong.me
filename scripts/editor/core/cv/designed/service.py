"""What the Designed CV page talks to. Owned by app.EditorState as `designed`.

The Designed CV has no file of its own to edit: it is the Designed variant of the CV content
set, so every edit here is an operation on the CV text service's ONE draft (the two tabs
always agree) and is saved by that service's Review & save, into content.json only.

Private by default (D9): this module writes PDFs into staging/cv-design-out/ and nowhere
else. There is no publish function. `designedPublish` in .local/settings.json is the one
switch a later publish path would have to read; it is off, no page can turn it on, and
nothing here copies a file into assets/ whatever its value.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Optional

from ...backups import atomic_write
from ...jobs import JobRunner
from .. import content as C
from .. import cvcheck, masters, scans
from ..textservice import CvTextService
from . import checks, export, model, render
from . import schema as S

log = logging.getLogger("editor.designed")

OUT_DIR = "staging/cv-design-out"
PERSONAL_FILE = "staging/editor-private/personal.json"
SEED_FILE = "staging/cv-design/seed.json"
OWNER = "Gideon Ong"  # as in the masters' file names
DOC_WORD = {"es": "Diseño", "en": "Designed"}
PUBLISH_FLAG = "designedPublish"
VIEW_KEY = "designedView"
VIEW_DEFAULT = {"layout": "c", "palette": "blue", "lang": "es", "webIcon": "mono", "browser": "auto"}
BROWSER_CHOICES = ("auto", "edge", "chrome")


def pdf_name(lang: str, layout: str, palette: str, stamp: str) -> str:
    """es Gideon Ong CV Diseño C 20261125.pdf · en Gideon Ong CV Designed E bronze 20261125.pdf
    (the palette only when it is not the default)."""
    extra = "" if palette == VIEW_DEFAULT["palette"] else f" {palette}"
    return f"{lang} {OWNER} CV {DOC_WORD[lang]} {layout.upper()}{extra} {stamp}.pdf"


class DesignedService:
    def __init__(
        self,
        repo_root: Path,
        cvtext: CvTextService,
        runner: Optional[JobRunner] = None,
        local_dir: Optional[Path] = None,
        settings: Callable[[], dict] = lambda: {},
        update_settings: Callable[..., dict] = lambda **kw: kw,
        today: Callable[[], date] = date.today,
    ):
        self.repo_root = Path(repo_root)
        self.cvtext = cvtext
        self.runner = runner or JobRunner()
        self.local_dir = Path(local_dir) if local_dir else None
        self.settings = settings
        self.update_settings = update_settings
        self.today = today
        self.opener: Callable[[str], object] = getattr(os, "startfile", lambda p: None)
        # the three things tests replace: which browser, how it measures, how it prints
        self.find_browser: Callable[[], Optional[tuple[str, Path]]] = self._find_browser
        self.measure = export.measure
        self.print_pdf = export.print_pdf
        self._ages: dict[str, tuple[float, Optional[int]]] = {}

    # ------------------------------------------------------------- private facts
    def birth(self) -> Optional[date]:
        """The birth date from staging/editor-private/personal.json (never printed, D7)."""
        try:
            j = json.loads((self.repo_root / PERSONAL_FILE).read_text(encoding="utf-8"))
            return date.fromisoformat(str(j["birth_date"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def age(self) -> Optional[int]:
        b = self.birth()
        return model.age_on(b, self.today()) if b else None

    def photo_path(self) -> Path:
        return self.repo_root / render.PHOTO_REL

    def photo_info(self) -> dict:
        p = self.photo_path()
        info: dict = {"path": render.PHOTO_REL, "exists": p.is_file(), "pixels": None, "dpi": {}}
        if info["exists"]:
            try:
                from PIL import Image

                with Image.open(p) as im:
                    info["pixels"] = list(im.size)
                info["dpi"] = {k: round(checks.photo_dpi(tuple(info["pixels"]), px)) for k, px in render.PHOTO_PX.items()}
                info["inches"] = {k: round(px / 96.0, 2) for k, px in render.PHOTO_PX.items()}
            except Exception as e:  # an unreadable picture is a warning, not a crash
                info["error"] = str(e)
        return info

    # ------------------------------------------------------------- view settings (.local/settings.json)
    def view(self) -> dict:
        v = dict(VIEW_DEFAULT)
        saved = self.settings().get(VIEW_KEY)
        if isinstance(saved, dict):
            v.update({k: saved[k] for k in VIEW_DEFAULT if isinstance(saved.get(k), str)})
        if v["layout"] not in render.LAYOUTS:
            v["layout"] = VIEW_DEFAULT["layout"]
        if v["palette"] not in render.PALETTES:
            v["palette"] = VIEW_DEFAULT["palette"]
        if v["lang"] not in render.LANGS:
            v["lang"] = VIEW_DEFAULT["lang"]
        if v["webIcon"] not in render.WEB_ICONS:
            v["webIcon"] = VIEW_DEFAULT["webIcon"]
        return v

    def set_view(self, **values) -> dict:
        v = self.view()
        for k, val in values.items():
            if k in VIEW_DEFAULT and isinstance(val, str):
                v[k] = val
        render.Options(v["layout"], v["palette"], v["lang"], v["webIcon"]).checked()
        if v["browser"] not in BROWSER_CHOICES and not Path(v["browser"]).is_file():
            raise ValueError("browser must be auto, edge, chrome or the path of a Chromium-family browser")
        self.update_settings(**{VIEW_KEY: v})
        return v

    def publish_enabled(self) -> bool:
        """The one switch a publish path would read (D9). Nothing reads it to copy a file today."""
        return self.settings().get(PUBLISH_FLAG) is True

    def _find_browser(self) -> Optional[tuple[str, Path]]:
        choice = self.view()["browser"]
        if choice not in BROWSER_CHOICES:  # the full path of another Chromium-family browser
            p = Path(choice)
            if p.is_file():
                return p.stem, p
            choice = "auto"  # it is gone (an update moved it): Edge, else Chrome, as if nothing was set
        found = [(name, var, rel) for name, var, rel in export.BROWSERS if (os.environ.get(var) and (Path(os.environ[var]) / rel).is_file())]
        if choice == "chrome":
            found.sort(key=lambda b: "Chrome" not in b[0])  # stable: Chrome first, Edge as the fallback
        for name, var, rel in found:
            return name, Path(os.environ[var]) / rel
        return None

    # ------------------------------------------------------------- operations (drafts of the CV text service)
    def op(self, body: dict) -> Optional[dict]:
        """Apply one operation to the shared draft. Returns {"id": …} when a row's id changed
        (an edit separated it for this output, a reset folded it back)."""
        name = body.get("op")

        def s(key: str) -> str:
            v = body.get(key)
            if not isinstance(v, str):
                raise ValueError(f"{key} must be a string")
            return v

        def n(key: str) -> int:
            v = body.get(key)
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(f"{key} must be an integer")
            return v

        d = self.cvtext._working()
        if "design" not in d:
            raise RuntimeError("this content set has no Designed block yet")
        result: Optional[dict] = None
        if name == "tick":
            model.tick(d, s("id"), bool(body.get("on")))
        elif name == "move":
            model.move(d, s("id"), n("delta"))
        elif name == "place":
            model.place(d, s("id"), s("section"))
        elif name == "remove":
            model.remove(d, s("id"))
        elif name == "text":
            result = {"id": model.edit_text(d, s("id"), s("field"), s("lang"), s("value"))}
        elif name == "reset":
            result = {"id": model.reset(d, s("id"))}
        elif name == "keep":
            model.keep_mine(d, s("id"))
        elif name == "add-bullet":
            result = {"id": model.add_bullet(d, s("id"))}
        elif name == "sort":
            result = {"undated": model.sort_newest(d, s("section"), self.today())}
        elif name == "title":
            if d["header"]["title"].get(C.DESIGNED) is None:
                d["header"]["title"][C.DESIGNED] = {"en": "", "es": ""}
            C.set_text(d, ["header", "title", C.DESIGNED, s("lang")], s("value"))
        elif name == "single-text":
            model.set_single(d, s("key"), s("lang"), s("value"))
        elif name == "single-include":
            model.include_single(d, s("key"), bool(body.get("on")))
        elif name == "heading":
            model.set_heading(d, s("key"), s("lang"), s("value"))
        elif name == "row-set":
            model.row_set(d, s("group"), s("id"), s("field"), s("lang"), s("value"))
        elif name == "row-include":
            model.row_include(d, s("group"), s("id"), bool(body.get("on")))
        elif name == "row-move":
            model.row_move(d, s("group"), s("id"), n("delta"))
        elif name == "row-add":
            result = {"id": model.row_add(d, s("group"))}
        elif name == "row-delete":
            model.row_delete(d, s("group"), s("id"))
        elif name == "row-keep":
            model.row_keep(d, s("group"), s("id"))
        elif name == "rows-sort":
            result = {"undated": model.rows_sort(d, s("group"), self.today())}
        elif name == "seed":
            result = self._seed(d)
        else:
            raise ValueError("unknown op")
        self.cvtext._commit(d)
        return result

    def seed_path(self) -> Path:
        return self.repo_root / SEED_FILE

    def _seed(self, d: dict) -> dict:
        if S.is_seeded(d):
            raise RuntimeError("the Designed CV is already seeded")
        try:
            seed = json.loads(self.seed_path().read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise RuntimeError(f"{SEED_FILE} cannot be read: {e}") from e
        return model.apply_seed(d, seed, self.today())

    # ------------------------------------------------------------- the page
    def options(self, layout: Optional[str] = None, palette: Optional[str] = None, lang: Optional[str] = None) -> render.Options:
        v = self.view()
        return render.Options(layout or v["layout"], palette or v["palette"], lang or v["lang"], v["webIcon"]).checked()

    def page_html(self, opts: render.Options, key: str = "") -> str:
        """The preview: the live content (drafts included), assets from the editor's own server."""
        content = self.cvtext.obj()
        if content is None or "design" not in content:
            raise RuntimeError("no content set with a Designed block")
        return render.render(content, opts, age=self.age(), base_href="/static/designed/", photo_src="/designed/photo" if self.photo_path().is_file() else "", key=key)

    # ------------------------------------------------------------- issues
    def _designed_keys(self, content: dict) -> set:
        keys = {"header.name", "header.contact", f"header.title.{C.DESIGNED}"}
        for sec in content["sections"]:
            for iid in sec["order"].get(C.DESIGNED) or []:
                item = content["items"].get(iid)
                if item is None:
                    continue
                keys.add(iid)
                keys.update(item.get("order", {}).get(C.DESIGNED) or [])
        return keys

    def issues(self, content: dict, all_issues: Optional[list] = None) -> list[dict]:
        """The CV text validation, narrowed to what the Designed CV prints or holds."""
        keys = self._designed_keys(content)
        out = []
        for i in all_issues if all_issues is not None else self.cvtext._issues(content):
            if i.key in keys or i.key.startswith("design."):
                if i.code.startswith("fit-"):
                    continue  # the one-line fit belongs to the Word masters
                out.append(self.cvtext._issue_json(content, i))
        return out

    def export_blockers(self) -> list[str]:
        """What stops an export before any browser starts."""
        ct = self.cvtext
        if ct.doc is None:
            return [ct.load_error or "no content set — import the masters first (CV text tab)"]
        reasons = []
        if "design" not in ct.doc.obj:
            return ["this content set has no Designed block yet"]
        if ct.draft is not None:
            reasons.append("save or discard the drafts first — the PDF is printed from the saved content")
        if ct.doc.disk_changed():
            reasons.append("content.json changed on disk since it was loaded — reload first")
        errors = [i for i in self.issues(ct.doc.obj) if i["level"] == "error"]
        if errors:
            reasons.append(f"{len(errors)} error(s) in the Designed CV's text — fix them first (e.g. {errors[0]['label']}: {errors[0]['message']})")
        if self.birth() is None:
            reasons.append(f"no birth date in {PERSONAL_FILE} — the age line cannot be computed")
        if self.find_browser() is None:
            reasons.append("neither Microsoft Edge nor Google Chrome was found in their standard install folders")
        return reasons

    # ------------------------------------------------------------- exported PDFs, the stale-age flag
    def out_dir(self) -> Path:
        return self.repo_root / OUT_DIR

    def exports(self) -> list[dict]:
        """Every PDF in staging/cv-design-out/ with the age it carries; `stale` when a birthday
        has passed since it was rendered (D7)."""
        now = self.age()
        out = []
        d = self.out_dir()
        if not d.is_dir():
            return out
        for p in sorted(d.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True):
            st = p.stat()
            cached = self._ages.get(p.name)
            if not cached or cached[0] != st.st_mtime:
                cached = (st.st_mtime, checks.pdf_age(p))
                self._ages[p.name] = cached
            age = cached[1]
            stale = now is not None and age is not None and age != now
            out.append(
                {
                    "name": p.name,
                    "mtime": st.st_mtime,
                    "size": st.st_size,
                    "age": age,
                    "stale": stale,
                    "note": f"rendered at {age}, you're now {now}: re-render" if stale else None,
                }
            )
        return out

    def open_out(self) -> str:
        d = self.out_dir()
        d.mkdir(parents=True, exist_ok=True)
        self.opener(str(d))
        return str(d)

    # ------------------------------------------------------------- export job
    def job_json(self) -> Optional[dict]:
        j = self.runner.json()
        return j if j and j.get("kind") == "designed-export" else None

    def start_export(self, layouts: Optional[list] = None, langs: Optional[list] = None, palette: Optional[str] = None) -> dict:
        v = self.view()
        layouts = layouts or [v["layout"]]
        langs = langs or [v["lang"]]
        palette = palette or v["palette"]
        todo = [render.Options(layout, palette, lang, v["webIcon"]).checked() for layout in layouts for lang in langs]
        blockers = self.export_blockers()
        if blockers:
            raise RuntimeError("; ".join(blockers))
        if self.runner.busy():
            raise RuntimeError("a job is already running")
        content = self.cvtext.doc.fresh_copy()  # the saved content, frozen for the whole job
        browser = self.find_browser()
        return self.runner.start("designed-export", lambda r: self._run_export(r, content, todo, browser), todo=[_tag(o) for o in todo], done=[], failed={}, current=None)

    def _run_export(self, runner: JobRunner, content: dict, todo: list, browser: tuple) -> dict:
        name, exe = browser
        work = (self.local_dir or self.repo_root / "scripts" / "editor" / ".local") / "designed" / time.strftime("job-%Y%m%d-%H%M%S")
        work.mkdir(parents=True, exist_ok=True)
        birth, age = self.birth(), self.age()
        terms, bl_warning = scans.load_blocklist(self.repo_root / masters.BLOCKLIST_PATH)
        stamp = self.today().strftime("%Y%m%d")
        photo = self.photo_info()
        runner.log_line(f"{name} ({exe}); age line: {render.age_text('es', age) if age is not None else '—'}")
        if bl_warning:
            runner.log_line(f"warning: {bl_warning}")
        try:
            for opts in todo:
                tag = _tag(opts)
                runner.update(current=tag)
                target = pdf_name(opts.lang, opts.layout, opts.palette, stamp)
                runner.log_line(f"{tag}: rendering → {target}")
                try:
                    problems, warnings = self._export_one(content, opts, exe, work, birth, age, terms, photo, target, runner.log_line)
                except export.ExportError as e:
                    problems, warnings = [str(e)], []
                except Exception as e:  # the page shows this; the job goes on to the next one
                    log.exception("designed export crashed")
                    problems, warnings = [f"unexpected error: {type(e).__name__}: {e}"], []
                for w in warnings:
                    runner.log_line(f"{tag}: warning — {w}")
                if problems:
                    with runner.lock:
                        runner.job["failed"][tag] = problems
                    for p in problems:
                        runner.log_line(f"{tag}: FAILED — {p}")
                else:
                    with runner.lock:
                        runner.job["done"].append({"tag": tag, "file": target, "warnings": warnings})
                    runner.log_line(f"{tag}: done — {OUT_DIR}/{target}")
        finally:
            shutil.rmtree(work, ignore_errors=True)
            runner.update(current=None)
        runner.log_line("export finished")
        j = runner.json()
        return {"done": list(j["done"]), "failed": dict(j["failed"])}

    def _export_one(self, content, opts, exe, work, birth, age, terms, photo, target, log_line) -> tuple[list[str], list[str]]:
        tag = _tag(opts)
        slug = f"{opts.layout}-{opts.palette}-{opts.lang}"
        page = work / f"{slug}.html"
        photo_src = self.photo_path().resolve().as_uri() if self.photo_path().is_file() else ""
        html_text = render.render(content, opts, age=age, base_href=render.TEMPLATE_DIR.resolve().as_uri() + "/", photo_src=photo_src)
        atomic_write(page, html_text.encode("utf-8"))
        m = self.measure(exe, page, work, log_line)
        log_line(f"{tag}: space left — main column {m.get('main')} px, sidebar {m.get('side')} px; fonts {m.get('fonts')}")
        problems = []
        for col, label in (("main", "main column"), ("side", "sidebar")):
            left = m.get(col)
            if isinstance(left, (int, float)) and left < 0:
                problems.append(f"the {label} is over by {-left:.0f} px (about {-left / 96 * 2.54:.1f} cm) — untick something")
        if str(m.get("fonts", "ok")) != "ok":
            problems.append(f"the page's fonts did not load ({m.get('fonts')}) — the PDF would print in a fallback font")
        if problems:
            return problems, []
        tmp_pdf = work / f"{slug}.pdf"
        self.print_pdf(exe, page, tmp_pdf, work, log_line)
        r = checks.check_pdf(
            tmp_pdf,
            content,
            opts.lang,
            age_line=render.age_text(opts.lang, age) if age is not None else None,
            birth=birth,
            terms=terms,
            photo=(tuple(photo["pixels"]), render.PHOTO_PX[opts.layout]) if photo.get("pixels") else None,
        )
        warnings = [w["message"] for w in r["warnings"]]
        if r["errors"]:
            return [e["message"] for e in r["errors"]], warnings
        out = self.out_dir()
        out.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_pdf, out / target)
        return [], warnings

    # ------------------------------------------------------------- state
    def state(self) -> dict:
        ct = self.cvtext
        content = ct.obj()
        has = content is not None and "design" in content
        age, birth, today = self.age(), self.birth(), self.today()
        base = {
            "contentPath": "staging/cv-content/content.json",
            "loaded": ct.doc is not None,
            "loadError": ct.load_error,
            "readOnly": ct.doc.read_only if ct.doc else (ct.load_error or "no content set"),
            "diskChanged": ct.doc.disk_changed() if ct.doc else False,
            "hasDesign": has,
            "draftCount": ct.draft_count(),
            "migrated": ct.migrated,
            "autosave": {"saved": ct.pending_autosave.get("saved")} if ct.pending_autosave else None,
            "today": today.isoformat(),
            "age": {
                "value": age,
                "birthLoaded": birth is not None,
                "file": PERSONAL_FILE,
                "line": {lang: render.age_text(lang, age) for lang in render.LANGS} if age is not None else None,
                "nextBirthday": model.next_birthday(birth, today).isoformat() if birth else None,
            },
            "view": self.view(),
            "options": {"layouts": render.LAYOUTS, "palettes": render.PALETTES, "webIcons": render.WEB_ICONS, "langs": list(render.LANGS), "browsers": list(BROWSER_CHOICES)},
            "browser": (lambda b: {"name": b[0], "path": str(b[1])} if b else None)(self.find_browser()),
            "linkedinIcon": (render.TEMPLATE_DIR / render.LINKEDIN_MASK).is_file(),
            "photo": self.photo_info(),
            "outDir": OUT_DIR,
            "exports": self.exports(),
            "job": self.job_json(),
            "publish": {"enabled": self.publish_enabled(), "note": "The Designed CV is private: nothing here copies it into assets/ or anywhere that deploys."},
            "seedAvailable": self.seed_path().is_file(),
        }
        if not has:
            return base
        d = content["design"]
        all_issues = ct._issues(content)
        issues = self.issues(content, all_issues)
        gate = ct.gate(all_issues)
        base.update(
            seeded=S.is_seeded(content),
            name=content["header"]["name"],
            title=content["header"]["title"].get(C.DESIGNED),
            contact={lang: render.contact_parts(content["header"]["contact"].get(lang, "")) for lang in render.LANGS},
            checklist=model.checklist(content, today),
            design={
                "profile": d["profile"],
                "gpa": d["gpa"],
                "headings": {k: model.heading(content, k) for k in S.DEFAULT_HEADINGS},
                "groups": {g: [dict(r, status=model.row_status(content, r)) for r in d.get(g) or []] for g in S.GROUPS},
                "fields": S.GROUPS,
                "labels": S.GROUP_LABELS,
            },
            issues=issues,
            gate=ct._gate_json(content, gate),
            touched=sorted(ct.touched()),
            exportBlockers=self.export_blockers(),
        )
        return base


def _tag(o: render.Options) -> str:
    return f"{o.layout.upper()} · {o.palette} · {o.lang.upper()}"
