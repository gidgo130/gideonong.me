"""Write content text back into a master's paragraphs.

4a: the paragraph writer and the forced re-render the losslessness proof uses.
4c: the edit-aware render (`render_master`): the slot map's paragraphs are
re-read from the master as it is now (`live_slots`, so a formatting-only Word
edit is what gets reused), only paragraphs whose wanted spans differ are
rewritten, new items clone the nearest paragraph of the same kind, removed
ones are dropped, and the body is re-sequenced to the content's order. The
result must pass `self_check` (re-import equals the content, every other
package part untouched) before the service writes it.

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
import difflib
import io
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lxml import etree

from . import content as C
from .importer import SEP, W_NS, XML_NS, MasterDoc, Span, hash_text, norm, read_master, role_length, spans_of, split_entry, structure, text_string, w
from .importer import other_parts as _other_parts


class RenderError(ValueError):
    pass


class StructureDrift(RenderError):
    """The master's paragraphs no longer match the slot map (something beyond text changed in Word)."""


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


def master_of(content: dict, master_file: str) -> tuple[str, str]:
    for v, langs in content["masters"].items():
        for lg, name in langs.items():
            if name == master_file:
                return v, lg
    raise KeyError(master_file)


# ----------------------------------------------------------------- 4c: live slots, templates


def kind_class(kind: str) -> str:
    """entry | bullet | empty | text — what a slot kind and a paragraph kind have in common."""
    return kind if kind in ("entry", "bullet", "empty") else "text"


def id_kind(content: dict, sid: str) -> str:
    """The slot kind an id renders as."""
    if sid.startswith("header.") or sid.startswith("section."):
        return "text"
    try:
        kind, *rest = C.find(content, sid)
    except KeyError:
        return "text"
    return rest[-1]["kind"]


def live_slots(doc: MasterDoc, slot_map: list[dict]) -> list[dict]:
    """The slot map's ids and kinds with the spans re-read from the master as it is now,
    plus each paragraph's element. Raises StructureDrift when the paragraphs no longer line up."""
    paras = doc.paragraphs
    if len(slot_map) != len(paras):
        raise StructureDrift(f"{doc.path.name}: {len(paras)} paragraphs now, {len(slot_map)} at the last import or apply")
    out = []
    for sl in slot_map:
        p = paras[sl["para"]]
        if kind_class(sl["kind"]) != kind_class(p.kind):
            raise StructureDrift(f"{doc.path.name}: paragraph {p.index + 1} is now a {p.kind} (“{norm(p.text)[:40]}”), it held a {sl['kind']}")
        entry = sl["kind"] == "entry"
        out.append({"id": sl["id"], "kind": sl["kind"], "para": sl["para"], "spans": [s.to_json() for s in p.spans], "sep": split_entry(p.spans)["sep"] if entry else None, "element": p.element})
    return out


def _nearest(order: list, sid: str, candidates: dict) -> Optional[dict]:
    """Among the ids of `order` that are in `candidates`, the one closest to sid's position."""
    if sid in order:
        i = order.index(sid)
        ranked = sorted((abs(j - i), j) for j, x in enumerate(order) if x != sid and x in candidates)
        if ranked:
            return candidates[order[ranked[0][1]]]
    for x in order:
        if x != sid and x in candidates:
            return candidates[x]
    return None


def template_for(content: dict, sid: str, variant: str, slots: list[dict]) -> Optional[dict]:
    """The slot whose paragraph a new `sid` would clone in this master: the nearest sibling of the
    same kind (same section for items, same entry for children, the previous section's heading
    for a heading), else any paragraph of that kind. None when the master has nothing to clone."""
    if sid.startswith("header."):
        return None
    by_kind: dict[str, dict] = {}
    for s in slots:
        by_kind.setdefault(s["kind"], {})[s["id"]] = s
    if sid.startswith("section."):
        heads = {k: v for k, v in by_kind.get("text", {}).items() if k.startswith("section.")}
        ids = [f"section.{s['id']}" for s in content["sections"]]
        return _nearest(ids, sid, heads) if heads else None
    try:
        kind, *rest = C.find(content, sid)
    except KeyError:
        return None
    node = rest[-1]
    cands = dict(by_kind.get(node["kind"], {}))
    if kind == "item":
        sec = C.section_of(content, sid)
        if sec is not None:
            cands = {k: v for k, v in cands.items() if k in content["items"]}
            order = sec["order"].get(variant) or []
            hit = _nearest(order, sid, cands)
            if hit is None:
                for o in sec["order"].values():
                    hit = _nearest(o, sid, cands)
                    if hit:
                        break
            if hit:
                return hit
        cands = {k: v for k, v in by_kind.get(node["kind"], {}).items() if k in content["items"]}
        return next(iter(cands.values()), None) or next(iter(by_kind.get(node["kind"], {}).values()), None)
    parent_id = rest[0]
    parent = content["items"][parent_id]
    siblings = {k: v for k, v in cands.items() if k in parent.get("children", {})}
    hit = _nearest(parent.get("order", {}).get(variant) or [], sid, siblings)
    if hit is None:
        for o in parent.get("order", {}).values():
            hit = _nearest(o, sid, siblings)
            if hit:
                break
    if hit:
        return hit
    return next(iter(cands.values()), None)


