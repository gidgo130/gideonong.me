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
    feedback.js               The feedback widget: footer button, "Comment on this", the panel,
                              owner mode, dry-run (see "Feedback" below)
    view-settings.js          The "View" button and popover in every series bar (theme, colorblind
                              charts, easier reading; the same keys as About) and the colorblind
                              hint under the first chart legend
    vendor/katex/             Self-hosted KaTeX, one pinned version, with its LICENSE (Reflections)
    og/                       Link-preview cards, 1200×630 PNG: learning.png (hub), <slug>.png per
                              module, reflections.png and <book>-<slug>.png for Reflections.
                              Made by learning/workshop/tools/make-og-cards.py; never edit by hand
  fits/<slug>/                One Reading Your Fits module (see fits/README.md)
  reflections/                The Reflections series (see reflections/README.md)
  workshop/                   Slide sources, figures, dev tools, the offline installer build
                              (tracked, never deployed: .vercelignore)
  workshop/tests/             The browser suites (Playwright, installed outside the repo): run.js,
                              lib.js, one file per suite, README.md with the install and the command
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
  `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\make-og-cards.py <name>`
  (its CARDS table holds the card text and either a figure crop or a `chart` function: learning.png
  for the hub, `<slug>.png` per module, reflections.png for the all-books and book pages,
  `<book>-<slug>.png` per reflection; every deck reuses its module's card). noindex and OG are
  independent: a shared link previews fine while the page stays out of search. One exception
  (2026-10-15): the hub's meta description and og:description read "Interactive notes and essays
  built with Claude, mostly for engineering students. Each series has its own format." while the
  on-page lead keeps "I [told Claude to] build"; the bracket stays out of the card.
- **Relative links only.** Each page's head script adds the trailing slash to folder URLs
  (`/learning` → `/learning/`); `LF.fixFileLinks` points folder links at index.html when the page
  is opened from disk. Anything that needs a server or a CDN gets `data-http-only` on its link.
- **Viewing settings** follow the main site's saved choices through the head snippet on every
  page: `viewTheme` (theme; else the OS setting), `viewReadability` (bigger, looser text; charts
  unchanged) and `viewColorblind`. Styled in learning.css → "Viewing settings"; a series'
  own stylesheet adds its own tokens under the same attributes. Since 2026-10-17 every series
  bar also has a **View** button (`assets/view-settings.js`, loaded before feedback.js on every
  page): the EN/ES toggle's sibling (same box and font, so it takes each bar's styling), opening a
  small popover with the theme (System / Light / Dark as `aria-pressed` buttons), "Colorblind-
  friendly charts", "Easier reading" and one note that the choice is saved in this browser and
  shared with the rest of gideonong.me. It writes the SAME keys About writes (`viewTheme`
  dark/light or removed, `viewReadability` "1" or removed, `viewColorblind` "1" or "0"), applies
  them at once, closes on Esc with focus back on the button, and works from file: and in the
  offline copy. "0" means turned off on purpose (About writes it too since 2026-10-17):
  `prefers-contrast: more` (head snippet and the script) turns the colorblind cues on only while
  the key is absent. On pages with charts the
  script adds one muted line under the first legend ("Hard to tell the colors apart? Turn on
  colorblind-friendly charts" / "Colorblind-friendly charts are on · Turn off") that toggles the
  mode in place. Under forced colors (Windows High Contrast) charts, legend swatches and the
  Reflections plot sheet keep their own colors (`forced-color-adjust: none`), so no line or point
  vanishes. Strings: `view*`, `cbHint*`, `cbTurn*`, `skipLink` in strings-common.js.
- **Skip link and main landmark.** Every page starts with `<a class="skip-link" href="#main">`
  (visually hidden until focused, the first tab stop; `data-i18n="skipLink"` on bilingual pages)
  and wraps its content in `<main id="main">` (the hub: header and bands; modules and book
  pages: header and sections, not the series nav or footer; the essay: `main.essay`).
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
  bar, dark footer). Each series is a full-bleed `.hub-band` (1px rule along the top edge,
  4.5rem padding) whose content sits in `.hub-col`, the frame's centered column. The Reading
  Your Fits band sets no tokens and inherits the base lab look; the Reflections band is the
  `.ref-panel`. The frame's and the panel's token values are COPIES (of css/style.css and of
  reflections.css: the offline copy ships neither); the comments beside those two blocks in
  learning.css say what to keep in step, and that is the only place the copies are documented.
  The hub renders the Reading Your Fits block from assets/modules.js (LF.moduleList) and the
  Reflections block from assets/reflections.js, which it loads only when `window.LEARN_OFFLINE`
  is unset and keeps hidden until the file has loaded; the band's three faces are requested by
  the hub script only when the band is shown. A new series gets its own band the same way.
  `.hub [hidden]` forces `display: none`, because bands set their own display. The hub's bar is
  STICKY (2026-10-16; hub only, module and Reflections pages keep a static bar): `position:
  sticky; top: env(safe-area-inset-top, 0px)`, always opaque (`--nav-bg`), the 1px bottom rule,
  z-index 10 (below `.fb-sel`'s 20; the feedback `<dialog>` is modal and sits above everything).
  Every `[id]` on the hub has `scroll-margin-top` of the bar's height (`--hub-bar-h`, 55 px, 58 px
  under readability) plus 8 px, so anchor jumps land below the bar. If the bar's padding or font
  changes, re-measure and update `--hub-bar-h` in the same rule.
