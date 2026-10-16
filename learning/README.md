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

## Feedback: how it works, how to read it (2026-10-16)

Every /learning page lets a reader report a mistake, something confusing or a suggestion without
leaving the page, and lets Gideon leave his own notes the same way. Decisions F1–F10 are in
learning-plan.md; the rules are in CLAUDE.md → /learning → Feedback widget. The portfolio pages
get nothing.

- **On the page.** The footer's "Found a mistake? <email>" span (`.fb-slot`) becomes a
  "Feedback" button once `assets/feedback.js` runs; it opens a small dialog (kind chips, message,
  optional email, Send, one privacy line). Selecting text with a mouse shows "Comment on this",
  which opens the same dialog with the quote filled in (not on touch screens: the footer button
  is the way there). Success says "Thanks. Sent."; failure keeps the text and shows the email.
  From disk and in the offline app the footer keeps the plain email line. On localhost the
  widget dry-runs (payload in the console, nothing posted) unless the URL has `?feedback=live`.
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
  disappears, the key stays in that browser, and the dialog shows "Posting as Gideon"; your
  issues get `source:gideon`. "Forget key" on the same screen clears it, so a visitor test and an
  owner test can run in one browser.
- **Setup, once.** Private repo `gidgo130/gideonong-feedback`; a fine-grained token (that repo,
  Issues read/write); Vercel env vars FEEDBACK_REPO, FEEDBACK_TOKEN, FEEDBACK_OWNER_KEY for
  Production and Preview; `gh auth login`; then from the repo root
  `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" scripts\feedback-labels.py`
  (creates the ten labels; rerunning only updates them).
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
- Every chart at 375 px: data strokes ≥ 2 px, dashes ≥ 6 px with gaps ≥ 4 px, dots ≥ 3 px every
  ≥ 5 px, measured as CSS value × the SVG's screen scale; in grayscale, dashed and dotted lines
  differ by ≥ 2.5× in run length. Chromium and Firefox (Playwright's build, in the scratchpad).
- Open `learning/index.html` straight from disk: module, book and reflection links and the back
  links still work; the math renders (KaTeX is local).
- `node learning/workshop/tools/check-es.js` passes (hub and module strings, the fb* strings
  included).
- Feedback tests pass: `node --test "scripts/tests/*.test.mjs"` (api/feedback.js with a stubbed fetch:
  origins, limits, silent rejects, owner key, fences, F2a, GitHub failures, throttle, headers)
  and `& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -I scripts\tests\test_feedback_pull.py`
  (the inbox parser against forged rows, headings, fences and email lines inside visitor text).
- Feedback: on each page type the footer shows "Feedback", the dialog opens and closes (Esc,
  ✕, backdrop; focus back on the button), a send on localhost logs `[feedback dry-run]` and
  shows "Thanks. Sent."; from disk the footer shows the email line and no button; at 375 px the
  dialog fits the viewport in both themes with readability on. The series-wide Playwright
  checks (136 on 2026-10-16) live in the session scratchpad, not the repo; the handler and
  parser tests above are in the repo (scripts/tests/).
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
