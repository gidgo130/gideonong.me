"""Key naming (CLAUDE.md → Data conventions) and which entry fields hold keys.

    proj<SlugCamel>Title / Desc / LongDesc / Alt / Search / Gallery<N>Alt /
        Section<N>Heading / Section<N>Body / Fact<N>Label / Fact<N>Value / Photo<N>Alt / Credit
    exp<SlugCamel>Role / Org / OrgShort / Bullet<N> / ImageAlt
    tag<IdCamel>
A "text field" is addressed as (file, slug, field) where `field` is a dotted
path with 1-based indexes for lists: "title", "gallery.2.alt", "page.sections.1.body",
"bullets.3". The key stored in the data file for that field is derived here.
"""

from __future__ import annotations

import re
from typing import Optional

from ..site_text import slug_camel

# field path (as the form addresses it) → (data-file property path, key suffix)
# The data-file path uses the real property names; list indexes are filled in.
PROJECT_TEXT = {
    "title": ("titleKey", "Title"),
    "desc": ("descKey", "Desc"),
    "longDesc": ("longDescKey", "LongDesc"),
    "search": ("searchTextKey", "Search"),
    "imageAlt": ("imageAlt", "Alt"),
    "thumbAlt": ("thumbAltKey", "ThumbAlt"),  # only when a thumb needs its own alt
    "gallery.N.alt": ("gallery.N.altKey", "GalleryNAlt"),
    "page.sections.N.heading": ("page.sections.N.headingKey", "SectionNHeading"),
    "page.sections.N.body": ("page.sections.N.bodyKey", "SectionNBody"),
    "page.facts.N.label": ("page.facts.N.labelKey", "FactNLabel"),
    "page.facts.N.value": ("page.facts.N.valueKey", "FactNValue"),
    "page.photos.N.alt": ("page.photos.N.altKey", "PhotoNAlt"),
    "page.credit": ("page.creditKey", "Credit"),
}
EXPERIENCE_TEXT = {
    "role": ("roleKey", "Role"),
    "org": ("orgKey", "Org"),
    "orgShort": ("orgShortKey", "OrgShort"),
    "bullets.N": ("bulletKeys.N", "BulletN"),
    "imageAlt": ("imageAltKey", "ImageAlt"),
}
TAG_TEXT = {"label": ("key", "")}
PREFIX = {"projects": "proj", "experience": "exp", "tags": "tag"}
TEXT_FIELDS = {"projects": PROJECT_TEXT, "experience": EXPERIENCE_TEXT, "tags": TAG_TEXT}

_NUM = re.compile(r"\.(\d+)(?=\.|$)")


def entry_prefix(file: str, slug: str) -> str:
    return PREFIX[file] + slug_camel(slug)


def _match(field: str, table: dict) -> tuple[str, str, list[int]]:
    """(data path template, key suffix template, indexes) for a field path like page.facts.2.label."""
    pattern = _NUM.sub(".N", field)
    if pattern not in table:
        raise KeyError(field)
    nums = [int(n) for n in _NUM.findall(field)]
    return table[pattern][0], table[pattern][1], nums


def key_for(file: str, slug: str, field: str) -> str:
    """The i18n key the conventions give this text field."""
    _, suffix, nums = _match(field, TEXT_FIELDS[file])
    for n in nums:
        suffix = suffix.replace("N", str(n), 1)
    return entry_prefix(file, slug) + suffix


def data_path(file: str, field: str) -> list:
    """The property path inside the entry that stores the key ("page.facts.2.labelKey" → ["page","facts",1,"labelKey"])."""
    template, _, nums = _match(field, TEXT_FIELDS[file])
    out: list = []
    it = iter(nums)
    for part in template.split("."):
        out.append(next(it) - 1 if part == "N" else part)
    return out


def get_path(obj, path: list):
    cur = obj
    for p in path:
        if cur is None:
            return None
        try:
            cur = cur[p]
        except (KeyError, IndexError, TypeError):
            return None
    return cur


def set_path(obj, path: list, value) -> None:
    cur = obj
    for p in path[:-1]:
        nxt = cur[p] if not isinstance(cur, list) or p < len(cur) else None
        if nxt is None:
            nxt = [] if isinstance(path[path.index(p) + 1], int) else {}
            cur[p] = nxt
        cur = nxt
    last = path[-1]
    if isinstance(cur, list) and last == len(cur):
        cur.append(value)
    else:
        cur[last] = value


def referenced_keys(file: str, entry: dict) -> set[str]:
    """Every i18n key an entry references (any field that holds a key)."""
    keys: set[str] = set()
    if file == "about":  # inline EN/ES text, no translations keys
        return keys
    if file == "tags":
        if entry.get("key"):
            keys.add(entry["key"])
        return keys
    if file == "experience":
        for f in ("roleKey", "orgKey", "orgShortKey", "imageAltKey"):
            if entry.get(f):
                keys.add(entry[f])
        keys.update(k for k in entry.get("bulletKeys", []) if k)
        return keys
    for f in ("titleKey", "descKey", "longDescKey", "imageAlt", "thumbAltKey", "searchTextKey"):
        if entry.get(f):
            keys.add(entry[f])
    for g in entry.get("gallery") or []:
        if isinstance(g, dict) and g.get("altKey"):
            keys.add(g["altKey"])
    page = entry.get("page") or {}
    if isinstance(page, dict):
        for s in page.get("sections") or []:
            for f in ("headingKey", "bodyKey"):
                if isinstance(s, dict) and s.get(f):
                    keys.add(s[f])
        for s in page.get("facts") or []:
            for f in ("labelKey", "valueKey"):
                if isinstance(s, dict) and s.get(f):
                    keys.add(s[f])
        for s in page.get("photos") or []:
            if isinstance(s, dict) and s.get("altKey"):
                keys.add(s["altKey"])
        if page.get("creditKey"):
            keys.add(page["creditKey"])
    return keys


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def valid_slug(slug: str) -> Optional[str]:
    """None when the slug is fine, else the problem."""
    if not slug:
        return "the slug is empty"
    if not SLUG_RE.match(slug):
        return "use lowercase letters, digits and single hyphens (e.g. pump-cylinder-failure)"
    if len(slug) > 60:
        return "keep the slug under 60 characters"
    return None
