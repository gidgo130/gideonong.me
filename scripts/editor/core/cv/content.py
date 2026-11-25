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
# The fourth document has no Word master (it is rendered from HTML, core/cv/designed/). VARIANTS
# stays the three master variants, so everything that walks the masters never sees it; the
# operations below accept ALL_VARIANTS. A missing "designed" key in an include dict means "not in it".
DESIGNED = "designed"
ALL_VARIANTS = VARIANTS + (DESIGNED,)
VARIANT_LABELS = {"full": "Full", "professional": "Professional", "resume": "Résumé", DESIGNED: "Designed"}
ITEM_KINDS = ("entry", "line")
CHILD_KINDS = ("bullet", "line")


def _check_variant(variant: str) -> None:
    if variant not in ALL_VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")


def _only(variant: str) -> dict:
    """An include dict for a node that is in `variant` alone."""
    inc = {v: v == variant for v in VARIANTS}
    if variant == DESIGNED:
        inc[DESIGNED] = True
    return inc


def in_masters(node: dict) -> bool:
    """True when the node is in at least one of the three Word documents."""
    return any(node.get("include", {}).get(v) for v in VARIANTS)


def on_shelf(content: dict, id: str) -> bool:
    """True when the id is on the Designed checklist (ticked or not): an item in some section's
    Designed order, or a child in its entry's Designed order."""
    if id in content["items"]:
        return any(id in (s["order"].get(DESIGNED) or []) for s in content["sections"])
    for item in content["items"].values():
        if id in item.get("children", {}):
            return id in (item.get("order", {}).get(DESIGNED) or [])
    return False


def copy_records(content: dict, create: bool = False) -> dict:
    """design.copies.designed: copy id → {"of": shared id, "base": the shared text when copied}.
    The outer key is the scope, so a narrower one (a layout, a language) can be added later."""
    design = content.get("design")
    if design is None:
        if not create:
            return {}
        design = content.setdefault("design", {})
    if create:
        return design.setdefault("copies", {}).setdefault(DESIGNED, {})
    return design.get("copies", {}).get(DESIGNED, {})


def text_snapshot(node: dict) -> dict:
    """The text fields of an entry (role / org / date) or of a line / bullet (text), copied."""
    keys = ("role", "org", "date") if node.get("kind") == "entry" else ("text",)
    return {k: dict(node[k]) for k in keys}


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


def section_of(content: dict, item_id: str, variant: Optional[str] = None) -> Optional[dict]:
    """The section that holds the item: the one whose order for `variant` lists it when there is
    one (an item may sit in a different section per document), else the first section that lists
    it for a Word document, else any section that lists it."""
    if variant:
        for sec in content["sections"]:
            if item_id in (sec["order"].get(variant) or []):
                return sec
    for sec in content["sections"]:
        if any(item_id in (sec["order"].get(v) or []) for v in VARIANTS):
            return sec
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
    if id.startswith("design."):
        parts = id.split(".")
        names = {"profile": "Profile", "gpa": "GPA line", "main": "main-column headings", "heading": "heading", "languages": "Languages", "skills": "Skills", "certs": "Certifications", "honors": "Honors"}
        out = "Designed › " + names.get(parts[1], parts[1])
        if len(parts) > 2:
            row = next((r for r in (content.get("design") or {}).get(parts[1]) or [] if isinstance(r, dict) and r.get("id") == parts[2]), None)
            first = next((v for v in (row or {}).values() if isinstance(v, dict)), None)
            out += " › " + ((first or {}).get(lang) or (first or {}).get("en") or parts[2])
        return out
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
    re.compile(r"^header\.title\.(full|professional|resume|designed)\.(en|es)$"),
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
    current = current if current in ALL_VARIANTS else variant
    kind, *rest = find(content, id)
    if variant == DESIGNED:
        _set_include_designed(content, id, kind, rest, on, current)
        return
    if kind == "item":
        item = rest[0]
        sec = section_of(content, id, variant)
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


def _set_include_designed(content: dict, id: str, kind: str, rest: list, on: bool, current: str) -> None:
    """The Designed document is a checklist: its order lists hold every item on the list, ticked
    or not, and the flag alone says what prints. So unticking keeps the place (and an entry's
    bullets keep their own ticks); ticking something that is not on the list yet puts it after
    its nearest neighbour from the current view."""
    def place(container: dict) -> None:
        # where it goes: after its nearest neighbour in the current view, else in the first
        # Word document that holds it (so bullets arrive in their usual order), else at the end
        order = _order_list(container, DESIGNED)
        if id in order:
            return
        orders = container.get("order", {})
        ref = next((orders[v] for v in (current,) + VARIANTS if id in (orders.get(v) or [])), None)
        if ref is None:
            order.append(id)
        else:
            _insert_after_neighbour(order, id, ref)

    if kind == "item":
        item = rest[0]
        if on and not on_shelf(content, id):
            sec = section_of(content, id)
            if sec is None:
                raise ValueError(f"{id} is in no section")
            place(sec)
            if item["kind"] == "entry":
                item.setdefault("order", {}).setdefault(DESIGNED, [])
        item["include"][DESIGNED] = bool(on)
    else:
        pid, child = rest
        parent = content["items"][pid]
        if on and not on_shelf(content, pid):
            raise ValueError(f"include the entry in {VARIANT_LABELS[DESIGNED]} first")
        if on:
            place(parent)
        child["include"][DESIGNED] = bool(on)


