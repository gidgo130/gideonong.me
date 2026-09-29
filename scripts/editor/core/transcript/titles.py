"""course-titles.json as rows, joined with transcript-data.json.

Shapes in the file:
    "ME 3033": { "en": ..., "es": ..., "source": ..., "verified": true }
    "ES 4863": { "sections": { "<transcript section title>": { en, es, source, verified } } }
The second form is for special-topics codes whose title changes per section;
make_transcript.py looks the section up by the course's transcript_title.
"""

from __future__ import annotations

from typing import Any, Optional

from .. import validate

ENTRY_KEYS = ("en", "es", "source", "verified")


def block_label(block: dict) -> str:
    return block.get("source") or f"{block.get('season')} {block.get('year')}"


def courses_on_transcript(data: dict, adjustments: Optional[dict] = None) -> list[dict]:
    """Every course the record will print: {code, transcript_title, term, added}."""
    out = []
    for b in data.get("blocks", []):
        label = block_label(b)
        for c in b.get("courses", []):
            out.append({"code": c["code"], "transcript_title": c.get("transcript_title", ""), "term": label, "added": False})
    for a in (adjustments or {}).get("add", []):
        c = a.get("course") or {}
        if c.get("code"):
            out.append({"code": c["code"], "transcript_title": c.get("transcript_title", ""), "term": a.get("block", ""), "added": True})
    return out


def lookup(titles: dict, code: str, transcript_title: str) -> Optional[dict]:
    entry = titles.get(code)
    if entry is None:
        return None
    if "sections" in entry:
        return entry["sections"].get(transcript_title)
    return entry


def rows(titles: dict, data: dict, adjustments: Optional[dict] = None) -> list[dict]:
    """One row per title entry (+ one per course with no title), in file order."""
    on = courses_on_transcript(data, adjustments)
    seen: dict[tuple, list[dict]] = {}
    for c in on:
        entry = titles.get(c["code"])
        key = (c["code"], c["transcript_title"] if entry is not None and "sections" in entry else "")
        seen.setdefault(key, []).append(c)
    out = []
    for code, entry in titles.items():
        if isinstance(entry, dict) and "sections" in entry:
            for section, e in entry["sections"].items():
                out.append(_row(code, section, e, seen.pop((code, section), [])))
        else:
            out.append(_row(code, "", entry, seen.pop((code, ""), [])))
    for (code, section), courses in seen.items():
        entry = titles.get(code)
        section = section or (courses[0]["transcript_title"] if entry is not None and "sections" in entry else "")
        out.append(_row(code, section, None, courses))
    return out


def _row(code: str, section: str, entry: Optional[dict], courses: list[dict]) -> dict:
    return {
        "id": f"{code}|{section}" if section else code,
        "code": code,
        "section": section,
        "en": (entry or {}).get("en", ""),
        "es": (entry or {}).get("es", ""),
        "source": (entry or {}).get("source", ""),
        "verified": bool((entry or {}).get("verified", False)),
        "missing": entry is None,
        "onTranscript": bool(courses),
        "terms": [c["term"] + (" (added)" if c["added"] else "") for c in courses],
        "transcriptTitle": courses[0]["transcript_title"] if courses else "",
    }


def keys_sorted(titles: dict) -> bool:
    ks = list(titles)
    return ks == sorted(ks)


def set_field(titles: dict, code: str, section: str, field: str, value: Any, keep_sorted: bool = True) -> None:
    """Set en / es / source / verified for a code (or a section of it), creating the entry if needed."""
    if field not in ENTRY_KEYS:
        raise KeyError(field)
    if field == "verified":
        value = bool(value)
    else:
        value = str(value)
    if section:
        entry = titles.setdefault(code, {"sections": {}})
        if "sections" not in entry:
            raise ValueError(f"{code} is a plain entry, not a special-topics code with sections")
        target = entry["sections"].setdefault(section, _blank())
    else:
        if code in titles and "sections" in titles[code]:
            raise ValueError(f"{code} has per-section titles; pick the section")
        target = titles.setdefault(code, _blank())
    target[field] = value
    if keep_sorted and list(titles) != sorted(titles):
        items = sorted(titles.items())
        titles.clear()
        titles.update(items)


def _blank() -> dict:
    return {"en": "", "es": "", "source": "", "verified": False}


def validate_titles(titles: dict, data: Optional[dict] = None, adjustments: Optional[dict] = None) -> list[validate.Issue]:
    issues: list[validate.Issue] = []
    for r in rows(titles, data or {"blocks": []}, adjustments):
        key = r["id"]
        if r["missing"]:
            issues.append(validate.Issue("error", "missing-title", key, "", f"{r['code']} is on the transcript but has no title (transcript says “{r['transcriptTitle']}”)"))
            continue
        for lang in ("en", "es"):
            if not r[lang].strip():
                issues.append(validate.Issue("error", "empty", key, lang, f"{lang.upper()} title is empty"))
            elif validate.is_todo(r[lang]):
                issues.append(validate.Issue("error", "todo", key, lang, "TODO in a title"))
        if r["en"].strip() and r["en"].strip() == r["es"].strip():
            issues.append(validate.Issue("warning", "same", key, "", "ES title is identical to EN"))
        if not r["verified"]:
            issues.append(validate.Issue("warning", "unverified", key, "", "not yet verified against bulletin.utulsa.edu"))
    return issues
