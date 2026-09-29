"""What the Content page talks to. Owned by app.EditorState as `content`.

Drafts (autosaved to .local/drafts/content.json):
    entries:     {file: {slug: entry dict | None (delete)}}   — full live entry
    newKeys:     {key: {"en": str, "es": str}}                — keys not on disk yet
    removedKeys: [key, ...]                                   — keys to delete
    shells:      {slug: "create" | "delete"}                  — projects/<slug>.html
Text edits to keys that exist on disk go through the Site text drafts
(EditorState.set_draft), so both tabs share one translations.js review.
"""

from __future__ import annotations

import copy
import json
import logging
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from .. import validate
from ..backups import atomic_write
from ..jsdata import JsDataError
from ..review import unified_diff
from ..site_text import SiteText
from . import datacheck, keys as keymod, order
from .datafiles import FILES, DataFile

log = logging.getLogger("editor.content")

SHELL_TEMPLATE = "projects/g-view.html"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}


def _season_today() -> dict:
    m = date.today().month
    season = "spring" if m <= 5 else "summer" if m <= 8 else "fall"
    return {"season": season, "year": date.today().year}


class ContentService:
    def __init__(self, state):
        self.state = state  # EditorState: repo_root, local_dir, backups, site, drafts, set_draft, load
        self.repo_root = Path(state.repo_root)
        self.files: dict[str, Optional[DataFile]] = {}
        self.load_errors: dict[str, str] = {}
        self.drafts: dict[str, Any] = self._empty()
        self.autosave_path = Path(state.local_dir) / "drafts" / "content.json"
        self.pending_autosave: Optional[dict] = self._read_autosave()
        self.load()

    @staticmethod
    def _empty() -> dict:
        return {"entries": {"projects": {}, "experience": {}, "tags": {}}, "newKeys": {}, "removedKeys": [], "shells": {}, "images": {}, "removedImages": []}

    @property
    def image_staging(self) -> Path:
        return Path(self.state.local_dir) / "drafts" / "images"

    # ------------------------------------------------------------- loading
    def load(self) -> None:
        for name in FILES:
            try:
                self.files[name] = DataFile(self.repo_root, name)
                self.load_errors.pop(name, None)
            except (OSError, JsDataError) as e:
                self.files[name] = None
                self.load_errors[name] = f"{FILES[name][0]}: {e}"
                log.error("cannot load %s: %s", name, e)
        # drop drafts that equal the disk state, keys that now exist on disk
        for name, d in self.drafts["entries"].items():
            f = self.files.get(name)
            if f is None:
                continue
            disk = {e[f.id_field]: e for e in f.entries()}
            for ident in list(d):
                if d[ident] is not None and disk.get(ident) == d[ident]:
                    d.pop(ident)
        site = self.state.site
        if site is not None:
            for k in list(self.drafts["newKeys"]):
                if site.value("en", k) is not None or site.value("es", k) is not None:
                    vals = self.drafts["newKeys"].pop(k)
                    for lang in ("en", "es"):
                        if site.value(lang, k) is not None and site.value(lang, k) != vals.get(lang, ""):
                            try:
                                self.state.set_draft(lang, k, vals.get(lang, ""))
                            except KeyError:
                                pass
            self.drafts["removedKeys"] = [k for k in self.drafts["removedKeys"] if site.value("en", k) is not None or site.value("es", k) is not None]
        self._write_autosave()

    @property
    def read_only(self) -> Optional[str]:
        problems = list(self.load_errors.values())
        if self.state.site is None:
            problems.append(self.state.load_error or "translations.js not loaded")
        return "; ".join(problems) if problems else None

    # ------------------------------------------------------------- live data
    def live_entries(self, name: str) -> list[dict]:
        """Disk entries with drafts applied (deleted ones removed, new ones appended)."""
        f = self.files.get(name)
        if f is None:
            return []
        d = self.drafts["entries"][name]
        out = []
        seen = set()
        for e in f.entries():
            ident = e[f.id_field]
            seen.add(ident)
            if ident in d:
                if d[ident] is None:
                    continue
                out.append(copy.deepcopy(d[ident]))
            else:
                out.append(e)
        for ident, e in d.items():
            if ident not in seen and e is not None:
                out.append(copy.deepcopy(e))
        return out

    def entry(self, name: str, ident: str) -> Optional[dict]:
        f = self.files[name]
        for e in self.live_entries(name):
            if e.get(f.id_field) == ident:
                return e
        return None

    def _working(self, name: str, ident: str) -> dict:
        """The draft copy of an entry, created on first touch."""
        d = self.drafts["entries"][name]
        if ident in d and d[ident] is not None:
            return d[ident]
        e = self.entry(name, ident)
        if e is None:
            raise KeyError(f"{name}/{ident}")
        d[ident] = copy.deepcopy(e)
        return d[ident]

    def _settle(self, name: str, ident: str) -> None:
        """Drop the draft when it equals the disk entry again."""
        f = self.files[name]
        d = self.drafts["entries"][name]
        disk = next((e for e in f.entries() if e[f.id_field] == ident), None)
        if disk is not None and d.get(ident) == disk:
            d.pop(ident)
        self._write_autosave()

    def texts(self) -> tuple[dict, dict]:
        """EN / ES dicts as they would be after saving (site drafts + new keys − removed)."""
        site = self.state.site
        en, es = site.apply(self.state.drafts) if site else ({}, {})
        for k, v in self.drafts["newKeys"].items():
            en[k], es[k] = v.get("en", ""), v.get("es", "")
        for k in self.drafts["removedKeys"]:
            en.pop(k, None)
            es.pop(k, None)
        return en, es

    def text(self, key: str, lang: str) -> Optional[str]:
        if key in self.drafts["newKeys"]:
            return self.drafts["newKeys"][key].get(lang, "")
        if key in self.drafts["removedKeys"]:
            return None
        v = self.state.drafts.get(f"{lang}.{key}")
        if v is not None:
            return v
        return self.state.site.value(lang, key) if self.state.site else None

    # ------------------------------------------------------------- edits
    def set_field(self, name: str, ident: str, path: list, value: Any = None, delete: bool = False) -> None:
        if self.read_only:
            raise RuntimeError(self.read_only)
        if not path or path[0] in ("slug", "id"):
            raise ValueError("the slug cannot be changed here (a rename wizard comes later)")
        e = self._working(name, ident)
        if delete:
            parent = keymod.get_path(e, path[:-1]) if len(path) > 1 else e
            if isinstance(parent, dict):
                parent.pop(path[-1], None)
            elif isinstance(parent, list) and isinstance(path[-1], int) and 0 <= path[-1] < len(parent):
                del parent[path[-1]]
        else:
            keymod.set_path(e, path, value)
        self._settle(name, ident)

    def set_text(self, name: str, ident: str, field: str, lang: str, value: str) -> str:
        """Set the EN or ES text of an entry's text field; the key is found or invented. Returns the key."""
        if self.read_only:
            raise RuntimeError(self.read_only)
        if lang not in ("en", "es"):
            raise ValueError("lang must be en or es")
        e = self._working(name, ident)
        path = keymod.data_path(name, field)
        key = keymod.get_path(e, path)
        if not key:
            key = keymod.key_for(name, ident, field)
            keymod.set_path(e, path, key)
        site = self.state.site
        on_disk = site is not None and (site.value("en", key) is not None or site.value("es", key) is not None)
        if on_disk and key not in self.drafts["removedKeys"]:
            if site.value(lang, key) is None:
                # the key exists in one language only: complete it as a new-key draft
                self.drafts["newKeys"].setdefault(key, {"en": site.value("en", key) or "", "es": site.value("es", key) or ""})[lang] = value
            else:
                self.state.set_draft(lang, key, value)
        else:
            if key in self.drafts["removedKeys"]:
                self.drafts["removedKeys"].remove(key)
            self.drafts["newKeys"].setdefault(key, {"en": "", "es": ""})[lang] = value
        self._settle(name, ident)
        return key

    def add_entry(self, name: str, ident: str, title_en: str = "", title_es: str = "") -> dict:
        if self.read_only:
            raise RuntimeError(self.read_only)
        problem = keymod.valid_slug(ident)
        if problem:
            raise ValueError(problem)
        f = self.files[name]
        if any(e.get(f.id_field) == ident for e in self.live_entries(name)):
            raise ValueError(f"“{ident}” already exists")
        if name == "projects":
            e = {
                "slug": ident, "titleKey": "", "descKey": "", "longDescKey": "", "dates": {"from": _season_today()},
                "sortDate": order.suggested_sort_date({"from": _season_today()}), "context": "coursework", "tags": [],
                "imageSrc": "", "imageAlt": "", "subpageUrl": "", "featured": False, "pinned": False, "searchTextKey": "",
                "listing": "hidden", "experience": "",
            }
        elif name == "experience":
            e = {
                "slug": ident, "roleKey": "", "orgKey": "", "dates": {"from": _season_today()},
                "sortDate": order.suggested_sort_date({"from": _season_today()}), "bulletKeys": [], "tags": [], "imageSrc": "",
                "imageAltKey": "", "subpageUrl": "", "layout": "textOnly", "status": None, "color": None, "visible": False,
            }
        else:
            raise ValueError("use add_tag for tags")
        self.drafts["entries"][name][ident] = e
        title_field = "title" if name == "projects" else "role"
        self.set_text(name, ident, title_field, "en", title_en)
        self.set_text(name, ident, title_field, "es", title_es)
        if name == "projects":
            for fld in ("desc", "search"):
                self.set_text(name, ident, fld, "en", "")
                self.set_text(name, ident, fld, "es", "")
        else:
            self.set_text(name, ident, "org", "en", "")
            self.set_text(name, ident, "org", "es", "")
        self._write_autosave()
        return self.entry(name, ident)

    def delete_entry(self, name: str, ident: str) -> dict:
        """Mark an entry for deletion; its keys that nothing else references go too."""
        if self.read_only:
            raise RuntimeError(self.read_only)
        f = self.files[name]
        e = self.entry(name, ident)
        if e is None:
            raise KeyError(ident)
        mine = keymod.referenced_keys(name, e)
        d = self.drafts["entries"][name]
        on_disk = ident in f.ids()
        if on_disk:
            d[ident] = None
        else:
            d.pop(ident, None)
        others: set[str] = set()
        for n in FILES:
            for other in self.live_entries(n):
                if n == name and other.get(f.id_field) == ident:
                    continue
                others |= keymod.referenced_keys(n, other)
        removed = sorted(k for k in mine if k not in others)
        for k in removed:
            if k in self.drafts["newKeys"]:
                self.drafts["newKeys"].pop(k)
            elif k not in self.drafts["removedKeys"]:
                self.drafts["removedKeys"].append(k)
            for lang in ("en", "es"):
                self.state.drafts.pop(f"{lang}.{k}", None)
        shell = None
        if name == "projects":
            if self.drafts["shells"].get(ident) == "create":
                self.drafts["shells"].pop(ident)
            elif (self.repo_root / "projects" / f"{ident}.html").is_file():
                self.drafts["shells"][ident] = "delete"
                shell = f"projects/{ident}.html"
        self._write_autosave()
        return {"removedKeys": removed, "shell": shell}

    def create_shell(self, ident: str) -> str:
        if self.read_only:
            raise RuntimeError(self.read_only)
        e = self.entry("projects", ident)
        if e is None:
            raise KeyError(ident)
        if (self.repo_root / "projects" / f"{ident}.html").is_file() and self.drafts["shells"].get(ident) != "delete":
            raise ValueError("the sub-page already exists")
        self.drafts["shells"][ident] = "create"
        w = self._working("projects", ident)
        w["subpageUrl"] = f"/projects/{ident}.html"
        self._settle("projects", ident)
        return w["subpageUrl"]

    def shell_html(self, ident: str) -> bytes:
        tpl = (self.repo_root / SHELL_TEMPLATE).read_text(encoding="utf-8")
        e = self.entry("projects", ident) or {}
        title = self.text(e.get("titleKey", ""), "en") or ident
        desc = self.text(e.get("descKey", ""), "en") or ""
        out = re.sub(r'data-slug="[^"]*"', f'data-slug="{ident}"', tpl)
        out = re.sub(r"<title>.*?</title>", f"<title>{_esc(title)} — Gideon A. Ong</title>", out, count=1, flags=re.S)
        out = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{_esc(desc)}">', out, count=1)
        return out.encode("utf-8")

    def add_tag(self, ident: str, en: str, es: str) -> None:
        if self.read_only:
            raise RuntimeError(self.read_only)
        problem = keymod.valid_slug(ident)
        if problem:
            raise ValueError(problem)
        if any(t.get("id") == ident for t in self.live_entries("tags")):
            raise ValueError(f"tag “{ident}” already exists")
        self.drafts["entries"]["tags"][ident] = {"id": ident, "key": ""}
        self.set_text("tags", ident, "label", "en", en)
        self.set_text("tags", ident, "label", "es", es)

    def delete_tag(self, ident: str) -> dict:
        used = [e.get("slug") for n in ("projects", "experience") for e in self.live_entries(n) if ident in (e.get("tags") or [])]
        if used:
            raise ValueError(f"tag “{ident}” is used by: {', '.join(used)} — remove it there first")
        return self.delete_entry("tags", ident)

    def discard_drafts(self) -> None:
        for info in self.drafts.get("images", {}).values():
            try:
                Path(info["file"]).unlink()
            except OSError:
                pass
        self.drafts = self._empty()
        self._write_autosave()

    def draft_count(self) -> int:
        d = self.drafts
        return (sum(len(v) for v in d["entries"].values()) + len(d["newKeys"]) + len(d["removedKeys"]) + len(d["shells"])
                + len(d.get("images", {})) + len(d.get("removedImages", [])))

    # ------------------------------------------------------------- images (Phase 5)
    IMAGE_FIELDS = {  # alt text field → the property path that holds the file
        "projects": {"imageAlt": ["imageSrc"], "thumbAlt": ["thumbSrc"], "gallery.N.alt": ["gallery", "N", "src"], "page.photos.N.alt": ["page", "photos", "N", "src"]},
        "experience": {"imageAlt": ["imageSrc"]},
    }

    def image_folder(self, name: str, ident: str) -> str:
        kind = {"projects": "projects", "experience": "experience"}.get(name)
        if kind is None:
            raise ValueError("images belong to a project or a role")
        return f"assets/images/{kind}/{ident}"

    def import_image(self, data: bytes, filename: str, name: str, ident: str, field: str, preset: str, alt_en: str, alt_es: str,
                     new_name: str = "", replace: bool = False) -> dict:
        from . import images as imgmod

        if self.read_only:
            raise RuntimeError(self.read_only)
        if not alt_en.strip() or not alt_es.strip():
            raise ValueError("alt text is required in both EN and ES")
        if self.entry(name, ident) is None:
            raise KeyError(f"{name}/{ident}")
        table = self.IMAGE_FIELDS.get(name) or {}
        pattern = re.sub(r"\.(\d+)(?=\.|$)", ".N", field)
        if pattern not in table:
            raise ValueError(f"{field} is not an image field of a {name[:-1]}")
        nums = [int(n) for n in re.findall(r"\.(\d+)(?=\.|$)", field)]
        # the list slot must exist or be the next one, before anything is staged
        probe = [(nums[0] - 1 if p == "N" else p) for p in table[pattern]] if nums else table[pattern]
        if len(probe) > 1 and isinstance(probe[-2], int):
            lst = keymod.get_path(self.entry(name, ident), probe[:-2])
            if probe[-2] > len(lst or []):
                raise ValueError("add the previous gallery / photo items first")
        out, info = imgmod.process(data, preset)
        fname = imgmod.output_name(new_name or filename or "image", preset, info["format"])
        rel = f"{self.image_folder(name, ident)}/{fname}"
        on_disk = (self.repo_root / rel).is_file()
        if on_disk and not replace:
            raise ValueError(f"{rel} already exists — tick “replace” to overwrite it (the old file is backed up)")
        if rel in self.drafts["removedImages"]:
            self.drafts["removedImages"].remove(rel)
        self.image_staging.mkdir(parents=True, exist_ok=True)
        staged = self.image_staging / (re.sub(r"[^a-z0-9]+", "-", rel.lower()).strip("-") + "-" + str(int(time.time() * 1000)) + Path(fname).suffix)
        atomic_write(staged, out)
        old = self.drafts["images"].get(rel)
        if old:
            try:
                Path(old["file"]).unlink()
            except OSError:
                pass
        self.drafts["images"][rel] = {"file": str(staged), "preset": preset, "source": filename, "width": info["width"], "height": info["height"], "kb": info["kb"], "replace": on_disk,
                                      "hadExif": info["hadExif"], "hadGps": info["hadGps"], "transposed": info["transposed"]}
        # the file path into the entry, then the alt text (keys named by the conventions)
        path = [(nums.pop(0) - 1 if p == "N" else p) for p in table[pattern]]
        e = self._working(name, ident)
        container = keymod.get_path(e, path[:-1]) if len(path) > 1 else e
        if isinstance(path[-2] if len(path) > 1 else None, int) and container is None:
            lst = keymod.get_path(e, path[:-2])
            if lst is None:
                keymod.set_path(e, path[:-2], [])
                lst = keymod.get_path(e, path[:-2])
            if path[-2] == len(lst):
                lst.append({"src": "", "altKey": ""})
            elif path[-2] > len(lst):
                raise ValueError("add the previous gallery / photo items first")
        keymod.set_path(e, path, rel)
        self._settle(name, ident)
        key = self.set_text(name, ident, field, "en", alt_en.strip())
        self.set_text(name, ident, field, "es", alt_es.strip())
        self._write_autosave()
        return {"path": rel, "key": key, **{k: v for k, v in self.drafts["images"][rel].items() if k != "file"}}

    def image_refs(self) -> dict[str, list[str]]:
        """rel path → who uses it (entries and fields, plus HTML pages)."""
        refs: dict[str, list[str]] = {}

        def add(rel, who):
            if rel:
                refs.setdefault(rel, []).append(who)

        for e in self.live_entries("projects"):
            s = e.get("slug")
            add(e.get("imageSrc"), f"project {s}: main image")
            add(e.get("thumbSrc"), f"project {s}: thumbnail")
            for i, g in enumerate(e.get("gallery") or [], 1):
                if isinstance(g, dict):
                    add(g.get("src"), f"project {s}: collage {i}")
            for i, ph in enumerate((e.get("page") or {}).get("photos") or [], 1):
                if isinstance(ph, dict):
                    add(ph.get("src"), f"project {s}: photo {i}")
        for e in self.live_entries("experience"):
            add(e.get("imageSrc"), f"role {e.get('slug')}: band image")
        for html in self.repo_root.glob("*.html"):
            try:
                text = html.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in re.finditer(r"assets/images/[\w./-]+", text):
                add(m.group(0), html.name)
        return refs

    def delete_image(self, rel: str) -> dict:
        if self.read_only:
            raise RuntimeError(self.read_only)
        rel = rel.replace("\\", "/").lstrip("/")
        if not rel.startswith("assets/images/") or ".." in rel:
            raise ValueError("only files under assets/images/ can be removed here")
        users = self.image_refs().get(rel, [])
        if users:
            raise ValueError(f"{rel} is still used by: {', '.join(users)} — change those first")
        if rel in self.drafts["images"]:
            try:
                Path(self.drafts["images"][rel]["file"]).unlink()
            except OSError:
                pass
            self.drafts["images"].pop(rel)
            self._write_autosave()
            return {"pending": True}
        if not (self.repo_root / rel).is_file():
            raise KeyError(rel)
        if rel not in self.drafts["removedImages"]:
            self.drafts["removedImages"].append(rel)
        self._write_autosave()
        return {"pending": False}

    def images_state(self) -> dict:
        from . import images as imgmod

        refs = self.image_refs()
        rows = []
        for item in imgmod.scan(self.repo_root):
            rel = item["path"]
            rows.append(dict(item, users=refs.get(rel, []), pending=None, removed=rel in self.drafts["removedImages"]))
        for rel, info in self.drafts["images"].items():
            rows.append({"path": rel, "info": {"width": info["width"], "height": info["height"], "kb": info["kb"], "format": Path(rel).suffix[1:], "exifTags": [], "gps": False, "icc": False},
                         "warnings": [], "users": refs.get(rel, []), "pending": "replace" if info.get("replace") else "add", "removed": False})
        rows.sort(key=lambda r: r["path"])
        return {"images": rows, "presets": {k: v["label"] for k, v in imgmod.PRESETS.items()}}

    # ------------------------------------------------------------- autosave
    def _read_autosave(self) -> Optional[dict]:
        try:
            if self.autosave_path.is_file():
                j = json.loads(self.autosave_path.read_text(encoding="utf-8"))
                d = j.get("drafts") if isinstance(j, dict) else None
                if isinstance(d, dict) and (any(d.get(k) for k in ("newKeys", "removedKeys", "shells", "images", "removedImages")) or any((d.get("entries") or {}).values())):
                    return j
        except (OSError, ValueError) as e:
            log.warning("content autosave unreadable: %s", e)
        return None

    def _write_autosave(self) -> None:
        try:
            if not self.draft_count():
                if self.autosave_path.exists():
                    self.autosave_path.unlink()
                return
            self.autosave_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(self.autosave_path, json.dumps({"saved": datetime.now().isoformat(timespec="seconds"), "drafts": self.drafts}, indent=2, ensure_ascii=False).encode("utf-8"))
        except OSError as e:
            log.warning("content autosave failed: %s", e)

    def restore_autosave(self) -> dict:
        pend, self.pending_autosave = self.pending_autosave, None
        if not pend:
            return {"applied": 0}
        d = pend.get("drafts") or {}
        base = self._empty()
        for k in base:
            if k in d and type(d[k]) is type(base[k]):
                base[k] = d[k]
        self.drafts = base
        self.load()
        return {"applied": self.draft_count()}

    def discard_autosave(self) -> None:
        self.pending_autosave = None
        if not self.draft_count() and self.autosave_path.exists():
            try:
                self.autosave_path.unlink()
            except OSError:
                pass

    # ------------------------------------------------------------- checks
    def _check(self, en: dict, es: dict, projects, experience, tags, shells_exist, pending_files=()) -> list[validate.Issue]:
        from ..cv import scans
        from ..cv.masters import BLOCKLIST_PATH

        terms, _ = scans.load_blocklist(self.repo_root / BLOCKLIST_PATH)
        return datacheck.check(self.repo_root, en, es, projects, experience, tags, blocklist_terms=terms, shells_exist=shells_exist, pending_files=pending_files)

    def baseline_issues(self) -> list[validate.Issue]:
        site = self.state.site
        if site is None or any(f is None for f in self.files.values()):
            return []
        en, es = site.as_dicts()
        return self._check(en, es, self.files["projects"].entries(), self.files["experience"].entries(), self.files["tags"].entries(), None)

    def draft_issues(self) -> list[validate.Issue]:
        if self.read_only:
            return []
        en, es = self.texts()
        shells = {}
        for e in self.live_entries("projects"):
            slug = e.get("slug")
            action = self.drafts["shells"].get(slug)
            shells[slug] = action == "create" or (action != "delete" and (self.repo_root / "projects" / f"{slug}.html").is_file())
        return self._check(en, es, self.live_entries("projects"), self.live_entries("experience"), self.live_entries("tags"), shells,
                           pending_files=set(self.drafts.get("images", {})))

    def touched(self) -> set[str]:
        t = {f"{n}:{ident}" for n, d in self.drafts["entries"].items() for ident in d}
        t |= {f"keys:{k}" for k in list(self.drafts["newKeys"]) + self.drafts["removedKeys"]}
        return t

    def gate(self) -> validate.SaveGate:
        return validate.blocking(self.baseline_issues(), self.draft_issues(), self.touched())

    # ------------------------------------------------------------- render / review / save
    def _touched_files(self) -> list[str]:
        return [n for n, d in self.drafts["entries"].items() if d]

    def image_checks(self) -> list[validate.Issue]:
        """Warnings for pending imports that still carried camera data (already stripped) — informational."""
        return []

    def render_file(self, name: str) -> bytes:
        f = self.files[name]
        d = self.drafts["entries"][name]
        on_disk = set(f.ids())
        existing = {k: v for k, v in d.items() if k in on_disk}
        new = [v for k, v in d.items() if k not in on_disk and v is not None]
        return f.render(existing, new)

    def render_translations(self) -> bytes:
        site = self.state.site
        return site.render(self.state.drafts, adds=self.drafts["newKeys"], removes=self.drafts["removedKeys"])

    def preview_overrides(self) -> dict:
        if self.read_only:
            return {}
        out = {}
        for n in self._touched_files():
            out[self.files[n].rel_path] = self.render_file(n)
        if self.drafts["newKeys"] or self.drafts["removedKeys"]:
            out[SiteText.REL_PATH] = self.render_translations()
        for slug, action in self.drafts["shells"].items():
            if action == "create":
                out[f"projects/{slug}.html"] = self.shell_html(slug)
        for rel, info in self.drafts.get("images", {}).items():
            try:
                out[rel] = Path(info["file"]).read_bytes()
            except OSError:
                pass
        return out

    def review(self) -> dict:
        if self.read_only:
            return {"readOnly": True, "error": self.read_only}
        files, changes = [], []
        disk_changed = False
        for n in self._touched_files():
            f = self.files[n]
            new = self.render_file(n)
            dc = f.disk_changed()
            disk_changed = disk_changed or dc
            files.append({"path": f.rel_path, "diff": unified_diff(f.raw, new, f.rel_path), "diskChanged": dc})
            changes += self._entry_changes(n)
        site = self.state.site
        if self.drafts["newKeys"] or self.drafts["removedKeys"] or self.state.drafts:
            from .. import review as review_mod

            new = self.render_translations()
            dc = site.disk_changed()
            disk_changed = disk_changed or dc
            files.append({"path": SiteText.REL_PATH, "diff": unified_diff(site.raw, new, SiteText.REL_PATH), "diskChanged": dc})
            j = site.to_json()
            for c in review_mod.change_list(self.state.drafts, j["entries"], j["sections"]):
                changes.append({"text": c["text"]})
        for k, v in self.drafts["newKeys"].items():
            changes.append({"text": f"Text › new: {k} — EN “{v.get('en', '')[:60]}”, ES “{v.get('es', '')[:60]}”"})
        for k in self.drafts["removedKeys"]:
            changes.append({"text": f"Text › removed: {k}"})
        shells = [{"slug": s, "action": a, "path": f"projects/{s}.html"} for s, a in self.drafts["shells"].items()]
        assets = [{"path": rel, "action": "replace" if i.get("replace") else "add", "kb": i["kb"], "size": f"{i['width']} × {i['height']}"} for rel, i in self.drafts.get("images", {}).items()]
        assets += [{"path": rel, "action": "remove"} for rel in self.drafts.get("removedImages", [])]
        gate = self.gate()
        site_gate = self.state.gate()
        return {
            "readOnly": False,
            "files": files,
            "changes": changes,
            "shells": shells,
            "assets": assets,
            "siteTextDrafts": len(self.state.drafts),
            "gate": gate.to_json(),
            "siteTextGate": site_gate.to_json(),
            "diskChanged": disk_changed,
            "noop": not files and not shells and not assets,
        }

    def _entry_changes(self, name: str) -> list[dict]:
        from ..jsonfile import changes as diff_changes

        f = self.files[name]
        disk = {e[f.id_field]: e for e in f.entries()}
        out = []
        label = {"projects": "Projects", "experience": "Experience", "tags": "Tags"}[name]
        for ident, new in self.drafts["entries"][name].items():
            if new is None:
                out.append({"text": f"{label} › {ident}: deleted"})
            elif ident not in disk:
                out.append({"text": f"{label} › {ident}: added"})
            else:
                for c in diff_changes(disk[ident], new):
                    where = ".".join(str(p) for p in c["path"])
                    if c["kind"] == "added":
                        out.append({"text": f"{label} › {ident} › {where}: added {json.dumps(c['new'], ensure_ascii=False)[:80]}"})
                    elif c["kind"] == "removed":
                        out.append({"text": f"{label} › {ident} › {where}: removed"})
                    else:
                        out.append({"text": f"{label} › {ident} › {where}: {json.dumps(c['old'], ensure_ascii=False)[:60]} → {json.dumps(c['new'], ensure_ascii=False)[:60]}"})
        return out

    def save(self) -> dict:
        if self.read_only:
            return {"ok": False, "error": "read-only", "message": self.read_only}
        if not self.draft_count() and not self.state.drafts:
            return {"ok": True, "noop": True, "message": "Nothing to save."}
        touched = self._touched_files()
        for n in touched:
            if self.files[n].disk_changed():
                return {"ok": False, "error": "changed-on-disk", "message": f"{self.files[n].rel_path} changed on disk since it was loaded. Reload and re-apply your edits."}
        site = self.state.site
        write_site = bool(self.drafts["newKeys"] or self.drafts["removedKeys"] or self.state.drafts)
        if write_site and site.disk_changed():
            return {"ok": False, "error": "changed-on-disk", "message": "js/translations.js changed on disk since it was loaded. Reload and re-apply your edits."}
        gate = self.gate()
        if not gate.ok():
            return {"ok": False, "error": "blocked", "message": "Fix the blocking errors first.", "gate": gate.to_json()}
        if write_site and not self.state.gate().ok():
            return {"ok": False, "error": "blocked", "message": "Fix the blocking errors in the site text first.", "gate": self.state.gate().to_json()}
        rendered = {n: self.render_file(n) for n in touched}
        site_bytes = self.render_translations() if write_site else None
        paths = [self.files[n].rel_path for n in touched] + ([SiteText.REL_PATH] if write_site else [])
        paths += [f"projects/{s}.html" for s, a in self.drafts["shells"].items() if a == "delete"]
        paths += [rel for rel, i in self.drafts.get("images", {}).items() if i.get("replace")]
        paths += list(self.drafts.get("removedImages", []))
        bset = self.state.backups.create(paths, "before saving content")
        written = []
        try:
            for rel, info in self.drafts.get("images", {}).items():
                dst = self.repo_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(dst, Path(info["file"]).read_bytes())
                written.append(rel)
            for rel in self.drafts.get("removedImages", []):
                p = self.repo_root / rel
                if p.is_file():
                    p.unlink()
                    written.append(f"{rel} (removed)")
                    # an emptied <slug>/ folder goes too (git would not keep it anyway)
                    parent = p.parent
                    images_root = self.repo_root / "assets" / "images"
                    while parent != images_root and parent.is_relative_to(images_root) and parent.is_dir() and not any(parent.iterdir()):
                        parent.rmdir()
                        parent = parent.parent
            for n in touched:
                atomic_write(self.files[n].path, rendered[n])
                written.append(self.files[n].rel_path)
            if write_site:
                atomic_write(site.path, site_bytes)
                written.append(SiteText.REL_PATH)
            for slug, action in self.drafts["shells"].items():
                p = self.repo_root / "projects" / f"{slug}.html"
                if action == "create":
                    atomic_write(p, self.shell_html(slug))
                    written.append(f"projects/{slug}.html")
                elif action == "delete" and p.is_file():
                    p.unlink()
                    written.append(f"projects/{slug}.html (removed)")
        except OSError as e:
            log.warning("content save failed: %s", e)
            return {"ok": False, "error": "write-failed", "message": f"A file could not be written ({e}) — it is probably open in another program. Written so far: {', '.join(written) or 'nothing'}; backup set {bset.id}.", "backup": bset.id}
        for info in self.drafts.get("images", {}).values():
            try:
                Path(info["file"]).unlink()
            except OSError:
                pass
        self.drafts = self._empty()
        self._write_autosave()
        if write_site:
            self.state.drafts.clear()
            self.state._write_autosave()
        self.state.load()
        self.load()
        log.info("saved content %s (backup %s)", written, bset.id)
        return {"ok": True, "backup": bset.id, "written": written, "message": f"Saved {', '.join(written)}. Backup set {bset.id}."}

    # ------------------------------------------------------------- pickers / state
    def images(self) -> list[dict]:
        root = self.repo_root / "assets" / "images"
        out = []
        if root.is_dir():
            for p in sorted(root.rglob("*")):
                if p.is_file() and p.suffix.lower() in IMAGE_EXT:
                    out.append({"path": p.relative_to(self.repo_root).as_posix(), "size": p.stat().st_size})
        return out

    def pdfs(self) -> list[str]:
        root = self.repo_root / "assets" / "pdfs" / "projects"
        return sorted(p.relative_to(self.repo_root).as_posix() for p in root.glob("*.pdf")) if root.is_dir() else []

    def state_json(self) -> dict:
        en, es = self.texts() if not self.read_only else ({}, {})
        issues = self.draft_issues()
        gate = self.gate() if not self.read_only else None
        by_owner: dict[str, list] = {}
        for i in issues:
            by_owner.setdefault(i.key, []).append(i.to_json())
        drafted = {n: list(d) for n, d in self.drafts["entries"].items()}
        projects = order.projects_display(self.live_entries("projects")) if not self.read_only else []
        experience = order.experience_display(self.live_entries("experience")) if not self.read_only else []
        tags = self.live_entries("tags") if not self.read_only else []
        uses: dict[str, int] = {}
        for n in ("projects", "experience"):
            for e in self.live_entries(n):
                for t in e.get("tags") or []:
                    uses[t] = uses.get(t, 0) + 1
        return {
            "readOnly": self.read_only,
            "files": {n: {"path": FILES[n][0], "loaded": self.files.get(n) is not None, "diskChanged": self.files[n].disk_changed() if self.files.get(n) else False} for n in FILES},
            "projects": [dict(e, _draft=e["slug"] in drafted["projects"], _meta=self._meta(e, en, es)) for e in projects],
            "experience": [dict(e, _draft=e["slug"] in drafted["experience"], _meta=self._meta(e, en, es)) for e in experience],
            "tags": [dict(t, _draft=t["id"] in drafted["tags"], uses=uses.get(t["id"], 0)) for t in tags],
            "deleted": {n: [k for k, v in d.items() if v is None] for n, d in self.drafts["entries"].items()},
            "texts": {"en": {k: en.get(k) for k in self._all_keys()}, "es": {k: es.get(k) for k in self._all_keys()}},
            "issues": by_owner,
            "gate": gate.to_json() if gate else None,
            "draftCount": self.draft_count(),
            "siteTextDrafts": len(self.state.drafts),
            "shells": self.drafts["shells"],
            "shellsOnDisk": sorted(p.stem for p in (self.repo_root / "projects").glob("*.html")),
            "images": self.images() + [{"path": rel, "size": i["kb"] * 1024, "pending": True} for rel, i in self.drafts.get("images", {}).items() if not (self.repo_root / rel).is_file()],
            "pendingImages": {rel: {k: v for k, v in i.items() if k != "file"} for rel, i in self.drafts.get("images", {}).items()},
            "presets": {k: v["label"] for k, v in __import__("core.site.images", fromlist=["PRESETS"]).PRESETS.items()},
            "removedImages": list(self.drafts.get("removedImages", [])),
            "pdfs": self.pdfs(),
            "autosave": {"saved": self.pending_autosave.get("saved")} if self.pending_autosave else None,
            "vocab": {"contexts": list(order.CONTEXTS), "listings": list(order.LISTINGS), "homeLayouts": list(order.HOME_LAYOUTS), "expLayouts": list(order.EXP_LAYOUTS), "seasons": list(order.SEASONS)},
        }

    def _all_keys(self) -> set[str]:
        keys: set[str] = set()
        for n in FILES:
            for e in self.live_entries(n):
                keys |= keymod.referenced_keys(n, e)
        return keys

    def _meta(self, e: dict, en: dict, es: dict) -> dict:
        return {
            "datesEn": order.format_dates(e.get("dates"), "en", en, es),
            "datesEs": order.format_dates(e.get("dates"), "es", en, es),
            "suggestedSortDate": order.suggested_sort_date(e.get("dates")),
        }


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