# ----------------------------------------------------------------- 4c: the edit-aware render


@dataclass
class RenderResult:
    file: str
    data: bytes
    report: dict = field(default_factory=dict)  # rewritten / added / removed / moved: lists of ids

    @property
    def changed(self) -> bool:
        return any(self.report.get(k) for k in ("rewritten", "added", "removed", "moved"))


def render_master(content: dict, slot_map: list[dict], master_path: Path) -> RenderResult:
    """Render the content into a copy of the master in memory (the file is not touched)."""
    master_path = Path(master_path)
    doc = read_master(master_path)
    variant, lang = master_of(content, doc.path.name)
    live = live_slots(doc, slot_map)
    by_id = {s["id"]: s for s in live if s["kind"] != "empty"}
    # empty paragraphs ride along with the paragraph before them
    trailing: dict[str, list] = {}
    leading: list = []
    prev = None
    for s in live:
        if s["kind"] == "empty":
            (trailing.setdefault(prev, []) if prev else leading).append(s["element"])
        else:
            prev = s["id"]
    body = doc.document.element.body
    wanted = wanted_ids(content, variant)
    report = {"rewritten": [], "added": [], "removed": [], "moved": []}
    sequence: list = []
    for sid in wanted:
        if not norm((_expected_text(content, sid, variant, lang) or "").replace("\t", " ")):
            raise RenderError(f"{doc.path.name}: {C.label_of(content, sid)} has no {lang.upper()} text — a master never gets an empty paragraph")
        slot = by_id.get(sid)
        if slot is not None:
            spans = slot_spans(content, slot, variant, lang)
            if spans is None:
                raise RenderError(f"{doc.path.name}: nothing to write for {sid}")
            if spans != [(s["rpr"], s["text"]) for s in slot["spans"]]:
                write_paragraph(slot["element"], spans)
                report["rewritten"].append(sid)
            sequence.append(slot["element"])
            sequence += trailing.get(sid, [])
            continue
        tmpl = template_for(content, sid, variant, live)
        if tmpl is None:
            raise RenderError(f"{doc.path.name}: no paragraph of the right kind to clone for {C.label_of(content, sid)}")
        el = copy.deepcopy(tmpl["element"])
        spans = slot_spans(content, {**tmpl, "id": sid, "kind": id_kind(content, sid), "element": None}, variant, lang)
        if spans is None:
            raise RenderError(f"{doc.path.name}: nothing to write for {sid}")
        write_paragraph(el, spans)
        sequence.append(el)
        report["added"].append(sid)
    wanted_set = set(wanted)
    for s in live:
        if s["kind"] != "empty" and s["id"] not in wanted_set:
            report["removed"].append(s["id"])
    old_seq = [s["id"] for s in live if s["kind"] != "empty" and s["id"] in wanted_set]
    new_seq = [sid for sid in wanted if sid in by_id]
    sm = difflib.SequenceMatcher(a=old_seq, b=new_seq, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            report["moved"] += [x for x in new_seq[j1:j2] if x not in report["moved"]]
    # re-sequence the body: every paragraph out, the wanted ones back in order before sectPr
    for p in list(body.findall(w("p"))):
        body.remove(p)
    sect = body.find(w("sectPr"))
    for el in leading + sequence:
        if sect is not None:
            sect.addprevious(el)
        else:
            body.append(el)
    buf = io.BytesIO()
    doc.document.save(buf)
    return RenderResult(doc.path.name, buf.getvalue(), report)


def _expected_text(content: dict, sid: str, variant: str, lang: str) -> Optional[str]:
    target = slot_target(content, {"id": sid, "kind": id_kind(content, sid)}, variant, lang)
    if target is None:
        return None
    if target[0] == "entry":
        return text_string({"role": target[1], "org": target[2], "date": target[3]}, True)
    return text_string({"text": target[1]}, False)


def self_check(content: dict, master_file: str, rendered: bytes, original_path: Path, relaxed: bool = False) -> list[str]:
    """Problems with a rendered master ([] = it may be written): its paragraphs must be exactly
    the content's wanted ids with the content's text, and every other package part unchanged.
    `relaxed` (the Word route): the package is Word's own save of the document, so its parts
    are not compared here — parts_changed() lists them for the report."""
    variant, lang = master_of(content, master_file)
    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="cv-check-")) / master_file
    try:
        tmp.write_bytes(rendered)
        try:
            doc = read_master(tmp)
        except Exception as e:
            return [f"{master_file}: the rendered file does not read back ({e})"]
        wanted = wanted_ids(content, variant)
        paras = [p for p in doc.paragraphs if p.kind != "empty"]
        if len(paras) != len(wanted):
            problems.append(f"{master_file}: {len(paras)} paragraphs rendered, {len(wanted)} expected")
        for p, sid in zip(paras, wanted):
            want_kind = kind_class(id_kind(content, sid))
            if kind_class(p.kind) != want_kind:
                problems.append(f"{master_file}, paragraph {p.index + 1}: rendered as a {p.kind}, expected {want_kind} ({C.label_of(content, sid)})")
                continue
            expected = _expected_text(content, sid, variant, lang)
            got = text_string(split_entry(p.spans), True) if want_kind == "entry" else text_string({"text": p.text}, False)
            if expected is None or got != expected:
                problems.append(f"{master_file}, paragraph {p.index + 1}: reads “{got[:60]}”, expected “{(expected or '')[:60]}”")
        try:
            a, b = _other_parts(Path(original_path)), _other_parts(tmp)
        except Exception as e:
            return problems + [f"{master_file}: package parts could not be compared ({e})"]
        for name in sorted(set(a) | set(b)):
            if a.get(name) != b.get(name) and not relaxed:
                problems.append(f"{master_file}: package part {name} would change")
    finally:
        try:
            tmp.unlink()
            tmp.parent.rmdir()
        except OSError:
            pass
    return problems