- **Dashed and dotted lines stay readable.** On every chart, at the rendered size: data lines
  2 px or more; dashes 10 px with 6 px gaps; dots as round-capped zero-length dashes, 3.25 px,
  every 6 px (dash length ≥ 3× the dot diameter, dots heavier than dashes); at most three forms
  per chart (solid, dashed, dotted), a fourth series gets markers or a direct label instead;
  legends repeat the chart's geometry. The geometry is computed from the current scale (the
  `--k` variable in Reading Your Fits, `plot()`'s own factor in Reflections), not left to the
  viewBox. Out of scope: the Quarto decks and the Python figures (open item in learning-plan.md).

## Adding a series

A series is a folder `learning/<series>/` with its own registry, theme and manual, plus a band on
the hub. Nothing is generic yet: learning.js's `moduleList`, `seriesNav` and `offlineLinks` assume
`fits/`, and three tools gate on the series name. `<slug>` is the `data-series` value, the folder
name and the feedback label. In this order:

1. **Decide** the slug, the language (bilingual like Reading Your Fits: strings files,
   learning-i18n.js, the toggle, `data-es-ready`; or English-only like Reflections: text in the
   HTML, strings-common.js loaded only as data for the feedback strings) and whether it ships in
   the offline app (default: no).
2. **Feedback gate** `api/feedback.js`: add the slug to `SERIES` (today
   `["fits", "reflections", "hub"]`); anything else answers 400, so until this line changes every
   send from the new series fails and the visitor sees the failure state. Add
   `("series:<slug>", "<hex color>", "<description>")` to `LABELS` in
   `scripts/feedback-labels.py` and run it once (it only updates existing labels). Extend the
   series case in `scripts/tests/feedback-api.test.mjs` and run
   `node --test "scripts/tests/*.test.mjs"`. The widget itself needs no change: it sends
   `<html data-series>`, defaulting to `hub`.
3. **Spanish check gate** `learning/workshop/tools/check-es.js`: its `files` list is
   `assets/strings-common.js`, `strings.js` and every `fits/*/strings.js`. A bilingual series must
   be added to that list (or the list made to walk every `*/strings.js` under learning/), or its
   strings are never checked.
