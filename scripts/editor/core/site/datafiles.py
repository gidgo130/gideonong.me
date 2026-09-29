"""The three JS data files as lists of entry dicts, written back with minimal
span edits (core/spans.py + core/emit.py).

render(drafts, new_entries):
  * an entry in `drafts` with a dict → property by property: a string value
    changed → the string token; anything else changed → the value span
    re-emitted in the file's style; a property gone from the dict → its line;
    a property new to the dict → inserted after the nearest earlier property of
    the file's schema order;
  * an entry in `drafts` with None → the whole object, comments between
    entries kept;
  * `new_entries` → appended before the closing bracket, properties in schema
    order.
Every render is re-parsed by the tokenizer before it is handed back.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .. import emit, spans
from ..jsdata import ArrayNode, Document, JsDataError, ObjectNode, StringNode, sha256_bytes

FILES = {
    "projects": ("js/projects-data.js", "projectsData", "slug"),
    "experience": ("js/experience-data.js", "experienceData", "slug"),
    "tags": ("js/tags-data.js", "TAGS", "id"),
}
FIELD_ORDER = {
    "projects": [
        "slug", "titleKey", "descKey", "longDescKey", "dates", "sortDate", "context", "tags", "imageSrc", "imageAlt",
        "thumbSrc", "thumbAltKey", "subpageUrl", "featured", "featuredOrder", "pinned", "searchTextKey", "listing",
        "experience", "homeLayout", "gallery", "page",
    ],
    "experience": [
        "slug", "roleKey", "orgKey", "orgShortKey", "dates", "sortDate", "bulletKeys", "tags", "imageSrc", "imageAltKey",
        "imageLink", "subpageUrl", "layout", "status", "color", "visible",
    ],
    "tags": ["id", "key"],
}


def ordered(name: str, entry: dict) -> dict:
    order = FIELD_ORDER[name]
    known = [k for k in order if k in entry]
    rest = [k for k in entry if k not in order]
    return {k: entry[k] for k in known + rest}


class DataFile:
    def __init__(self, repo_root: Path, name: str):
        self.repo_root = Path(repo_root)
        self.name = name
        self.rel_path, self.const, self.id_field = FILES[name]
        self.path = self.repo_root / self.rel_path
        st = os.stat(self.path)
        self.raw = self.path.read_bytes()
        self.mtime_ns, self.size = st.st_mtime_ns, st.st_size
        self.sha256 = sha256_bytes(self.raw)
        self.doc = Document.from_bytes(self.raw, source=str(self.path))
        arr = self.doc.const(self.const)
        if not isinstance(arr, ArrayNode):
            raise JsDataError(f"`{self.const}` is not an array literal", arr.line)
        self.arr = arr
        for it in arr.items:
            if not isinstance(it, ObjectNode):
                raise JsDataError("every entry must be an object literal", it.line)
        self._entries = [spans.to_python(it) for it in arr.items]

    # ------------------------------------------------------------- queries
    def entries(self) -> list[dict]:
        return [dict(e) for e in self._entries]

    def ids(self) -> list[str]:
        return [e.get(self.id_field) for e in self._entries]

    def node(self, ident: str) -> Optional[ObjectNode]:
        for it, e in zip(self.arr.items, self._entries):
            if e.get(self.id_field) == ident:
                return it
        return None

    def line_of(self, ident: str) -> Optional[int]:
        n = self.node(ident)
        return n.line if n else None

    def disk_changed(self) -> bool:
        try:
            st = os.stat(self.path)
            if st.st_mtime_ns == self.mtime_ns and st.st_size == self.size == len(self.raw):
                return False
            return sha256_bytes(self.path.read_bytes()) != self.sha256
        except OSError:
            return True

    # ------------------------------------------------------------- rendering
    def render(self, drafts: dict[str, Optional[dict]], new_entries: list[dict]) -> bytes:
        edits: list[spans.Edit] = []
        for i, (node, cur) in enumerate(zip(self.arr.items, self._entries)):
            ident = cur.get(self.id_field)
            if ident not in drafts:
                continue
            new = drafts[ident]
            if new is None:
                edits.append(spans.delete_item(self.doc, self.arr, i))
                continue
            edits += self._entry_edits(node, cur, new)
        for e in new_entries:
            item = ordered(self.name, e)
            text = emit.inline(item) if self.name == "tags" else emit.entry(item, "  ")  # tags are one line each
            edits.append(spans.append_item(self.doc, self.arr, text))
        if not edits:
            return self.raw
        return spans.apply(self.doc, edits).to_bytes({})

    def _entry_edits(self, node: ObjectNode, cur: dict, new: dict) -> list[spans.Edit]:
        edits: list[spans.Edit] = []
        for prop in node.props:
            k = prop.key
            if k not in new:
                edits.append(spans.delete_prop(self.doc, node, k))
                continue
            if cur[k] == new[k] and type(cur[k]) is type(new[k]):
                continue
            if isinstance(prop.value, StringNode) and isinstance(new[k], str):
                edits.append(spans.replace_string(self.doc, prop.value, new[k]))
            else:
                indent = spans.indent_of(self.doc, prop.key_tok)
                edits.append(spans.replace_value(self.doc, prop.value, emit.value(new[k], k, indent)))
        existing = [p.key for p in node.props if p.key in new]
        added = [k for k in ordered(self.name, new) if node.get(k) is None]
        if added:
            order = FIELD_ORDER[self.name]
            groups: dict[Optional[str], list[tuple[str, str]]] = {}
            indent = spans.prop_indent(self.doc, node)
            placed = list(existing)
            for k in added:
                pos = order.index(k) if k in order else len(order)
                anchor = None
                for e in placed:
                    epos = order.index(e) if e in order else len(order)
                    if epos <= pos and e in existing:
                        anchor = e
                if anchor is None and existing:
                    anchor = None  # first
                groups.setdefault(anchor, []).append((k, emit.value(new[k], k, indent)))
                placed.append(k)
            for anchor, items in groups.items():
                edits.append(spans.insert_props_after(self.doc, node, anchor, items))
        return edits
