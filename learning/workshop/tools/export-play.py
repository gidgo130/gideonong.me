"""export-play.py — export a module's marimo notebook as its "Play with the code" page.

    python learning/workshop/tools/export-play.py <slug>

Reads   learning/workshop/modules/<slug>/notebook.py
Writes  learning/fits/<slug>/play/index.html   (ONE file, --single-file: marimo's editor is
        loaded from jsDelivr, version-pinned, like Pyodide; the folder is wiped first)

marimo regenerates index.html on every export, so the tweaks the site needs are applied
here, after the export, not by hand:
  * <meta name="robots" content="noindex">  (every /learning page has it while in progress)
  * the trailing-slash fix used by every /learning page (…/play → …/play/), so its URL
    matches the rest of /learning
  * the page title and description
  * three baked-in marimo settings: cells run on load, AI panels off, theme follows the OS

Needs marimo and uv in the same Python (python -m pip install marimo uv). On this machine
that Python is  %LOCALAPPDATA%\\Python\\pythoncore-3.14-64\\python.exe  (not `python`).
The page runs Python in the browser through Pyodide, which is fetched from a CDN on first
load; it only works over HTTP, never from file:.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # tools → workshop → learning → repo
NOINDEX = (
    '    <!-- /learning is unlisted while in progress: remove this line to let search engines index the page. -->\n'
    '    <meta name="robots" content="noindex">\n'
)
SLASH_FIX = (
    '    <script>\n'
    '      /* Relative links need a trailing slash on folder URLs (…/play/). Add it if missing. */\n'
    '      (function () {\n'
    '        var p = location.pathname;\n'
    '        if (/^https?:$/.test(location.protocol) && !/\\/$/.test(p) && !/\\.[a-z0-9]+$/i.test(p)) {\n'
    '          location.replace(p + "/" + location.search + location.hash);\n'
    '        }\n'
    '      })();\n'
    '    </script>\n'
)


def main(slug: str) -> int:
    notebook = ROOT / "learning" / "workshop" / "modules" / slug / "notebook.py"
    out = ROOT / "learning" / "fits" / slug / "play"
    if not notebook.is_file():
        print(f"No notebook at {notebook}")
        return 1
    if not (ROOT / "learning" / "fits" / slug / "index.html").is_file():
        print(f"No module page at learning/fits/{slug}/ — make the module first")
        return 1

    title = re.search(r'app_title="([^"]+)"', notebook.read_text(encoding="utf-8"))
    title = title.group(1) if title else f"{slug} · play with the code"

    if out.exists():
        shutil.rmtree(out)          # also clears the 480-file assets/ of a pre-single-file export
    out.mkdir()
    page = out / "index.html"

    # marimo shells out to `uv`; make sure the one next to this interpreter is found.
    env = dict(os.environ)
    scripts = Path(sys.executable).parent / ("Scripts" if os.name == "nt" else "")
    env["PATH"] = str(scripts) + os.pathsep + env.get("PATH", "")
    cmd = [sys.executable, "-m", "marimo", "export", "html-wasm", str(notebook),
           "-o", str(page), "--mode", "edit", "--single-file", "--force"]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, env=env)

    html = page.read_text(encoding="utf-8")
    if "cdn.jsdelivr.net/npm/@marimo-team/frontend@" not in html:
        raise SystemExit("expected the editor assets to come from jsDelivr; did --single-file change?")
    if "robots" in html:
        raise SystemExit("index.html already has a robots tag; check the export")
    html, n = re.subn(r'(\s*<meta charset="utf-8" />\n)', lambda m: m.group(1) + NOINDEX + SLASH_FIX, html, count=1)
    if n != 1:
        raise SystemExit("could not find <meta charset> in index.html; marimo's template changed")
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1)
    html = html.replace('<meta name="description" content="a marimo app" />',
                        '<meta name="description" content="The module\'s Python, editable and runnable in the browser (marimo + Pyodide)." />')
    # marimo's WASM export bakes its own defaults into __MARIMO_MOUNT_CONFIG__ and ignores the
    # user/project config except for `display`. Three of those defaults are wrong for a public
    # teaching page, so fix them in the baked JSON (each one must be found exactly once).
    for old, new in (
        ('"auto_instantiate": false', '"auto_instantiate": true'),   # run every cell on load (0.25 default: off)
        ('"ai": {"allow_provider_config": true, "custom_providers": {}, "enabled": true',
         '"ai": {"allow_provider_config": false, "custom_providers": {}, "enabled": false'),  # no AI panels
        ('"theme": "light"', '"theme": "system"'),                    # follow the OS, like a phone expects
    ):
        if html.count(old) != 1:
            raise SystemExit(f"expected exactly one {old!r} in index.html; marimo's config layout changed")
        html = html.replace(old, new)
    page.write_text(html, encoding="utf-8", newline="\n")

    stray = [p.name for p in out.iterdir() if p != page]
    if stray:
        raise SystemExit(f"the export left extra files next to index.html: {stray}")
    # ASCII only: the Windows console may be cp1252.
    print(f"\nWrote {page.relative_to(ROOT)}: {page.stat().st_size / 1e3:.0f} KB, one file (noindex added)")
    print(f"Check it over HTTP, e.g. Live Server: /learning/fits/{slug}/play/")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