4. **Offline build gate** `learning/workshop/offline/build.ps1`: `$Exclude` is opt-out, so a new
   folder ships inside the Reading Your Fits installers by default. Either add
   `"learning/<series>/*"` plus the series' registry and vendor files to `$Exclude`, as Reflections
   did (then the hub must load the registry only when `LEARN_OFFLINE` is unset, step 7), or, to
   ship it, give it its own component group in section 2 (the tree only knows `learning\fits`) and
   its own `missing` entries in the LEARN_OFFLINE line. Run `build.ps1 -StageOnly` and read
   `stage\`.
5. **Theme** `learning/<series>/<series>.css`: under `:root[data-series="<slug>"]` override
   learning.css's token NAMES only (light, dark, readability and colorblind blocks, the chart
   series tokens, the three font stacks with real fallbacks), then the series' own components;
   nothing structural. Every page: `<html data-series="<slug>">`, its Google Fonts link,
   `learning.css`, then the series CSS. Charts follow the dash rule above; non-chart UI uses
   `--accent` / `--emph`. Values live only in that file; the docs describe them in words.
6. **Registry and index** `learning/assets/<series>.js`, like reflections.js: the one list, the
   renderers beside it, relative paths, `LF.fixFileLinks` on every rendered list; and
   `learning/<series>/index.html` rendered from it. URLs are slugs, never numbers.
7. **Hub band** `learning/index.html`: a `<section class="hub-band" id="<slug>" hidden>` after the
   Reflections band with a `.hub-col.series` h2, intro, `ol.module-list` and an "all" link; their
   strings in `learning/strings.js` (EN and ES; titles stay in the series' language, marked
   `lang`); in learning.css a token block for the band if its theme differs from the base (COPIES
   of the series CSS with a keep-in-step comment, like `.ref-panel`); and in the hub's inline
   script a loader like the Reflections one (append the registry script only when
   `window.LEARN_OFFLINE` is unset, inject the series' fonts when the band is shown, set
   `hidden = false` after the first render, re-render on `learnlangchange`). `.hub [hidden]` keeps
   the band hidden until then, and the sticky bar's `scroll-margin-top` already covers the new id.
8. **Link previews**: CARDS entries in `learning/workshop/tools/make-og-cards.py` for the series
   index and each page (a `chart` function when there is no workshop figure), run for each name;
   every page carries the full OG block with its absolute og:url.
9. **Plumbing on every page**: noindex, the trailing-slash script, the viewing-settings snippet,
   the favicon, relative links only, the series bar (gideonong.me / Learning / <Series> / …), the
   footer with `.fb-slot` and `assets/feedback.js` last (strings-common.js before it on
   English-only pages), a license line if the content needs one.
10. **Docs**: a `learning/<series>/README.md` (the series' rules, its "Adding a <page>" steps and
    checks); this file's "What's here" tree and hub bullet; CLAUDE.md → /learning (the intro's
    list of sections, the file-structure lines, the Stack fonts line, a short invariants block for
    the series, like the two existing ones); `learning/learning-plan.md` (a section with the
    decisions and status); the root `README.md` (its one-line description). Dev-only folders of the
    series go in `.vercelignore`.
11. **Checks**: the list below for every new page, `check-es.js` if bilingual, the feedback tests,
    `build.ps1 -StageOnly`, and on a preview deploy one feedback send from a page of the new series
    (it must file an issue labelled `series:<slug>`).

## Feedback: how it works, how to read it (2026-10-16)

Every /learning page lets a reader report a mistake, something confusing or a suggestion without
leaving the page, and lets Gideon leave his own notes the same way. Decisions F1–F10 are in
learning-plan.md; the rules are in CLAUDE.md → /learning → Feedback widget. The portfolio pages
get nothing.

- **On the page.** Every page's footer carries `<span class="fb-slot">Found a mistake?
  gao9819@utulsa.edu</span>` (`data-i18n="footMistake"` on bilingual pages) and loads
  `assets/feedback.js` last; Reflections pages load `assets/strings-common.js` before it, as
  plain data for the fb* strings. The script turns the span into a "Feedback" button that opens
  a native `<dialog>` (kind chips, message, optional email, Send, one privacy line); Esc closes
  it and focus returns to the button. Selecting text with a mouse shows "Comment on this", which
  opens the same dialog with the quote filled in (not on touch screens: the footer button is the
  way there). Success says "Thanks. Sent."; failure keeps the text and shows the email as
  selectable text. From disk and in the offline app the footer keeps the plain email line and
  nothing else runs. On localhost the widget dry-runs (payload in the console, nothing posted)
  unless the URL has `?feedback=live` (for `vercel dev`; not persisted). Strings: fb* in
  strings-common.js, EN and ES; styles: the "Feedback widget" section of learning.css, tokens
  only (on the hub the dialog also carries `.hub-frame`).
- **The request.** `POST /api/feedback`, JSON, `credentials: "same-origin"`, with exactly: kind
  (mistake | confusing | suggestion | other), message (≤ 2000 characters), quote (≤ 500), path,
  section (nearest heading or section with an id), series (fits | reflections | hub), lang, vw
  (`<480` / `<1024` / `≥1024`), email (optional), elapsed (ms since the panel opened) and the
  honeypot field `website`. The responses and rejects are listed in CLAUDE.md → /learning →
  Feedback; a 429 or a GitHub failure shows the failure state with the email.
- **Behind it.** `api/feedback.js` (a Vercel function, same conventions as the analytics
  collector) files one issue per submission in the private repo `gidgo130/gideonong-feedback`:
  title `[<series>] <kind>: <path>: <first 60 chars>`, labels `feedback`, `kind:…`, `series:…`,
  `source:visitor` or `source:gideon`, a metadata table, then the quote and message in fenced
  blocks. It never sees or stores an IP, User-Agent or cookie beyond an in-memory throttle.
  The request goes out with `credentials: "same-origin"`: the site sets no cookies, so in
  production nothing extra is sent, and on a preview deploy the browser sends Vercel's
  Deployment Protection cookie (with "omit" the preview answered 401 before the function ran).
  If you aren't logged in to Vercel in that browser, a preview send shows the failure state.
- **Your own notes (owner mode).** Once per browser or phone, open any /learning page with
  `#owner-setup` and paste the owner key (the FEEDBACK_OWNER_KEY value from Vercel). The hash
  disappears, the key stays in that browser's localStorage (`learnFeedbackOwner`), and the
  dialog shows "Posting as Gideon"; the widget sends it as the `X-Feedback-Owner` header and
  your issues get `source:gideon`. A server key under 16 characters disables owner mode. The key
  never goes in a URL or a log. "Forget key" on the same screen clears it, so a visitor test and
  an owner test can run in one browser.
