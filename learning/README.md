# /learning — how this section works

Dev notes for the Learning section of gideonong.me. Not deployed (`*.md` is in `.vercelignore`).
The build plan, status and decisions live in `learning/learning-plan.md` (the root `plan.md` is
the main site's and only points there). The rules live in `CLAUDE.md` → **/learning**. This file
is the hub-wide manual; each series has its own:

- `learning/fits/README.md` — Reading Your Fits (modules, strings, slides, marimo, adding a module)
- `learning/reflections/README.md` — Reflections (English-only essays, KaTeX, series colors,
  adding a reflection)

## What's here

```
learning/
  index.html                  Hub: "Learning" home, the Reading Your Fits module list and the
                              Reflections block (hidden in the offline copy)
  strings.js                  Hub text (EN/ES), including the Reflections block's four strings
  learning-plan.md            Roadmap, status, decisions (dev-only, not deployed)
  README.md                   This manual (dev-only, not deployed)
  assets/
    learning.css              Shared look for every /learning page (the "lab notebook" style)
    learning.js               LF: seeded random numbers, fits (OLS, Deming), SVG charts,
                              number formatting, series nav, hub list, offline link fix
    learning-i18n.js          LI18N: EN/ES strings, shared "lang" key, hidden toggle, dev check
    strings-common.js         Text shared by the module pages (series name, module titles, nav words)
    modules.js                The ONE module registry (Reading Your Fits): order, slug, ready flag
    reflections.js            The ONE book/reflection registry (Reflections) + its renderers
    vendor/katex/             Self-hosted KaTeX, one pinned version, with its LICENSE (Reflections)
    og/                       Link-preview cards, 1200×630 PNG: learning.png (hub), <slug>.png per
                              module, reflections.png and <book>-<slug>.png for Reflections.
                              Made by learning/workshop/tools/make-og-cards.py; never edit by hand
  fits/<slug>/                One Reading Your Fits module (see fits/README.md)
  reflections/                The Reflections series (see reflections/README.md)
  workshop/                   Slide sources, figures, dev tools, the offline installer build
                              (tracked, never deployed: .vercelignore)
```

Pages are plain HTML/CSS/JS with relative links, so they work on the site, on a Vercel
preview and opened straight from disk (the offline Windows app, which ships Reading Your Fits
only).

## The hub is a hub of sections

`learning/index.html` is the Learning home. Each series sets its own language and design
extensions; the hub-wide rules below apply to all of them. The Reading Your Fits block renders
from `assets/modules.js` through `LF.moduleList`; the Reflections block renders from
`assets/reflections.js`, which the hub loads only when `window.LEARN_OFFLINE` is unset (the
installed copy never asks for it) and whose block stays hidden until the file has loaded.

## Hub-wide rules

- **Unlisted, and it stays that way.** Every page carries `<meta name="robots" content="noindex">`
  (slides get it through `include-in-header` in `slides.qmd`), and that is permanent (Phase C,
  2026-09-28): /learning is found by link (shared cards), not by search. Don't remove it.
- **No link from the site (since 2026-09-29).** The About page's "Interesting sites" list
  (js/about-data.js, ABOUT_SITES) was unhidden with a different entry in place of the Learning
  one. /learning is reached by URL and by its shared link-preview cards. A Learning entry can
  be added back there through the editor (Content › About).
- **Link previews are static.** Every page and deck carries Open Graph + Twitter-card meta
  (`og:title` / `og:description` = the EN page title and lead, absolute `og:url` with a trailing
  slash, `og:image` = a 1200×630 card in `learning/assets/og/`). Scrapers don't run JS, so the
  tags live in the HTML. If a title or lead changes, update the tags and re-run
  `python learning/workshop/tools/make-og-cards.py <name>` (its CARDS table holds the card text
  and either a figure crop or a `chart` function). noindex and OG are independent: a shared link
  previews fine while the page stays out of search.
- **Relative links only.** Each page's head script adds the trailing slash to folder URLs
  (`/learning` → `/learning/`); `LF.fixFileLinks` points folder links at index.html when the page
  is opened from disk. Anything that needs a server or a CDN gets `data-http-only` on its link.
- **Viewing settings** follow the main site's saved choices through the head snippet on every
  page: `viewTheme` (theme; else the OS setting), `viewReadability` (bigger, looser text; charts
  unchanged) and `viewColorblind`. Styled in learning.css → "Viewing settings"; a series'
  own stylesheet adds its own tokens under the same attributes. No switches on /learning:
  change them on About.
- **The series bar** (gideonong.me / Learning / <series> / …) tops every page, in learning.css.
  The EN/ES toggle sits in it only on bilingual pages (Reading Your Fits).
- **No page-load or scroll animation.** Slider-driven redraws only.
- **Simulated data only**, with the true model stated on the page.
- **Cited papers and books** are linked (DOI, publisher, catalog page), never hosted.
- **External resources:** Google Fonts, and nothing else. Libraries are self-hosted and pinned
  (KaTeX under `assets/vendor/`).
- **One base, a theme per series (2026-10-15).** learning.css is the shared base: series bar,
  layout, spacing, footer, viewing settings and the token NAMES every component uses (`--paper`,
  `--plot`, `--grid`, `--rule`, `--ink`, `--muted`, `--pt`, `--note-bg`, `--accent`, `--emph`,
  `--font-display` / `-body` / `-mono`, plus the chart tokens). Each series sets
  `data-series="fits" | "reflections"` on `<html>` and overrides only tokens in its own CSS.
  Non-chart UI (links, focus rings, status pills, flagged readouts, slider thumbs) uses
  `--accent` / `--emph`, never `--fit` / `--fix` directly.
- **The hub is a main-site frame with one band per series (2026-10-16).** learning/index.html
  (`body.hub`, no `data-series`): the series bar, header and footer are `.hub-frame` in the main
  site's design (Palette B and its §6 dark palette, Lora + DM Sans, sentence-case eyebrow, white
  bar, dark footer), with token values COPIED from css/style.css because the offline copy
  doesn't ship it: keep in step. Each series is a full-bleed `.hub-band` (1px rule along the
  top edge, 4.5rem padding) whose content sits in `.hub-col`, the frame's centered column. The
  Reading Your Fits band sets no tokens and inherits the base lab look; the Reflections band
  is the `.ref-panel` (tokens copied from reflections.css). A new series gets its own band the
  same way. `.hub [hidden]` forces `display: none`, because bands set their own display.
