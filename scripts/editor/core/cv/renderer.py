"""Write content text back into a master's paragraphs (Phase 4a: the paragraph
writer + the forced re-render used by the losslessness proof; 4c adds the
edit-aware render, cloning and drift).

A slot's spans carry the original run properties (rPr XML) and original texts.
Writing a paragraph replaces its runs with one run per span, each with its
stored rPr; text tabs become <w:tab/>. When the wanted text equals the
original, the original spans are re-emitted exactly, so a no-edit render
reproduces the paragraph (that is what the proof checks). When it differs,
the whole text goes into the first span of that part (entry: role / org / date
spans; others: the first span) and the remaining spans of that part are dropped.
"""

from __future__ import annotations

import copy
import io
from pathlib import Path
from typing import Optional

from lxml import etree

from .importer import SEP, W_NS, XML_NS, MasterDoc, Span, norm, role_length, w


def _rpr_from_json(s: Optional[str]):
    return etree.fromstring(s) if s else None


def _make_run(rpr_xml: Optional[str], text: str):
    r = etree.SubElement(etree.Element(w("p")), w("r"))  # detached run
    rpr = _rpr_from_json(rpr_xml)
    if rpr is not None:
        r.append(rpr)
    for i, piece in enumerate(text.split("\t")):
        if i:
            etree.SubElement(r, w("tab"))
        if piece:
            t = etree.SubElement(r, w("t"))
            t.text = piece
            if piece != piece.strip() or "  " in piece:
                t.set(f"{{{XML_NS}}}space", "preserve")
    return r


def write_paragraph(p_el, spans: list[tuple[Optional[str], str]]) -> None:
    """Replace the paragraph's runs by one run per (rPr XML, text); empty texts are skipped."""
    for child in list(p_el):
        if child.tag in (w("r"), w("proofErr")):
            p_el.remove(child)
    for rpr_xml, text in spans:
        if text == "":
            continue
        p_el.append(_make_run(rpr_xml, text))


def entry_spans(slot: dict, role: str, org: str, date: str, sep: Optional[str] = None) -> list[tuple[Optional[str], str]]:
    """Spans for an entry line from its parts, reusing the slot's formats.

    Unchanged parts re-emit the original spans (so the proof holds and NBSPs in
    dates survive); a changed part is written into that part's first span.
    """
    role_spans, rest_spans, date_spans = entry_part_spans(slot, role, org, date, sep)
    return role_spans + rest_spans + date_spans


def entry_part_spans(slot: dict, role: str, org: str, date: str, sep: Optional[str] = None) -> tuple[list, list, list]:
    """entry_spans() split into its three groups: (role, separator + org + tab, date).

    The fit meter (cvcheck.py) measures each group with that part's own format.
    """
    spans = slot["spans"]
    full = "".join(s["text"] for s in spans)
    before, _, orig_date = full.rpartition("\t")
    orig_role = before[: role_length([Span(s["key"], s["text"]) for s in spans])]
    orig_rest = before[len(orig_role):]
    sep = sep if sep is not None else (slot.get("sep") or SEP)
    # which spans belong to which part
    role_spans, rest_spans, date_spans = [], [], []
    pos = 0
    for s in spans:
        start, end = pos, pos + len(s["text"])
        pos = end
        if end <= len(orig_role):
            role_spans.append(s)
        elif start >= len(before) + 1:
            date_spans.append(s)
        else:
            rest_spans.append(s)
    out_role: list[tuple[Optional[str], str]] = []
    out_rest: list[tuple[Optional[str], str]] = []
    out_date: list[tuple[Optional[str], str]] = []
    if norm(role) == norm(orig_role) and role_spans:
        out_role += [(s["rpr"], s["text"]) for s in role_spans]
    else:
        fmt = role_spans[0]["rpr"] if role_spans else (spans[0]["rpr"] if spans else None)
        trailing = orig_role[len(orig_role.rstrip()):]  # a role that carried its own space before the separator keeps it
        out_role.append((fmt, role + trailing))
    wanted_rest = (sep + org if org else "") + "\t"
    if norm(orig_rest) == norm(wanted_rest) and rest_spans:
        out_rest += [(s["rpr"], s["text"]) for s in rest_spans]
    else:
        fmt = rest_spans[0]["rpr"] if rest_spans else None
        out_rest.append((fmt, wanted_rest))
    if norm(date) == norm(orig_date) and date_spans:
        out_date += [(s["rpr"], s["text"]) for s in date_spans]
    else:
        fmt = date_spans[0]["rpr"] if date_spans else None
        out_date.append((fmt, date.replace(" ", "\xa0")))
    return out_role, out_rest, out_date


