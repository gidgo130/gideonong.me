"""profile.json (name, contact, EN/ES program facts) and adjustments.json
(courses to add that TU's transcript does not print yet): validation only —
the editing itself is generic path edits on the JSON documents.
"""

from __future__ import annotations

from typing import Optional

from .. import validate
from .titles import block_label

# from make_transcript.py — kept in step by hand (the script is never imported here)
POINTS = {"A", "B", "C", "D", "F"}
NO_GPA = {"P", "S", "U", "W", "I", "NG", ""}
PROFILE_LANG_KEYS = ("university", "program", "majors", "minors", "expected_graduation")


def validate_profile(profile: dict) -> list[validate.Issue]:
    issues: list[validate.Issue] = []
    for k in ("name", "contact"):
        if not str(profile.get(k, "")).strip():
            issues.append(validate.Issue("error", "empty", k, "", f"{k} is empty"))
    for lang in ("en", "es"):
        p = profile.get(lang)
        if not isinstance(p, dict):
            issues.append(validate.Issue("error", "missing-lang", lang, lang, f"no {lang.upper()} block"))
            continue
        for k in PROFILE_LANG_KEYS:
            v = p.get(k)
            key = f"{lang}.{k}"
            if k in ("majors", "minors"):
                if not isinstance(v, list) or not v:
                    issues.append(validate.Issue("error", "empty", key, lang, f"{k} must be a non-empty list"))
                elif any(not str(x).strip() for x in v):
                    issues.append(validate.Issue("error", "empty", key, lang, f"{k} has an empty item"))
            elif not str(v or "").strip():
                issues.append(validate.Issue("error", "empty", key, lang, f"{k} is empty"))
            elif validate.is_todo(str(v)):
                issues.append(validate.Issue("error", "todo", key, lang, "TODO in a visible value"))
    en, es = profile.get("en") or {}, profile.get("es") or {}
    for k in ("majors", "minors"):
        if isinstance(en.get(k), list) and isinstance(es.get(k), list) and len(en[k]) != len(es[k]):
            issues.append(validate.Issue("warning", "parity", k, "", f"{k}: EN lists {len(en[k])}, ES lists {len(es[k])}"))
    return issues


def validate_adjustments(adj: dict, data: Optional[dict]) -> list[validate.Issue]:
    issues: list[validate.Issue] = []
    blocks = {block_label(b): [c["code"] for c in b.get("courses", [])] for b in (data or {}).get("blocks", [])}
    on_transcript = {c for codes in blocks.values() for c in codes}
    seen: set = set()
    adds = adj.get("add")
    if adds is None:
        return issues
    if not isinstance(adds, list):
        return [validate.Issue("error", "shape", "add", "", "`add` must be a list")]
    for i, a in enumerate(adds):
        key = f"add[{i}]"
        c = a.get("course") if isinstance(a, dict) else None
        if not isinstance(c, dict):
            issues.append(validate.Issue("error", "shape", key, "", "entry needs a `course` object"))
            continue
        code = str(c.get("code", "")).strip()
        label = f"{key} {code or '(no code)'}"
        if not code:
            issues.append(validate.Issue("error", "empty", label, "", "course code is empty"))
        elif code in on_transcript:
            issues.append(validate.Issue("error", "on-transcript", label, "", f"{code} is already on the TU transcript — remove this adjustment"))
        elif code in seen:
            issues.append(validate.Issue("error", "duplicate", label, "", f"{code} is added twice"))
        seen.add(code)
        block = a.get("block", "")
        if block not in blocks:
            issues.append(validate.Issue("error", "block", label, "", f"block “{block}” is not on the transcript (blocks: {', '.join(blocks) or 'none'})"))
        elif a.get("after") and a["after"] not in blocks[block]:
            issues.append(validate.Issue("warning", "after", label, "", f"“after” course {a['after']} is not in {block}; the course will go last"))
        credits = c.get("credits")
        if not isinstance(credits, int) or isinstance(credits, bool) or not 0 <= credits <= 6:
            issues.append(validate.Issue("error", "credits", label, "", "credits must be a whole number from 0 to 6"))
        grade = c.get("grade", "")
        if grade not in POINTS and grade not in NO_GPA:
            issues.append(validate.Issue("error", "grade", label, "", f"unknown grade {grade!r} (use A–F, P, S, U, W, I, NG or blank)"))
        if not str(a.get("reason", "")).strip():
            issues.append(validate.Issue("warning", "reason", label, "", "no reason given"))
    return issues
