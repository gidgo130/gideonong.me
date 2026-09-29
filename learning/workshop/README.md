# Workshop — Reading Your Fits

Source material for the /learning decks. It lives in the repo so GitHub backs it up, but it is
**never deployed**: `.vercelignore` lists `learning/workshop/`. Visitors only load what's in
`learning/` outside this folder. The plan and status are in `learning/learning-plan.md`; how
the section works is in `learning/README.md`.

```
modules/<slug>/
  slides.qmd, custom.scss    Slide source (Quarto revealjs)
  figures/                   PNGs made by the module's Python script (tracked)
  notebook.py                marimo notebook behind the module's "Play with the code" page
tools/
  check-es.js                Checks the ES strings against EN
  export-play.py             Exports notebook.py to learning/fits/<slug>/play/ (adds noindex etc.)
  make-og-cards.py           Makes the link-preview cards in learning/assets/og/ (fonts/ it fetches is git-ignored)
.gitignore                   Keeps build output out of git (rendered slides.html, installer builds)
```

## Rebuild a module's slides

From `learning\workshop\modules\<slug>\` in PowerShell:

1. Make the figures (they land in `figures\` here):
   `python ..\..\..\fits\<slug>\<slug>.py`
2. `quarto render slides.qmd`
3. Quarto marks the embedded interactive as an image (`role="img"`), which hides its controls
   from screen readers. Remove it:
   `(Get-Content slides.html -Raw) -replace '<iframe role="img" ', '<iframe ' | Set-Content slides.html -Encoding utf8`
4. Copy it to the page folder (the tracked copy):
   `Copy-Item slides.html ..\..\..\fits\<slug>\slides.html`

The `slides.html` left here is ignored by git. Its "Try it yourself" slide is blank here,
because it loads the `index.html` next to it, which only exists in the page folder.

Quarto: install from https://quarto.org/docs/get-started/ and the Quarto extension for VS Code.

## Export a module's "Play with the code" page (marimo)

`modules/<slug>/notebook.py` is a marimo notebook: the module's Python with short markdown
cells and marimo sliders for the page's knobs. The site serves it as an editable, in-browser
notebook at `learning/fits/<slug>/play/` (Python runs through Pyodide, fetched from a CDN on
first load, so the page only works over HTTP, never from disk). Pilot: residual-plots.

Rebuild it from the repo root (the marimo Python, not `python`):

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\export-play.py residual-plots
```

One-time setup in that Python: `python -m pip install marimo uv` (marimo's export shells out
to `uv`). The script wipes `play/`, runs `marimo export html-wasm ... --mode edit --single-file`
(one `index.html`; marimo's editor loads from jsDelivr, version-pinned, like Pyodide), then
patches that fresh `index.html`, because marimo regenerates it on every export:

- `<meta name="robots" content="noindex">` (every /learning page has it while in progress;
  Phase C removes it here too: delete the NOINDEX line in the script and re-export)
- the trailing-slash fix used by every /learning page, so `…/play` lands on `…/play/`
- the page title (from `app_title` in the notebook) and description
- three settings marimo bakes in from its own defaults and ignores from any config file:
  cells run on load (`auto_instantiate`, off by default in marimo 0.25), AI panels off, theme
  follows the OS

Never edit `play/index.html` by hand; change the notebook or the script and re-export.
Check the notebook first with `python -m marimo check --fix notebook.py` and a headless run
(`$env:MPLBACKEND="Agg"; python notebook.py`). To edit it live: `python -m marimo edit notebook.py`.

Packages: only what Pyodide ships as wheels works in the browser. numpy and matplotlib are
used; scipy also works but costs a 14 MB download, so the notebook fits the exponential with
numpy alone (a plain sweep over τ; same answer as `curve_fit` to three decimals). The export is one
~80 KB `index.html`; the ~11 MB of marimo editor a visitor downloads comes from jsDelivr.

## Check the Spanish strings

From the repo root: `node learning/workshop/tools/check-es.js`. It checks every strings file:
same keys in `en` and `es`, same {placeholders}, same tag counts in *Html keys, and an `es`
phrase on every chip. It ends with "All files OK" or a problem count (exit code 1).
