"""Content set → the Designed CV page (HTML). The preview and the PDF are this same string;
only where the stylesheets and the photo are fetched from differs (the editor's server for the preview, file
URLs for the print job).

The template is static/designed/page.html with its pieces in parts.html; every text is
escaped here. Nothing personal is in the template or in this module: the name, the contact
line (the one place the phone lives, decision 9), every entry and the sidebar rows come
from the content set, the age from staging/editor-private/personal.json through the caller.
"""

from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .. import content as C
from ..cvcheck import education_section
from ..importer import norm
from . import model as M
from . import schema as S

D = C.DESIGNED
TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "static" / "designed"
LAYOUTS = {"c": "Experience first", "e": "Light right rail"}
PALETTES = {"blue": "TU blue", "bronze": "gideonong.me bronze"}
WEB_ICONS = {"mono": "Angular G", "web": "Globe", "browser": "Browser", "compass": "Compass", "code": "Code"}
LANGS = ("es", "en")  # Spanish first (D12)
# the photo's own size in CSS px (the box minus its border, see designed.css .photo)
PHOTO_PX = {"c": 140, "e": 86}
LINKEDIN_MASK = "icons/InBug-White-noR.png"
PHOTO_REL = "assets/images/about/headshot.jpg"
AGE_TEXT = {"es": "Edad: {n} años", "en": "Age: {n}"}
PHOTO_ALT = {"es": "Foto de {name}", "en": "Photo of {name}"}
DOC_TITLE = {"es": "CV — {name}", "en": "CV — {name}"}


@dataclass(frozen=True)
class Options:
    layout: str = "c"
    palette: str = "blue"
    lang: str = "es"
    web_icon: str = "mono"

    def checked(self) -> "Options":
        if self.layout not in LAYOUTS:
            raise ValueError(f"unknown layout {self.layout!r}")
        if self.palette not in PALETTES:
            raise ValueError(f"unknown palette {self.palette!r}")
        if self.lang not in LANGS:
            raise ValueError(f"unknown language {self.lang!r}")
        if self.web_icon not in WEB_ICONS:
            raise ValueError(f"unknown website icon {self.web_icon!r}")
        return self


# ----------------------------------------------------------------- template pieces

_parts_cache: dict = {}


def _parts() -> dict[str, str]:
    path = TEMPLATE_DIR / "parts.html"
    mtime = path.stat().st_mtime
    if _parts_cache.get("mtime") != mtime:
        text = path.read_text(encoding="utf-8")
        chunks = re.split(r"<!--\s*part:\s*([\w-]+)\s*-->", text)
        parts = {chunks[i]: re.sub(r"<!--.*?-->", "", chunks[i + 1], flags=re.S).strip() for i in range(1, len(chunks) - 1, 2)}
        _parts_cache.update(mtime=mtime, parts=parts)
    return _parts_cache["parts"]


def _fill(template: str, **values: str) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), template)


def part(_part: str, /, **values: str) -> str:
    return _fill(_parts()[_part], **values)


def esc(s: str) -> str:
    return html.escape(norm(s), quote=True)


# ----------------------------------------------------------------- contact line

_PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


def contact_parts(text: str) -> list[tuple[str, str]]:
    """header.contact ("a@b.c | +1 (918) … | site | linkedin.com/in/…") as (kind, text) rows in
    the page's order: phone, email, web, linkedin, then anything else. The phone and email are
    read from here on purpose — they are stored once, in the header."""
    rows: dict[str, list[str]] = {"tel": [], "mail": [], "web": [], "linkedin": [], "link": []}
    for piece in re.split(r"\s*\|\s*", norm(text)):
        if not piece:
            continue
        if _EMAIL_RE.match(piece):
            rows["mail"].append(piece)
        elif _PHONE_RE.match(piece) and sum(ch.isdigit() for ch in piece) >= 7:
            rows["tel"].append(piece)
        elif "linkedin." in piece.lower():
            rows["linkedin"].append(piece)
        elif re.match(r"^(https?://)?[\w-]+(\.[\w-]+)+(/\S*)?$", piece):
            rows["web"].append(piece)
        else:
            rows["link"].append(piece)
    return [(k, v) for k in ("tel", "mail", "web", "linkedin", "link") for v in rows[k]]


def linkedin_mask() -> Optional[str]:
    """The LinkedIn [in] shape as a data: URI of the vendored file's own bytes (None when the
    file is not on this machine — the row then gets the generic link icon)."""
    p = TEMPLATE_DIR / LINKEDIN_MASK
    if not p.is_file():
        return None
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def _icon(key: str) -> str:
    return part("icon", key=key, cls=' class="big"' if key == "mono" else "", paths=part(f"glyph-{key}"))


# ----------------------------------------------------------------- the page


def age_text(lang: str, age: int) -> str:
    return AGE_TEXT[lang].format(n=age)


def _sec(key: str, heading: str, body: str) -> str:
    return part("sec", key=esc(key), heading=esc(heading), body=body) if body else ""