def shelf_remove(content: dict, id: str) -> None:
    """Take an item or child off the Designed checklist altogether. Something that exists only
    for the Designed document is deleted (it would be unreachable otherwise)."""
    kind, *rest = find(content, id)
    node = rest[-1]
    if not in_masters(node):
        delete(content, id)
        return
    node["include"].pop(DESIGNED, None)
    if kind == "item":
        for sec in content["sections"]:
            order = sec["order"].get(DESIGNED) or []
            while id in order:
                order.remove(id)
            if DESIGNED in sec["order"] and not sec["order"][DESIGNED]:
                del sec["order"][DESIGNED]  # an empty checklist section is the same as none
        if node["kind"] == "entry":
            for cid in list(node.get("children", {})):
                child = node["children"][cid]
                if in_masters(child):
                    child["include"].pop(DESIGNED, None)
                else:
                    delete(content, cid)
            node.get("order", {}).pop(DESIGNED, None)
    else:
        order = content["items"][rest[0]].get("order", {}).get(DESIGNED) or []
        while id in order:
            order.remove(id)


def move(content: dict, id: str, variant: str, delta: int, visible_only: bool = False) -> None:
    """Move an item within its section, or a child within its entry, in one variant's order.
    `visible_only` (the Designed order seen from the CV text tab, which lists ticked items only):
    step over unticked neighbours, so the item changes place with the next one shown."""
    _check_variant(variant)
    if delta not in (-1, 1):
        raise ValueError("delta must be -1 or 1")
    kind, *rest = find(content, id)
    if kind == "item":
        sec = section_of(content, id, variant)
        order = (sec or {}).get("order", {}).get(variant)
        siblings = content["items"]
    else:
        order = content["items"][rest[0]].get("order", {}).get(variant)
        siblings = content["items"][rest[0]].get("children", {})
    if not order or id not in order:
        raise ValueError(f"{id} is not in {VARIANT_LABELS[variant]}")
    i = order.index(id)
    j = i + delta
    if visible_only:
        while 0 <= j < len(order) and not (siblings.get(order[j]) or {}).get("include", {}).get(variant):
            j += delta
    if not 0 <= j < len(order):
        return
    order.insert(j, order.pop(i))


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
            "include": _only(variant),
            "order": {variant: []},
            "children": {},
        }
    else:
        iid = unique_id(f"{section_id}-{slugify(en_text, 'line')[:24]}", used)
        content["items"][iid] = {"kind": "line", "text": {"en": en_text, "es": ""}, "include": _only(variant)}
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
    if not item["include"].get(variant) and not (variant == DESIGNED and on_shelf(content, item_id)):
        raise ValueError(f"include the entry in {VARIANT_LABELS[variant]} first")
    used = all_ids(content)
    n = len(item["children"]) + 1
    while f"{item_id}-{n}" in used:
        n += 1
    cid = f"{item_id}-{n}"
    item["children"][cid] = {"kind": kind, "text": {"en": "", "es": ""}, "include": _only(variant)}
    _order_list(item, variant).append(cid)
    return cid


def delete(content: dict, id: str) -> None:
    """Remove an item (with its children) or a child, and every reference in the order lists."""
    kind, *rest = find(content, id)
    records = copy_records(content)
    for gone in [id] + (list(rest[0].get("children", {})) if kind == "item" else []):
        records.pop(gone, None)
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


def duplicate(content: dict, id: str, variant: str) -> str:
    """Separate a shared item or child for one document: a copy with the same texts takes its
    place in `variant` (only there), and the original leaves `variant` but stays in the others.
    An entry's copy takes the children it shows in that document. Refused when the item is in
    `variant` alone (nothing to separate)."""
    _check_variant(variant)
    kind, *rest = find(content, id)
    node = rest[-1]
    if variant == DESIGNED:
        return _duplicate_designed(content, id, kind, rest)
    if not node["include"].get(variant):
        raise ValueError(f"{id} is not in {VARIANT_LABELS[variant]}")
    if sum(1 for on in node["include"].values() if on) < 2:
        raise ValueError(f"it is only in {VARIANT_LABELS[variant]} — there is nothing to separate it from")
    used = all_ids(content)
    new_id = unique_id(f"{id}-{variant}", used)
    only_here = {v: v == variant for v in VARIANTS}
    if kind == "item":
        sec = section_of(content, id, variant)
        if sec is None:
            raise ValueError(f"{id} is in no section")
        new_item: dict = {"kind": node["kind"], "include": dict(only_here)}
        if node["kind"] == "entry":
            for k in ("role", "org", "date"):
                new_item[k] = dict(node[k])
            new_item["sep"] = node.get("sep", SEP)
            children, order = {}, []
            used.add(new_id)
            for cid in node.get("order", {}).get(variant, []):
                ch = node.get("children", {}).get(cid)
                if not ch or not ch["include"].get(variant):
                    continue
                ncid = unique_id(f"{new_id}-{len(children) + 1}", used)
                used.add(ncid)
                children[ncid] = {"kind": ch["kind"], "text": dict(ch["text"]), "include": dict(only_here)}
                order.append(ncid)
            new_item["order"] = {variant: order}
            new_item["children"] = children
        else:
            new_item["text"] = dict(node["text"])
        content["items"][new_id] = new_item
        sec_order = sec["order"].get(variant) or []
        sec_order[sec_order.index(id)] = new_id
        set_include(content, id, variant, False)
    else:
        pid = rest[0]
        parent = content["items"][pid]
        parent["children"][new_id] = {"kind": node["kind"], "text": dict(node["text"]), "include": dict(only_here)}
        porder = parent.get("order", {}).get(variant) or []
        porder[porder.index(id)] = new_id
        node["include"][variant] = False
    return new_id


