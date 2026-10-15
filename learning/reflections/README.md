# /learning/reflections — the Reflections series

Dev manual for the Reflections section: Gideon's reflections on the 11 books Professor Donnell
recommends to industrial engineers, one question per reflection. Not deployed (`*.md` is in
`.vercelignore`). Hub-wide rules (noindex, unlisted, relative links, viewing settings, series bar,
link previews) are in `learning/README.md`; the decisions (R1–R10), the book table and the status
are in `learning/learning-plan.md` → Reflections. This file is the series' own rules and the
"adding a reflection" steps.

## What's here

```
learning/
  assets/reflections.js       The ONE registry: 11 books in Professor Donnell's order, each with its
                              reflections (slug, title, date, summary, ready), plus the three
                              renderers (hub block, all-books list, book-page list)
  assets/vendor/katex/        Self-hosted KaTeX 0.19.0 (katex.min.js, katex.min.css,
                              auto-render.min.js, fonts/*.woff2, LICENSE). Pinned; see "Math" below
  assets/og/reflections.png   Link-preview card for the all-books page and every book page
  assets/og/<book>-<slug>.png One card per reflection
  reflections/
    index.html                All 11 books (English), rendered from the registry
    reflections.css           The essay pieces on top of learning.css (see "Design")
    README.md                 This manual
    <book>/index.html         One book and its reflections (only for a book that has a ready one)
    <book>/<slug>/
      index.html              The reflection: static English text, math in \( \) and $$ $$
      main.js                 Its charts and readouts (slider-driven redraws only)
      <slug>.py               Companion script with "# %%" cell markers (Colab-ready)
      <slug>.ipynb            GENERATED from the .py by workshop/tools/make-ipynb.py; never edit
```

URLs: `learning/reflections/` → `learning/reflections/<book>/` → `learning/reflections/<book>/<slug>/`.
Slugs, never numbers. The hub (`learning/index.html`) shows the ready reflections newest first
and links the all-books page.

## Rules of this series

- **English only (R3).** Reflection pages, book pages and the all-books page carry their text in
  the HTML (and in main.js for redrawn readouts), not in strings files. They do not load
  learning-i18n.js or strings-common.js, their `<html>` has no `data-es-ready`, and the series
  bar has no EN/ES toggle. Only the hub's Reflections block is bilingual (hub strings.js:
  `refTitle`, `refIntro`, `refAll`, `refListAria`). Book and reflection titles stay English in
  both languages and are marked `lang="en"` on the hub.
- **Professor Donnell's name** lives in exactly two places per language: the hub's `refIntro`
  strings, and the all-books page (its `<title>`, `<h1>`, meta description and og tags, all in
  that one file). Cards never carry the name. If the name has to change, those are the edits.
- **Design (R5).** learning.css is the chrome; `reflections.css` adds the essay pieces: `§n`
  section labels (`.sec`), theorem blocks (`.thm`), "from a probability course" asides (`.tie`),
  figures with controls (`.fig`, `.controls`, `.legend`, `.readout`), tables (`.tbl`), the
  reading list (`.books`), the all-books and book-page lists. Sizes are in em so About's
  readability setting scales them.
- **Chart colors (R5).** Never `--fit` / `--fix`: across Reading Your Fits those mean "what an
  ordinary fit reports" and "a corrected estimate". Reflections use the series tokens
  `--s1..--s4` (reflections.css: light, dark, and an Okabe–Ito set under `data-colorblind`), and
  every line that shares a chart also has its own dash pattern or marker: series 1 solid, then
  `9 5`, `2 4`, `9 4 2 4` (legend classes `.d2` / `.d3` / `.d4`, generic `.dash` = `6 5`), dots
  `.dot`, a hollow ring `.ring`. main.js's `plot()` takes `dash: "<pattern>"` and `ring: true`.
- **Chart text on phones.** Charts are authored with a 640-wide viewBox. main.js's `plot()`
  keeps it at desktop, but below the 820 px one-column breakpoint it sizes the viewBox from the
  container's width (at least 300 units; height keeps the authored ratio, never under 220), so
  13-unit text renders at about 13 px on a phone instead of 6. Each SVG remembers its authored
  viewBox in `data-vb` and its last plot options, and a debounced resize handler redraws every
  chart (same data, no re-simulation). A static diagram that is not drawn by `plot()` scrolls in
  its box under 520 px instead (`.fig[style*="overflow-x"] svg { min-width }`).
