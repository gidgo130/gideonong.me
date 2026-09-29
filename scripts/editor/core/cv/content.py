"""Pure operations on the CV content set (staging/cv-content/content.json) — no I/O.

The shape (see importer.py): header, sections[] with per-variant order lists of
item ids, items{} (entry | line) with include flags per variant, entries with
children{} and per-variant child order lists. Membership of an item in a variant
is BOTH its include flag and its presence in a section's order list for that
variant; every operation here keeps the two in step. Everything works on a
plain dict (the service's draft), so the same functions serve tests and the UI.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .importer import SEP, VARIANTS, norm, slugify

LANGS = ("en", "es")
VARIANT_LABELS = {"full": "Full", "professional": "Professional", "resume": "Résumé"}
ITEM_KINDS = ("entry", "line")
CHILD_KINDS = ("bullet", "line")


def _check_variant(variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")


def _check_lang(lang: str) -> None:
    if lang not in LANGS:
        raise ValueError(f"unknown language {lang!r}")


# ----------------------------------------------------------------- lookups


def find(content: dict, id: str) -> tuple:
    """("item", item) or ("child", parent_id, child); KeyError when the id is unknown."""
    items = content["items"]
    if id in items:
        return ("item", items[id])
    for pid, item in items.items():
        if id in item.get("children", {}):
            return ("child", pid, item["children"][id])
    raise KeyError(id)


def section_of(content: dict, item_id: str) -> Optional[dict]:
    """The section whose order lists (any variant) hold the item."""
    for sec in content["sections"]:
        if any(item_id in o for o in sec["order"].values()):
            return sec
    return None


def all_ids(content: dict) -> set:
    ids = {s["id"] for s in content["sections"]}
    for iid, item in content["items"].items():
        ids.add(iid)
        ids.update(item.get("children", {}))
    return ids


def unique_id(base: str, used: set) -> str:
    cand, n = base, 2
    while cand in used:
        cand = f"{base}-{n}"
        n += 1
    return cand


def label_of(content: dict, id: str, lang: str = "en") -> str:
    """A short human label: role (entries), text (lines), heading (sections), header parts."""
    if id.startswith("header."):
        return "Header › " + id.split(".", 1)[1]
    if id.startswith("section."):
        sec = next((s for s in content["sections"] if s["id"] == id.split(".", 1)[1]), None)
        return f"Section “{sec['heading'][lang]}”" if sec else id
    try:
        kind, *rest = find(content, id)
    except KeyError:
        return id
    node = rest[-1]
    if kind == "item":
        text = node["role"][lang] if node["kind"] == "entry" else node["text"][lang]
    else:
        text = node["text"][lang]
    text = norm(text) or norm(node["role"]["es"] if kind == "item" and node["kind"] == "entry" else node["text"].get("es", "")) or id
    return text if len(text) <= 60 else text[:57] + "…"


# ----------------------------------------------------------------- text edits

_TEXT_PATHS = [
    re.compile(r"^header\.name$"),
    re.compile(r"^header\.contact\.(en|es)$"),
    re.compile(r"^header\.title\.(full|professional|resume)\.(en|es)$"),
    re.compile(r"^sections\.\d+\.heading\.(en|es)$"),
    re.compile(r"^items\.[^.]+\.(role|org|date|text)\.(en|es)$"),
    re.compile(r"^items\.[^.]+\.children\.[^.]+\.text\.(en|es)$"),
]


def set_text(content: dict, path: list, value: Any) -> None:
    """Set one text field. Only the text leaves are editable this way (the structural
    fields — include flags, orders, kinds, ids — go through the operations below)."""
    if not isinstance(value, str):
        raise ValueError("value must be a string")
    key = ".".join(str(p) for p in path)
    if not any(r.match(key) for r in _TEXT_PATHS):
        raise ValueError(f"{key} is not an editable text field")
    cur = content
    for p in path[:-1]:
        if isinstance(cur, list):
            if not isinstance(p, int) or not 0 <= p < len(cur):
                raise KeyError(key)
            cur = cur[p]
        elif isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            raise KeyError(key)
    if cur is None:  # header.title.<variant> is null where the master has no title line
        raise ValueError(f"{key}: this variant has no title line")
    if not isinstance(cur, dict) or path[-1] not in cur:
        raise KeyError(key)
    cur[path[-1]] = norm(value)


# ----------------------------------------------------------------- membership / order


def _order_list(container: dict, variant: str) -> list:
    return container.setdefault("order", {}).setdefault(variant, [])


def _insert_after_neighbour(order: list, id: str, siblings_current: list) -> None:
    """Insert `id` into `order` after the nearest preceding sibling (in the current variant's
    order) that is also in `order`; at the start when none is."""
    if id in order:
        return
    pos = 0
    if id in siblings_current:
        before = siblings_current[: siblings_current.index(id)]
        for sib in reversed(before):
            if sib in order:
                pos = order.index(sib) + 1
                break
    order.insert(pos, id)


def set_include(content: dict, id: str, variant: str, on: bool, current: Optional[str] = None) -> None:
    """Put an item or child into a variant (or take it out), keeping the order lists in step.

    `current` is the variant the user is looking at; a newly included id lands after its
    nearest neighbour from that view. Taking an entry out of a variant takes its children
    out too. A child cannot be included where its parent is not."""
    _check_variant(variant)
    current = current if current in VARIANTS else variant
    kind, *rest = find(content, id)
    if kind == "item":
        item = rest[0]
        sec = section_of(content, id)
        if sec is None:
            raise ValueError(f"{id} is in no section")
        item["include"][variant] = bool(on)
        order = _order_list(sec, variant)
        if on:
            _insert_after_neighbour(order, id, sec["order"].get(current) or [])
        else:
            if id in order:
                order.remove(id)
            if item["kind"] == "entry":
                for cid, child in item.get("children", {}).items():
                    child["include"][variant] = False
                item.setdefault("order", {})[variant] = []
    else:
        pid, child = rest
        parent = content["items"][pid]
        if on and not parent["include"].get(variant):
            raise ValueError(f"include the entry in {VARIANT_LABELS[variant]} first")
        child["include"][variant] = bool(on)
        order = _order_list(parent, variant)
        if on:
            _insert_after_neighbour(order, id, parent.get("order", {}).get(current) or [])
        elif id in order:
            order.remove(id)


def move(content: dict, id: str, variant: str, delta: int) -> None:
    """Move an item within its section, or a child within its entry, in one variant's order."""
    _check_variant(variant)
    if delta not in (-1, 1):
        raise ValueError("delta must be -1 or 1")
    kind, *rest = find(content, id)
    if kind == "item":
        sec = section_of(content, id)
        order = (sec or {}).get("order", {}).get(variant)
    else:
        order = content["items"][rest[0]].get("order", {}).get(variant)
    if not order or id not in order:
        raise ValueError(f"{id} is not in {VARIANT_LABELS[variant]}")
    i = order.index(id)
    j = i + delta
    if not 0 <= j < len(order):
        return
    order[i], order[j] = order[j], order[i]