def _duplicate_designed(content: dict, id: str, kind: str, rest: list) -> str:
    """duplicate() for the Designed document. The copy takes the original's place on the
    checklist with its tick as it was; an entry's copy takes every bullet on the checklist,
    ticked or not. Each copy is recorded in design.copies with the shared text at this moment,
    which is what "edited for Diseño", "the shared text changed" and Reset work from."""
    node = rest[-1]
    if not on_shelf(content, id):
        raise ValueError(f"{id} is not in {VARIANT_LABELS[DESIGNED]}")
    if not in_masters(node):
        raise ValueError(f"it is only in {VARIANT_LABELS[DESIGNED]} — there is nothing to separate it from")
    records = copy_records(content, create=True)
    used = all_ids(content)
    new_id = unique_id(f"{id}-{DESIGNED}", used)
    used.add(new_id)

    def only_designed(src: dict) -> dict:
        inc = {v: False for v in VARIANTS}
        inc[DESIGNED] = bool(src["include"].get(DESIGNED))
        return inc

    if kind == "child":
        parent = content["items"][rest[0]]
        parent["children"][new_id] = {"kind": node["kind"], "text": dict(node["text"]), "include": only_designed(node)}
        order = parent["order"][DESIGNED]
        order[order.index(id)] = new_id
        node["include"].pop(DESIGNED, None)
        records[new_id] = {"of": id, "base": text_snapshot(node)}
        return new_id
    sec = section_of(content, id, DESIGNED)
    new_item: dict = {"kind": node["kind"], "include": only_designed(node)}
    if node["kind"] == "entry":
        for k in ("role", "org", "date"):
            new_item[k] = dict(node[k])
        new_item["sep"] = node.get("sep", SEP)
        children, order = {}, []
        for cid in list(node.get("order", {}).get(DESIGNED, [])):
            ch = node.get("children", {}).get(cid)
            if not ch:
                continue
            ncid = unique_id(f"{new_id}-{len(children) + 1}", used)
            used.add(ncid)
            children[ncid] = {"kind": ch["kind"], "text": dict(ch["text"]), "include": only_designed(ch)}
            order.append(ncid)
            if in_masters(ch):
                ch["include"].pop(DESIGNED, None)
                records[ncid] = {"of": cid, "base": text_snapshot(ch)}
            else:  # a bullet that already existed for Designed only moves over, with its record
                if cid in records:
                    records[ncid] = records.pop(cid)
                del node["children"][cid]
        node.get("order", {}).pop(DESIGNED, None)
        new_item["order"] = {DESIGNED: order}
        new_item["children"] = children
    else:
        new_item["text"] = dict(node["text"])
    content["items"][new_id] = new_item
    sec_order = sec["order"][DESIGNED]
    sec_order[sec_order.index(id)] = new_id
    node["include"].pop(DESIGNED, None)
    records[new_id] = {"of": id, "base": text_snapshot(node)}
    return new_id


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

    def shown(v: str, order: list) -> list:
        """What a document prints from an order list: everything, except that the Designed
        order also holds the unticked items of its checklist."""
        if v == DESIGNED:
            return [i for i in order if (items.get(i) or {}).get("include", {}).get(DESIGNED)]
        return list(order)

    elsewhere = {i for sec in content["sections"] for i in shown(variant, sec["order"].get(variant) or [])}
    out = []
    for sec in content["sections"]:
        order = shown(variant, sec["order"].get(variant) or [])
        seen = set(order)
        others = []
        for o in sec["order"].values():
            for iid in o:
                # an item this document shows under another section is not "missing" here
                if iid not in seen and iid not in elsewhere:
                    seen.add(iid)
                    others.append(iid)
        out.append(
            {
                "id": sec["id"],
                "heading": sec["heading"],
                "variants": [v for v, o in sec["order"].items() if shown(v, o)],
                "items": [iid for iid in order if iid in items],
                "others": [iid for iid in others if iid in items],
            }
        )
    return out