- **Long equations on phones.** A one-line display equation that would scroll sideways on a
  phone gets a two-line twin: `<span class="eq-wide">$$…$$</span>` with the original TeX,
  byte-identical, and `<span class="eq-narrow">$$\begin{aligned}…\\…\end{aligned}$$</span>`
  with the same tokens split by `&` and `\\`. reflections.css shows the narrow one only under
  520 px. Do this only where the wide line really overflows at 375 px; shorter ones scroll fine.
- **Math (R6).** Self-hosted KaTeX, one exact version, loaded only by pages that have math:
  `katex.min.css` in the head, `katex.min.js` + `auto-render.min.js` at the end, then
  `renderMathInElement(main, { delimiters: [$$ display, \( \) inline], throwOnError: false,
  strict: ignore unknownSymbol })`. Exactly those two delimiter pairs: no single `$`, so a dollar
  amount in prose can never turn into math. Display math wider than the column scrolls inside
  its own box (`.katex-display`). Only the woff2 fonts ship (every current browser takes them
  first). To upgrade: download the npm tarball of the new version, verify its integrity hash
  against the registry, copy the same five parts, update the version in the page comment, this
  file, learning-plan.md and CLAUDE.md, and rerun the checks. The LICENSE must stay; `.vercelignore`
  re-includes it (`!learning/assets/vendor/katex/LICENSE`) so it deploys with the code.
- **Plumbing (R9)** is the hub's: noindex (permanent), static OG + Twitter tags, the
  trailing-slash head script, the viewing-settings head snippet, relative links only (and
  learning.js's `LF.fixFileLinks` for file:), slider-driven redraws only, simulated data with the
  model stated.
- **License line (R8).** Every page's footer: "Text, figures and code here are CC BY-SA 4.0.
  Quotations from the books remain their authors' and publishers'." Quotes stay short and cite
  edition and page.
- **Python (R10).** A reflection with code ships `<slug>.py` (percent markers, runs top to bottom)
  and its generated `<slug>.ipynb`. The "Take it with you" row after the reading list links the
  .py (download) and "Open in Colab" (the .ipynb from the public GitHub repo). No marimo `play/`
  for reflections.
- **Offline app (R7).** Reflections are excluded from the installers (`build.ps1` `$Exclude`:
  `learning/reflections/*`, `learning/assets/reflections.js`, `learning/assets/vendor/*`). The hub
  loads reflections.js only when `window.LEARN_OFFLINE` is unset, so the installed copy never
  requests it; when the file is missing the block stays hidden.
- **Registry (R4).** `learning/assets/reflections.js` is the one list. `edition` and `about` on a
  book are optional; an empty `about` renders nothing. Dates are `"YYYY-MM-DD"` and are formatted
  from their parts with `timeZone: "UTC"`, never `new Date(string)` (that is UTC midnight and shows
  the previous day in US time zones).

## Adding a reflection

1. Write it as a self-contained page in `staging/reflections/<book>/<slug>/` (gitignored), get the
   content approved, then port: `learning/reflections/<book>/<slug>/index.html` with the head block
   (copy from balanced-plant: noindex, OG tags, trailing-slash fix, viewing-settings snippet, fonts,
   learning.css, katex.min.css if there is math, reflections.css), the series bar
   (gideonong.me / Learning / Reflections / <book>), `<main class="essay">`, the "Take it with
   you" row after the reading list, and the footer (built-with, "Found a mistake?", the license
   line). Charts: `main.js`, colors from `--s1..--s4`, a dash or marker per line.
2. Companion: `<slug>.py` with `# %%` markers, then from the repo root
   `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\make-ipynb.py reflections/<book>/<slug> --check`.
3. Registry: add the entry under its book in `assets/reflections.js` (`ready: true` when it goes
   live). If the book had no page yet, create `learning/reflections/<book>/index.html` from
   `the-goal/index.html` (title, authors, year, edition, `data-book`, og tags).
4. Link preview: a CARDS entry `"<book>-<slug>"` in `workshop/tools/make-og-cards.py` with a
   `chart` function (reflections have no workshop figure), then
   `python learning/workshop/tools/make-og-cards.py <book>-<slug>`; the page's og:image points at
   `learning/assets/og/<book>-<slug>.png`.
5. Checks: the hub-wide list in `learning/README.md`, plus: no raw `\(` or `$$` in the rendered
   text and no `.katex-error` spans; every control changes its chart or readout; the dash/marker
   cues hold in dark mode and with colorblind on; at 375 px every chart's tick text renders at
   11 px or more (CSS font-size × the SVG's screen scale) and no equation scrolls sideways
   unless it has to; `build.ps1 -StageOnly` stages nothing from Reflections; the page opens
   from disk with the math rendered.
