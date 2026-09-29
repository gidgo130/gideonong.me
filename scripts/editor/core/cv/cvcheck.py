"""Validation of the CV content set and the live one-line fit meter (Phase 4b).

check() turns a content dict into validate.Issue objects (key = item / child id,
"header.<part>" or "section.<id>"; lang en | es | ""):

  errors    empty EN or ES on an item included in any variant (entries: role and
            date; org may be empty), TODO or HTML, a blocklist hit (the +1 (918)
            phone is allowed — decision 9 — this text only ever becomes the
            CV / résumé PDFs), a degree line naming a degree or minor that
            scripts/transcript/profile.json does not list (decision 4), and an
            entry line that overflows its master ("fit-overflow-<variant>").
  warnings  voice words ("leveraged" is Gideon's own word in the Spinelli item),
            a GPA line that disagrees with the transcript's cumulative GPA, and
            an entry line within 3 % of its width ("fit-tight-<variant>").

The fit meter builds, per master, the exact spans the render would write
(renderer.entry_part_spans) and measures them with fit.check_entry on a
synthetic paragraph carrying the master's own geometry and run formats, so an
unchanged item measures exactly what the CV & résumé tab reports for the file.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from .. import validate
from ..validate import Issue
from . import content as C
from . import fit, scans
from .docxread import DocInfo, Para, Run
from .importer import VARIANTS, Span, norm, role_length
from .renderer import entry_part_spans

GPA_RE = re.compile(r"GPA\)?:\s*(\d(?:[.,]\d+)?)")
ABBR_RE = re.compile(r"\b[A-Z](?:\.[A-Z])+\.")  # B.A., B.S.M.E., B.S.B.A.
MINOR_RE = re.compile(r"\b(minors?|menor(?:es)?|menci[oó]n(?:es)?)\b", re.IGNORECASE)
EDU_RE = re.compile(r"education|formaci", re.IGNORECASE)
_MINOR_SPLIT = re.compile(r"\s*(?:,|;|\by\b|\band\b|\be\b)\s*")


# ----------------------------------------------------------------- walking the content


def education_section(content: dict) -> Optional[dict]:
    for sec in content["sections"]:
        if sec["id"] == "education" or EDU_RE.search(sec["heading"].get("en", "")) or EDU_RE.search(sec["heading"].get("es", "")):
            return sec
    return None


def _included(node: dict) -> bool:
    return any(node.get("include", {}).values())


def texts(content: dict) -> Iterable[tuple[str, str, str, str, bool, Optional[dict]]]:
    """(key, lang, part, text, required, entry) for every text in the set.

    `required` = must be non-empty (the node is included somewhere); `entry` = the
    parent entry of a child, or the entry itself, for the Spinelli exemption."""
    header = content["header"]
    yield "header.name", "", "name", header["name"], True, None
    for lang in C.LANGS:
        yield "header.contact", lang, "contact", header["contact"][lang], True, None
        for v, title in header["title"].items():
            if title:
                yield f"header.title.{v}", lang, "title", title.get(lang, ""), True, None
    for sec in content["sections"]:
        shown = any(sec["order"].values())
        for lang in C.LANGS:
            yield f"section.{sec['id']}", lang, "heading", sec["heading"][lang], shown, None
    for iid, item in content["items"].items():
        inc = _included(item)
        if item["kind"] == "entry":
            for lang in C.LANGS:
                yield iid, lang, "role", item["role"][lang], inc, item
                yield iid, lang, "org", item["org"][lang], False, item
                yield iid, lang, "date", item["date"][lang], inc, item
            for cid, child in item.get("children", {}).items():
                cinc = _included(child)
                for lang in C.LANGS:
                    yield cid, lang, child["kind"], child["text"][lang], cinc, item
        else:
            for lang in C.LANGS:
                yield iid, lang, "line", item["text"][lang], inc, item


_PART_LABEL = {"name": "Name", "contact": "Contact line", "title": "Title line", "heading": "Heading", "role": "Role", "org": "Organization", "date": "Date", "bullet": "Bullet", "line": "Line"}


def _spinelli(text: str, entry: Optional[dict]) -> bool:
    if scans.SPINELLI_RE.search(text):
        return True
    return bool(entry and entry.get("kind") == "entry" and any(scans.SPINELLI_RE.search(entry["role"].get(l, "")) for l in C.LANGS))


# ----------------------------------------------------------------- degree and GPA lines


def degree_issues(text: str, lang: str, profile: Optional[dict], key: str) -> list[Issue]:
    """A degree line must only name degrees / minors that profile.json lists (decision 4)."""
    n = norm(text)
    if not n or not (ABBR_RE.search(n) or MINOR_RE.search(n)):
        return []
    if not profile or lang not in profile:
        return [Issue("warning", "degree-unchecked", key, lang, "degree line not checked: scripts/transcript/profile.json is not loaded")]
    known = [norm(s) for s in (profile[lang].get("majors") or []) + (profile[lang].get("minors") or []) if norm(s)]
    low = n.lower()
    covered = [False] * len(n)
    for k in known:
        start = 0
        kl = k.lower()
        while True:
            i = low.find(kl, start)
            if i < 0:
                break
            for j in range(i, i + len(k)):
                covered[j] = True
            start = i + len(k)
    out: list[Issue] = []
    for m in ABBR_RE.finditer(n):
        if all(covered[m.start() : m.end()]):
            continue
        what, pos = m.group(0), 0
        for seg in n.split(";"):  # the ";"-separated segment the abbreviation sits in
            if pos <= m.start() < pos + len(seg):
                what = seg.strip(" ,")
                break
            pos += len(seg) + 1
        out.append(Issue("error", "degree", key, lang, f"degree “{what}” is not in scripts/transcript/profile.json ({lang.upper()}) — add it there first, or fix the line"))
    mm = MINOR_RE.search(n)
    if mm:
        rest = n[mm.end() :].lstrip(" :").split(";")[0]
        minors = {norm(s).lower() for s in (profile[lang].get("minors") or [])}
        for seg in _MINOR_SPLIT.split(rest):
            seg = seg.strip(" .")
            if seg and seg.lower() not in minors:
                out.append(Issue("error", "degree", key, lang, f"minor “{seg}” is not in scripts/transcript/profile.json ({lang.upper()})"))
    return out


def gpa_issue(text: str, lang: str, gpa: Optional[str], key: str) -> Optional[Issue]:
    m = GPA_RE.search(text or "")
    if not m or not gpa:
        return None
    try:
        shown, mine = float(m.group(1).replace(",", ".")), float(gpa)
    except ValueError:
        return None
    if abs(shown - mine) > 0.005:
        return Issue("warning", "gpa", key, lang, f"says GPA {m.group(1)} but the transcript's cumulative GPA is {gpa}")
    return None


# ----------------------------------------------------------------- the rules


def check(
    content: dict,
    profile: Optional[dict] = None,
    gpa: Optional[str] = None,
    terms: Iterable[scans.Term] = (),
    fits: Optional[dict] = None,
) -> list[Issue]:
    issues: list[Issue] = []
    terms = list(terms)
    edu = education_section(content)
    edu_items = set()
    if edu:
        for o in edu["order"].values():
            edu_items.update(o)
    for key, lang, part, text, required, entry in texts(content):
        label = _PART_LABEL.get(part, part)
        if not norm(text):
            if required:
                issues.append(Issue("error", "empty", key, lang, f"{label} is empty ({lang.upper()})" if lang else f"{label} is empty"))
            continue
        if validate.is_todo(text):
            issues.append(Issue("error", "todo", key, lang, f"{label}: TODO placeholder"))
        if validate.has_html(text):
            issues.append(Issue("error", "html", key, lang, f"{label}: HTML in the text"))
        for h in scans.blocklist_hits(text, terms, scans.ALLOWED_IN_PUBLISHED_PDFS):
            issues.append(Issue("error", "blocklist", key, lang, f"{label}: blocked term “{h['term']}” ({h['reason'] or 'no reason given'})"))
        words = validate.voice_words(text)
        if words and _spinelli(text, entry):
            words = [w for w in words if not w.startswith("leverag")]
        if words:
            issues.append(Issue("warning", "voice", key, lang, f"{label}: voice words — {', '.join(words)}"))
        if part in ("bullet", "line") and entry is not None and entry.get("kind") == "entry":
            parent_id = next((iid for iid, it in content["items"].items() if it is entry), None)
            if parent_id in edu_items:
                issues += degree_issues(text, lang, profile, key)
                g = gpa_issue(text, lang, gpa, key)
                if g:
                    issues.append(g)
    for iid, per_variant in (fits or {}).items():
        for variant, langs in per_variant.items():
            for lang, line in (langs or {}).items():
                if not line:
                    continue
                where = f"{C.VARIANT_LABELS.get(variant, variant)} {lang.upper()}"
                if line["status"] == "overflow":
                    issues.append(Issue("error", f"fit-overflow-{variant}", iid, lang, f"“{line['text']}” + date is {-line['left_pt']:.1f} pt too wide for one line in the {where} master"))
                elif line["status"] == "tight":
                    issues.append(Issue("warning", f"fit-tight-{variant}", iid, lang, f"“{line['text']}” has only {line['left_pt']:.1f} pt ({line['left_pct']:.1f} %) left before its date wraps in the {where} master"))
    return issues


# ----------------------------------------------------------------- fit meter


def _fmt_at(para: Para, offset: int, info: DocInfo) -> Run:
    """The run of the master's paragraph that holds character `offset` (the last run past the end)."""
    pos = 0
    last = None
    for r in para.runs:
        last = r
        if offset < pos + len(r.text):
            return r
        pos += len(r.text)
    return last or Run("", False, False, False, info.body_size_pt, info.default_font)


