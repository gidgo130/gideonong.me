"""Phase 4a: read the CV masters into a content set + slot maps, and prove the
round trip is lossless before anything is ever written back.

A master is paragraphs only (checked: anything else — tables, fields,
hyperlinks, tracked changes, content controls — refuses the import naming the
paragraph). Each paragraph becomes a list of SPANS: adjacent runs whose run
properties are equal after dropping the revision (rsid) attributes are merged;
spell-check markers and cached page breaks are dropped. Entry lines split into
role (first span) · org (the plain text before the tab, minus the " · "
separator) · date (after the tab); every other paragraph is one text.

Content model (staging/cv-content/content.json, gitignored):
    header.name / title[variant] / contact          EN + ES texts
    sections[]  {id, heading{en,es}, order{variant: [item ids]}}
    items{}     {id, kind: entry|line, role/org/date or text {en,es}, include{variant},
                 sep (entry separator), order{variant: [child ids]}, children{} …}
    hashes      master file → slot id → sha1 of the text at import / last render
Slot maps (staging/cv-content/slots/<master>.json): paragraph index and the
formatting spans (rPr XML + original texts) for every slot of every master.
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lxml import etree

from . import docxread

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


ALLOWED_BODY = {w("p"), w("sectPr")}
ALLOWED_PARA = {w("pPr"), w("r"), w("proofErr")}
ALLOWED_RUN = {w("rPr"), w("t"), w("tab"), w("lastRenderedPageBreak")}
SEP = " · "
VARIANTS = ("full", "professional", "resume")


class ImportError_(ValueError):
    pass


# ----------------------------------------------------------------- spans


def strip_rsid(el):
    e = copy.deepcopy(el)
    for x in e.iter():
        for a in list(x.attrib):
            if "rsid" in a.lower():
                del x.attrib[a]
    return e


def rpr_key(rpr) -> str:
    """Canonical text of a run's properties (rsid dropped); "" for no properties."""
    if rpr is None:
        return ""
    return etree.tostring(strip_rsid(rpr), method="c14n").decode("utf-8")


def run_text(r) -> str:
    out = []
    for c in r:
        if c.tag == w("t"):
            out.append(c.text or "")
        elif c.tag == w("tab"):
            out.append("\t")
    return "".join(out)


@dataclass
class Span:
    key: str  # rpr_key
    text: str
    rpr: Optional[object] = None  # the first original rPr element (deepcopied), for re-emission

    def to_json(self) -> dict:
        return {"key": self.key, "text": self.text, "rpr": etree.tostring(self.rpr).decode("utf-8") if self.rpr is not None else None}


@dataclass
class MPara:
    index: int
    kind: str
    spans: list[Span]
    ppr_key: str
    element: object = field(repr=False)

    @property
    def text(self) -> str:
        return "".join(s.text for s in self.spans)


@dataclass
class MasterDoc:
    path: Path
    paragraphs: list[MPara]
    document: object = field(repr=False)  # python-docx Document (kept for writing)
    info: object = field(repr=False)  # docxread.DocInfo


def _check_allowed(body) -> None:
    for i, child in enumerate(body):
        if child.tag not in ALLOWED_BODY:
            raise ImportError_(f"body element {child.tag.split('}')[1]} (not a paragraph) at position {i} is not supported")
    for pi, p in enumerate(body.findall(w("p"))):
        for c in p:
            if c.tag not in ALLOWED_PARA:
                raise ImportError_(f"paragraph {pi + 1} holds a {c.tag.split('}')[1]} (field, hyperlink, tracked change or content control) — not supported")
            if c.tag == w("r"):
                for rc in c:
                    if rc.tag not in ALLOWED_RUN:
                        raise ImportError_(f"paragraph {pi + 1} holds a run with {rc.tag.split('}')[1]} — not supported")


def spans_of(p) -> list[Span]:
    spans: list[Span] = []
    for c in p:
        if c.tag != w("r"):
            continue
        rpr = c.find(w("rPr"))
        key = rpr_key(rpr)
        text = run_text(c)
        if spans and spans[-1].key == key:
            spans[-1].text += text
        else:
            spans.append(Span(key, text, copy.deepcopy(rpr) if rpr is not None else None))
    return [s for s in spans if s.text != ""] or spans[:1]


def read_master(path: Path) -> MasterDoc:
    from docx import Document

    path = Path(path)
    doc = Document(str(path))
    body = doc.element.body
    _check_allowed(body)
    info = docxread.read(path)
    paras = []
    for i, p in enumerate(body.findall(w("p"))):
        ppr = p.find(w("pPr"))
        paras.append(MPara(i, info.paragraphs[i].kind, spans_of(p), rpr_key(ppr), p))
    return MasterDoc(path, paras, doc, info)


