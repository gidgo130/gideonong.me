"""What the Content page talks to. Owned by app.EditorState as `content`.

Drafts (autosaved to .local/drafts/content.json):
    entries:     {file: {slug: entry dict | None (delete)}}   — full live entry, keyed by the
                                                                 slug ON DISK (a renamed entry
                                                                 keeps its disk key)
    newKeys:     {key: {"en": str, "es": str}}                — keys not on disk yet
    removedKeys: [key, ...]                                   — keys to delete
    shells:      {slug: "create" | "delete"}                  — projects/<slug>.html
    renames:     {entries: {file: {new slug: disk slug}},     — the slug-rename wizard:
                  keys: {new key: old key},                      keys renamed in place in
                  files: {old rel: new rel},                     translations.js, files and
                  summary: {file: {new slug: {...}}}}            folders moved on save
Text edits to keys that exist on disk go through the Site text drafts
(EditorState.set_draft), so both tabs share one translations.js review.
"""

from __future__ import annotations

import copy
import json
import logging
import os
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
from . import about as aboutmod
from . import datacheck, keys as keymod, order
from .datafiles import FILES as DATA_FILES, DataFile

FILES = dict(DATA_FILES, about=(aboutmod.REL_PATH, "ABOUT_*", "id"))  # the About lists edit like a fourth data file

log = logging.getLogger("editor.content")

