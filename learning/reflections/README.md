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
  learning-i18n.js (strings-common.js is loaded only as plain data, for the feedback widget's
  fb* strings), their `<html>` has no `data-es-ready`, and the series bar has no EN/ES toggle. Only the hub's Reflections block is bilingual (hub strings.js:
  `refTitle`, `refIntro`, `refAll`, `refListAria`). Book and reflection titles stay English in
  both languages and are marked `lang="en"` on the hub.
- **Professor Donnell's name** lives in exactly two places per language: the hub's `refIntro`
  strings, and the all-books page (its `<title>`, `<h1>`, meta description and og tags, all in
  that one file). Cards never carry the name. If the name has to change, those are the edits.
- **The hub panel copies the theme.** learning.css's `.ref-panel` (the hub's Reflections band)
  carries COPIES of this series' paper, surface, rule, ink, muted, accent and font tokens (light,
  dark, readability), because reflections.css can't load on the hub (the offline app excludes
  it). When a value changes in reflections.css, change the copy too; the comment above
  `.ref-panel` in learning.css is the one place that documents the copy (its `--note-bg` is the
  paper color on purpose: the row hover).
- **Theme: "engineering computation pad" (decided 2026-10-15).** Every page has
  `<html data-series="reflections">`; `reflections.css` overrides learning.css's token NAMES
  under that selector and adds nothing structural. Industrial engineering's own paper and
  shop-floor vernacular: blue-grey steel paper and neutrals, graphite ink, a brass accent, steel
  blue, and ANSI safety colors (orange, green) used sparingly for emphasis; related to the main
  site's warm bronze but not the same. The values (light, dark, readability, colorblind) live
  ONLY in reflections.css, each with its meaning in a comment; the decision record with the
  numbers as fixed on 2026-10-15 is learning-plan.md → R11. Type: Archivo (headings, width axis
  at 112.5 for a slightly expanded cut), IBM Plex Serif (body), IBM Plex Mono (numbers,
  readouts, labels, legends, table figures), each with a real fallback stack. Details, kept
  restrained: surface color offset on figure panels; no decorative grid (the computation-pad
  squares were removed on 2026-10-15; the grid token now colors only the charts' own
  gridlines), with a paper-colored sheet drawn behind each plot area; tables like a time-study
  sheet (mono tabular figures, ruled rows, a heavier rule under the header); safety orange only
  where it means "attention" (the theorem box border, a flagged readout), never decoration or a
  large fill; no stencil fonts, hazard stripes or fake textures. Contrast: body text and chart
  labels at least 4.5:1 in both themes (checked on rendered colors, see the checks below).
- **Essay pieces (R5).** `reflections.css` also holds the essay components: `§n` section labels
  (`.sec`), theorem blocks (`.thm`), "from a probability course" asides (`.tie`), figures with
  controls (`.fig`, `.controls`, `.legend`, `.readout`), tables (`.tbl`), the reading list
  (`.books`), the all-books and book-page lists. Sizes are in em so About's readability setting
  scales them.
- **Chart colors and line forms (R5).** Never `--fit` / `--fix`: across Reading Your Fits those
  mean "what an ordinary fit reports" and "a corrected estimate". Reflections use the series
  tokens `--s1..--s4` (light, dark, and an Okabe–Ito set under `data-colorblind`). Lines that
  share a chart are told apart by shape, at most three forms: solid (2.2 px), dashed (10 px
  dashes, 6 px gaps, 2 px) and dotted (round 3.25 px dots every 6 px). Rule of thumb: dash
  length at least 3× the dot diameter, and dots heavier than dashes. A fourth series gets a
  second cue instead of a fourth form: hollow square markers plus direct labels in the right
  margin (§8; dropped on phones, see "Direct labels"). main.js's `plot()` takes `dash: "dashed" | "dotted"` (`true` = dashed), `dots: true`
  with `ring: true` or `marker: "square"`, and `label: "…"`; it converts screen pixels to user
  units with its own scale factor so strokes, dashes and markers keep their size on screen at
  any viewBox scale. Legend classes repeat the same geometry: `.dash`, `.dotted`, `.dot`, `.ring`,
  `.sq`.
- **Chart text at every width (2026-10-15).** main.js's `plot()` sizes each viewBox from the
  container's width at every screen size (at least 300 units; height keeps the authored 640-wide
  ratio, between 220 and 1.25× the authored height), so one user unit is one CSS pixel and chart
  text renders at 12 to 13 px on a phone, a tablet and a desktop alike. Axis titles are 13 px,
  12 px if that does not fit, and two lines at 12 px if even that is too long (the margin grows to
  match); never smaller. Each SVG remembers its authored viewBox in `data-vb` and its last plot
  options, and a debounced resize handler redraws every chart (same data, no re-simulation). A
  static diagram that is not drawn by `plot()` scrolls in its box under 520 px instead
  (`.fig[style*="overflow-x"] svg { min-width }`).
- **Direct labels.** A series with `label: "…"` gets its name in a right margin reserved for it,
  at the line's final y, nudged apart to 1.2× the label's box height (about 1.6× its font size)
  and kept inside the plot's vertical span, so it never sits on a line, a point or another label.
  When that margin would leave less than 200 px of plot (phones), the labels are dropped and the
  legend carries the names; line forms and markers stay.
- **Captions** are IBM Plex Serif at 0.875 rem, normal weight, muted; a `<b>` lead-in stays ink.
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
  file and learning-plan.md, and rerun the checks. The LICENSE must stay; `.vercelignore`
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
   you" row after the reading list, and the footer (built-with, "Found a mistake?" in a
   `<span class="fb-slot">`, the license line), with the two script tags at the end
   (`assets/strings-common.js` as plain data, then `assets/feedback.js`: the feedback widget,
   see learning/README.md → Feedback). Charts: `main.js`, colors from `--s1..--s4`, a dash or
   marker per line.
2. Companion: `<slug>.py` with `# %%` markers, then from the repo root
   `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\make-ipynb.py reflections/<book>/<slug> --check`.
3. Registry: add the entry under its book in `assets/reflections.js` (`ready: true` when it goes
   live). If the book had no page yet, create `learning/reflections/<book>/index.html` from
   `the-goal/index.html` (title, authors, year, edition, `data-book`, og tags).
4. Link preview: a CARDS entry `"<book>-<slug>"` in `workshop/tools/make-og-cards.py` with a
   `chart` function (reflections have no workshop figure), then
   `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\make-og-cards.py <book>-<slug>`;
   the page's og:image points at
   `learning/assets/og/<book>-<slug>.png`.
5. Checks: the hub-wide list in `learning/README.md`, plus: no raw `\(` or `$$` in the rendered
   text and no `.katex-error` spans; every control changes its chart or readout; the dash/marker
   cues hold in dark mode and with colorblind on (and under deuteranopia / achromatopsia
   emulation); at 375, 768 and 1280 px every chart's text renders at 12 to 13 px (CSS font-size
   × the SVG's screen scale) and no two text boxes in a chart overlap; data lines at 2 px or
   more, dashes at 10/6 and dots at 3.25 px every 6 px, and no equation scrolls sideways unless
   it has to; body, muted, chart-label and brass
   text at 4.5:1 or better on the rendered colors in both themes; `build.ps1 -StageOnly` stages
   nothing from Reflections; the page opens from disk with the math rendered.