def entry_fit(content: dict, item: dict, lang: str, slot: dict, para: Para, info: DocInfo) -> fit.FitLine:
    """Measure one entry as it would be written into `slot` (its own, or a template slot)."""
    groups = entry_part_spans(slot, item["role"][lang], item["org"][lang], item["date"][lang])
    orig_full = "".join(s["text"] for s in slot["spans"])
    before = orig_full.rpartition("\t")[0] if "\t" in orig_full else orig_full
    rlen = min(role_length([Span(s["key"], s["text"]) for s in slot["spans"]]), len(before))
    fmts = (
        _fmt_at(para, 0, info),
        _fmt_at(para, rlen, info),
        _fmt_at(para, len(before) + 1 if len(orig_full) > len(before) + 1 else max(len(orig_full) - 1, 0), info),
    )
    runs = []
    for group, f in zip(groups, fmts):
        for _, text in group:
            if text:
                runs.append(Run(text, f.bold, f.italic, f.underline, f.size_pt, f.font))
    synthetic = Para(
        index=para.index,
        text="".join(r.text for r in runs),
        kind="entry",
        runs=runs,
        centered=False,
        is_bullet=False,
        tab_right_pt=para.tab_right_pt,
        left_indent_pt=para.left_indent_pt,
        right_indent_pt=para.right_indent_pt,
    )
    return fit.check_entry(synthetic, info)


