# Workshop — Reading Your Fits

Source material for the /learning decks. It lives in the repo so GitHub backs it up, but it is
**never deployed**: `.vercelignore` lists `learning/workshop/`. Visitors only load what's in
`learning/` outside this folder. The plan and status are in `learning/learning-plan.md`; how
the section works is in `learning/README.md`.

```
modules/<slug>/
  slides.qmd, custom.scss    Slide source (Quarto revealjs)
  slides.es.qmd              The Spanish deck (same YAML plus lang: es; uses figures-es/)
  figures/                   PNGs made by the module's Python script (tracked)
  figures-es/                The same PNGs with Spanish text (tracked; made by tools/figures-es.py)
  figures-es.json            EN → ES table for every piece of text in the module's figures
  notebook.py                marimo notebook behind the module's "Play with the code" page
tools/
  check-es.js                Checks the ES strings against EN
  figures-es.py              Makes figures-es/ from the unchanged public script (see below)
  export-play.py             Exports notebook.py to learning/fits/<slug>/play/ (adds noindex etc.)
  make-ipynb.py              Turns learning/fits/<slug>/<slug>.py into the Colab notebook <slug>.ipynb
  make-og-cards.py           Makes the link-preview cards in learning/assets/og/ (fonts/ it fetches is git-ignored)
.gitignore                   Keeps build output out of git (rendered slides.html, installer builds)
```

## Rebuild a module's slides

From `learning\workshop\modules\<slug>\` in PowerShell:

1. Make the figures (they land in `figures\` here):
   `python ..\..\..\fits\<slug>\<slug>.py`
2. `quarto render slides.qmd`
3. Quarto marks the embedded interactive as an image (`role="img"`), which hides its controls
   from screen readers. Remove it and copy the deck to the page folder (the tracked copy) in one
   step. This writes UTF-8 without a byte-order mark; `Set-Content -Encoding utf8` in Windows
   PowerShell 5.1 would add one:
   `$h = [IO.File]::ReadAllText("$PWD\slides.html") -replace '<iframe role="img" ', '<iframe '; [IO.File]::WriteAllText("$PWD\..\..\..\fits\<slug>\slides.html", $h, (New-Object Text.UTF8Encoding $false))`

The `slides.html` left here is ignored by git. Its "Try it yourself" slide is blank here,
because it loads the `index.html` next to it, which only exists in the page folder. Quarto
warns "Could not fetch resource index.html" for the same reason; that warning is expected.

Quarto: 1.10.18 on Gideon's machine (winget `Posit.Quarto`; every deck was re-rendered with it
on 2026-09-29, pixel-identical to the 1.7.32 renders). Optional: the Quarto extension for VS Code.

## Rebuild a module's Spanish deck

Same steps, with two differences: the figures come from `tools/figures-es.py`, and the deck is
`slides.es.qmd` → `slides.es.html`.

1. Make the Spanish figures (from the repo root; they land in `modules\<slug>\figures-es\`):
   `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\figures-es.py <slug>`
2. From `learning\workshop\modules\<slug>\`: `quarto render slides.es.qmd`
3. Step 3 above with `slides.es.html` in both places.

`figures-es.py` runs the module's public script (`learning/fits/<slug>/<slug>.py`) unchanged,
so the data and seeds match the English figures exactly and the script stays English. It
translates every piece of text matplotlib draws (titles, axis labels, legends, notes, ticks)
through `figures-es.json` and turns decimal points into commas. The table's keys are the
English text with each number written as `#` (`"without it: #"` → `"sin él: #"`); the numbers
come back in the same order. Text that is only numbers, symbols or one letter needs no entry.
The Spanish goes in before `tight_layout` and before saving, so the layout fits the Spanish.

- `figures-es.py <slug> --list` prints every key the script draws, as a JSON skeleton for a new
  module's table (it writes nothing).
- A run fails (exit 1) and lists the text if any key is missing from the table, and warns about
  table entries the script never drew, so no English slips into a Spanish figure.
- When the script's figure text changes, re-run it: the missing keys show up there.
- Look at the result: Spanish runs longer, so a title or note can hit the edge or another mark.
  Shorten the Spanish in the table; never change the public script for it.

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

## Build a module's Colab notebook

Each module page has an "Open in Colab" link. It opens `learning/fits/<slug>/<slug>.ipynb`
straight from GitHub (so the repo must be public), and that file is GENERATED from the
module's companion script by:

```powershell
& "$env:LOCALAPPDATAPythonpythoncore-3.14-64python.exe" learningworkshop	oolsmake-ipynb.py all --check
```

The script `<slug>.py` stays an ordinary Python file that runs top to bottom (the slide
figures still come from running it). Its cells are marked with comments in the "percent"
format: `# %% [markdown]` starts a markdown cell (every line after it is `# text`, a bare
`#` for a blank line) and `# %%` starts a code cell (an optional title may follow). The
module docstring becomes the first markdown cell, so it is written as markdown (its first
line is the `# Title`). Each trial has a "knobs" cell: UPPER_CASE variables with the page's
range in a comment, then the call, so a student changes a number and reruns that cell.

`--check` runs the notebook's code cells as one script and the original script, both
headless in temp folders, and fails if their printed output differs; it also validates the
JSON against the nbformat schema when that package is installed. Re-running the tool on an
unchanged script produces no diff (deterministic cell ids). Never edit an `.ipynb` by hand.

## Check the Spanish strings

From the repo root: `node learning/workshop/tools/check-es.js`. It checks every strings file:
same keys in `en` and `es`, same {placeholders}, same tag counts in *Html keys, and an `es`
phrase on every chip. It ends with "All files OK" or a problem count (exit code 1).
