"""Pure operations on the Designed part of the content set — no I/O (see schema.py for the shape).

The checklist is the Designed order lists: `sections[].order.designed` for items (which is
also where an item's section in this output is decided, D17 — the résumé already places the
Eagle project under another section the same way) and `items[].order.designed` for bullets.
An order holds everything on the checklist, ticked or not; `include.designed` says what prints.

Per-output text (D18) is the copy "Duplicate into" makes: the first edit of a shared item or
bullet separates it for this output (content.duplicate records what it copied in
design.copies), later edits change the copy. Reset puts the shared wording back and folds the
copy into the shared item again once nothing in it differs.
"""

from __future__ import annotations

import copy
import re
import unicodedata
from datetime import date
from typing import Callable, Optional

from .. import content as C
from ..importer import norm
from . import schema as S

D = C.DESIGNED
LANGS = C.LANGS


def design(content: dict) -> dict:
    d = content.get("design")
    if not isinstance(d, dict):
        raise ValueError("this content set has no Designed block")
    return d


def _lang(lang: str) -> None:
    if lang not in LANGS:
        raise ValueError(f"unknown language {lang!r}")


# ----------------------------------------------------------------- age (D7)


def age_on(birth: date, today: date) -> int:
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def next_birthday(birth: date, today: date) -> date:
    for year in (today.year, today.year + 1):
        try:
            d = birth.replace(year=year)
        except ValueError:  # 29 February
            d = date(year, 3, 1)
        if d > today:
            return d
    return birth.replace(year=today.year + 1)


# ----------------------------------------------------------------- dates (D16)

_SEASON_END = {"spring": 5, "primavera": 5, "summer": 8, "verano": 8, "fall": 12, "autumn": 12, "otono": 12, "winter": 1, "invierno": 1}
_MONTHS = {
    m: i + 1
    for names in (
        ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"),
        ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"),
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"),
    )
    for i, m in enumerate(names)
}
_PRESENT_RE = re.compile(r"\b(present|presente|current|actual|actualidad|now|ongoing|in progress|en curso)\b")
_YEAR_RE = re.compile(r"\b(19|20)\d\d\b")


