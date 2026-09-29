"""The Word route (Phase 4d): make the same edits as renderer.render_master, but
through a PRIVATE Word instance, so Word itself keeps the layout consistent.

plan_ops() decides everything without Word — from the live slots, the wanted
ids and the same clone templates the python route uses — as a Plan of
paragraph operations: deletes, a placement walk (keep / move / insert, each
new paragraph a copy of its template), and text rewrites (an entry's role /
separator + organization + tab / date replaced part by part inside the
paragraph, so each part keeps its own formatting). simulate() applies a Plan
to a plain list of paragraph texts (tests). execute() drives Word over a temp
copy of the master (win32com DispatchEx, hidden, quits itself; the real master
is never opened): one live Range per paragraph, FormattedText copies for
moves and inserts (paragraph properties, numbering and runs come along), a
temporary anchor paragraph so nothing is ever inserted after the final
paragraph mark, every bookmark deleted (Word's _GoBack would refuse the
import), Save. The result goes through the same self-check as the python
route (renderer.self_check, relaxed for the package parts Word re-saves).
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import content as C
from .importer import Span, norm, read_master, role_length
from .renderer import RenderError, RenderResult, _expected_text, entry_part_spans, id_kind, live_slots, master_of, template_for, wanted_ids

WD_CHARACTER = 1
WD_LIST_APPLY_TO_SELECTION = 2

Ref = tuple  # ("orig", index) | ("new", k)


@dataclass
class Rewrite:
    ref: Ref
    replacements: list  # [(offset, old_len, new_text)] in DESCENDING offset order


@dataclass
class Step:
    kind: str  # keep | move | insert
    ref: Ref
    template: Optional[Ref] = None  # insert only


@dataclass
class Plan:
    file: str
    deletes: list = field(default_factory=list)  # orig indexes
    steps: list = field(default_factory=list)  # the placement walk, final order
    rewrites: list = field(default_factory=list)
    report: dict = field(default_factory=lambda: {"rewritten": [], "added": [], "removed": [], "moved": []})
    ids: dict = field(default_factory=dict)  # ref → slot id

    @property
    def changed(self) -> bool:
        return any(self.report.get(k) for k in ("rewritten", "added", "removed", "moved"))


# ----------------------------------------------------------------- planning (no Word)


def _group_texts(slot: dict) -> tuple[str, str, str, str]:
    """(role, rest, date, full) texts of an entry slot as they are now."""
    full = "".join(s["text"] for s in slot["spans"])
    before, _, date = full.rpartition("\t") if "\t" in full else (full, "", "")
    rlen = min(role_length([Span(s["key"], s["text"]) for s in slot["spans"]]), len(before))
    return full[:rlen], full[rlen : len(before) + 1] if "\t" in full else full[rlen:], date, full


def replacements_for(content: dict, slot: dict, sid: str, variant: str, lang: str) -> list:
    """Part-wise replacements turning the slot's current text into the content's text."""
    kind = id_kind(content, sid)
    if kind == "entry":
        item = content["items"][sid]
        groups = entry_part_spans(slot, item["role"][lang], item["org"][lang], item["date"][lang])
        new = ["".join(t for _, t in g) for g in groups]
        role, rest, date, full = _group_texts(slot)
        out = []
        offsets = ((0, role), (len(role), rest), (len(role) + len(rest), date))
        for (off, old), new_text in zip(offsets, new):
            if old != new_text:
                out.append((off, len(old), new_text))
        return sorted(out, key=lambda r: -r[0])
    text = _expected_text(content, sid, variant, lang) or ""
    full = "".join(s["text"] for s in slot["spans"])
    return [] if norm(full) == norm(text) else [(0, len(full), text)]


def plan_ops(content: dict, slot_map: list[dict], master_path: Path) -> Plan:
    master_path = Path(master_path)
    doc = read_master(master_path)
    variant, lang = master_of(content, doc.path.name)
    live = live_slots(doc, slot_map)
    plan = Plan(doc.path.name)
    by_id = {s["id"]: s for s in live if s["kind"] != "empty"}
    wanted = wanted_ids(content, variant)
    wanted_set = set(wanted)
    for sid in wanted:
        if not norm((_expected_text(content, sid, variant, lang) or "").replace("\t", " ")):
            raise RenderError(f"{doc.path.name}: {C.label_of(content, sid)} has no {lang.upper()} text — a master never gets an empty paragraph")
    # deletes
    for s in live:
        if s["kind"] != "empty" and s["id"] not in wanted_set:
            plan.deletes.append(s["para"])
            plan.report["removed"].append(s["id"])
    # placement walk
    remaining = deque(s["id"] for s in live if s["kind"] != "empty" and s["id"] in wanted_set)
    new_k = 0
    for sid in wanted:
        slot = by_id.get(sid)
        if slot is not None:
            ref = ("orig", slot["para"])
            plan.ids[ref] = sid
            if remaining and remaining[0] == sid:
                remaining.popleft()
                plan.steps.append(Step("keep", ref))
            else:
                remaining.remove(sid)
                plan.steps.append(Step("move", ref))
                plan.report["moved"].append(sid)
            reps = replacements_for(content, slot, sid, variant, lang)
            if reps:
                plan.rewrites.append(Rewrite(ref, reps))
                plan.report["rewritten"].append(sid)
        else:
            tmpl = template_for(content, sid, variant, live)
            if tmpl is None:
                raise RenderError(f"{doc.path.name}: no paragraph of the right kind to clone for {C.label_of(content, sid)}")
            ref = ("new", new_k)
            new_k += 1
            plan.ids[ref] = sid
            plan.steps.append(Step("insert", ref, ("orig", tmpl["para"])))
            plan.report["added"].append(sid)
            reps = replacements_for(content, tmpl, sid, variant, lang)
            if reps:
                plan.rewrites.append(Rewrite(ref, reps))
    return plan


def simulate(plan: Plan, texts: list[str]) -> list[str]:
    """Apply a plan to a plain list of paragraph texts (what the Word steps must produce)."""
    para = {("orig", i): t for i, t in enumerate(texts)}
    for i in plan.deletes:
        para.pop(("orig", i))
    for st in plan.steps:
        if st.kind == "insert":
            para[st.ref] = para[st.template]
    for rw in plan.rewrites:
        t = para[rw.ref]
        for off, old_len, new in rw.replacements:
            t = t[:off] + new + t[off + old_len :]
        para[rw.ref] = t
    return [para[st.ref] for st in plan.steps]


# ----------------------------------------------------------------- Word


def word_available() -> Optional[str]:
    """None when the Word route can run, else why not (no instance is started)."""
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        return "pywin32 is not installed (run the requirements install)"
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application"):
            return None
    except OSError:
        return "Microsoft Word is not installed (Word.Application is not registered)"


def execute(plan: Plan, working_copy: Path, log: Callable[[str], None] = lambda s: None) -> None:
    """Carry out a plan on `working_copy` (a temp copy of the master) with a private Word."""
    try:
        import pythoncom
        import win32com.client
    except ImportError as e:  # pragma: no cover
        raise RenderError(f"pywin32 is not installed ({e})") from e
    pythoncom.CoInitialize()
    word = None
    try:
        try:
            word = win32com.client.DispatchEx("Word.Application")
        except Exception as e:
            raise RenderError(f"Word could not be started ({e}). Is Microsoft Word installed?") from e
        try:
            word.Visible = False
            word.DisplayAlerts = 0
            log(f"Word {getattr(word, 'Version', '?')} started (private instance)")
            doc = word.Documents.Open(str(working_copy), ReadOnly=False, AddToRecentFiles=False, Visible=False)
            try:
                _run(plan, doc, log)
                for bm in list(doc.Bookmarks):
                    bm.Delete()
                doc.Save()
                log(f"saved {working_copy.name}")
            finally:
                doc.Close(0)
        except RenderError:
            raise
        except Exception as e:
            raise RenderError(f"Word did not complete the edit of {plan.file}: {e}") from e
        finally:
            if word is not None:
                try:
                    word.Quit()
                except Exception:  # pragma: no cover
                    pass
    finally:
        pythoncom.CoUninitialize()


def _trim(ranges: dict, anchor, pos: int, copy_end: int, keep) -> None:
    """Word's live ranges grow when text is inserted at their boundaries: after a copy landed at
    `pos`, shrink the range that ended there and the ones that started there back to their own
    paragraphs (the copy is `keep`, left alone)."""
    for r in list(ranges.values()) + [anchor]:
        if r is keep:
            continue
        if r.End > pos and r.Start < pos:
            r.SetRange(r.Start, pos)  # it ended at pos and swallowed the copy
        elif r.Start == pos and r.End > copy_end:
            r.SetRange(copy_end, r.End)  # it started at pos and the copy went inside it


def _run(plan: Plan, doc, log: Callable[[str], None]) -> None:
    n = doc.Paragraphs.Count
    ranges = {("orig", i): doc.Paragraphs(i + 1).Range for i in range(n)}  # live ranges
    doc.Content.InsertParagraphAfter()  # the anchor: nothing is ever inserted after the final mark
    anchor = doc.Paragraphs(doc.Paragraphs.Count).Range
    last_orig = ranges[("orig", n - 1)]
    if last_orig.End > anchor.Start:
        last_orig.SetRange(last_orig.Start, anchor.Start)  # the new mark was absorbed into it
    for i in plan.deletes:
        ranges.pop(("orig", i)).Delete()
    log(f"{plan.file}: {len(plan.deletes)} paragraph(s) deleted")
    last = None  # the range of the last placed paragraph
    for st in plan.steps:
        if st.kind == "keep":
            last = ranges[st.ref]
            continue
        pos = last.End if last is not None else 0
        src = ranges[st.ref] if st.kind == "move" else ranges[st.template]
        doc.Range(pos, pos).FormattedText = src.FormattedText
        copy = doc.Range(pos, pos + 1).Paragraphs(1).Range
        _trim(ranges, anchor, pos, copy.End, copy)
        if st.kind == "move":
            src.Delete()
        ranges[st.ref] = copy
        last = copy
    log(f"{plan.file}: {sum(1 for s in plan.steps if s.kind == 'move')} moved, {sum(1 for s in plan.steps if s.kind == 'insert')} inserted")
    for rw in plan.rewrites:
        r = ranges[rw.ref]
        for off, old_len, new in rw.replacements:
            doc.Range(r.Start + off, r.Start + off + old_len).Text = new
    log(f"{plan.file}: {len(plan.rewrites)} paragraph(s) rewritten")
    # remove the anchor: give it the last real paragraph's formatting, then join them
    if last is None:
        raise RenderError(f"{plan.file}: nothing left to write")
    real_last = doc.Paragraphs(doc.Paragraphs.Count - 1)
    a = doc.Paragraphs(doc.Paragraphs.Count)
    a.Format = real_last.Format
    a.Style = real_last.Style
    lf = real_last.Range.ListFormat
    if lf.ListType != 0:
        a.Range.ListFormat.ApplyListTemplateWithLevel(lf.ListTemplate, True, WD_LIST_APPLY_TO_SELECTION, 0, lf.ListLevelNumber)
    else:
        a.Range.ListFormat.RemoveNumbers()
    doc.Range(real_last.Range.End - 1, real_last.Range.End).Delete()


def render_master(content: dict, slot_map: list[dict], master_path: Path, log: Callable[[str], None] = lambda s: None) -> RenderResult:
    """The Word route's counterpart of renderer.render_master: bytes of the edited copy + report."""
    master_path = Path(master_path)
    plan = plan_ops(content, slot_map, master_path)
    if not plan.changed:
        return RenderResult(master_path.name, master_path.read_bytes(), plan.report)
    problem = word_available()
    if problem:
        raise RenderError(problem)
    tmp = Path(tempfile.mkdtemp(prefix="cv-word-")) / master_path.name
    try:
        shutil.copy2(master_path, tmp)
        execute(plan, tmp, log)
        data = tmp.read_bytes()
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)
    return RenderResult(master_path.name, data, plan.report)