def template_slot(content: dict, item_id: str, variant: str, slots: list[dict]) -> Optional[dict]:
    """For an entry with no paragraph in a master yet: the nearest entry slot of a sibling in the
    same section (the paragraph 4c would clone), else the master's first entry slot."""
    entry_slots = {s["id"]: s for s in slots if s["kind"] == "entry"}
    if not entry_slots:
        return None
    sec = C.section_of(content, item_id)
    if sec:
        order = sec["order"].get(variant) or []
        if item_id in order:
            i = order.index(item_id)
            ranked = sorted((abs(j - i), j) for j, sid in enumerate(order) if sid != item_id and sid in entry_slots)
            if ranked:
                return entry_slots[order[ranked[0][1]]]
        for o in sec["order"].values():
            for sid in o:
                if sid in entry_slots:
                    return entry_slots[sid]
    return next(iter(entry_slots.values()))


def fits_for_item(content: dict, item_id: str, slots_by_master: dict, docs_by_master: dict) -> dict:
    """{variant: {lang: FitLine json | None}} for every variant the entry is included in."""
    item = content["items"].get(item_id)
    out: dict = {}
    if not item or item["kind"] != "entry":
        return out
    for variant in VARIANTS:
        if not item["include"].get(variant):
            continue
        out[variant] = {}
        for lang in C.LANGS:
            master = content["masters"].get(variant, {}).get(lang)
            slots = slots_by_master.get(master) or []
            info = docs_by_master.get(master)
            if info is None or not slots:
                out[variant][lang] = None
                continue
            slot = next((s for s in slots if s["id"] == item_id and s["kind"] == "entry"), None) or template_slot(content, item_id, variant, slots)
            if slot is None or slot["para"] >= len(info.paragraphs):
                out[variant][lang] = None
                continue
            try:
                line = entry_fit(content, item, lang, slot, info.paragraphs[slot["para"]], info)
            except fit.FontUnavailable:
                out[variant][lang] = None
                continue
            out[variant][lang] = line.to_json()
    return out


def all_fits(content: dict, slots_by_master: dict, docs_by_master: dict) -> dict:
    return {iid: fits_for_item(content, iid, slots_by_master, docs_by_master) for iid, it in content["items"].items() if it["kind"] == "entry"}
