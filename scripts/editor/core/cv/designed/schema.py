"""content.json version 2: the Designed variant and its `design` block.

What version 2 adds to version 1 (nothing else changes, so the six masters and every master
path read the file exactly as before):

    version                  2
    header.title.designed    {en, es}   the title line of the Designed CV (starts as the
                                        Professional CV's)
    include.designed         true | false on items and children; a MISSING key means false
    order.designed           on sections and entries: the checklist — every item on it,
                             ticked or not (the flag alone decides what prints)
    design                   everything only the Designed CV has:
        profile, gpa         {include, text{en,es}}
        main                 [{section, heading?}]  the main column's sections, in order;
                             `heading` replaces the section's own heading in this output
        headings             {profile|contact|languages|skills|certs|honors: {en,es}}
        languages, skills, certs, honors
                             [{id, include, <field a>{en,es}, <field b>{en,es}, from?}]
                             (GROUPS names the two fields; `from` = the shared line it came from,
                             `base` = that line's text then)
        copies               {"designed": {copy id: {of, base}}}  — per-output text (D18): the
                             copy "Duplicate into" makes, what it copied and the shared text at
                             that moment. The outer key is the scope.

The phone and email are NOT here: the page reads them from header.contact, the one place the
phone lives (decision 9).
"""

from __future__ import annotations

import copy
from typing import Optional

from .. import content as C
from ..importer import VARIANTS, norm

VERSION = 2
DESIGNED = C.DESIGNED
# sidebar group → its two text fields
GROUPS = {"languages": ("name", "level"), "skills": ("label", "list"), "certs": ("name", "issuer"), "honors": ("name", "years")}
GROUP_LABELS = {"languages": "Languages", "skills": "Skills", "certs": "Certifications", "honors": "Honors"}
SINGLES = ("profile", "gpa")
SINGLE_LABELS = {"profile": "Profile", "gpa": "GPA line"}
DEFAULT_HEADINGS = {
    "profile": {"en": "Profile", "es": "Perfil"},
    "contact": {"en": "Personal details", "es": "Datos personales"},
    "languages": {"en": "Languages", "es": "Idiomas"},
    "skills": {"en": "Skills", "es": "Habilidades"},
    "certs": {"en": "Certifications", "es": "Certificaciones"},
    "honors": {"en": "Honors", "es": "Reconocimientos"},
}
MAIN_DEFAULT = ("education", "experience", "projects", "leadership-service")


def empty_design(content: dict) -> dict:
    ids = [s["id"] for s in content.get("sections", [])]
    return {
        "profile": {"include": False, "text": {"en": "", "es": ""}},
        "gpa": {"include": False, "text": {"en": "", "es": ""}},
        "main": [{"section": sid} for sid in MAIN_DEFAULT if sid in ids],
        "headings": copy.deepcopy(DEFAULT_HEADINGS),
        "languages": [],
        "skills": [],
        "certs": [],
        "honors": [],
        "copies": {DESIGNED: {}},
    }


def version_of(content: dict) -> int:
    v = content.get("version", 1)
    return v if isinstance(v, int) else 1


def migrate(content: dict) -> dict:
    """A version-2 copy of `content` (the same object back when it already is one).
    Version 1 → 2 only adds: the version number, the Designed title line and an empty
    `design` block. Include flags are not touched — a missing "designed" key means false."""
    if version_of(content) >= VERSION:
        return content
    src = copy.deepcopy(content)
    out: dict = {}
    for k, v in src.items():
        if k == "hashes":
            out["design"] = empty_design(src)
        out[k] = v
    out.setdefault("design", empty_design(src))
    out["version"] = VERSION
    titles = out.setdefault("header", {}).setdefault("title", {})
    if DESIGNED not in titles:
        pro = titles.get("professional")
        titles[DESIGNED] = dict(pro) if pro else None
    return out


def strip_designed(content: dict) -> dict:
    """The inverse of migrate() plus everything the Designed variant adds on top: a version-1
    copy with no trace of it. Used by the tests (migrate → strip gives the file back) and to
    show what the masters see."""
    out = copy.deepcopy(content)
    out["version"] = 1
    out.pop("design", None)
    out.get("header", {}).get("title", {}).pop(DESIGNED, None)
    for sec in out.get("sections", []):
        sec.get("order", {}).pop(DESIGNED, None)
    for iid in list(out.get("items", {})):
        item = out["items"][iid]
        if not C.in_masters(item) and DESIGNED in item.get("include", {}):
            del out["items"][iid]  # exists for the Designed CV only
            continue
        item.get("include", {}).pop(DESIGNED, None)
        item.get("order", {}).pop(DESIGNED, None)
        for cid in list(item.get("children", {})):
            child = item["children"][cid]
            if not C.in_masters(child) and DESIGNED in child.get("include", {}):
                del item["children"][cid]
                continue
            child.get("include", {}).pop(DESIGNED, None)
    return out


def is_seeded(content: dict) -> bool:
    return bool((content.get("design") or {}).get("seeded"))


# ----------------------------------------------------------------- carry-over on "Import masters"


def _same_text(a: dict, b: dict) -> bool:
    keys = ("role", "org", "date") if a.get("kind") == "entry" else ("text",)
    return a.get("kind") == b.get("kind") and all(norm(a[k]["en"]) == norm(b[k]["en"]) and norm(a[k]["es"]) == norm(b[k]["es"]) for k in keys)


def _label(node: dict) -> str:
    t = node["role"] if node.get("kind") == "entry" else node["text"]
    s = norm(t.get("en") or t.get("es") or "")
    return s if len(s) <= 60 else s[:57] + "…"