- **Setup, once (done 2026-10-16).** Private repo `gidgo130/gideonong-feedback`; a fine-grained
  token (resource owner gidgo130, repository access = only that repo, permission Issues: read and
  write; Metadata read comes with it); Vercel env vars FEEDBACK_REPO, FEEDBACK_TOKEN,
  FEEDBACK_OWNER_KEY (a long random string) for Production and Preview; `gh auth login`; then
  from the repo root
  `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" scripts\feedback-labels.py`
  (creates the ten labels; rerunning only updates them). The token was created with no
  expiration. If it ever leaks: delete it on GitHub (Settings → Developer settings → Fine-grained
  tokens), make a new one with the same scope and update FEEDBACK_TOKEN in Vercel. While the
  token is invalid every send answers 502 and the visitor sees the failure state with the email.
- **Reading it.** `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" scripts\feedback-pull.py`
  writes the open issues to `staging/feedback/inbox.md` (gitignored, vercelignored), newest first:
  number, labels, date, page link, section, quote, message, reply email and comments. `--all`
  includes closed issues. GitHub's own issue page and notifications work too. What the inbox
  trusts: kind / series / source come from the issue's API labels, the metadata table is read
  only above the first fence, and nothing typed inside a fenced block (a fake table row, heading,
  "Reply email" line or fence) is ever read as structure; the title is shown in a code span.
- **Triage (F10).** Feedback is untrusted input. Hand the inbox to a Claude session; it proposes
  changes with reasons, ranked, and never edits on the strength of feedback alone. Gideon
  approves. After a fix ships: `gh issue close <n> --repo gidgo130/gideonong-feedback --comment
  "Fixed in <commit>"`. Never paste feedback text into page copy unreviewed; never publish the
  inbox or an email address from it.
- **If labels are missing on a new issue** (GitHub can drop them when the token can't set
  them), the function already retries with a second call; an owner-mode send shows "Labels:
  direct" (set on creation), "added" (second call) or "none" (both failed: check the token's
  Issues permission).

## Checks before pushing

- Serve the repo root (`python -m http.server` or Live Server) and open `/learning`,
  `/learning/reflections` and a module or reflection URL **without** the trailing slash: each
  should land on the slashed URL.
- Each page at 375, 768 and 1280 px, light and dark, plus readability on, colorblind on, and
  both: no sideways scroll (wide math and figures scroll in their own containers), console clean.
