"""The About page's three lists (js/about-data.js: ABOUT_BOOKS, ABOUT_FAQ,
ABOUT_SITES) as one data file for the Content tab, and the `hidden` attribute
of their blocks in about.html.

AboutFile reads the three arrays of the one file into entries that carry a
`_list` marker (books | faq | sites); ids are unique across the lists. Text is
inline EN/ES (titleEN / titleES …), not translations keys. render() writes
per-entry span edits like the other data files; a reordered list is re-emitted
as a whole (one entry per line, the file's own style).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from .. import emit, spans, validate
from ..jsdata import ArrayNode, Document, JsDataError, ObjectNode, sha256_bytes
from ..validate import Issue
from .datafiles import DataFile

REL_PATH = "js/about-data.js"
PAGE = "about.html"
LISTS = {"books": "ABOUT_BOOKS", "faq": "ABOUT_FAQ", "sites": "ABOUT_SITES"}
SECTIONS = {"books": "about-reading", "faq": "about-faq", "sites": "about-sites"}
LABELS = {"books": "Books", "faq": "FAQ", "sites": "Interesting sites"}
FIELD_ORDER = {
    "books": ["id", "coverSrc", "titleEN", "titleES", "descEN", "descES", "visible"],
    "faq": ["id", "questionEN", "questionES", "answerEN", "answerES", "visible"],
    "sites": ["id", "url", "internal", "labelEN", "labelES", "descEN", "descES", "visible"],
}
# (EN field, ES field, label) per list
TEXT_PAIRS = {
    "books": [("titleEN", "titleES", "title"), ("descEN", "descES", "description")],
    "faq": [("questionEN", "questionES", "question"), ("answerEN", "answerES", "answer")],
    "sites": [("labelEN", "labelES", "label"), ("descEN", "descES", "description")],
}
COVER_DIR = "assets/images/about/books"
_URL_OK = re.compile(r"^(https?://\S+|[\w][\w./-]*/?)$")
_TAG = re.compile(r'<(?:section|div)\b[^>]*\bid="(about-(?:reading|faq|sites))"[^>]*>')


def new_entry(list_name: str, ident: str, en: str = "", es: str = "") -> dict:
    if list_name == "books":
        return {"id": ident, "coverSrc": "", "titleEN": en, "titleES": es, "descEN": "", "descES": "", "visible": False, "_list": "books"}
    if list_name == "faq":
        return {"id": ident, "questionEN": en, "questionES": es, "answerEN": "", "answerES": "", "visible": False, "_list": "faq"}
    if list_name == "sites":
        return {"id": ident, "url": "", "internal": False, "labelEN": en, "labelES": es, "descEN": "", "descES": "", "visible": False, "_list": "sites"}
    raise ValueError(f"unknown About list {list_name!r}")


def strip(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if k != "_list"}


def ordered(list_name: str, entry: dict) -> dict:
    order = FIELD_ORDER[list_name]
    e = strip(entry)
    return {k: e[k] for k in order if k in e} | {k: v for k, v in e.items() if k not in order}


class AboutFile(DataFile):
    """js/about-data.js: three arrays, one DataFile-shaped object (name "about", id field "id")."""

    def __init__(self, repo_root: Path, name: str = "about"):  # noqa: D107 — same shape as DataFile
        self.repo_root = Path(repo_root)
        self.name = "about"
        self.rel_path, self.const, self.id_field = REL_PATH, ", ".join(LISTS.values()), "id"
        self.path = self.repo_root / self.rel_path
        st = os.stat(self.path)
        self.raw = self.path.read_bytes()
        self.mtime_ns, self.size = st.st_mtime_ns, st.st_size
        self.sha256 = sha256_bytes(self.raw)
        self.doc = Document.from_bytes(self.raw, source=str(self.path))
        self.arrays: dict[str, ArrayNode] = {}
        self._entries = []
        for lst, const in LISTS.items():
            arr = self.doc.const(const)
            if not isinstance(arr, ArrayNode):
                raise JsDataError(f"`{const}` is not an array literal", arr.line)
            for it in arr.items:
                if not isinstance(it, ObjectNode):
                    raise JsDataError(f"every {const} entry must be an object literal", it.line)
            self.arrays[lst] = arr
            self._entries += [dict(spans.to_python(it), _list=lst) for it in arr.items]
        self.arr = self.arrays["books"]  # DataFile compatibility (unused by render below)

    def node(self, ident: str) -> Optional[ObjectNode]:
        for lst, arr in self.arrays.items():
            for it, e in zip(arr.items, self.list_entries(lst)):
                if e.get("id") == ident:
                    return it
        return None

    def list_entries(self, lst: str) -> list[dict]:
        return [dict(e) for e in self._entries if e["_list"] == lst]

    def render(self, drafts: dict[str, Optional[dict]], new_entries: list[dict], order: Optional[dict] = None) -> bytes:
        """drafts: id → entry dict (with `_list`) | None (delete); new_entries: entries with `_list`;
        order: list name → the wanted ids (a reordered list is re-emitted whole)."""
        order = order or {}
        edits: list[spans.Edit] = []
        for lst, arr in self.arrays.items():
            cur = list(zip(arr.items, self.list_entries(lst)))
            live: list[dict] = []
            for _, e in cur:
                if e["id"] in drafts:
                    if drafts[e["id"]] is None:
                        continue
                    live.append(drafts[e["id"]])
                else:
                    live.append(e)
            live += [n for n in new_entries if n.get("_list") == lst]
            wanted = order.get(lst)
            if wanted and [e["id"] for e in live] != wanted and set(wanted) == {e["id"] for e in live}:
                by = {e["id"]: e for e in live}
                indent = spans.indent_of(self.doc, arr.items[0].first) if arr.items else "  "
                body = ",\n".join(indent + emit.inline(ordered(lst, by[i])) for i in wanted)
                s, e = self.doc.tokens[arr.first].end, self.doc.tokens[arr.last].start
                edits.append((s, e, "\n" + body + "\n"))
                continue
            for i, (node, e) in enumerate(cur):
                if e["id"] not in drafts:
                    continue
                new = drafts[e["id"]]
                if new is None:
                    edits.append(spans.delete_item(self.doc, arr, i))
                else:
                    edits += self._entry_edits(node, strip(e), strip(new), FIELD_ORDER[lst])
            for n in new_entries:
                if n.get("_list") == lst:
                    edits.append(spans.append_item(self.doc, arr, emit.inline(ordered(lst, n))))
        if not edits:
            return self.raw
        return spans.apply(self.doc, edits).to_bytes({})


# ----------------------------------------------------------------- the `hidden` attribute in about.html


def read_shown(html: str) -> dict[str, bool]:
    """block id → shown (no `hidden` attribute on its element)."""
    out = {}
    for m in _TAG.finditer(html):
        out[m.group(1)] = re.search(r"\shidden(?=[\s>])", m.group(0)) is None
    return out


def render_shown(html: str, shown: dict[str, bool]) -> str:
    """The page with each named block's `hidden` attribute set or removed."""

    def fix(m):
        tag, bid = m.group(0), m.group(1)
        if bid not in shown:
            return tag
        without = re.sub(r"\shidden(?=[\s>])", "", tag)
        return without if shown[bid] else without[:-1].rstrip() + " hidden>"

    return _TAG.sub(fix, html)