# ----------------------------------------------------------------- structure


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def is_bold(key: str) -> bool:
    """The canonical rPr text writes <w:b></w:b> (never self-closing); a w:val="0" turns bold off."""
    return bool(re.search(r"<w:b(?:\s[^>]*)?>(?:</w:b>)?", key)) and 'w:b w:val="0"' not in key and 'w:b w:val="false"' not in key


def role_length(spans: list[Span]) -> int:
    """Characters of the role: the leading bold spans (or the first span), never past the tab."""
    full = "".join(s.text for s in spans)
    before = full.rpartition("\t")[0] if "\t" in full else full
    n = 0
    for i, s in enumerate(spans):
        if i and not (is_bold(s.key) and is_bold(spans[0].key)):
            break
        n += len(s.text)
        if not is_bold(s.key):
            break
    return min(n, len(before))


def split_entry(spans: list[Span]) -> dict:
    """role / org / date / sep from an entry line's spans (role = leading bold spans, date = after the tab)."""
    full = "".join(s.text for s in spans)
    before, _, date = full.rpartition("\t")
    role = before[: role_length(spans)]
    rest = before[len(role):]
    m = re.match(r"^\s*·\s*", rest)
    sep = m.group(0) if m else ""
    org = rest[len(sep):]
    notes = []
    if spans and not is_bold(spans[0].key):
        notes.append("role is not bold")
    if org and (role + sep) != (role.rstrip() + SEP):
        notes.append(f"separator is “{(role[len(role.rstrip()):] + sep)!r}” not “ · ”")
    return {"role": norm(role), "org": norm(org), "date": norm(date), "sep": sep if org else SEP, "notes": notes}


def slugify(s: str, fallback: str = "item") -> str:
    s = re.sub(r"[^a-z0-9]+", "-", norm(s).lower()).strip("-")
    return (s[:40].rstrip("-")) or fallback


@dataclass
class Node:
    """One paragraph of a master in its structural place."""

    para: MPara
    kind: str  # name | title | contact | heading | entry | child-bullet | child-line | line | empty
    parts: dict  # role/org/date/sep for entries, text for others


def structure(doc: MasterDoc) -> list[Node]:
    nodes: list[Node] = []
    header_done = False
    in_entry = False
    for p in doc.paragraphs:
        k = p.kind
        if k in ("name", "title", "contact"):
            nodes.append(Node(p, k, {"text": norm(p.text)}))
            continue
        if k == "empty":
            nodes.append(Node(p, "empty", {}))
            continue
        header_done = True
        if k == "heading":
            in_entry = False
            nodes.append(Node(p, "heading", {"text": norm(p.text)}))
        elif k == "entry":
            in_entry = True
            nodes.append(Node(p, "entry", split_entry(p.spans)))
        elif k == "bullet":
            nodes.append(Node(p, "child-bullet" if in_entry else "line", {"text": norm(p.text)}))
        else:
            nodes.append(Node(p, "child-line" if in_entry else "line", {"text": norm(p.text)}))
    return nodes


def pair(en: list[Node], es: list[Node]) -> tuple[list[tuple[Optional[Node], Optional[Node]]], list[str]]:
    """Align EN and ES nodes by kind sequence; gaps pair with None. Returns (pairs, notes)."""
    ka, kb = [n.kind for n in en], [n.kind for n in es]
    sm = difflib.SequenceMatcher(a=ka, b=kb, autojunk=False)
    pairs: list[tuple[Optional[Node], Optional[Node]]] = []
    notes: list[str] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            pairs += list(zip(en[i1:i2], es[j1:j2]))
        else:
            for n in en[i1:i2]:
                pairs.append((n, None))
                notes.append(f"EN paragraph {n.para.index + 1} ({n.kind}: “{(n.parts.get('text') or n.parts.get('role', ''))[:50]}”) has no ES twin")
            for n in es[j1:j2]:
                pairs.append((None, n))
                notes.append(f"ES paragraph {n.para.index + 1} ({n.kind}: “{(n.parts.get('text') or n.parts.get('role', ''))[:50]}”) has no EN twin")
    return pairs, notes


# ----------------------------------------------------------------- merge into the content set


def _lang_pair(a: Optional[Node], b: Optional[Node], key: str) -> dict:
    return {"en": a.parts.get(key, "") if a else "", "es": b.parts.get(key, "") if b else ""}


def _item_key(kind: str, parts: dict) -> tuple:
    if kind == "entry":
        return (kind, parts["role"]["en"], parts["role"]["es"], parts["org"]["en"], parts["org"]["es"], parts["date"]["en"], parts["date"]["es"])
    return (kind, parts["text"]["en"], parts["text"]["es"])