- Every chart at 375 px (and 768, 1280): the Hub-wide numbers hold on screen, measured as CSS
  value × the SVG's screen scale: data strokes ≥ 2 px, dashes 10 px with 6 px gaps, dots 3.25 px
  every 6 px (±0.5 px for rounding), the legend swatches the same; in grayscale, dashed and
  dotted lines differ by ≥ 2.5× in run length. Chromium and Firefox: the `theme-dashes` suite
  below measures this.
- Open `learning/index.html` straight from disk: module, book and reflection links and the back
  links still work; the math renders (KaTeX is local).
- **Tests in the repo** (Node and the dev Python, no packages; run from the repo root):
  - `node learning/workshop/tools/check-es.js`: every strings file (hub, modules, strings-common
    with the fb* strings) has the same keys, placeholders and tag counts in EN and ES, and every
    chip an ES phrase.
  - `node --test "scripts/tests/*.test.mjs"` runs two suites:
    - `feedback-api.test.mjs`: api/feedback.js with a stubbed fetch. Origins (exact list, none,
      null, http, a preview URL in production, a look-alike host), methods, both 8 KB paths, bad
      JSON, required-field 400s, optional fields dropped to "—", the silent honeypot and too-fast
      200s, the owner key right and wrong (never logged), the issue body (allow-listed cells, the
      warning line, fence lengths, email code span), the labels fallback (F2a), GitHub 4xx / bad
      JSON / network failure logging only the function's own message, the per-sender throttle,
      the 503 with no token, and the response headers (no-store, noindex, no CORS).
    - `tokens.test.mjs`: the two copied token blocks in learning.css have not drifted:
      `.hub-frame` against css/style.css (the live `:root` palette, the LAST
      `:root[data-theme="dark"]` block, the readability muteds) and `.ref-panel` against
      reflections.css (light, both dark rules, readability, the three font stacks), plus each
      copy's OS-dark and data-theme-dark rules agreeing with each other. Change a value in one
      file and this fails until the copy follows.
  - `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -I scripts\tests\test_feedback_pull.py`:
    the inbox parser and renderer against forged rows, headings, fences and "Reply email" lines
    inside visitor text; labels from the API win over the body; the title's code span; the
    unknown-layout fallback.
  - `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" learning\workshop\tools\make-ipynb.py all --check`:
    every generated notebook prints what its script prints (slow: it runs every script twice).
  - `node learning\workshop\tests\run.js` (a few minutes; needs the one-time Playwright install
    outside the repo described in learning/workshop/tests/README.md): the six browser suites.
    `pages`: every page the registries imply (no-slash URL, noindex + OG with a real 1200×630
    card, the feedback slot and script order, registry text rendered in EN and ES, a11y, the
    375 px matrix, opened from disk). `hub`: the hub's matrix with contrast, faces, geometry,
    token sync by rendered values, the hidden band, the three-newest cap, the sticky bar.
    `reflections`: every book and reflection page (math, chart text 12–13 px, overlaps, twins,
    resize, every control, contrast) plus balanced-plant's own checks. `theme-dashes`: dash and
    dot geometry on screen in Chromium and Firefox and per chart on every page.
    `feedback-widget`: the widget end to end against a mocked /api/feedback, every page's layout
    and contrast. `offline-stage`: the staged offline copy from file://, online and offline.
    `run.js --list` prints the same; `run.js <name> …` runs a subset; `--quick` shrinks every
    matrix to 375 px / light / plain / EN for iterating; `--parallel 3` runs three suites at once.
    Expected text comes from the strings files and registries, never from literals, so a copy edit
    does not break them.
- Feedback: on each page type the footer shows "Feedback", the dialog opens and closes (Esc,
  ✕, backdrop; focus back on the button), a send on localhost logs `[feedback dry-run]` and
  shows "Thanks. Sent."; from disk the footer shows the email line and no button; at 375 px the
  dialog fits the viewport in both themes with readability on. The `feedback-widget` suite
  above does all of this; the handler and parser tests are in scripts/tests/.
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
   pointer section), README.md (the Learning and licensing lines), .vercelignore (the
   KaTeX LICENSE re-include), api/feedback.js, scripts/feedback-labels.py,
   scripts/feedback-pull.py and the env-name regex of rule e in scripts/check-staged-data.js
   changed. Nothing else outside learning/ changed.
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