def parts_changed(a_path: Path, b_path: Path) -> list[str]:
    a, b = _other_parts(Path(a_path)), _other_parts(Path(b_path))
    return [n for n in sorted(set(a) | set(b)) if a.get(n) != b.get(n)]


def compare_layout(a_path: Path, b_path: Path) -> list[str]:
    """How two renders of the same content differ in what a reader sees: paragraph count, each
    paragraph's kind, text and resolved run formatting (bold / italic / underline / size,
    adjacent equal runs merged). Raw XML is not compared — Word and python write it differently."""
    from . import docxread

    a, b = docxread.read(Path(a_path)), docxread.read(Path(b_path))
    problems = []
    if len(a.paragraphs) != len(b.paragraphs):
        problems.append(f"paragraph count differs: {len(a.paragraphs)} vs {len(b.paragraphs)}")

    def runs(p):
        out = []
        for r in p.runs:
            key = (r.bold, r.italic, r.underline, round(r.size_pt, 1))
            if out and out[-1][0] == key:
                out[-1] = (key, out[-1][1] + r.text)
            else:
                out.append((key, r.text))
        return [(k, t.replace("\xa0", " ")) for k, t in out]

    for i, (pa, pb) in enumerate(zip(a.paragraphs, b.paragraphs), 1):
        if pa.kind != pb.kind:
            problems.append(f"paragraph {i}: {pa.kind} vs {pb.kind}")
        elif norm(pa.text) != norm(pb.text):
            problems.append(f"paragraph {i}: text differs (“{norm(pa.text)[:40]}” vs “{norm(pb.text)[:40]}”)")
        elif runs(pa) != runs(pb):
            problems.append(f"paragraph {i}: run formatting differs (“{norm(pa.text)[:40]}”)")
    return problems


def rebuild_slots(content: dict, master_path: Path) -> tuple[list[dict], dict]:
    """The slot map and hashes for a master as it is on disk now (after a write)."""
    master_path = Path(master_path)
    doc = read_master(master_path)
    variant, lang = master_of(content, doc.path.name)
    wanted = wanted_ids(content, variant)
    slots, hashes = [], {}
    k = 0
    for p in doc.paragraphs:
        if p.kind == "empty":
            slots.append({"id": f"empty.{p.index}", "kind": "empty", "para": p.index, "spans": [s.to_json() for s in p.spans], "sep": None})
            continue
        if k >= len(wanted):
            raise RenderError(f"{doc.path.name}: more paragraphs than the content expects")
        sid = wanted[k]
        k += 1
        kind = id_kind(content, sid)
        entry = kind == "entry"
        slots.append({"id": sid, "kind": kind, "para": p.index, "spans": [s.to_json() for s in p.spans], "sep": split_entry(p.spans)["sep"] if entry else None})
        hashes[sid] = hash_text(text_string(split_entry(p.spans), True) if entry else text_string({"text": p.text}, False))
    if k != len(wanted):
        raise RenderError(f"{doc.path.name}: fewer paragraphs than the content expects")
    return slots, hashes


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
