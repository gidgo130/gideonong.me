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

`<book>` is the book's registry slug and `<slug>` the reflection's: lowercase, hyphenated, never a
number. Write the reflection first as a self-contained page in the gitignored
`staging/reflections/<book>/<slug>/` (recreate the folder if it is gone), get the content approved,
then port it. Porting changes styling and plumbing only, never wording, equations or numbers. The
reference for every copy below is `the-goal/balanced-plant/` (page, main.js, script) and
`the-goal/index.html` (book page).

1. **The page** `learning/reflections/<book>/<slug>/index.html`, copied from
   `the-goal/balanced-plant/index.html` and edited top to bottom:
   - `<html lang="en" data-series="reflections">`; the noindex meta stays; `<title>` =
     "<Title> · Reflections · Gideon A. Ong"; `<meta name="description">` = the summary.
   - The OG block: og:title "<Title> · Reflections", og:description = the same summary, og:url
     `https://gideonong.me/learning/reflections/<book>/<slug>/`, og:image
     `https://gideonong.me/learning/assets/og/<book>-<slug>.png`, og:image:alt describing the card.
   - Keep as they are: the favicon link, the trailing-slash script (change the slug in its
     comment), the viewing-settings snippet, the font preconnects and the Reflections Google Fonts
     link, `../../../assets/learning.css`, then `../../reflections.css`; add
     `../../../assets/vendor/katex/katex.min.css` between them only if the page has math.
   - The series bar: gideonong.me (`../../../../`) / Learning (`../../../`) / Reflections
     (`../../`) / <Book title> (`../`).
   - `<div class="wrap essay-wrap"><main class="essay">`: `<header class="top">` with the `.sec`
     eyebrow ("Reflections · <i>Book</i>, Authors (year)"), the h1 and the `.dek`; the `.answer`
     box; `nav.toc`; then the sections as `<h2 id="sN"><span class="sec">§N</span>Heading</h2>` (the
     ids are what the feedback widget reports as the section). Math in `\( \)` and `$$ $$` only;
     a display equation that overflows at 375 px gets the `.eq-wide` / `.eq-narrow` twins (see
     "Long equations on phones"). Every chart `<svg>` carries `role="img"` and an `aria-label`.
   - The reading list (`ol.books`, papers linked by DOI), then the "Take it with you" row:
     `<a href="<slug>.py" download>Python script</a>` and the Colab link
     `https://colab.research.google.com/github/gidgo130/gideonong.me/blob/main/learning/reflections/<book>/<slug>/<slug>.ipynb`
     (`target="_blank" rel="noopener"`).
   - The footer `p.foot`: the built-with line, `<span class="fb-slot">Found a mistake?
     gao9819@utulsa.edu</span>` (the feedback widget replaces it with its button) and the license
     line (R8).
   - Scripts, in this order: if there is math, `../../../assets/vendor/katex/katex.min.js`,
     `../../../assets/vendor/katex/auto-render.min.js` and the inline `renderMathInElement(...)`
     call with exactly the two delimiter pairs (copy it); then `../../../assets/learning.js`,
     `main.js`, `../../../assets/strings-common.js` and `../../../assets/feedback.js` last.
2. **Charts and readouts** `main.js`: start from balanced-plant's `plot()` helper. Colors from
   `--s1..--s4` only; each line told apart by `dash: "dashed" | "dotted"` or a marker; a fourth
   series gets `label:`; every SVG keeps its authored viewBox in `data-vb`; every control redraws
   on input and nothing animates on load. Readouts need no live region of their own: learning.js
   adds a debounced, visually hidden live mirror beside every `.readout`. Headings keep a space
   after the `§N` label (`<span class="sec">§N</span> Heading`) so the accessible name does not
   read as one word; table header cells carry `scope`; the Colab link has
   `aria-describedby="new-tab-note"` and the page a `<span id="new-tab-note" hidden>Opens in a new
   tab</span>` after the "Take it with you" row.
