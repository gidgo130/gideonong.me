# /learning browser suites

Playwright checks for the /learning pages: the hub, every Reading Your Fits module, the Reflections
pages and the feedback widget, driven from the registries so a new module or reflection is covered
the day it is `ready`. Dev-only: this folder is in `.vercelignore` (through `learning/workshop/`) and
in build.ps1's `$Exclude`. The repo stays free of npm: the suites are plain Node scripts, and
Playwright lives OUTSIDE the repo.

## Install, once

```powershell
mkdir "$env:LOCALAPPDATA\pw"; cd "$env:LOCALAPPDATA\pw"
npm init -y
npm i playwright@1.64.0 pngjs@7.0.0
npx playwright install chromium firefox     # skipped if the browsers are already in %LOCALAPPDATA%\ms-playwright
```

`lib.js` loads Playwright from `$env:LOCALAPPDATA\pw\node_modules`; set `LEARN_PW` to another
`node_modules` folder to use a different install. The version is pinned because Playwright and its
browser builds go together (1.64.0 ↔ chromium 1248, firefox 1555).

## Run

From the repo root (Live Server may keep :5500; the suites use :5599):

```powershell
node learning\workshop\tests\run.js                      # every suite, in order; exit 1 on any failure
node learning\workshop\tests\run.js pages feedback-widget   # a subset
node learning\workshop\tests\run.js --list               # names and coverage
node learning\workshop\tests\hub.js                      # one suite on its own (it starts its own server)
node learning\workshop\tests\offline-stage.js --no-build # skip build.ps1 -StageOnly and reuse offline/stage/
```

`run.js` starts one static server for the repo (Vercel-style: a folder URL with or without the
trailing slash serves its index.html, no redirect), passes it to each suite as `LEARN_BASE`, echoes
their output and ends with a table. Each suite prints `N passed, M failed` as its last line. The
whole run takes a few minutes; Firefox is used only by `theme-dashes`.

## What each suite covers

| Suite | Covers |
| --- | --- |
| `pages.js` | Every page the registries imply: the no-slash URL lands on the slashed one; noindex and the full OG + Twitter block (og:url matches, og:image is a real 1200×630 PNG); the `.fb-slot` footer span and the script order; `data-series` / `data-es-ready`; the registry text is rendered (hub strings EN and ES, module titles and h1s from each strings.js, book and reflection titles and dates); a11y (labels, heading order, one h1, ids, chart roles); the feedback dialog's focus behavior; the View button and its popover (markup and roles, registry texts EN/ES, open / Esc / outside click, Dark / System and the two checkboxes applied and saved at once, the colorblind hint under the first legend, the same box as the EN/ES toggle, one bar row at 375 px, `prefers-contrast: more` with and without the script); the skip link (first in `<body>`, hidden until focused, the first Tab stop, `#main` holds the h1); forced colors (charts keep forced-color-adjust none, a painted background and distinct strokes); highlighted points and flagged bars (ink outline × `--k`, heavier under colorblind); every ready module's decks and play page (noindex and og:url in the first 2048 bytes, one charset first, the play OG set); the 375 px matrix (light/dark × readability × colorblind) plus 768/1280 for overflow and console; the pages opened from disk (links rewritten and resolvable, KaTeX local). |
| `hub.js` | learning/index.html: the 375/768/1280 × light/dark × modes × EN/ES matrix (every text ≥ 4.5:1 against its own band, geometry, faces, no overflow, console); rendered text equals the registry strings; token sync by rendered values (frame = about.html, Reading Your Fits band = every module page, Reflections band = a Reflections page); the hidden band in the installed copy / without the registry / without JS; font requests; the three-newest cap; static head descriptions; the sticky bar (pinned, opaque, anchors land below it, dialog above it). |
| `reflections.js` | The all-books page and every book page against the registry; every ready reflection: math renders with no raw delimiters or error spans, chart text 12–13 px with no overlapping labels at 375/768/1280, viewBoxes follow the container, equation twins, resize redraw, every control changes its chart or readout, contrast of body, muted, brass, orange, tick and series colors; balanced-plant's own checks (§8 labels, cues and markers, kSim, §1 diagram, §13 link). |
| `theme-dashes.js` | Dash and dot geometry as rendered: a synthetic page with the real stylesheets measured by grayscale run lengths in Chromium and Firefox (10/6 dashes, 3.25/6 dots, dash ÷ dot ≥ 2.5), plus every chart on every page from the DOM at 375 px. |
| `feedback-widget.js` | The widget with a mocked `/api/feedback`: footer trigger, payload field set and `same-origin`, the selection button and quote, failure keeps the text and shows the email, the non-JSON 401 path, dry-run on localhost, file: and LEARN_OFFLINE show only the email line, owner setup / forget, Spanish strings and the toggle, touch has no selection button, the dialog fits at 375/768/1280 × light/dark × readability on every page, contrast. |
| `offline-stage.js` | Runs `build.ps1 -StageOnly`, copies the stage, appends the installer's LEARN_OFFLINE line and opens the hub and a module page from `file://`, online and with the network cut: nothing from Reflections, the frame renders, the band stays hidden with no request, module rows and the offline footer line, hidden http-only links, console clean apart from Google Fonts offline. |

Expected text always comes from the source of truth (`learning/strings.js`, `assets/strings-common.js`,
each module's `strings.js`, `assets/reflections.js`, `assets/modules.js`) through `lib.registries()`:
a copy edit never breaks a test, missing or unrendered text still does. Checks that apply to every
page iterate `lib.pages()`; page-specific checks are keyed by slug.

Other tests, outside this folder: `scripts/tests/` (api/feedback.js, the inbox parser, the copied
token blocks), `learning/workshop/tools/check-es.js`, `make-ipynb.py --check`. The full list with
commands: learning/README.md → Checks before pushing.

## Adding a check

Put it in the suite whose loop already visits the page. Read expected text from `L.registries()`,
never from a literal. For a check that applies to every page of a kind, loop over `L.pages()` and
filter by `kind`; for one page, key it on the slug. Output files go to `out/` (gitignored).