# ----------------------------------------------------------------- validation


def check(entries: list[dict], root: Path, pending_files=(), terms=None, shown: Optional[dict] = None) -> list[Issue]:
    """Issues over the About lists (entries carry `_list`); keys are "about:<id>". `shown`: block
    id → shown; an entry in a hidden block is treated as hidden (its problems are warnings)."""
    issues: list[Issue] = []
    seen: set[str] = set()
    pending = set(pending_files)
    shown = shown or {}
    for e in entries:
        lst = e.get("_list")
        ident = e.get("id") or "?"
        owner = f"about:{ident}"
        if not e.get("id"):
            issues.append(Issue("error", "empty-key", owner, "", f"{LABELS.get(lst, lst)}: an entry has no id"))
        elif ident in seen:
            issues.append(Issue("error", "duplicate", owner, "", f"duplicate id “{ident}”"))
        seen.add(ident)
        if lst not in TEXT_PAIRS:
            issues.append(Issue("error", "shape", owner, "", f"unknown list {lst!r}"))
            continue
        visible = bool(e.get("visible")) and shown.get(SECTIONS[lst], True)
        for en_f, es_f, label in TEXT_PAIRS[lst]:
            for lang, f in (("en", en_f), ("es", es_f)):
                v = e.get(f)
                if not isinstance(v, str):
                    issues.append(Issue("error", "shape", owner, lang, f"{label} ({lang.upper()}) must be text"))
                    continue
                if not v.strip():
                    issues.append(Issue("error" if visible else "warning", "missing-key", owner, lang, f"{label}: no {lang.upper()} text yet" + ("" if visible else " (entry is hidden)")))
                    continue
                if validate.is_todo(v):
                    issues.append(Issue("error" if visible else "warning", "todo", owner, lang, f"{label} ({lang.upper()}) still says TODO"))
                if validate.has_html(v):
                    issues.append(Issue("error", "html", owner, lang, f"{label} ({lang.upper()}) contains HTML"))
                words = validate.voice_words(v)
                if words:
                    issues.append(Issue("warning", "voice", owner, lang, f"{label} ({lang.upper()}): voice words {', '.join(words)}"))
                if terms:
                    from ..cv import scans

                    for h in scans.blocklist_hits(v, terms):
                        issues.append(Issue("error", "blocklist", owner, lang, f"{label} ({lang.upper()}): blocked term “{h['term']}” ({h['reason'] or 'no reason given'})"))
            a, b = e.get(en_f), e.get(es_f)
            if isinstance(a, str) and isinstance(b, str) and a.strip() and a == b and not validate.identical_allowed(f"about{ident}", a):
                issues.append(Issue("warning", "same", owner, "", f"{label}: ES is identical to EN"))
        if lst == "books":
            cover = e.get("coverSrc")
            if not cover:
                issues.append(Issue("error" if visible else "warning", "missing-file", owner, "", "no cover image"))
            elif cover.lstrip("/") not in pending and not (root / cover.lstrip("/")).is_file():
                issues.append(Issue("error" if visible else "warning", "missing-file", owner, "", f"cover: {cover} does not exist" + ("" if visible else " (entry is hidden)")))
        if lst == "sites":
            url = e.get("url")
            if not isinstance(url, str) or not url.strip() or url.strip() == "#" or not _URL_OK.match(url.strip()):
                issues.append(Issue("error" if visible else "warning", "url", owner, "", "url must be https://… or a site-relative path"))
            if url and isinstance(url, str) and url.startswith("http") and e.get("internal"):
                issues.append(Issue("warning", "url", owner, "", "an external site should open in a new tab (internal: false)"))
    return issues