def _fold(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", (s or "").lower()) if not unicodedata.combining(ch))


def date_key(text: str, today: date) -> Optional[tuple[int, int]]:
    """(year, month) a date text ENDS at: a term is its last month (Spring → May, Summer →
    August, Fall → December), a plain year its December, "present" today. None when there is
    nothing to read."""
    t = _fold(text)
    if not t.strip():
        return None
    end = re.split(r"\s*[–—-]\s*|\s+to\s+|\s+a\s+", t)[-1]
    if _PRESENT_RE.search(end):
        return (today.year, today.month)
    years = _YEAR_RE.findall(end) and [m.group(0) for m in _YEAR_RE.finditer(end)]
    if not years:
        years = [m.group(0) for m in _YEAR_RE.finditer(t)]
        if not years:
            return None
    year = max(int(y) for y in years)
    for word in re.findall(r"[a-z]+", end):
        if word in _SEASON_END:
            return (year, _SEASON_END[word])
        if word in _MONTHS:
            return (year, _MONTHS[word])
    return (year, 12)


def _node_date_key(node: dict, today: date) -> Optional[tuple[int, int]]:
    if node.get("kind") != "entry":
        return None
    return date_key(node["date"].get("en", ""), today) or date_key(node["date"].get("es", ""), today)


def _sorted_in_place(ids: list, keys: list) -> list:
    """`ids` with the dated ones (key not None) newest first, ties in their current order; the
    undated ones do not move."""
    dated = [i for i, k in enumerate(keys) if k is not None]
    ranked = sorted(dated, key=lambda i: keys[i], reverse=True)  # stable
    out = list(ids)
    for slot, src in zip(dated, ranked):
        out[slot] = ids[src]
    return out


# ----------------------------------------------------------------- copies: status, reset


def _find(content: dict, id: str) -> Optional[tuple]:
    try:
        return C.find(content, id)
    except KeyError:
        return None


def status(content: dict, id: str) -> dict:
    """How a checklist row relates to the shared text:
    shared      it IS the shared item (an edit here would separate it for this output)
    copy        made from shared text; `edited` = it reads differently now, `sharedChanged` =
                the shared text is no longer what it was when the copy was made
    neither     written for the Designed CV only"""
    f = _find(content, id)
    if f is None:
        return {"shared": False, "copy": False}
    node = f[-1]
    rec = C.copy_records(content).get(id)
    if rec is None:
        return {"shared": C.in_masters(node), "copy": False}
    o = _find(content, rec["of"])
    if o is None:
        return {"shared": False, "copy": True, "of": rec["of"], "sharedGone": True, "edited": True, "sharedChanged": False, "sharedText": None, "base": rec["base"]}
    cur = C.text_snapshot(o[-1])
    return {
        "shared": False,
        "copy": True,
        "of": rec["of"],
        "sharedGone": False,
        "edited": C.text_snapshot(node) != cur,
        "sharedChanged": cur != rec["base"],
        "sharedText": cur,
        "base": rec["base"],
    }


def edit_text(content: dict, id: str, field: str, lang: str, value: str) -> str:
    """Set one text of a checklist row for this output only. A shared row is separated first
    (the returned id is then the copy's)."""
    _lang(lang)
    if not isinstance(value, str):
        raise ValueError("value must be a string")
    kind, *rest = C.find(content, id)
    node = rest[-1]
    fields = ("role", "org", "date") if node["kind"] == "entry" and kind == "item" else ("text",)
    if field not in fields:
        raise ValueError(f"{field!r} is not a text of this row")
    value = norm(value)
    if node[field][lang] == value:
        return id
    if not C.on_shelf(content, id):
        raise ValueError("it is not on the Designed checklist")
    if C.in_masters(node):
        id = C.duplicate(content, id, D)
        node = C.find(content, id)[-1]
    node[field][lang] = value
    return id


def keep_mine(content: dict, id: str) -> None:
    """Dismiss "the shared text changed": the copy's wording stays, measured against the shared
    text as it is now."""
    rec = C.copy_records(content).get(id)
    if rec is None:
        raise ValueError("this text is not a copy of shared text")
    o = _find(content, rec["of"])
    if o is None:
        raise ValueError("the shared text no longer exists")
    rec["base"] = C.text_snapshot(o[-1])


def reset(content: dict, id: str) -> str:
    """Reset to shared text: the copy reads as the shared item does now and is folded back into
    the shared item, so later shared edits reach this output again. Bullets are reset one by
    one: resetting an entry's line leaves a bullet with its own wording as it is (it stays a
    Designed-only bullet under the shared entry). Returns the id the row has now."""
    records = C.copy_records(content)
    rec = records.get(id)
    if rec is None:
        raise ValueError("this text is not a copy of shared text")
    o = _find(content, rec["of"])
    if o is None:
        raise ValueError("the shared text no longer exists — there is nothing to reset to")
    kind, *rest = C.find(content, id)
    node, orig = rest[-1], o[-1]
    snap = C.text_snapshot(orig)
    for k, v in snap.items():
        node[k] = dict(v)
    rec["base"] = copy.deepcopy(snap)
    if kind == "child":
        parent_id, orig_parent = rest[0], o[1]
        if parent_id == orig_parent:  # a bullet separated on its own: put the shared bullet back in its place
            parent = content["items"][parent_id]
            order = parent["order"][D]
            order[order.index(id)] = rec["of"]
            orig["include"][D] = bool(node["include"].get(D))
            C.delete(content, id)
            return rec["of"]
        _fold_item(content, parent_id)
        return id if _find(content, id) else rec["of"]
    return _fold_item(content, id)


def _fold_item(content: dict, id: str) -> str:
    """Replace a copied item by its shared original once its own line reads the same (see
    reset()). An entry's bullets go back with it: one that reads as its shared bullet gives its
    place (and tick) to that bullet; one with its own wording, or written for this output,
    moves under the shared entry and stays Designed-only."""
    records = C.copy_records(content)
    rec = records.get(id)
    node = content["items"].get(id)
    if rec is None or node is None:
        return id
    orig = content["items"].get(rec["of"])
    if orig is None or orig["kind"] != node["kind"] or C.text_snapshot(node) != C.text_snapshot(orig):
        return id
    sec = C.section_of(content, id, D)
    if sec is None:
        return id
    order = sec["order"][D]
    order[order.index(id)] = rec["of"]
    orig["include"][D] = bool(node["include"].get(D))
    if node["kind"] == "entry":
        used = C.all_ids(content)
        new_order = []
        for cid in node.get("order", {}).get(D, []):
            ch = node["children"].get(cid)
            if ch is None:
                continue
            crec = records.get(cid)
            och = orig.get("children", {}).get(crec["of"]) if crec else None
            if och is not None and C.text_snapshot(ch) == C.text_snapshot(och):
                och["include"][D] = bool(ch["include"].get(D))
                records.pop(cid, None)
                new_order.append(crec["of"])
                continue
            nid = cid
            if och is not None and f"{crec['of']}-{D}" not in used:
                nid = f"{crec['of']}-{D}"  # the name duplicate() gives a bullet separated on its own
            used.add(nid)
            orig["children"][nid] = ch
            if crec is not None and nid != cid:
                records[nid] = records.pop(cid)
            new_order.append(nid)
        orig.setdefault("order", {})[D] = new_order
        node["children"], node["order"] = {}, {}  # they moved: deleting the copy must not take their records
    C.delete(content, id)
    return rec["of"]


# ----------------------------------------------------------------- checklist operations


def tick(content: dict, id: str, on: bool) -> None:
    C.set_include(content, id, D, bool(on), D)


def move(content: dict, id: str, delta: int) -> None:
    C.move(content, id, D, delta)


def remove(content: dict, id: str) -> None:
    C.shelf_remove(content, id)


def main_ids(content: dict) -> list[str]:
    known = {s["id"] for s in content["sections"]}
    return [m["section"] for m in design(content).get("main", []) if m.get("section") in known]


def place(content: dict, id: str, section_id: str) -> None:
    """Show an item under another section in the Designed CV only (D17)."""
    if id not in content["items"]:
        raise KeyError(id)
    if section_id not in main_ids(content):
        raise ValueError(f"{section_id!r} is not a section of the Designed page")
    current = C.section_of(content, id, D)
    if current is None or id not in (current["order"].get(D) or []):
        raise ValueError("it is not on the Designed checklist")
    if current["id"] == section_id:
        return
    current["order"][D].remove(id)
    if not current["order"][D]:
        del current["order"][D]
    target = next(s for s in content["sections"] if s["id"] == section_id)
    target["order"].setdefault(D, []).append(id)


def add_bullet(content: dict, entry_id: str) -> str:
    return C.add_child(content, entry_id, "bullet", D)


def sort_newest(content: dict, section_id: str, today: date) -> list[str]:
    """Order a section's checklist newest first by the entries' dates (D16). Returns the labels
    of the items whose date could not be read; they stay where they are."""
    sec = next((s for s in content["sections"] if s["id"] == section_id), None)
    if sec is None:
        raise KeyError(section_id)
    order = sec["order"].get(D) or []
    keys = [_node_date_key(content["items"].get(i, {}), today) for i in order]
    sec["order"][D] = _sorted_in_place(order, keys)
    return [C.label_of(content, i) for i, k in zip(order, keys) if k is None]


# ----------------------------------------------------------------- the design block


def set_single(content: dict, key: str, lang: str, value: str) -> None:
    _lang(lang)
    if key not in S.SINGLES:
        raise ValueError(f"unknown block {key!r}")
    design(content)[key]["text"][lang] = norm(value)


def include_single(content: dict, key: str, on: bool) -> None:
    if key not in S.SINGLES:
        raise ValueError(f"unknown block {key!r}")
    design(content)[key]["include"] = bool(on)


def set_heading(content: dict, key: str, lang: str, value: str) -> None:
    """A heading of the page: one of the fixed blocks, or "main:<section id>" for a main-column
    section (an empty text there goes back to the section's shared heading)."""
    _lang(lang)
    d = design(content)
    if key.startswith("main:"):
        sid = key[5:]
        m = next((x for x in d.get("main", []) if x.get("section") == sid), None)
        sec = next((s for s in content["sections"] if s["id"] == sid), None)
        if m is None or sec is None:
            raise KeyError(key)
        h = m.setdefault("heading", dict(sec["heading"]))
        h[lang] = norm(value)
        if h == sec["heading"] or not any(h.values()):
            m.pop("heading", None)
        return
    if key not in S.DEFAULT_HEADINGS:
        raise ValueError(f"unknown heading {key!r}")
    d.setdefault("headings", {}).setdefault(key, dict(S.DEFAULT_HEADINGS[key]))[lang] = norm(value)


def main_heading(content: dict, section_id: str) -> dict:
    m = next((x for x in design(content).get("main", []) if x.get("section") == section_id), None)
    sec = next((s for s in content["sections"] if s["id"] == section_id), None)
    if m and m.get("heading"):
        return m["heading"]
    return sec["heading"] if sec else {"en": section_id, "es": section_id}


def heading(content: dict, key: str) -> dict:
    return design(content).get("headings", {}).get(key) or S.DEFAULT_HEADINGS[key]


def _rows(content: dict, group: str) -> list:
    if group not in S.GROUPS:
        raise ValueError(f"unknown group {group!r}")
    return design(content).setdefault(group, [])


def _row(content: dict, group: str, row_id: str) -> tuple[int, dict]:
    for i, r in enumerate(_rows(content, group)):
        if r.get("id") == row_id:
            return i, r
    raise KeyError(row_id)


def row_set(content: dict, group: str, row_id: str, field: str, lang: str, value: str) -> None:
    _lang(lang)
    _, r = _row(content, group, row_id)
    if field not in S.GROUPS[group]:
        raise ValueError(f"{field!r} is not a field of {group}")
    r[field][lang] = norm(value)


def row_include(content: dict, group: str, row_id: str, on: bool) -> None:
    _row(content, group, row_id)[1]["include"] = bool(on)


def row_move(content: dict, group: str, row_id: str, delta: int) -> None:
    if delta not in (-1, 1):
        raise ValueError("delta must be -1 or 1")
    rows = _rows(content, group)
    i, _ = _row(content, group, row_id)
    j = i + delta
    if 0 <= j < len(rows):
        rows.insert(j, rows.pop(i))


def row_add(content: dict, group: str) -> str:
    rows = _rows(content, group)
    used = {r.get("id") for r in rows}
    stem = {"languages": "lang", "skills": "skill", "certs": "cert", "honors": "honor"}[group]
    n = len(rows) + 1
    while f"{stem}-{n}" in used:
        n += 1
    a, b = S.GROUPS[group]
    rows.append({"id": f"{stem}-{n}", "include": True, a: {"en": "", "es": ""}, b: {"en": "", "es": ""}})
    return f"{stem}-{n}"


def row_delete(content: dict, group: str, row_id: str) -> None:
    i, _ = _row(content, group, row_id)
    del _rows(content, group)[i]


def row_keep(content: dict, group: str, row_id: str) -> None:
    """Dismiss "the shared line changed" on a linked row."""
    _, r = _row(content, group, row_id)
    src = content["items"].get(r.get("from") or "")
    if src is None:
        raise ValueError("this row is not linked to a shared line")
    r["base"] = C.text_snapshot(src)


def rows_sort(content: dict, group: str, today: date) -> list[str]:
    """Newest first by the years a row names (honors). Returns the rows with no year."""
    rows = _rows(content, group)
    b = S.GROUPS[group][1]
    keys = [date_key(r[b].get("en", ""), today) or date_key(r[b].get("es", ""), today) for r in rows]
    order = _sorted_in_place(list(range(len(rows))), keys)
    design(content)[group] = [rows[i] for i in order]
    a = S.GROUPS[group][0]
    return [r[a].get("en") or r[a].get("es") or r["id"] for r, k in zip(rows, keys) if k is None]


def row_status(content: dict, row: dict) -> dict:
    src = content["items"].get(row.get("from") or "")
    if src is None:
        return {"linked": False}
    cur = C.text_snapshot(src)
    return {"linked": True, "from": row["from"], "sharedText": cur, "sharedChanged": row.get("base") is not None and cur != row.get("base")}


# ----------------------------------------------------------------- what the page lists


def _row_json(content: dict, id: str, node: dict, today: date) -> dict:
    out = {"id": id, "kind": node["kind"], "on": bool(node["include"].get(D)), "status": status(content, id), "inMasters": [v for v in C.VARIANTS if node["include"].get(v)]}
    if node["kind"] == "entry" and "role" in node:
        out.update(role=node["role"], org=node["org"], date=node["date"], dated=_node_date_key(node, today) is not None)
        out["children"] = [
            {"id": cid, "kind": ch["kind"], "on": bool(ch["include"].get(D)), "text": ch["text"], "status": status(content, cid), "inMasters": [v for v in C.VARIANTS if ch["include"].get(v)]}
            for cid in node.get("order", {}).get(D, [])
            for ch in [node.get("children", {}).get(cid)]
            if ch is not None
        ]
    else:
        out["text"] = node["text"]
    return out


def checklist(content: dict, today: date) -> dict:
    """The main column as the page shows it: per section of design.main, its heading and the
    rows of its Designed order; `stray` = rows on the checklist under a section the page does
    not show (ticked in the CV text tab) — they print nowhere until they are moved."""
    d = design(content)
    main = main_ids(content)
    by_id = {s["id"]: s for s in content["sections"]}
    out = {"main": [], "stray": [], "sections": [{"id": sid, "label": main_heading(content, sid)} for sid in main]}
    for sid in main:
        sec = by_id[sid]
        rows = [_row_json(content, iid, content["items"][iid], today) for iid in sec["order"].get(D) or [] if iid in content["items"]]
        m = next(x for x in d["main"] if x.get("section") == sid)
        out["main"].append({"section": sid, "heading": main_heading(content, sid), "sharedHeading": sec["heading"], "ownHeading": bool(m.get("heading")), "rows": rows})
    for sec in content["sections"]:
        if sec["id"] in main:
            continue
        for iid in sec["order"].get(D) or []:
            if iid in content["items"]:
                r = _row_json(content, iid, content["items"][iid], today)
                r["section"] = sec["heading"]
                out["stray"].append(r)
    return out


def ticked_texts(content: dict, lang: str) -> list[tuple[str, str]]:
    """(label, text) of everything the page prints from the content set in `lang` — what the
    export check looks for in the PDF (D8). The age line is the caller's."""
    _lang(lang)
    d = design(content)
    out: list[tuple[str, str]] = [("name", content["header"]["name"])]
    title = content["header"]["title"].get(D)
    if title and norm(title.get(lang, "")):
        out.append(("title line", title[lang]))
    if d["profile"].get("include"):
        out.append(("profile", d["profile"]["text"][lang]))
    by_id = {s["id"]: s for s in content["sections"]}
    for sid in main_ids(content):
        shown = False
        for iid in by_id[sid]["order"].get(D) or []:
            item = content["items"].get(iid)
            if not item or not item["include"].get(D):
                continue
            if item["kind"] == "entry" and not norm(item["role"][lang]):
                continue  # not on this language's page (render.main_html)
            shown = True
            label = C.label_of(content, iid, lang)
            if item["kind"] == "entry":
                for part in ("role", "org", "date"):
                    if norm(item[part][lang]):
                        out.append((f"{label} › {part}", item[part][lang]))
                for cid in item.get("order", {}).get(D, []):
                    ch = item.get("children", {}).get(cid)
                    if ch and ch["include"].get(D):
                        out.append((f"{label} › {ch['kind']}", ch["text"][lang]))
            else:
                out.append((label, item["text"][lang]))
        if shown:
            out.append((f"heading of {sid}", main_heading(content, sid)[lang]))
    for group, (a, b) in S.GROUPS.items():
        rows = [r for r in d.get(group, []) if r.get("include")]
        if rows:
            out.append((f"heading of {group}", heading(content, group)[lang]))
        for r in rows:
            for f in (a, b):
                if norm(r[f][lang]):
                    out.append((f"{S.GROUP_LABELS[group]} › {r[a].get('en') or r['id']} › {f}", r[f][lang]))
    out.append(("heading of contact", heading(content, "contact")[lang]))
    if d["profile"].get("include"):
        out.append(("heading of profile", heading(content, "profile")[lang]))
    return [(k, norm(v)) for k, v in out if norm(v)]


# ----------------------------------------------------------------- review lines / issue keys (textservice)


def issue_key(base: dict, draft: dict, path: list) -> str:
    """The issue key a change path under "design" belongs to (cvcheck.texts uses the same keys)."""
    if len(path) < 2:
        return ""
    part = path[1]
    if part in S.SINGLES:
        return f"design.{part}"
    if part == "headings" and len(path) > 2:
        return f"design.heading.{path[2]}"
    if part == "main":
        return "design.main"
    if part in S.GROUPS and len(path) > 2 and isinstance(path[2], int):
        for src in (draft, base):
            rows = (src.get("design") or {}).get(part) or []
            if path[2] < len(rows):
                return f"design.{part}.{rows[path[2]].get('id')}"
    return ""


def change_line(base: dict, draft: dict, c: dict, q: Callable, seen: set) -> Optional[str]:
    """One plain-language line for a change under "design", or None when it needs none (the
    copy records are bookkeeping; a sidebar group is summed up once)."""
    p = c["path"]
    part = p[1] if len(p) > 1 else ""
    bd, dd = base.get("design") or {}, draft.get("design") or {}
    if part in ("copies", "seeded"):
        return None
    if part in S.SINGLES:
        name = S.SINGLE_LABELS[part]
        if len(p) > 3 and p[2] == "text":
            return f"Designed › {name} ({str(p[3]).upper()}): {q(c['old'])} → {q(c['new'])}"
        if len(p) > 2 and p[2] == "include":
            return f"Designed › {name}: {'now shown' if c['new'] else 'no longer shown'}"
    if part == "headings" and len(p) > 3:
        return f"Designed › heading of {p[2]} ({str(p[3]).upper()}): {q(c['old'])} → {q(c['new'])}"
    if part == "main":
        if "main" in seen:
            return None
        seen.add("main")
        return "Designed › main-column sections or their headings changed"
    if part in S.GROUPS:
        if part in seen:
            return None
        seen.add(part)
        a = S.GROUPS[part][0]
        old = {r["id"]: r for r in bd.get(part) or []}
        new = {r["id"]: r for r in dd.get(part) or []}
        name = lambda r: r[a].get("en") or r[a].get("es") or r["id"]  # noqa: E731
        bits = []
        added = [name(r) for i, r in new.items() if i not in old]
        removed = [name(r) for i, r in old.items() if i not in new]
        edited = [name(r) for i, r in new.items() if i in old and {k: v for k, v in r.items() if k != "include"} != {k: v for k, v in old[i].items() if k != "include"}]
        ticks = [f"{name(r)} {'on' if r.get('include') else 'off'}" for i, r in new.items() if i in old and bool(r.get("include")) != bool(old[i].get("include"))]
        if added:
            bits.append("added " + ", ".join(q(x) for x in added))
        if removed:
            bits.append("removed " + ", ".join(q(x) for x in removed))
        if edited:
            bits.append("edited " + ", ".join(q(x) for x in edited))
        if ticks:
            bits.append("ticks: " + ", ".join(ticks))
        if [i for i in new if i in old] != [i for i in old if i in new]:
            bits.append("order changed")
        return f"Designed › {S.GROUP_LABELS[part]}: " + ("; ".join(bits) or "changed")
    return "Designed › " + " › ".join(str(x) for x in p[1:]) + f": {q(c['old'])} → {q(c['new'])}"


# ----------------------------------------------------------------- seed (D3)


def apply_seed(content: dict, seed: dict, today: date) -> dict:
    """Fill the Designed variant from a seed (staging/cv-design/seed.json — private; the seed
    names items by their ids in THIS content set). Everything goes through the operations
    above, so the result is exactly what the same clicks in the tab would give. Returns
    {"placed": n, "missing": [ids the content set does not have]}."""
    d = design(content)
    report = {"placed": 0, "missing": []}
    records = C.copy_records(content, create=True)
    if seed.get("title"):
        content["header"]["title"][D] = {l: norm(seed["title"].get(l, "")) for l in LANGS}
    for key in S.SINGLES:
        if seed.get(key):
            d[key] = {"include": True, "text": {l: norm(seed[key].get(l, "")) for l in LANGS}}
    known = {s["id"]: s for s in content["sections"]}
    if seed.get("main"):
        d["main"] = []
        for m in seed["main"]:
            if m.get("section") not in known:
                report["missing"].append(f"section {m.get('section')}")
                continue
            entry = {"section": m["section"]}
            if m.get("heading"):
                entry["heading"] = {l: norm(m["heading"].get(l, "")) for l in LANGS}
            d["main"].append(entry)
    for key, h in (seed.get("headings") or {}).items():
        if key in S.DEFAULT_HEADINGS:
            d.setdefault("headings", {})[key] = {l: norm(h.get(l, "")) for l in LANGS}
    for sid, specs in (seed.get("sections") or {}).items():
        sec = known.get(sid)
        if sec is None:
            report["missing"].append(f"section {sid}")
            continue
        for spec in specs:
            iid = spec["id"]
            item = content["items"].get(iid)
            if item is None:
                report["missing"].append(iid)
                continue
            for s in content["sections"]:
                if iid in (s["order"].get(D) or []):
                    s["order"][D].remove(iid)
            sec["order"].setdefault(D, []).append(iid)
            item["include"][D] = bool(spec.get("on", True))
            report["placed"] += 1
            if item["kind"] == "entry":
                item.setdefault("order", {})[D] = []
                for cs in spec.get("children") or []:
                    if "new" in cs:
                        cid = C.add_child(content, iid, cs.get("kind", "bullet"), D)
                        ch = item["children"][cid]
                        ch["text"] = {l: norm(cs["new"].get(l, "")) for l in LANGS}
                        ch["include"][D] = bool(cs.get("on", True))
                        src = item["children"].get(cs.get("of") or "")
                        if cs.get("of") and src is None:
                            report["missing"].append(cs["of"])
                        elif src is not None:
                            records[cid] = {"of": cs["of"], "base": C.text_snapshot(src)}
                        report["placed"] += 1
                        continue
                    cid = cs["id"]
                    ch = item["children"].get(cid)
                    if ch is None:
                        report["missing"].append(cid)
                        continue
                    item["order"][D].append(cid)
                    ch["include"][D] = bool(cs.get("on", True))
                    report["placed"] += 1
                    if cs.get("edit"):
                        ncid = C.duplicate(content, cid, D)
                        item["children"][ncid]["text"] = {l: norm(cs["edit"].get(l, "")) for l in LANGS}
            if spec.get("edit"):
                nid = C.duplicate(content, iid, D)
                node = content["items"][nid]
                for part, texts in spec["edit"].items():
                    if part in (("role", "org", "date") if node["kind"] == "entry" else ("text",)):
                        node[part] = {l: norm(texts.get(l, "")) for l in LANGS}
    for group, (a, b) in S.GROUPS.items():
        if group not in seed:
            continue
        d[group] = []
        for spec in seed[group]:
            rid = row_add(content, group)
            _, r = _row(content, group, rid)
            r["include"] = bool(spec.get("on", True))
            for f in (a, b):
                r[f] = {l: norm((spec.get(f) or {}).get(l, "")) for l in LANGS}
            src = content["items"].get(spec.get("from") or "")
            if spec.get("from") and src is None:
                report["missing"].append(spec["from"])
            elif src is not None:
                r["from"] = spec["from"]
                r["base"] = C.text_snapshot(src)
    d["seeded"] = today.isoformat()
    return report
