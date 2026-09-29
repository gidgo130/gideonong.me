"""Python port of siteData.checkData (js/data-helpers.js), as validate.Issues.

The JS check only warns in the browser console. Here the plan's §5 table decides:
errors block a save, warnings do not. Issue keys are "<file>:<slug>" (or
"<file>:<slug>.<field>") so the gate can tell "touched" entries apart.

Errors: missing EN/ES key, unknown tag id, duplicate slug, bad or hidden
`experience` target, image / PDF / shell path that does not exist, malformed
`dates` or a sortDate that disagrees, more than 3 featured, featured on a
non-index entry, reserved "nested" or unknown listing / context / homeLayout /
layout, gallery and page shape problems, TODO or HTML in visible text, a
blocklist hit in any deployable string.
Warnings: unused per-entry keys, ES = EN, voice words, two visible "current"
roles, ES tag label much longer than EN, empty-key fields the site tolerates.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional

from .. import validate
from ..validate import Issue
from . import keys as keymod
from .order import CONTEXTS, EXP_LAYOUTS, FEATURED_MAX, GALLERY_MAX, GALLERY_MIN, HOME_LAYOUTS, LISTINGS, SEASON_MONTHS, projects_featured

SORT_DATE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class Checker:
    def __init__(self, repo_root: Path, en: dict, es: dict, projects: list[dict], experience: list[dict], tags: list[dict],
                 hidden_prefixes: Iterable[str] = (), blocklist_terms: Optional[list] = None, shells_exist: Optional[dict] = None,
                 pending_files: Iterable[str] = (), about: Optional[list[dict]] = None, about_shown: Optional[dict] = None):
        self.root = Path(repo_root)
        self.pending_files = set(pending_files)  # files a draft will add on save (imported images)
        self.about = about  # the About page's lists (core/site/about.py), or None to skip them
        self.about_shown = about_shown  # block id → shown (the `hidden` attribute in about.html)
        self.en, self.es = en, es
        self.projects, self.experience, self.tags = projects, experience, tags
        self.hidden = list(hidden_prefixes)
        self.terms = blocklist_terms or []
        self.shells_exist = shells_exist  # slug → bool (tests inject); None → look on disk
        self.issues: list[Issue] = []
        self.tag_ids = {t.get("id") for t in tags if isinstance(t, dict)}

    # ------------------------------------------------------------- helpers
    def err(self, key: str, code: str, msg: str, lang: str = "") -> None:
        self.issues.append(Issue("error", code, key, lang, msg))

    def warn(self, key: str, code: str, msg: str, lang: str = "") -> None:
        self.issues.append(Issue("warning", code, key, lang, msg))

    def key_present(self, owner: str, field: str, k, visible: bool = True) -> None:
        if not k or not isinstance(k, str):
            self.err(owner, "empty-key", f"{field} is empty")
            return
        for lang, d in (("en", self.en), ("es", self.es)):
            v = d.get(k)
            if v is None or (visible and not v.strip()):
                self.err(owner, "missing-key", f"{field}: no {lang.upper()} text yet", lang)
            elif not v.strip():
                self.warn(owner, "missing-key", f"{field}: no {lang.upper()} text yet (entry is hidden)", lang)
            elif visible and validate.is_todo(v):
                self.err(owner, "todo", f"{field} ({lang.upper()}) still says TODO", lang)
            elif visible and validate.has_html(v):
                self.err(owner, "html", f"{field} ({lang.upper()}) contains HTML", lang)
            elif visible:
                self._scan_text(owner, field, lang, v)
        e, s = self.en.get(k), self.es.get(k)
        if e is not None and s is not None and e == s and not validate.identical_allowed(k, e):
            self.warn(owner, "same", f"{field}: ES is identical to EN")

    def _scan_text(self, owner: str, field: str, lang: str, v: str) -> None:
        words = validate.voice_words(v)
        if words:
            self.warn(owner, "voice", f"{field} ({lang.upper()}): voice words {', '.join(words)}", lang)
        if self.terms:
            from ..cv import scans

            for h in scans.blocklist_hits(v, self.terms):
                self.err(owner, "blocklist", f"{field} ({lang.upper()}): blocked term “{h['term']}” ({h['reason'] or 'no reason given'})", lang)

    def file_exists(self, owner: str, field: str, rel: str) -> None:
        if not rel:
            return
        if rel.lstrip("/") in self.pending_files:
            return
        p = self.root / rel.lstrip("/")
        if not p.is_file():
            self.err(owner, "missing-file", f"{field}: {rel} does not exist")

    def check_tags(self, owner: str, tags) -> None:
        if tags is None:
            return
        if not isinstance(tags, list):
            self.err(owner, "shape", "tags must be a list of tag ids")
            return
        for t in tags:
            if t not in self.tag_ids:
                self.err(owner, "unknown-tag", f"unknown tag id “{t}”")

    def check_point(self, owner: str, field: str, p) -> bool:
        if not isinstance(p, dict):
            self.err(owner, "dates", f"{field} must be {{ season, year }}, {{ month, year }} or {{ year }}")
            return False
        ok = True
        if not isinstance(p.get("year"), int) or isinstance(p.get("year"), bool):
            self.err(owner, "dates", f"{field}.year must be a whole number")
            ok = False
        if "season" in p and p["season"] not in SEASON_MONTHS:
            self.err(owner, "dates", f"{field}.season “{p['season']}” (expected spring | summer | fall | winter)")
            ok = False
        if "month" in p and not (isinstance(p["month"], int) and 1 <= p["month"] <= 12):
            self.err(owner, "dates", f"{field}.month must be 1–12")
            ok = False
        if "season" in p and "month" in p:
            self.err(owner, "dates", f"{field} has both season and month — use one")
            ok = False
        return ok

    def check_dates(self, owner: str, dates, sort_date) -> None:
        if not isinstance(dates, dict):
            self.err(owner, "dates", "dates must be { from, to? } — never a literal string")
            return
        from_ok = self.check_point(owner, "dates.from", dates.get("from"))
        to = dates.get("to")
        to_ok = True
        if to not in (None, "", "present"):
            to_ok = self.check_point(owner, "dates.to", to)
        if not isinstance(sort_date, str) or not SORT_DATE.match(sort_date):
            self.err(owner, "sortDate", "missing or malformed sortDate (expected “YYYY-MM”)")
            return
        if not from_ok or not to_ok:
            return
        ref = to if isinstance(to, dict) else dates.get("from")
        y, m = int(sort_date[:4]), int(sort_date[5:7])
        if ref.get("year") != y:
            self.err(owner, "sortDate", f"sortDate {sort_date} does not match the dates year {ref.get('year')}")
        elif "month" in ref and ref["month"] != m:
            self.err(owner, "sortDate", f"sortDate {sort_date} does not match dates month {ref['month']}")
        elif "season" in ref and m not in SEASON_MONTHS.get(ref["season"], ()):
            self.err(owner, "sortDate", f"sortDate {sort_date} is outside {ref['season']}")

    # ------------------------------------------------------------- run
    def run(self) -> list[Issue]:
        self.issues = []
        seen = set()
        for t in self.tags:
            owner = f"tags:{t.get('id') or '?'}"
            if not t.get("id"):
                self.err(owner, "empty-key", "tag without an id")
            elif t["id"] in seen:
                self.err(owner, "duplicate", f"duplicate tag id “{t['id']}”")
            seen.add(t.get("id"))
            self.key_present(owner, "label", t.get("key"))
            k = t.get("key")
            e, s = self.en.get(k, ""), self.es.get(k, "")
            if e and s and len(s) > len(e) * 1.3 + 2:
                self.warn(owner, "long-label", f"ES label “{s}” is much longer than EN “{e}” — the pill will resize")
        exp_slugs: dict[str, dict] = {}
        current = 0
        for i, e in enumerate(self.experience):
            slug = e.get("slug") or f"#{i}"
            owner = f"experience:{slug}"
            if not e.get("slug"):
                self.err(owner, "slug", "missing slug")
            elif e["slug"] in exp_slugs:
                self.err(owner, "duplicate", f"duplicate slug “{e['slug']}”")
            exp_slugs[e.get("slug")] = e
            vis = bool(e.get("visible"))
            self.key_present(owner, "role", e.get("roleKey"), vis)
            self.key_present(owner, "organization", e.get("orgKey"), vis)
            if e.get("orgShortKey"):
                self.key_present(owner, "short organization", e["orgShortKey"], vis)
            if e.get("imageLink") is not None and not isinstance(e.get("imageLink"), str):
                self.err(owner, "shape", "imageLink must be a URL string")
            if e.get("imageLink") and not e.get("imageSrc"):
                self.err(owner, "image", "imageLink set without an image — nothing to link")
            if e.get("imageSrc"):
                self.file_exists(owner, "image", e["imageSrc"])
                if e.get("layout") != "textOnly":
                    if not e.get("imageAltKey"):
                        self.err(owner, "alt", "the band image has no alt text")
                    else:
                        self.key_present(owner, "image alt", e["imageAltKey"], vis)
            for n, k in enumerate(e.get("bulletKeys") or [], 1):
                self.key_present(owner, f"bullet {n}", k, vis)
            self.check_tags(owner, e.get("tags"))
            self.check_dates(owner, e.get("dates"), e.get("sortDate"))
            if e.get("layout") not in EXP_LAYOUTS:
                self.err(owner, "layout", f"unknown layout “{e.get('layout')}” (expected {' | '.join(EXP_LAYOUTS)})")
            if e.get("status") == "current" and vis:
                current += 1
            if e.get("subpageUrl"):
                self.file_exists(owner, "subpageUrl", e["subpageUrl"])
        if current > 1:
            self.warn("experience:", "current", "more than one visible role is marked current — the hero shows the first")
        proj_slugs = set()
        featured = 0
        for i, p in enumerate(self.projects):
            slug = p.get("slug") or f"#{i}"
            owner = f"projects:{slug}"
            if not p.get("slug"):
                self.err(owner, "slug", "missing slug")
            elif p["slug"] in proj_slugs:
                self.err(owner, "duplicate", f"duplicate slug “{p['slug']}”")
            proj_slugs.add(p.get("slug"))
            listing = p.get("listing")
            vis = listing in ("index", "unlisted")
            if listing == "nested":
                self.err(owner, "listing", "listing “nested” is reserved and not implemented — the entry will not render")
            elif listing not in LISTINGS:
                self.err(owner, "listing", f"unknown listing “{listing}” (expected index | unlisted | hidden)")
            self.key_present(owner, "title", p.get("titleKey"), vis)
            self.key_present(owner, "description", p.get("descKey"), vis)
            if p.get("featured") or p.get("longDescKey"):
                self.key_present(owner, "long description", p.get("longDescKey"), vis)
            self.key_present(owner, "search text", p.get("searchTextKey"), False)
            if p.get("imageSrc"):
                self.file_exists(owner, "image", p["imageSrc"])
                if not p.get("imageAlt"):
                    self.err(owner, "alt", "the image has no alt text")
                else:
                    self.key_present(owner, "image alt", p["imageAlt"], vis)
            if p.get("thumbSrc"):
                self.file_exists(owner, "thumbnail", p["thumbSrc"])
                if not p.get("imageSrc"):
                    self.err(owner, "image", "a thumbnail without a main image — the row shows nothing")
                if not p.get("thumbAltKey"):
                    self.err(owner, "alt", "the thumbnail has no alt text")
                else:
                    self.key_present(owner, "thumbnail alt", p["thumbAltKey"], vis)
            self.check_tags(owner, p.get("tags"))
            if p.get("experience"):
                target = exp_slugs.get(p["experience"])
                if target is None:
                    self.err(owner, "experience", f"“Part of” role “{p['experience']}” matches no role")
                elif not target.get("visible"):
                    self.err(owner, "experience", f"“Part of” role “{p['experience']}” is hidden — the link would be omitted")
            if p.get("featured") and listing != "index":
                self.err(owner, "featured", f"featured on a non-index entry (listing “{listing}”)")
            if p.get("featured") and listing == "index":
                featured += 1
            fo = p.get("featuredOrder")
            if fo is not None and (not isinstance(fo, (int, float)) or isinstance(fo, bool)):
                self.err(owner, "featured", "featuredOrder must be a number")
            self.check_dates(owner, p.get("dates"), p.get("sortDate"))
            if not p.get("context"):
                self.err(owner, "context", "missing context")
            elif p["context"] not in CONTEXTS:
                self.err(owner, "context", f"unknown context “{p['context']}” (expected {' | '.join(CONTEXTS)})")
            hl = p.get("homeLayout")
            if hl is not None and hl not in HOME_LAYOUTS:
                self.err(owner, "homeLayout", f"unknown homeLayout “{hl}” (expected {' | '.join(HOME_LAYOUTS)})")
            g = p.get("gallery")
            if g is not None:
                if not isinstance(g, list):
                    self.err(owner, "gallery", "gallery must be a list of { src, altKey }")
                else:
                    if hl != "collage":
                        self.err(owner, "gallery", "gallery is set but homeLayout is not “collage” — it would be ignored")
                    if len(g) > GALLERY_MAX:
                        self.err(owner, "gallery", f"gallery has {len(g)} images (max {GALLERY_MAX})")
                    if hl == "collage" and len(g) < GALLERY_MIN:
                        self.err(owner, "gallery", f"a collage needs at least {GALLERY_MIN} images")
                    for n, item in enumerate(g, 1):
                        if not isinstance(item, dict) or not item.get("src"):
                            self.err(owner, "gallery", f"gallery image {n} has no file")
                        else:
                            self.file_exists(owner, f"gallery image {n}", item["src"])
                        if isinstance(item, dict) and not item.get("altKey"):
                            self.err(owner, "gallery", f"gallery image {n} has no alt text")
                        elif isinstance(item, dict):
                            self.key_present(owner, f"gallery image {n} alt", item["altKey"], vis)
            page = p.get("page")
            if page is not None:
                if not isinstance(page, dict):
                    self.err(owner, "page", "page must be an object { sections, facts, photos, reportPdf, creditKey }")
                else:
                    if not p.get("subpageUrl"):
                        self.err(owner, "page", "sub-page content is set but there is no sub-page — create the sub-page")
                    for n, s in enumerate(page.get("sections") or [], 1):
                        if not isinstance(s, dict):
                            self.err(owner, "page", f"section {n} is empty")
                            continue
                        self.key_present(owner, f"section {n} heading", s.get("headingKey"), vis)
                        self.key_present(owner, f"section {n} body", s.get("bodyKey"), vis)
                    for n, f in enumerate(page.get("facts") or [], 1):
                        if not isinstance(f, dict):
                            self.err(owner, "page", f"fact {n} is empty")
                            continue
                        self.key_present(owner, f"fact {n} label", f.get("labelKey"), vis)
                        self.key_present(owner, f"fact {n} value", f.get("valueKey"), vis)
                    for n, ph in enumerate(page.get("photos") or [], 1):
                        if not isinstance(ph, dict) or not ph.get("src"):
                            self.err(owner, "page", f"photo {n} has no file")
                        else:
                            self.file_exists(owner, f"photo {n}", ph["src"])
                        if isinstance(ph, dict) and not ph.get("altKey"):
                            self.err(owner, "page", f"photo {n} has no alt text")
                        elif isinstance(ph, dict):
                            self.key_present(owner, f"photo {n} alt", ph["altKey"], vis)
                    if page.get("reportPdf") is not None and not isinstance(page.get("reportPdf"), str):
                        self.err(owner, "page", "reportPdf must be a path or “”")
                    elif page.get("reportPdf"):
                        self.file_exists(owner, "report PDF", page["reportPdf"])
                    if page.get("creditKey"):
                        self.key_present(owner, "credit", page["creditKey"], vis)
            if p.get("subpageUrl"):
                exists = self.shells_exist.get(p["slug"]) if self.shells_exist is not None else (self.root / p["subpageUrl"].lstrip("/")).is_file()
                if not exists:
                    self.err(owner, "missing-file", f"sub-page {p['subpageUrl']} does not exist — create it or clear subpageUrl")
        if featured > FEATURED_MAX:
            self.err("projects:", "featured", f"{featured} featured projects (max {FEATURED_MAX}) — the site shows the first three")
        self._about()
        self._unused_keys()
        return self.issues

    def _about(self) -> None:
        if self.about is None:
            return
        from . import about as aboutmod

        shown = self.about_shown
        if shown is None:
            try:
                shown = aboutmod.read_shown((self.root / aboutmod.PAGE).read_text(encoding="utf-8", errors="replace"))
            except OSError:
                shown = {}
        self.issues += aboutmod.check(self.about, self.root, self.pending_files, self.terms, shown)

    def _unused_keys(self) -> None:
        referenced: set[str] = set()
        for p in self.projects:
            referenced |= keymod.referenced_keys("projects", p)
        for e in self.experience:
            referenced |= keymod.referenced_keys("experience", e)
        for t in self.tags:
            referenced |= keymod.referenced_keys("tags", t)
        family = re.compile(r"^(proj|exp|tag)[A-Z]")
        chrome = re.compile(r"^(proj|exp)(Search|Featured|Index|View|Part|Tag|Count|Empty|Report|All|Lightbox|CaseStudy|Current|Related|Hero)")
        for k in list(self.en) + [k for k in self.es if k not in self.en]:
            if family.match(k) and not chrome.match(k) and k not in referenced:
                self.warn(f"keys:{k}", "unused-key", f"{k} is not referenced by any entry")


def check(repo_root: Path, en: dict, es: dict, projects: list[dict], experience: list[dict], tags: list[dict], **kw) -> list[Issue]:
    return Checker(repo_root, en, es, projects, experience, tags, **kw).run()