def _entry(content: dict, iid: str, item: dict, lang: str, extra_lines: str = "") -> str:
    lines = [part("org", attrs="", text=esc(item["org"][lang]))] if norm(item["org"][lang]) else []
    bullets: list[str] = []

    def flush() -> None:
        if bullets:
            lines.append(part("bullets", items="".join(bullets)))
            bullets.clear()

    for cid in item.get("order", {}).get(D, []):
        ch = item.get("children", {}).get(cid)
        if not ch or not ch["include"].get(D) or not norm(ch["text"][lang]):
            continue
        if ch["kind"] == "bullet":
            bullets.append(part("bullet", id=esc(cid), text=esc(ch["text"][lang])))
        else:
            flush()
            lines.append(part("org", attrs=f' data-id="{esc(cid)}"', text=esc(ch["text"][lang])))
    flush()
    return part("entry", id=esc(iid), role=esc(item["role"][lang]), date=esc(item["date"][lang]), lines="".join(lines) + extra_lines)


def main_html(content: dict, lang: str) -> str:
    d = M.design(content)
    out = []
    if d["profile"].get("include") and norm(d["profile"]["text"][lang]):
        out.append(_sec("profile", M.heading(content, "profile")[lang], part("profile", text=esc(d["profile"]["text"][lang]))))
    edu = education_section(content)
    by_id = {s["id"]: s for s in content["sections"]}
    for sid in M.main_ids(content):
        body = []
        gpa = ""
        if edu is not None and sid == edu["id"] and d["gpa"].get("include") and norm(d["gpa"]["text"][lang]):
            gpa = part("org", attrs=' data-id="design.gpa"', text=esc(d["gpa"]["text"][lang]))
        for iid in by_id[sid]["order"].get(D) or []:
            item = content["items"].get(iid)
            if not item or not item["include"].get(D):
                continue
            if item["kind"] == "entry":
                body.append(_entry(content, iid, item, lang, gpa))
                gpa = ""  # under the first entry of the education section only
            elif norm(item["text"][lang]):
                body.append(part("org", attrs=f' data-id="{esc(iid)}"', text=esc(item["text"][lang])))
        out.append(_sec(sid, M.main_heading(content, sid)[lang], "".join(body)))
    return "".join(out)


def side_html(content: dict, opts: Options, age: Optional[int], mask: Optional[str]) -> str:
    d = M.design(content)
    lang = opts.lang
    rows = []
    if age is not None:
        rows.append(part("contact-row", key="age", icon=_icon("cake"), text=esc(age_text(lang, age))))
    for kind, text in contact_parts(content["header"]["contact"].get(lang) or content["header"]["contact"].get("en", "")):
        if kind == "linkedin" and mask:
            icon = part("icon-linkedin", mask=mask)
        elif kind == "web":
            icon = _icon(opts.web_icon)
        else:
            icon = _icon("link" if kind in ("linkedin", "link") else kind)
        rows.append(part("contact-row", key=kind, icon=icon, text=esc(text)))
    out = [_sec("contact", M.heading(content, "contact")[lang], part("contact", rows="".join(rows)) if rows else "")]

    def shown(group: str) -> list[dict]:
        a = S.GROUPS[group][0]
        return [r for r in d.get(group) or [] if r.get("include") and norm(r[a][lang])]

    langs = shown("languages")
    out.append(_sec("languages", M.heading(content, "languages")[lang], part("langs", cells="".join(part("lang", id=esc(r["id"]), a=esc(r["name"][lang]), b=esc(r["level"][lang])) for r in langs)) if langs else ""))
    skills = shown("skills")
    out.append(_sec("skills", M.heading(content, "skills")[lang], part("skl", rows="".join(part("skl-row", id=esc(r["id"]), a=esc(r["label"][lang]), b=esc(r["list"][lang])) for r in skills)) if skills else ""))
    for group in ("certs", "honors"):
        a, b = S.GROUPS[group]
        rs = shown(group)
        body = "".join(part("mini-row", id=esc(r["id"]), a=esc(r[a][lang]), b=part("mini-b", text=esc(r[b][lang])) if norm(r[b][lang]) else "") for r in rs)
        out.append(_sec(group, M.heading(content, group)[lang], part("mini", rows=body) if rs else ""))
    return "".join(out)


def render(content: dict, opts: Options, *, age: Optional[int], base_href: str, photo_src: str, key: str = "") -> str:
    """The whole page for one layout, palette and language."""
    opts = opts.checked()
    lang = opts.lang
    name = content["header"]["name"]
    title = content["header"]["title"].get(D) or {}
    columns = part(
        f"columns-{opts.layout}",
        name=esc(name),
        title=part("title", text=esc(title.get(lang, ""))) if norm(title.get(lang, "")) else "",
        photo=part("photo", alt=esc(PHOTO_ALT[lang].format(name=name)), src=html.escape(photo_src, quote=True)) if photo_src else "",
        main=main_html(content, lang),
        side=side_html(content, opts, age, linkedin_mask()),
    )
    page = (TEMPLATE_DIR / "page.html").read_text(encoding="utf-8")
    return _fill(
        page,
        lang=lang,
        layout=opts.layout,
        palette=opts.palette,
        doc_title=esc(DOC_TITLE[lang].format(name=name)),
        base_href=html.escape(base_href, quote=True),
        columns=columns,
        key=esc(key),
    )