def text_spans(slot: dict, text: str) -> list[tuple[Optional[str], str]]:
    spans = slot["spans"]
    orig = "".join(s["text"] for s in spans)
    if norm(text) == norm(orig):
        return [(s["rpr"], s["text"]) for s in spans]
    return [(spans[0]["rpr"] if spans else None, text)]


def slot_target(content: dict, slot: dict, variant: str, lang: str) -> Optional[tuple]:
    """What the content wants in a slot's paragraph: ("entry", role, org, date), ("text", text),
    or None when the slot's id no longer exists in the content (a removed item) or is empty."""
    sid, kind = slot["id"], slot["kind"]
    if kind == "empty":
        return None
    if kind == "entry":
        item = content["items"].get(sid)
        if item is None:
            return None
        return ("entry", item["role"][lang], item["org"][lang], item["date"][lang])
    if sid.startswith("header."):
        part = sid.split(".", 1)[1]
        if part == "name":
            return ("text", content["header"]["name"])
        if part == "title":
            title = content["header"]["title"].get(variant)
            return ("text", title.get(lang, "")) if title else None
        return ("text", content["header"]["contact"][lang])
    if sid.startswith("section."):
        sec = next((s for s in content["sections"] if s["id"] == sid.split(".", 1)[1]), None)
        return ("text", sec["heading"][lang]) if sec else None
    item = content["items"].get(sid)
    if item is None:  # a child
        item = next((c for it in content["items"].values() for cid, c in it.get("children", {}).items() if cid == sid), None)
    if item is None:
        return None
    return ("text", item["text"][lang])


def slot_spans(content: dict, slot: dict, variant: str, lang: str) -> Optional[list[tuple[Optional[str], str]]]:
    """The (rPr XML, text) spans the render would write into this slot, or None (see slot_target)."""
    target = slot_target(content, slot, variant, lang)
    if target is None:
        return None
    if target[0] == "entry":
        return entry_spans(slot, target[1], target[2], target[3])  # the slot's own separator
    return text_spans(slot, target[1])


def wanted_ids(content: dict, variant: str) -> list[str]:
    """Slot ids a master of this variant holds, in document order: header, then per section
    (only sections with items in this variant) its heading, items and their children."""
    header = content["header"]
    out = ["header.name"]
    if header["title"].get(variant):
        out.append("header.title")
    out.append("header.contact")
    items = content["items"]
    for sec in content["sections"]:
        order = sec["order"].get(variant) or []
        if not order:
            continue
        out.append(f"section.{sec['id']}")
        for iid in order:
            item = items.get(iid)
            if item is None:
                continue
            out.append(iid)
            if item["kind"] == "entry":
                out += [cid for cid in item.get("order", {}).get(variant, []) if cid in item.get("children", {})]
    return out


def plan_master(content: dict, slots: list[dict], master_file: str) -> dict:
    """What rendering `content` into this master would do, without touching it:
    changed = slots whose spans differ from what is there, added = wanted ids with no slot,
    removed = slots whose id is no longer wanted. 4b shows it in the review; 4c renders from it."""
    variant = lang = None
    for v, langs in content["masters"].items():
        for lg, name in langs.items():
            if name == master_file:
                variant, lang = v, lg
    if variant is None:
        raise KeyError(master_file)
    wanted = wanted_ids(content, variant)
    wanted_set = set(wanted)
    by_id = {s["id"]: s for s in slots}
    changed, added, removed = [], [], []
    for sid in wanted:
        slot = by_id.get(sid)
        if slot is None:
            added.append(sid)
            continue
        spans = slot_spans(content, slot, variant, lang)
        if spans is None or spans != [(s["rpr"], s["text"]) for s in slot["spans"]]:
            changed.append(sid)
    for slot in slots:
        if slot["kind"] != "empty" and slot["id"] not in wanted_set:
            removed.append(slot["id"])
    return {"file": master_file, "variant": variant, "lang": lang, "changed": changed, "added": added, "removed": removed}


def force_render(doc: MasterDoc, slots: list[dict], content: dict, out_path: Path) -> Path:
    """Re-write EVERY slot paragraph from the content (no edits) and save a copy — the proof input."""
    paras = doc.document.element.body.findall(w("p"))
    variant, lang = _variant_of(doc, content), _lang_of(doc, content)
    for slot in slots:
        spans = slot_spans(content, slot, variant, lang)
        if spans is None:
            continue
        write_paragraph(paras[slot["para"]], spans)
    buf = io.BytesIO()
    doc.document.save(buf)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(buf.getvalue())
    return out_path


def _variant_of(doc: MasterDoc, content: dict) -> str:
    for v, langs in content["masters"].items():
        if doc.path.name in langs.values():
            return v
    raise KeyError(doc.path.name)


def _lang_of(doc: MasterDoc, content: dict) -> str:
    for langs in content["masters"].values():
        for lang, name in langs.items():
            if name == doc.path.name:
                return lang
    raise KeyError(doc.path.name)