SHELL_TEMPLATE = "projects/g-view.html"
# Link-preview cards (made by scripts/make-og-cards.py): a sub-page's card is <slug>.jpg|png here.
OG_DIR = "assets/images/og/"
OG_EXT = (".jpg", ".png")
# The template's link-preview block (comment + og:/twitter: metas) belongs to G-View: a new
# shell drops it, so it never shares with another page's card. CLAUDE.md → Link previews.
_OG_BLOCK = re.compile(r'^[ \t]*(?:<!-- Link previews\b.*?-->|<meta (?:property="og:|name="twitter:)[^>]*>)[ \t]*\r?\n', re.M | re.S)
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
        return {"entries": {"projects": {}, "experience": {}, "tags": {}, "about": {}}, "newKeys": {}, "removedKeys": [], "shells": {}, "images": {}, "removedImages": [],
                "aboutOrder": {}, "aboutShown": {}, "renames": {"entries": {}, "keys": {}, "files": {}, "summary": {}}}

    def _normalize(self) -> None:
        """Fill in draft parts an older autosave may lack."""
        for k, v in self._empty().items():
            if k not in self.drafts:
                self.drafts[k] = v
        for k, v in self._empty()["renames"].items():
            self.drafts["renames"].setdefault(k, v)
        self.drafts["entries"].setdefault("about", {})

    # ------------------------------------------------------------- the slug-rename map
    def _disk_ident(self, name: str, ident: str) -> str:
        """The slug an entry has on disk (a pending rename maps the new slug back to it)."""
        return self.drafts["renames"]["entries"].get(name, {}).get(ident, ident)

    def _new_ident(self, name: str, disk_ident: str) -> str:
        for new, old in self.drafts["renames"]["entries"].get(name, {}).items():
            if old == disk_ident:
                return new
        return disk_ident

    @property
    def image_staging(self) -> Path:
        return Path(self.state.local_dir) / "drafts" / "images"

    # ------------------------------------------------------------- loading
    def load(self) -> None:
        self._normalize()
        for name in FILES:
            try:
                self.files[name] = aboutmod.AboutFile(self.repo_root) if name == "about" else DataFile(self.repo_root, name)
                self.load_errors.pop(name, None)
            except (OSError, JsDataError) as e:
                self.files[name] = None
                self.load_errors[name] = f"{FILES[name][0]}: {e}"
                log.error("cannot load %s: %s", name, e)
        try:
            self.page_raw: Optional[bytes] = (self.repo_root / aboutmod.PAGE).read_bytes()
        except OSError:
            self.page_raw = None
        for k in list(self.drafts.get("aboutShown", {})):  # a flag that equals the page again is no draft
            if self.page_raw is not None and aboutmod.read_shown(self.page_raw.decode("utf-8", "replace")).get(k) == self.drafts["aboutShown"][k]:
                self.drafts["aboutShown"].pop(k)
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
        if name == "about" and self.drafts.get("aboutOrder"):
            for lst, ids in self.drafts["aboutOrder"].items():
                mine = [e for e in out if e.get("_list") == lst]
                by = {e["id"]: e for e in mine}
                wanted = [by[i] for i in ids if i in by] + [e for e in mine if e["id"] not in ids]
                it = iter(wanted)
                out = [next(it) if e.get("_list") == lst else e for e in out]
        return out

    def entry(self, name: str, ident: str) -> Optional[dict]:
        f = self.files[name]
        for e in self.live_entries(name):
            if e.get(f.id_field) == ident:
                return e
        return None

    def _working(self, name: str, ident: str) -> dict:
        """The draft copy of an entry, created on first touch (keyed by its slug on disk)."""
        d = self.drafts["entries"][name]
        key = self._disk_ident(name, ident)
        if key in d and d[key] is not None:
            return d[key]
        e = self.entry(name, ident)
        if e is None:
            raise KeyError(f"{name}/{ident}")
        d[key] = copy.deepcopy(e)
        return d[key]

    def _settle(self, name: str, ident: str) -> None:
        """Drop the draft when it equals the disk entry again."""
        f = self.files[name]
        d = self.drafts["entries"][name]
        key = self._disk_ident(name, ident)
        disk = next((e for e in f.entries() if e[f.id_field] == key), None)
        if disk is not None and d.get(key) == disk:
            d.pop(key)
            self.drafts["renames"]["entries"].get(name, {}).pop(ident, None)
            self.drafts["renames"]["summary"].get(name, {}).pop(ident, None)
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
        for new, old in self.drafts["renames"]["keys"].items():
            if old in en:
                en[new] = en.pop(old)
            if old in es:
                es[new] = es.pop(old)
        return en, es

    def text(self, key: str, lang: str) -> Optional[str]:
        key = self.drafts["renames"]["keys"].get(key, key)
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
        stored = key
        key = self.drafts["renames"]["keys"].get(key, key)  # a renamed key is still its old self on disk
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
        return stored

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

    # ------------------------------------------------------------- the slug-rename wizard
    def rename_entry(self, name: str, old: str, new: str) -> dict:
        """Rename a project's or role's slug everywhere, as a draft: the entry, its keys (in
        place in translations.js), its image paths and sub-page URL, references from other
        entries, the sub-page file and the image folder (moved on save)."""
        if self.read_only:
            raise RuntimeError(self.read_only)
        if name not in ("projects", "experience"):
            raise ValueError("only projects and roles have slugs")
        new = (new or "").strip()
        problem = keymod.valid_slug(new)
        if problem:
            raise ValueError(problem)
        if new == old:
            raise ValueError("that is the current slug")
        f = self.files[name]
        if any(e.get("slug") == new for e in self.live_entries(name)):
            raise ValueError(f"“{new}” already exists")
        e = self.entry(name, old)
        if e is None:
            raise KeyError(f"{name}/{old}")
        disk_ident = self._disk_ident(name, old)
        if self.drafts["entries"][name].get(disk_ident, "x") is None:
            raise ValueError("this entry is marked for deletion")
        w = self._working(name, old)
        kind = "projects" if name == "projects" else "experience"
        old_prefix, new_prefix = keymod.entry_prefix(name, old), keymod.entry_prefix(name, new)
        summary = {"from": old, "to": new, "keys": [], "keysKept": [], "paths": 0, "references": [], "files": []}
        # 1. keys: rename every key that follows the convention and belongs to this entry alone
        others: set[str] = set()
        for n in FILES:
            for other in self.live_entries(n):
                if n == name and other.get("slug") == old:
                    continue
                others |= keymod.referenced_keys(n, other)
        rename_map: dict[str, str] = {}
        for k in sorted(keymod.referenced_keys(name, e)):
            follows = k.startswith(old_prefix) and (len(k) == len(old_prefix) or k[len(old_prefix)].isupper() or k[len(old_prefix)].isdigit())
            if follows and k not in others:
                rename_map[k] = new_prefix + k[len(old_prefix):]
            else:
                summary["keysKept"].append(k)
        _replace_strings(w, rename_map)
        for k_old, k_new in rename_map.items():
            if k_old in self.drafts["newKeys"]:  # not on disk yet: just rename the pending key
                self.drafts["newKeys"][k_new] = self.drafts["newKeys"].pop(k_old)
            else:
                origin = self.drafts["renames"]["keys"].pop(k_old, k_old)  # a rename of a rename keeps the disk name
                if origin == k_new:
                    continue
                self.drafts["renames"]["keys"][k_new] = origin
            summary["keys"].append([k_old, k_new])
        # 2. paths inside the entry
        folder_old, folder_new = f"assets/images/{kind}/{old}/", f"assets/images/{kind}/{new}/"
        summary["paths"] = _replace_prefix(w, folder_old, folder_new)
        if name == "projects" and w.get("subpageUrl") == f"/projects/{old}.html":
            w["subpageUrl"] = f"/projects/{new}.html"
            summary["paths"] += 1
        # 3. references from other entries
        if name == "experience":
            for p in self.live_entries("projects"):
                if p.get("experience") == old:
                    self._working("projects", p["slug"])["experience"] = new
                    summary["references"].append(f"project {p['slug']} › Part of")
        forms = {f"projects/{old}.html": f"projects/{new}.html"} if name == "projects" else {f"projects.html?part={old}": f"projects.html?part={new}"}
        for x in self.live_entries("experience"):
            link = x.get("imageLink") or ""
            if link in forms:
                target = w if (name == "experience" and x.get("slug") == old) else self._working("experience", x["slug"])
                target["imageLink"] = forms[link]
                summary["references"].append(f"role {x['slug']} › image link")
        # files inside the moved folder that OTHER entries point at (a band image borrowed from a project)
        for n in ("projects", "experience", "about"):
            id_field = "id" if n == "about" else "slug"
            for x in self.live_entries(n):
                if n == name and x.get(id_field) == old:
                    continue
                if _replace_prefix(copy.deepcopy(x), folder_old, folder_new):
                    _replace_prefix(self._working(n, x[id_field]), folder_old, folder_new)
                    summary["references"].append(f"{'project' if n == 'projects' else 'role' if n == 'experience' else 'about'} {x[id_field]} › image path")
        # 4. files: the sub-page shell and the image folder move on save
        files = self.drafts["renames"]["files"]
        if name == "projects":
            shell_old, shell_new = f"projects/{old}.html", f"projects/{new}.html"
            if self.drafts["shells"].get(old) == "create":
                self.drafts["shells"].pop(old)
                self.drafts["shells"][new] = "create"
            elif (self.repo_root / shell_old).is_file() and self.drafts["shells"].get(old) != "delete":
                origin = next((o for o, t in files.items() if t == shell_old), None)
                if origin:
                    files.pop(origin)
                    if origin != shell_new:
                        files[origin] = shell_new
                else:
                    files[shell_old] = shell_new
                summary["files"].append([shell_old, shell_new])
            for ext in OG_EXT:  # the link-preview card follows its slug
                card_old, card_new = f"{OG_DIR}{old}{ext}", f"{OG_DIR}{new}{ext}"
                origin = next((o for o, t in files.items() if t == card_old), None)
                if origin:
                    files.pop(origin)
                    if origin != card_new:
                        files[origin] = card_new
                elif (self.repo_root / card_old).is_file():
                    files[card_old] = card_new
                else:
                    continue
                summary["files"].append([card_old, card_new])
        if (self.repo_root / folder_old).is_dir():
            origin = next((o for o, t in files.items() if t == folder_old), None)
            if origin:
                files.pop(origin)
                if origin != folder_new:
                    files[origin] = folder_new
            else:
                files[folder_old] = folder_new
            summary["files"].append([folder_old, folder_new])
        for rel in list(self.drafts["images"]):
            if rel.startswith(folder_old):
                self.drafts["images"][folder_new + rel[len(folder_old):]] = self.drafts["images"].pop(rel)
        self.drafts["removedImages"] = [folder_new + r[len(folder_old):] if r.startswith(folder_old) else r for r in self.drafts["removedImages"]]
        # 5. the slug itself; the draft stays under the disk slug
        w["slug"] = new
        ent = self.drafts["renames"]["entries"].setdefault(name, {})
        ent.pop(old, None)
        if new != disk_ident:
            ent[new] = disk_ident
        summ = self.drafts["renames"]["summary"].setdefault(name, {})
        summ.pop(old, None)
        summ[new] = summary
        self._settle(name, new)
        return dict(summary, entry=self.entry(name, new))

    def _renamed_files(self) -> list[dict]:
        """Pending moves as [{from, to, kind}] with the files a folder move carries."""
        out = []
        for old, new in self.drafts["renames"]["files"].items():
            if old.endswith("/"):
                folder = self.repo_root / old
                names = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()) if folder.is_dir() else []
                out.append({"from": old, "to": new, "kind": "folder", "files": names})
            else:
                out.append({"from": old, "to": new, "kind": "file", "files": []})
        return out

    def _renamed_shell_bytes(self, old_rel: str, new_slug: str) -> bytes:
        if not old_rel.endswith(".html"):  # a link-preview card moves as it is
            return (self.repo_root / old_rel).read_bytes()
        text = (self.repo_root / old_rel).read_text(encoding="utf-8")
        old_slug = Path(old_rel).stem
        text = text.replace(f'/projects/{old_slug}.html">', f'/projects/{new_slug}.html">')  # og:url
        text = text.replace(f"{OG_DIR}{old_slug}.", f"{OG_DIR}{new_slug}.")  # og:image and its comment
        return re.sub(r'data-slug="[^"]*"', f'data-slug="{new_slug}"', text, count=1).encode("utf-8")

    # ------------------------------------------------------------- the About lists
    def add_about_entry(self, list_name: str, ident: str, en: str = "", es: str = "") -> dict:
        if self.read_only:
            raise RuntimeError(self.read_only)
        if list_name not in aboutmod.LISTS:
            raise ValueError("list must be books, faq or sites")
        problem = keymod.valid_slug(ident)
        if problem:
            raise ValueError(problem)
        if any(e.get("id") == ident for e in self.live_entries("about")):
            raise ValueError(f"“{ident}” already exists")
        self.drafts["entries"]["about"][ident] = aboutmod.new_entry(list_name, ident, en.strip(), es.strip())
        self._write_autosave()
        return self.entry("about", ident)

    def set_about_order(self, list_name: str, ids: list) -> None:
        if self.read_only:
            raise RuntimeError(self.read_only)
        if list_name not in aboutmod.LISTS:
            raise ValueError("list must be books, faq or sites")
        current = [e["id"] for e in self.live_entries("about") if e.get("_list") == list_name]
        if sorted(ids) != sorted(current) or len(set(ids)) != len(ids):
            raise ValueError("the order must name every entry of the list exactly once")
        f = self.files["about"]
        disk = [e["id"] for e in f.list_entries(list_name)] if f else []
        new_ids = [i for i in ids if i not in disk]
        if list(ids) == disk + new_ids:  # the file's own order (new entries after it): no draft
            self.drafts["aboutOrder"].pop(list_name, None)
        else:
            self.drafts["aboutOrder"][list_name] = list(ids)
        self._write_autosave()

    def set_about_shown(self, section_id: str, shown: bool) -> None:
        if self.read_only:
            raise RuntimeError(self.read_only)
        if section_id not in aboutmod.SECTIONS.values():
            raise ValueError("unknown About block")
        if self.page_raw is None:
            raise RuntimeError(f"{aboutmod.PAGE} could not be read")
        on_disk = aboutmod.read_shown(self.page_raw.decode("utf-8", "replace")).get(section_id)
        if on_disk == bool(shown):
            self.drafts["aboutShown"].pop(section_id, None)
        else:
            self.drafts["aboutShown"][section_id] = bool(shown)
        self._write_autosave()

    def about_shown(self) -> dict:
        """block id → shown, drafts applied."""
        cur = aboutmod.read_shown(self.page_raw.decode("utf-8", "replace")) if self.page_raw is not None else {}
        cur.update(self.drafts.get("aboutShown", {}))
        return cur

    def render_page(self) -> bytes:
        html = self.page_raw.decode("utf-8") if self.page_raw is not None else ""
        return aboutmod.render_shown(html, self.drafts.get("aboutShown", {})).encode("utf-8")

    def page_disk_changed(self) -> bool:
        try:
            return (self.repo_root / aboutmod.PAGE).read_bytes() != self.page_raw
        except OSError:
            return True

    def delete_entry(self, name: str, ident: str) -> dict:
        """Mark an entry for deletion; its keys that nothing else references go too."""
        if self.read_only:
            raise RuntimeError(self.read_only)
        f = self.files[name]
        e = self.entry(name, ident)
        if e is None:
            raise KeyError(ident)
        keys_map = self.drafts["renames"]["keys"]
        mine = {keys_map.get(k, k) for k in keymod.referenced_keys(name, e)}  # renamed keys by their disk names
        d = self.drafts["entries"][name]
        disk_ident = self._disk_ident(name, ident)
        if disk_ident != ident:  # a pending rename: undo it, then delete the disk entry
            self.drafts["renames"]["entries"].get(name, {}).pop(ident, None)
            self.drafts["renames"]["summary"].get(name, {}).pop(ident, None)
            for k_new in [k for k, v in keys_map.items() if v in mine]:
                keys_map.pop(k_new)
            kind = "projects" if name == "projects" else "experience"
            for old_rel in [o for o, t in self.drafts["renames"]["files"].items() if t in (f"projects/{ident}.html", f"assets/images/{kind}/{ident}/") + tuple(f"{OG_DIR}{ident}{x}" for x in OG_EXT)]:
                self.drafts["renames"]["files"].pop(old_rel)
            ident = disk_ident
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
        out = _OG_BLOCK.sub("", tpl)
        out = re.sub(r'data-slug="[^"]*"', f'data-slug="{ident}"', out)
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
                + len(d.get("images", {})) + len(d.get("removedImages", [])) + len(d.get("aboutOrder", {})) + len(d.get("aboutShown", {}))
                + len(d.get("renames", {}).get("files", {})))

    # ------------------------------------------------------------- images (Phase 5)
    IMAGE_FIELDS = {  # alt text field → the property path that holds the file
        "projects": {"imageAlt": ["imageSrc"], "thumbAlt": ["thumbSrc"], "gallery.N.alt": ["gallery", "N", "src"], "page.photos.N.alt": ["page", "photos", "N", "src"]},
        "experience": {"imageAlt": ["imageSrc"]},
        "about": {"cover": ["coverSrc"]},  # book covers: decorative (the strip is aria-hidden), no alt text
    }

    def image_folder(self, name: str, ident: str) -> str:
        if name == "about":
            return aboutmod.COVER_DIR
        kind = {"projects": "projects", "experience": "experience"}.get(name)
        if kind is None:
            raise ValueError("images belong to a project or a role")
        return f"assets/images/{kind}/{ident}"

    def import_image(self, data: bytes, filename: str, name: str, ident: str, field: str, preset: str, alt_en: str, alt_es: str,
                     new_name: str = "", replace: bool = False) -> dict:
        from . import images as imgmod

        if self.read_only:
            raise RuntimeError(self.read_only)
        if name != "about" and (not alt_en.strip() or not alt_es.strip()):
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
        key = None
        if name != "about":
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
        for e in self.live_entries("about"):
            if e.get("_list") == "books":
                add(e.get("coverSrc"), f"book {e.get('id')}: cover")
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
    def _check(self, en: dict, es: dict, projects, experience, tags, shells_exist, pending_files=(), about=None, about_shown=None) -> list[validate.Issue]:
        from ..cv import scans
        from ..cv.masters import BLOCKLIST_PATH

        terms, _ = scans.load_blocklist(self.repo_root / BLOCKLIST_PATH)
        return datacheck.check(self.repo_root, en, es, projects, experience, tags, blocklist_terms=terms, shells_exist=shells_exist, pending_files=pending_files,
                               about=about, about_shown=about_shown)

    def baseline_issues(self) -> list[validate.Issue]:
        site = self.state.site
        if site is None or any(f is None for f in self.files.values()):
            return []
        en, es = site.as_dicts()
        disk_shown = aboutmod.read_shown(self.page_raw.decode("utf-8", "replace")) if self.page_raw is not None else {}
        return self._check(en, es, self.files["projects"].entries(), self.files["experience"].entries(), self.files["tags"].entries(), None,
                           about=self.files["about"].entries(), about_shown=disk_shown)

    def draft_issues(self) -> list[validate.Issue]:
        if self.read_only:
            return []
        en, es = self.texts()
        renamed_to = set(self.drafts["renames"]["files"].values())
        shells = {}
        for e in self.live_entries("projects"):
            slug = e.get("slug")
            action = self.drafts["shells"].get(slug)
            shells[slug] = action == "create" or (action != "delete" and (self.repo_root / "projects" / f"{slug}.html").is_file()) or f"projects/{slug}.html" in renamed_to
        pending = set(self.drafts.get("images", {}))
        for mv in self._renamed_files():
            if mv["kind"] == "folder":
                pending |= {mv["to"] + n for n in mv["files"]}
        return self._check(en, es, self.live_entries("projects"), self.live_entries("experience"), self.live_entries("tags"), shells,
                           pending_files=pending, about=self.live_entries("about"), about_shown=self.about_shown())

    def touched(self) -> set[str]:
        t = {f"{n}:{ident}" for n, d in self.drafts["entries"].items() for ident in d}
        t |= {f"keys:{k}" for k in list(self.drafts["newKeys"]) + self.drafts["removedKeys"]}
        return t

    def gate(self) -> validate.SaveGate:
        return validate.blocking(self.baseline_issues(), self.draft_issues(), self.touched())

    # ------------------------------------------------------------- render / review / save
    def _touched_files(self) -> list[str]:
        return [n for n, d in self.drafts["entries"].items() if d or (n == "about" and self.drafts.get("aboutOrder"))]

    def image_checks(self) -> list[validate.Issue]:
        """Warnings for pending imports that still carried camera data (already stripped) — informational."""
        return []

    def render_file(self, name: str) -> bytes:
        f = self.files[name]
        d = self.drafts["entries"][name]
        on_disk = set(f.ids())
        existing = {k: v for k, v in d.items() if k in on_disk}
        new = [v for k, v in d.items() if k not in on_disk and v is not None]
        if name == "about":
            return f.render(existing, new, self.drafts.get("aboutOrder", {}))
        return f.render(existing, new)

    def render_translations(self) -> bytes:
        site = self.state.site
        renames = {old: new for new, old in self.drafts["renames"]["keys"].items()}
        return site.render(self.state.drafts, adds=self.drafts["newKeys"], removes=self.drafts["removedKeys"], renames=renames)

    def preview_overrides(self) -> dict:
        if self.read_only:
            return {}
        out = {}
        for n in self._touched_files():
            out[self.files[n].rel_path] = self.render_file(n)
        if self.drafts["newKeys"] or self.drafts["removedKeys"] or self.drafts["renames"]["keys"]:
            out[SiteText.REL_PATH] = self.render_translations()
        if self.drafts.get("aboutShown"):
            out[aboutmod.PAGE] = self.render_page()
        for slug, action in self.drafts["shells"].items():
            if action == "create":
                out[f"projects/{slug}.html"] = self.shell_html(slug)
        for mv in self._renamed_files():  # pending moves: the new paths serve the old files
            if mv["kind"] == "file":
                try:
                    out[mv["to"]] = self._renamed_shell_bytes(mv["from"], Path(mv["to"]).stem)
                except OSError:
                    pass
            else:
                for n in mv["files"]:
                    out[mv["to"] + n] = self.repo_root / mv["from"] / n
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
        if self.drafts["newKeys"] or self.drafts["removedKeys"] or self.state.drafts or self.drafts["renames"]["keys"]:
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
        for lst in self.drafts.get("aboutOrder", {}):
            changes.append({"text": f"About › {aboutmod.LABELS[lst]}: order changed"})
        for n, summ in self.drafts["renames"]["summary"].items():
            for new, s in summ.items():
                label = "project" if n == "projects" else "role"
                bits = [f"{len(s['keys'])} key(s) renamed in place", f"{s['paths']} path(s)"] + [f"{len(s['references'])} reference(s) in other entries"] * bool(s["references"]) + [f"{len(s['files'])} file / folder move(s)"] * bool(s["files"])
                changes.insert(0, {"text": f"Rename {label} “{s['from']}” → “{new}”: " + ", ".join(bits) + (" — keys kept as they are: " + ", ".join(s["keysKept"]) if s["keysKept"] else "")})
        renames = self._renamed_files()
        if self.drafts.get("aboutShown"):
            new = self.render_page()
            dc = self.page_disk_changed()
            disk_changed = disk_changed or dc
            files.append({"path": aboutmod.PAGE, "diff": unified_diff(self.page_raw or b"", new, aboutmod.PAGE), "diskChanged": dc})
            names = {v: k for k, v in aboutmod.SECTIONS.items()}
            for sec, shown in self.drafts["aboutShown"].items():
                changes.append({"text": f"About › {aboutmod.LABELS[names[sec]]}: {'shown on the site' if shown else 'hidden on the site'}"})
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
            "renames": renames,
            "gate": gate.to_json(),
            "siteTextGate": site_gate.to_json(),
            "diskChanged": disk_changed,
            "noop": not files and not shells and not assets and not renames,
        }

    def _entry_changes(self, name: str) -> list[dict]:
        from ..jsonfile import changes as diff_changes

        f = self.files[name]
        disk = {e[f.id_field]: e for e in f.entries()}
        out = []
        label = {"projects": "Projects", "experience": "Experience", "tags": "Tags", "about": "About"}[name]
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
        write_site = bool(self.drafts["newKeys"] or self.drafts["removedKeys"] or self.state.drafts or self.drafts["renames"]["keys"])
        if write_site and site.disk_changed():
            return {"ok": False, "error": "changed-on-disk", "message": "js/translations.js changed on disk since it was loaded. Reload and re-apply your edits."}
        write_page = bool(self.drafts.get("aboutShown"))
        if write_page and self.page_disk_changed():
            return {"ok": False, "error": "changed-on-disk", "message": f"{aboutmod.PAGE} changed on disk since it was loaded. Reload and re-apply your edits."}
        gate = self.gate()
        if not gate.ok():
            return {"ok": False, "error": "blocked", "message": "Fix the blocking errors first.", "gate": gate.to_json()}
        if write_site and not self.state.gate().ok():
            return {"ok": False, "error": "blocked", "message": "Fix the blocking errors in the site text first.", "gate": self.state.gate().to_json()}
        rendered = {n: self.render_file(n) for n in touched}
        site_bytes = self.render_translations() if write_site else None
        paths = [self.files[n].rel_path for n in touched] + ([SiteText.REL_PATH] if write_site else []) + ([aboutmod.PAGE] if write_page else [])
        paths += [f"projects/{s}.html" for s, a in self.drafts["shells"].items() if a == "delete"]
        paths += [rel for rel, i in self.drafts.get("images", {}).items() if i.get("replace")]
        paths += list(self.drafts.get("removedImages", []))
        moves = self._renamed_files()
        for mv in moves:
            paths += [mv["from"]] if mv["kind"] == "file" else [mv["from"] + n for n in mv["files"]]
            if (self.repo_root / mv["to"]).exists():
                return {"ok": False, "error": "blocked", "message": f"{mv['to']} already exists — the rename cannot move {mv['from']} there."}
        bset = self.state.backups.create(paths, "before saving content")
        written = []
        try:
            for mv in moves:  # moves first, so the data files never point at files that are not there yet
                src, dst = self.repo_root / mv["from"], self.repo_root / mv["to"]
                if mv["kind"] == "file":
                    atomic_write(dst, self._renamed_shell_bytes(mv["from"], Path(mv["to"]).stem))
                    src.unlink()
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(src, dst)
                written.append(f"{mv['from']} → {mv['to']}")
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
            if write_page:
                atomic_write(self.repo_root / aboutmod.PAGE, self.render_page())
                written.append(aboutmod.PAGE)
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
        drafted = {n: [self._new_ident(n, k) for k in d] for n, d in self.drafts["entries"].items()}
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
            "about": {
                "lists": {lst: [dict(e, _draft=e["id"] in drafted["about"]) for e in self.live_entries("about") if e.get("_list") == lst] for lst in aboutmod.LISTS} if not self.read_only else {},
                "labels": aboutmod.LABELS,
                "sections": aboutmod.SECTIONS,
                "shown": self.about_shown(),
                "shownDrafts": dict(self.drafts.get("aboutShown", {})),
                "orderDrafts": list(self.drafts.get("aboutOrder", {})),
                "coverDir": aboutmod.COVER_DIR,
            },
            "deleted": {n: [k for k, v in d.items() if v is None] for n, d in self.drafts["entries"].items()},
            "texts": {"en": {k: en.get(k) for k in self._all_keys()}, "es": {k: es.get(k) for k in self._all_keys()}},
            "issues": by_owner,
            "gate": gate.to_json() if gate else None,
            "draftCount": self.draft_count(),
            "siteTextDrafts": len(self.state.drafts),
            "shells": self.drafts["shells"],
            "renamed": self.drafts["renames"]["entries"],
            "shellsOnDisk": sorted(p.stem for p in (self.repo_root / "projects").glob("*.html")) + [Path(t).stem for t in self.drafts["renames"]["files"].values() if t.endswith(".html")],
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


def _replace_strings(obj: Any, mapping: dict) -> int:
    """Replace, in place, every string value of a nested dict / list that is a key of `mapping`."""
    n = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v in mapping:
                obj[k] = mapping[v]
                n += 1
            else:
                n += _replace_strings(v, mapping)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and v in mapping:
                obj[i] = mapping[v]
                n += 1
            else:
                n += _replace_strings(v, mapping)
    return n


def _replace_prefix(obj: Any, old: str, new: str) -> int:
    """Replace, in place, the prefix of every string value that starts with `old`."""
    n = 0
    if isinstance(obj, dict):
        items = list(obj.items())
        for k, v in items:
            if isinstance(v, str) and v.startswith(old):
                obj[k] = new + v[len(old):]
                n += 1
            else:
                n += _replace_prefix(v, old, new)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and v.startswith(old):
                obj[i] = new + v[len(old):]
                n += 1
            else:
                n += _replace_prefix(v, old, new)
    return n
