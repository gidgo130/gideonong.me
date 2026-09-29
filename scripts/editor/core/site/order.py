"""Rendered order, mirroring js/data-helpers.js / js/projects.js / js/experience.js.

  * projects index: listing "index" only; `pinned` first, then sortDate desc (stable);
  * featured: listing "index" + featured true; featuredOrder asc (entries without it
    follow, by sortDate desc); the site shows at most 3;
  * experience: visible entries, sortDate desc.
Date rendering follows siteData.formatDates so the list can show "<Context> · <dates>".
"""

from __future__ import annotations

from typing import Optional

SEASONS = ("spring", "summer", "fall", "winter")
SEASON_MONTHS = {"spring": (1, 2, 3, 4, 5), "summer": (6, 7, 8), "fall": (9, 10, 11, 12), "winter": (12, 1, 2)}
SEASON_LAST_MONTH = {"spring": 5, "summer": 8, "fall": 12, "winter": 2}
CONTEXTS = ("industry", "coursework", "personal", "service", "research")
LISTINGS = ("index", "unlisted", "hidden")
HOME_LAYOUTS = ("stacked", "imageLeft", "imageRight", "collage")
EXP_LAYOUTS = ("imageLeft", "imageRight", "fullBleed", "textOnly")
FEATURED_MAX = 3
GALLERY_MIN, GALLERY_MAX = 2, 4


def _sort_key(e: dict) -> str:
    return e.get("sortDate") or ""


def projects_index(entries: list[dict]) -> list[dict]:
    rows = [e for e in entries if e.get("listing") == "index"]
    rows.sort(key=_sort_key, reverse=True)
    return [e for e in rows if e.get("pinned")] + [e for e in rows if not e.get("pinned")]


def projects_featured(entries: list[dict]) -> list[dict]:
    rows = [e for e in entries if e.get("listing") == "index" and e.get("featured")]
    with_order = sorted([e for e in rows if isinstance(e.get("featuredOrder"), (int, float)) and not isinstance(e.get("featuredOrder"), bool)], key=lambda e: e["featuredOrder"])
    without = sorted([e for e in rows if e not in with_order], key=_sort_key, reverse=True)
    return with_order + without


def projects_display(entries: list[dict]) -> list[dict]:
    """Every entry once, in the order the page shows them, with a `tier` note: featured, index, unlisted, hidden, other."""
    out, seen = [], set()
    for e in projects_featured(entries)[:FEATURED_MAX]:
        out.append(dict(e, _tier="featured"))
        seen.add(e["slug"])
    for e in projects_index(entries):
        if e["slug"] not in seen:
            out.append(dict(e, _tier="index"))
            seen.add(e["slug"])
    rest = [e for e in entries if e.get("slug") not in seen]
    rest.sort(key=_sort_key, reverse=True)
    for e in rest:
        out.append(dict(e, _tier=e.get("listing") if e.get("listing") in LISTINGS else "other"))
    return out


def experience_display(entries: list[dict]) -> list[dict]:
    rows = sorted(entries, key=_sort_key, reverse=True)
    return [dict(e, _tier="visible" if e.get("visible") else "hidden") for e in rows]


def suggested_sort_date(dates: Optional[dict]) -> Optional[str]:
    """sortDate the dev check accepts for these dates: month → that month; season → its last month; year → 12."""
    if not isinstance(dates, dict):
        return None
    ref = dates.get("to") if isinstance(dates.get("to"), dict) else dates.get("from")
    if not isinstance(ref, dict) or not isinstance(ref.get("year"), int):
        return None
    y = ref["year"]
    if isinstance(ref.get("month"), int):
        return f"{y}-{ref['month']:02d}"
    if ref.get("season") in SEASON_LAST_MONTH:
        return f"{y}-{SEASON_LAST_MONTH[ref['season']]:02d}"
    return f"{y}-12"


def format_point(p: dict, lang: str, en: dict, es: dict) -> str:
    t = en if lang == "en" else es
    if not isinstance(p, dict):
        return ""
    if p.get("season"):
        return t.get("dateSeasonYear", "{season} {year}").replace("{season}", t.get("date" + p["season"].capitalize(), p["season"])).replace("{year}", str(p.get("year", "")))
    if p.get("month"):
        return t.get("dateMonthYear", "{month} {year}").replace("{month}", t.get(f"dateMonth{p['month']}", str(p["month"]))).replace("{year}", str(p.get("year", "")))
    return str(p.get("year", ""))


def format_dates(dates: Optional[dict], lang: str, en: dict, es: dict) -> str:
    if not isinstance(dates, dict):
        return ""
    t = en if lang == "en" else es
    a = format_point(dates.get("from"), lang, en, es)
    to = dates.get("to")
    if to == "present":
        b = t.get("datePresent", "present")
    elif isinstance(to, dict):
        b = format_point(to, lang, en, es)
    else:
        return a
    return t.get("dateRange", "{from} – {to}").replace("{from}", a).replace("{to}", b)