3. **Companion** `<slug>.py` with `# %%` cell markers (module docstring first, written as
   markdown; markdown cells as `# text`; a knobs cell per figure), then from the repo root
   `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\make-ipynb.py reflections/<book>/<slug> --check`,
   which writes `<slug>.ipynb` beside it and fails if the notebook's cells print anything
   different from the script. Never edit the .ipynb. A reflection with no code skips this step
   and the "Take it with you" row.
4. **Registry** `learning/assets/reflections.js`: in the book's entry add
   `{ slug: "<slug>", title: "<Title>", date: "YYYY-MM-DD", ready: true, summary: "…" }`
   (`ready: false` while drafting: it is then listed nowhere). The hub's Reflections block (the 3
   newest by date), the all-books page (its count and link) and the book page all render from this
   one entry; nothing else lists reflections.
5. **Book page, only for a book's first reflection**: `learning/reflections/<book>/index.html`
   copied from `the-goal/index.html` and edited: `<title>` and og:title ("<Book> · Reflections…"),
   meta description and og:description ("Reflections on <Book> by <Authors> (<year>), one question
   at a time."), og:url `https://gideonong.me/learning/reflections/<book>/` (og:image stays
   `reflections.png`), the trailing-slash comment's slug, `<body data-book="<book>">` (must equal
   the registry slug: `bookPage` looks the book up by it), the crumb text, the eyebrow "Reflections
   · Book N of 11" (N = the book's position in the registry, typed by hand), the h1 (full title),
   the lead ("Authors, year. The copy I read: <edition>.") and the list's
   `aria-label="Reflections on <Book>"`. The rest is shared markup and stays.
6. **Link preview**: a CARDS entry `"<book>-<slug>"` in `learning/workshop/tools/make-og-cards.py`
   (`eyebrow` "Reflections · <Book>", `title`, `lead` = the summary, and `chart` naming a new
   function in that file that draws a small figure in the S1..S4 colors: reflections have no
   workshop figure), then
   `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\make-og-cards.py <book>-<slug>`
   (Pillow and matplotlib in that Python; on first run it fetches its fonts into the gitignored
   `learning/workshop/tools/fonts/`). It writes `learning/assets/og/<book>-<slug>.png`, the file
   og:image already names.
7. **Plan**: `learning/learning-plan.md` → Reflections: the book's row in the table and a status
   line. Nothing changes in CLAUDE.md, the hub's markup or strings, api/feedback.js (the series is
   already allowed), check-es.js (English only) or the offline build (the whole series is in
   `$Exclude`).
8. **Checks**: the hub-wide list in `learning/README.md` → Checks (the no-slash redirect for the new
   URL; 375 / 768 / 1280 × light / dark × readability / colorblind with no sideways scroll and a
   clean console; opened from disk with the math rendered; `check-es.js`; the feedback tests;
   `build.ps1 -StageOnly` staging nothing from Reflections), plus: no raw `\(` or `$$` in the
   rendered text and no `.katex-error` spans; every control changes its chart or readout; the
   dash / marker cues hold in dark mode and with colorblind on (and under deuteranopia /
   achromatopsia emulation); at 375, 768 and 1280 px every chart's text renders at 12 to 13 px
   and no two text boxes overlap; data lines ≥ 2 px, dashes 10/6, dots 3.25 px every 6 px; no
   equation scrolls sideways unless it has to; body, muted, chart-label and brass text ≥ 4.5:1 on
   the rendered colors in both themes; the new reflection shows on the hub, the all-books page
   and the book page with the right date (America/Chicago included); the DOIs resolve; after the
   push, the Colab link opens the notebook (the repo is public). Then the Fable review (prompt in
   learning/README.md).

**A twelfth book** is not a reflection: "11" is typed in `learning/strings.js` (refIntro, refAll,
EN and ES), `learning/reflections/index.html` (title, description, og tags, h1, the intro, the
all-books link text), every book page's eyebrow ("Book N of 11") and `ref-all` link, the
`"reflections"` card lead in make-og-cards.py, and the book table in learning-plan.md. Change all
of them together, then re-run the card.