def _unique(base: str, used: set) -> str:
    cand, n = base, 2
    while cand in used:
        cand = f"{base}-{n}"
        n += 1
    used.add(cand)
    return cand


def merge(variant_docs: dict) -> tuple[dict, dict, dict]:
    """variant → {"en": MasterDoc, "es": MasterDoc}  ⇒  (content, slots, report).

    Items are shared across variants only when EN and ES both match; differing
    wording stays a separate item (the report lists near-duplicates).
    """
    content = {
        "version": 1,
        "masters": {v: {lang: d.path.name for lang, d in docs.items()} for v, docs in variant_docs.items()},
        "header": {"name": "", "title": {v: None for v in variant_docs}, "contact": {"en": "", "es": ""}},
        "sections": [],
        "items": {},
        "hashes": {},
    }
    slots: dict[str, list] = {}
    report = {"variants": {}, "unpaired": {}, "shared": 0, "nearDuplicates": [], "sections": [], "formatting": []}
    item_by_key: dict[tuple, str] = {}
    child_by_key: dict[tuple, str] = {}
    section_by_en: dict[str, dict] = {}
    used_ids: set = set()

    def add_slot(doc: MasterDoc, node: Optional[Node], sid: str, kind: str):
        if node is None:
            return
        slots.setdefault(doc.path.name, []).append(
            {"id": sid, "kind": kind, "para": node.para.index, "spans": [s.to_json() for s in node.para.spans], "sep": node.parts.get("sep")}
        )
        content["hashes"].setdefault(doc.path.name, {})[sid] = text_hash(node)

    for variant in VARIANTS:
        docs = variant_docs.get(variant)
        if not docs:
            continue
        en_doc, es_doc = docs["en"], docs["es"]
        en_nodes, es_nodes = structure(en_doc), structure(es_doc)
        pairs, notes = pair(en_nodes, es_nodes)
        report["unpaired"][variant] = notes
        stats = {"entries": 0, "lines": 0, "children": 0, "sharedWithEarlier": 0}
        current_section: Optional[dict] = None
        current_item: Optional[str] = None
        for a, b in pairs:
            n = a or b
            kind = n.kind
            if kind == "name":
                content["header"]["name"] = content["header"]["name"] or (a.parts["text"] if a else b.parts["text"])
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, "header.name", "text")
            elif kind == "title":
                content["header"]["title"][variant] = _lang_pair(a, b, "text")
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, "header.title", "text")
            elif kind == "contact":
                if not content["header"]["contact"]["en"]:
                    content["header"]["contact"] = _lang_pair(a, b, "text")
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, "header.contact", "text")
            elif kind == "empty":
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, f"empty.{node.para.index}" if node else "", "empty")
            elif kind == "heading":
                heading = _lang_pair(a, b, "text")
                sec = section_by_en.get(heading["en"])
                if sec is None:
                    sec = {"id": _unique(slugify(heading["en"] or heading["es"], "section"), used_ids), "heading": heading, "order": {}}
                    section_by_en[heading["en"]] = sec
                    content["sections"].append(sec)
                sec["order"].setdefault(variant, [])
                current_section, current_item = sec, None
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, f"section.{sec['id']}", "text")
            elif kind == "entry":
                parts = {k: _lang_pair(a, b, k) for k in ("role", "org", "date")}
                key = _item_key("entry", parts)
                iid = item_by_key.get(key)
                if iid is None:
                    iid = _unique(slugify(parts["role"]["en"] or parts["role"]["es"], "entry"), used_ids)
                    item_by_key[key] = iid
                    content["items"][iid] = {"kind": "entry", **parts, "sep": n.parts.get("sep", SEP), "include": {v: False for v in VARIANTS}, "order": {}, "children": {}}
                    stats["entries"] += 1
                else:
                    stats["sharedWithEarlier"] += 1
                item = content["items"][iid]
                item["include"][variant] = True
                item["order"].setdefault(variant, [])
                if current_section is None:
                    current_section = {"id": _unique("untitled", used_ids), "heading": {"en": "", "es": ""}, "order": {}}
                    content["sections"].append(current_section)
                current_section["order"].setdefault(variant, []).append(iid)
                current_item = iid
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, iid, "entry")
                    for note in (node.parts.get("notes") or []) if node else []:
                        report["formatting"].append(f"{doc.path.name}, paragraph {node.para.index + 1} (“{node.parts['role'][:40]}”): {note}")
            elif kind in ("child-bullet", "child-line"):
                text = _lang_pair(a, b, "text")
                ckind = "bullet" if kind == "child-bullet" else "line"
                key = (current_item, ckind, text["en"], text["es"])
                cid = child_by_key.get(key)
                parent = content["items"][current_item]
                if cid is None:
                    cid = _unique(f"{current_item}-{len(parent['children']) + 1}", used_ids)
                    child_by_key[key] = cid
                    parent["children"][cid] = {"kind": ckind, "text": text, "include": {v: False for v in VARIANTS}}
                    stats["children"] += 1
                else:
                    stats["sharedWithEarlier"] += 1
                parent["children"][cid]["include"][variant] = True
                parent["order"].setdefault(variant, []).append(cid)
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, cid, ckind)
            else:  # line at section level
                text = _lang_pair(a, b, "text")
                key = _item_key("line", {"text": text})
                iid = item_by_key.get(key)
                if iid is None:
                    sec_id = current_section["id"] if current_section else "top"
                    iid = _unique(f"{sec_id}-{slugify(text['en'] or text['es'], 'line')[:24]}", used_ids)
                    item_by_key[key] = iid
                    content["items"][iid] = {"kind": "line", "text": text, "include": {v: False for v in VARIANTS}}
                    stats["lines"] += 1
                else:
                    stats["sharedWithEarlier"] += 1
                content["items"][iid]["include"][variant] = True
                if current_section is None:
                    current_section = {"id": _unique("untitled", used_ids), "heading": {"en": "", "es": ""}, "order": {}}
                    content["sections"].append(current_section)
                current_section["order"].setdefault(variant, []).append(iid)
                current_item = None
                for doc, node in ((en_doc, a), (es_doc, b)):
                    add_slot(doc, node, iid, "line")
        report["variants"][variant] = stats
    report["shared"] = sum(1 for it in content["items"].values() if sum(it["include"].values()) > 1)
    report["sections"] = [{"id": s["id"], "heading": s["heading"]["en"], "variants": [v for v, o in s["order"].items() if o]} for s in content["sections"]]
    # near-duplicates: same EN, different ES (or the reverse) across items
    by_en: dict[str, list[str]] = {}
    for iid, it in content["items"].items():
        en_text = it["role"]["en"] if it["kind"] == "entry" else it["text"]["en"]
        by_en.setdefault(en_text, []).append(iid)
    report["nearDuplicates"] = [ids for ids in by_en.values() if len(ids) > 1]
    return content, slots, report