def carry_over(old: dict, new: dict) -> dict:
    """Put the Designed variant of `old` onto `new` (a content set freshly built from the
    masters, already migrated): the `design` block, the title line, the checklist with its
    ticks and order, the Designed-only items and copies with their records.

    A shared item is found again by its id (ids come from the English role / text) and its
    bullets by their text, because a bullet's id is its position and shifts when Word adds or
    removes one. Returns {"kept": n, "moved": [...], "dropped": [...]} — everything that could
    not be put back exactly is named."""
    report: dict = {"kept": 0, "moved": [], "dropped": []}
    if not old.get("design"):
        return report
    new["design"] = copy.deepcopy(old["design"])
    old_title = old.get("header", {}).get("title", {}).get(DESIGNED)
    if old_title is not None:
        new["header"]["title"][DESIGNED] = copy.deepcopy(old_title)
    old_records = C.copy_records(old)
    records: dict = {}
    new["design"].setdefault("copies", {})[DESIGNED] = records
    new_sections = {s["id"]: s for s in new["sections"]}
    remap: dict[str, str] = {}  # old shared id → new id
    used = C.all_ids(new)

    def fresh_id(wanted: str) -> str:
        nid = wanted if wanted not in used else C.unique_id(wanted, used)
        used.add(nid)
        return nid

    def keep_record(old_id: str, new_id: str, what: str) -> None:
        rec = old_records.get(old_id)
        if not rec:
            return
        target = remap.get(rec["of"])
        if target is None:
            report["moved"].append(f"{what}: the shared text it was copied from is no longer in the masters — it stays, as Designed-only text")
            return
        records[new_id] = {"of": target, "base": copy.deepcopy(rec["base"])}

    def match_child(old_item: dict, new_item: dict, cid: str) -> Optional[str]:
        och = old_item["children"][cid]
        for ncid, nch in new_item.get("children", {}).items():
            if _same_text(och, nch):
                return ncid
        return None

    # 1. shared items and their shared bullets: where are they now?
    for iid, item in old["items"].items():
        if not C.in_masters(item) or iid not in new["items"]:
            continue
        remap[iid] = iid
        for cid, ch in item.get("children", {}).items():
            if C.in_masters(ch):
                hit = match_child(item, new["items"][iid], cid)
                if hit:
                    remap[cid] = hit

    # 2. the checklist, section by section, in its order
    pending_records: list[tuple[str, str, str]] = []
    for sec in old["sections"]:
        for iid in sec["order"].get(DESIGNED) or []:
            item = old["items"].get(iid)
            if item is None:
                continue
            label = _label(item)
            shared = C.in_masters(item)
            if shared and iid not in remap:
                report["dropped"].append(f"{label}: no longer in the masters under that name — tick it again in the CV text tab")
                continue
            target = new_sections.get(sec["id"])
            if target is None:
                anchor = remap.get(iid) if shared else remap.get((old_records.get(iid) or {}).get("of", ""))
                target = C.section_of(new, anchor) if anchor else None
                if target is None:
                    report["dropped"].append(f"{label}: its section “{sec['heading'].get('en') or sec['id']}” is gone from the masters")
                    continue
                report["moved"].append(f"{label}: section “{sec['heading'].get('en') or sec['id']}” is gone — placed under “{target['heading'].get('en') or target['id']}”")
            if shared:
                nid = iid
                node = new["items"][nid]
                node["include"][DESIGNED] = bool(item["include"].get(DESIGNED))
            else:
                nid = fresh_id(iid)
                node = {k: copy.deepcopy(v) for k, v in item.items() if k not in ("children", "order")}
                if item["kind"] == "entry":
                    node["order"] = {}
                    node["children"] = {}
                new["items"][nid] = node
                pending_records.append((iid, nid, label))
            target["order"].setdefault(DESIGNED, []).append(nid)
            report["kept"] += 1
            if item["kind"] != "entry":
                continue
            corder = node.setdefault("order", {}).setdefault(DESIGNED, [])
            for cid in item.get("order", {}).get(DESIGNED) or []:
                ch = item.get("children", {}).get(cid)
                if ch is None:
                    continue
                clabel = f"{label} › {_label(ch)}"
                if C.in_masters(ch):
                    ncid = remap.get(cid)
                    if ncid is None or ncid not in node["children"]:
                        report["dropped"].append(f"{clabel}: that bullet's text is no longer in the masters")
                        continue
                    node["children"][ncid]["include"][DESIGNED] = bool(ch["include"].get(DESIGNED))
                else:
                    ncid = fresh_id(cid)
                    node["children"][ncid] = copy.deepcopy(ch)
                    pending_records.append((cid, ncid, clabel))
                corder.append(ncid)
                report["kept"] += 1
    for old_id, new_id, label in pending_records:
        keep_record(old_id, new_id, label)

    # 3. the design block's own references
    design = new["design"]
    kept_main = []
    for m in design.get("main", []):
        if m.get("section") in new_sections:
            kept_main.append(m)
        else:
            report["dropped"].append(f"main-column section “{m.get('section')}” is gone from the masters")
    design["main"] = kept_main
    for group in GROUPS:
        for row in design.get(group, []):
            src = row.get("from")
            if src and src not in new["items"]:
                row.pop("from", None)
                row.pop("base", None)
                report["moved"].append(f"{GROUP_LABELS[group]} row “{row[GROUPS[group][0]].get('en') or row['id']}”: the shared line it was linked to is gone — the row stays, unlinked")
    return report