# ----------------------------------------------------------------- add / delete


def add_item(content: dict, section_id: str, kind: str, en_text: str, variant: str) -> str:
    """A new entry or line at the end of the section in `variant` (included there only)."""
    _check_variant(variant)
    if kind not in ITEM_KINDS:
        raise ValueError(f"kind must be one of {', '.join(ITEM_KINDS)}")
    sec = next((s for s in content["sections"] if s["id"] == section_id), None)
    if sec is None:
        raise KeyError(section_id)
    en_text = norm(en_text)
    if not en_text:
        raise ValueError("the English text is required (it names the item)")
    used = all_ids(content)
    if kind == "entry":
        iid = unique_id(slugify(en_text, "entry"), used)
        content["items"][iid] = {
            "kind": "entry",
            "role": {"en": en_text, "es": ""},
            "org": {"en": "", "es": ""},
            "date": {"en": "", "es": ""},
            "sep": SEP,
            "include": {v: v == variant for v in VARIANTS},
            "order": {variant: []},
            "children": {},
        }
    else:
        iid = unique_id(f"{section_id}-{slugify(en_text, 'line')[:24]}", used)
        content["items"][iid] = {"kind": "line", "text": {"en": en_text, "es": ""}, "include": {v: v == variant for v in VARIANTS}}
    _order_list(sec, variant).append(iid)
    return iid


def add_child(content: dict, item_id: str, kind: str, variant: str) -> str:
    """A new bullet or line at the end of the entry's children in `variant` (included there only)."""
    _check_variant(variant)
    if kind not in CHILD_KINDS:
        raise ValueError(f"kind must be one of {', '.join(CHILD_KINDS)}")
    item = content["items"].get(item_id)
    if item is None:
        raise KeyError(item_id)
    if item["kind"] != "entry":
        raise ValueError("only an entry can hold bullets or lines")
    if not item["include"].get(variant):
        raise ValueError(f"include the entry in {VARIANT_LABELS[variant]} first")
    used = all_ids(content)
    n = len(item["children"]) + 1
    while f"{item_id}-{n}" in used:
        n += 1
    cid = f"{item_id}-{n}"
    item["children"][cid] = {"kind": kind, "text": {"en": "", "es": ""}, "include": {v: v == variant for v in VARIANTS}}
    _order_list(item, variant).append(cid)
    return cid


def delete(content: dict, id: str) -> None:
    """Remove an item (with its children) or a child, and every reference in the order lists."""
    kind, *rest = find(content, id)
    if kind == "item":
        del content["items"][id]
        for sec in content["sections"]:
            for order in sec["order"].values():
                while id in order:
                    order.remove(id)
    else:
        pid = rest[0]
        parent = content["items"][pid]
        del parent["children"][id]
        for order in parent.get("order", {}).values():
            while id in order:
                order.remove(id)


def add_section(content: dict, en: str, es: str, variant: str) -> str:
    """A new, empty section at the end (it appears in a document once an item is added there)."""
    _check_variant(variant)
    en, es = norm(en), norm(es)
    if not en:
        raise ValueError("the English heading is required (it names the section)")
    sid = unique_id(slugify(en, "section"), all_ids(content) | {"header", "top"})
    content["sections"].append({"id": sid, "heading": {"en": en, "es": es}, "order": {variant: []}})
    return sid


def delete_section(content: dict, section_id: str) -> None:
    """Remove a section that holds no item in any document."""
    sec = next((s for s in content["sections"] if s["id"] == section_id), None)
    if sec is None:
        raise KeyError(section_id)
    if any(sec["order"].values()):
        raise ValueError("the section still holds items — delete or move them first")
    content["sections"].remove(sec)


# ----------------------------------------------------------------- listing for the page


def listing(content: dict, variant: str) -> list[dict]:
    """Sections with their items in this variant's order, then the section's other items
    (present in some other variant only) — what the left list shows."""
    _check_variant(variant)
    items = content["items"]
    out = []
    for sec in content["sections"]:
        order = sec["order"].get(variant) or []
        seen = set(order)
        others = []
        for o in sec["order"].values():
            for iid in o:
                if iid not in seen:
                    seen.add(iid)
                    others.append(iid)
        out.append(
            {
                "id": sec["id"],
                "heading": sec["heading"],
                "variants": [v for v, o in sec["order"].items() if o],
                "items": [iid for iid in order if iid in items],
                "others": [iid for iid in others if iid in items],
            }
        )
    return out