def text_string(parts: dict, entry: bool) -> str:
    """The one string a paragraph's text hashes to: role⇥org⇥date for entries, the text otherwise."""
    if entry:
        return "\t".join([norm(parts.get("role", "")), norm(parts.get("org", "")), norm(parts.get("date", ""))])
    return norm(parts.get("text", ""))


def hash_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def text_hash(node: Node) -> str:
    return hash_text(text_string(node.parts, node.kind == "entry"))


# ----------------------------------------------------------------- proof of losslessness


def normalized_paragraphs(doc: MasterDoc) -> list[tuple[str, list[tuple[str, str]]]]:
    return [(p.ppr_key, [(s.key, s.text) for s in p.spans]) for p in doc.paragraphs]


def other_parts(path: Path) -> dict[str, bytes]:
    """Every part of the package except document.xml, canonicalized (python-docx re-serializes XML)."""
    out = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name == "word/document.xml":
                continue
            data = z.read(name)
            if name.endswith((".xml", ".rels")):
                try:
                    root = etree.fromstring(data)
                    if name == "[Content_Types].xml":
                        # python-docx rewrites this part from its own list: compare as a set
                        data = b"\n".join(sorted(etree.tostring(c, method="c14n") for c in root))
                    else:
                        data = etree.tostring(root, method="c14n")
                except etree.XMLSyntaxError:
                    pass
            out[name] = data
    return out


def compare(original: Path, rendered: Path) -> list[str]:
    """Differences between two masters after normalization; [] means lossless."""
    problems = []
    a, b = read_master(original), read_master(rendered)
    na, nb = normalized_paragraphs(a), normalized_paragraphs(b)
    if len(na) != len(nb):
        problems.append(f"paragraph count differs: {len(na)} vs {len(nb)}")
    for i, (pa, pb) in enumerate(zip(na, nb), 1):
        if pa[0] != pb[0]:
            problems.append(f"paragraph {i}: paragraph properties differ")
        if pa[1] != pb[1]:
            ta, tb = "".join(t for _, t in pa[1]), "".join(t for _, t in pb[1])
            problems.append(f"paragraph {i}: {'text' if ta != tb else 'run formatting'} differs (“{ta[:40]}” vs “{tb[:40]}”)")
    pa, pb = other_parts(original), other_parts(rendered)
    for name in sorted(set(pa) | set(pb)):
        if pa.get(name) != pb.get(name):
            problems.append(f"package part {name} differs")
    return problems
