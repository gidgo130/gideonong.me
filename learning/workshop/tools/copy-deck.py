"""copy-deck.py — copy a rendered Quarto deck into its module folder with the site's two fixes.

    $py learning/workshop/tools/copy-deck.py <slug>            slides.html
    $py learning/workshop/tools/copy-deck.py <slug> --es       slides.es.html
    $py learning/workshop/tools/copy-deck.py <slug> --in-place re-apply the fixes to the tracked copy
    $py learning/workshop/tools/copy-deck.py all --in-place    every ready module, both decks

Source: learning/workshop/modules/<slug>/slides[.es].html (Quarto's render, gitignored), or with
--in-place the tracked copy learning/fits/<slug>/slides[.es].html itself (idempotent).
Fixes, in order:
  1. drop role="img" from the embedded "Try it yourself" iframe (Quarto adds it, which hides the
     interactive's controls from screen readers);
  2. move <meta charset="utf-8"> and the include-in-header block (noindex, Open Graph, Twitter) to
     the top of <head>. Quarto appends that block after its embedded CSS, about 3.6 MB into the
     file, where link-preview scrapers that read only the first kilobytes never see it.
Writes UTF-8 without a byte-order mark and keeps the source's line endings (the renders are CRLF).
Dev-only; `$py` is %LOCALAPPDATA%\\Python\\pythoncore-3.14-64\\python.exe on this machine.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BLOCK = re.compile(r'(?:[ \t]*<meta name="robots" content="noindex">\r?\n)(?:[ \t]*<meta (?:property|name)="(?:og:|twitter:)[^"]*" content="[^"]*">\r?\n)+')
CHARSET = re.compile(r'[ \t]*<meta charset="utf-8">\r?\n')


def fix(text: str) -> str:
    nl = "\r\n" if "\r\n" in text else "\n"
    text = text.replace('<iframe role="img" ', "<iframe ")
    blocks = BLOCK.findall(text)
    if len(blocks) != 1:
        raise SystemExit(f"expected exactly one noindex + OG block, found {len(blocks)}")
    block = blocks[0]
    text = text.replace(block, "", 1)
    charsets = CHARSET.findall(text)
    if not charsets:
        raise SystemExit("no <meta charset=\"utf-8\"> line")
    text = text.replace(charsets[0], "", 1)
    head = text.find("<head>")
    if head < 0 or head > 500:          # the document's own <head>; Quarto's templates hold more, later
        raise SystemExit("no <head> near the top of the document")
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    top = "<head>" + nl + '<meta charset="utf-8">' + nl + nl.join(lines) + nl
    return text[:head] + top + text[head + len("<head>"):]


def one(slug: str, es: bool, in_place: bool) -> None:
    name = "slides.es.html" if es else "slides.html"
    dest = ROOT / "learning" / "fits" / slug / name
    src = dest if in_place else ROOT / "learning" / "workshop" / "modules" / slug / name
    if not src.is_file():
        raise SystemExit(f"no deck at {src}")
    text = src.read_bytes().decode("utf-8-sig")
    out = fix(text)
    dest.write_bytes(out.encode("utf-8"))
    pos = out.find('<meta name="robots"')
    print(f"{dest.relative_to(ROOT)}: noindex + OG at byte {pos}, {len(out.encode('utf-8')) // 1024} KB")


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    es, in_place = "--es" in argv, "--in-place" in argv
    if args[0] == "all":
        import json, re as _re
        mods = _re.findall(r'slug:\s*"([a-z0-9-]+)",\s*ready:\s*true', (ROOT / "learning/assets/modules.js").read_text(encoding="utf-8"))
        for slug in mods:
            for flag in (False, True):
                one(slug, flag, True)
        return 0
    one(args[0], es, in_place)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