- **Dashed and dotted lines stay readable.** On every chart, at the rendered size: data lines
  2 px or more; dashes 10 px with 6 px gaps; dots as round-capped zero-length dashes, 3.25 px,
  every 6 px (dash length ≥ 3× the dot diameter, dots heavier than dashes); at most three forms
  per chart (solid, dashed, dotted), a fourth series gets markers or a direct label instead;
  legends repeat the chart's geometry. The geometry is computed from the current scale (the
  `--k` variable in Reading Your Fits, `plot()`'s own factor in Reflections), not left to the
  viewBox. Out of scope: the Quarto decks and the Python figures (open item in learning-plan.md).

## Checks before pushing

- Serve the repo root (`python -m http.server` or Live Server) and open `/learning`,
  `/learning/reflections` and a module or reflection URL **without** the trailing slash: each
  should land on the slashed URL.
- Each page at 375, 768 and 1280 px, light and dark, plus readability on, colorblind on, and
  both: no sideways scroll (wide math and figures scroll in their own containers), console clean.
- Every chart at 375 px: data strokes ≥ 2 px, dashes ≥ 6 px with gaps ≥ 4 px, dots ≥ 3 px every
  ≥ 5 px, measured as CSS value × the SVG's screen scale; in grayscale, dashed and dotted lines
  differ by ≥ 2.5× in run length. Chromium and Firefox (Playwright's build, in the scratchpad).
- Open `learning/index.html` straight from disk: module, book and reflection links and the back
  links still work; the math renders (KaTeX is local).
- `node learning/workshop/tools/check-es.js` passes (hub and module strings).
- `build.ps1 -StageOnly` stages nothing from Reflections or `assets/vendor/`.
- On the Vercel preview: repeat the no-slash checks, and view source for `noindex`.
- Then the series' own checks (fits/README.md, reflections/README.md).

## Fable review prompt (Claude Code, in this repo)

Paste this into Claude Code with the Fable model, on the branch you're about to merge:

```
Review the /learning section of this repo before I merge. First read CLAUDE.md (the
"/learning" section and the main-site rules it overrides), learning/learning-plan.md (plan,
status, decisions), learning/README.md (hub-wide structure and conventions) and the series
manuals learning/fits/README.md and learning/reflections/README.md. The root plan.md is the
main site's roadmap; it should contain only a short pointer section about /learning.

Then check, and report findings ranked by severity with file and line:

1. Statistics and math: every claim, formula and number on each module page, its slides and
   its Python script, and on each reflection page and its script, is correct and consistent
   (e.g. attenuation factor σx²/(σx²+σu²), Deming slope, t critical values, confidence-interval
   coverage; for the reflections, the queueing results and the exact Markov-chain numbers).
   Flag anything misleading for a student with no statistics background.
2. Code: run the pages mentally or in a browser; look for JS errors, controls that don't
   update, edge cases at slider extremes (zero noise, max noise, utilization near 1), the
   offline (file:) link fix, and KaTeX error spans or raw delimiters on reflection pages.
3. Scope: outside learning/, only js/about-data.js (an Interesting-sites "Learning" entry, when
   one exists), CLAUDE.md (the /learning section and file-structure lines), plan.md (the
   pointer section), README.md (the Learning and licensing lines) and .vercelignore (the
   KaTeX LICENSE re-include) changed. Nothing else outside learning/ changed.
4. Rules: the /learning rules in CLAUDE.md are followed (noindex, unlisted, own design, fixed
   fit colors in Reading Your Fits and the series tokens in Reflections, relative links,
   simulated data, English-only Reflections with the hub block bilingual).
5. i18n readiness (Reading Your Fits): no hard-coded display text outside strings files; every
   data-i18n key exists; numbers go through LF.num; the EN/ES toggle stays hidden until
   data-es-ready.
6. Accessibility and layout: labels on every control, aria-labels on charts, visible focus,
   no horizontal scroll at 375 px, both themes readable, every line in a shared chart told
   apart by dash or marker as well as color.
7. Deploy: noindex present on every /learning page including slides.html; relative links
   work with and without the trailing slash; nothing in learning/ that shouldn't be public
   (*.md files are excluded by .vercelignore); Reflections and assets/vendor/ excluded from the
   offline installers.

Don't change files; list what you'd change and why.
```
