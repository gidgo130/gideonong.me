# /learning — how this section works

Dev notes for the Learning section of gideonong.me. Not deployed (`*.md` is in `.vercelignore`).
The build plan, status and decisions live in `learning/learning-plan.md` (the root `plan.md` is
the main site's and only points there). The rules
live in `CLAUDE.md` → **/learning**. This file is the working manual.

## What's here

```
learning/
  index.html                  Hub: "Learning" home + the Reading Your Fits module list
  strings.js                  Hub text (EN/ES)
  learning-plan.md            Roadmap, status, decisions (dev-only, not deployed)
  README.md                   This manual (dev-only, not deployed)
  assets/
    learning.css              Shared look for every /learning page (the "lab notebook" style)
    learning.js               LF: seeded random numbers, fits (OLS, Deming), SVG charts,
                              number formatting, series nav, hub list, offline link fix
    learning-i18n.js          LI18N: EN/ES strings, shared "lang" key, hidden toggle, dev check
    strings-common.js         Text shared by all pages (series name, module titles, nav words)
    modules.js                The ONE module registry: order, slug, ready flag
  fits/<slug>/
    index.html                The module's interactive page
    strings.js                All of that page's display text (EN/ES)
    main.js                   The page's logic (trials)
    slides.html               Rendered Quarto deck (source lives in the workshop, not here)
    <slug>.py                 Companion Python script, offered as a download
```

Pages are plain HTML/CSS/JS with relative links, so they work on the site, on a Vercel
preview and opened straight from disk (the planned offline Windows app).

## The workshop (outside this repo)

`C:\Users\gidgo\Documents\dev\statistics and error plots for engineers\modules\<slug>\` holds
the slide source (`slides.qmd`, `custom.scss`) and the figures. Only rendered output comes into
the repo. To rebuild a deck: run the module's `.py` from the workshop folder (writes
`figures/`), then `quarto render slides.qmd`, then copy `slides.html` into
`learning/fits/<slug>/`.

## Rules of thumb

- **Unlisted while in progress.** Every page carries `<meta name="robots" content="noindex">`
  (slides get it through `include-in-header` in `slides.qmd`). Going public = delete that line
  on every /learning page and the qmd option, then re-render the slides.
- **Linked only from About.** The About page's "Interesting sites" list (js/about.js) has the
  Learning entry. That block is `hidden` in about.html right now, so the link shows only once
  that attribute is removed.
- **English first, Spanish required.** Every visible word goes through a strings file. A page
  turns Spanish on by adding `data-es-ready` to its `<html>` once its `es` strings are complete;
  that also un-hides its EN/ES toggle. The toggle shares the main site's `lang` key.
- **Colors mean the same thing everywhere:** dashed ink = the truth, red = what an ordinary fit
  reports, blue = a corrected estimate, grey dots = measured points.
- **Theme** follows the main site's saved choice (`viewTheme`), else the OS setting.
- **Simulated data only**, with the true model stated on the page.

## Strings

- `data-i18n="key"` → text, `data-i18n-html="keyHtml"` → markup (keys ending in `Html` only,
  and only `<b>`, `<i>`, `<code>`), `data-i18n-aria="key"` → aria-label,
  `<title data-i18n-title="key">`.
- The HTML also contains the English text as a no-JS fallback. On localhost or file:, the i18n
  dev check warns in the console if that text drifts from its EN string or a key is missing.
- Placeholders are `{name}`, filled by the page's `main.js` through `LI18N.t(key, vars)`.
- Numbers go through `LF.num(value, decimals)` so Spanish gets a decimal comma.

## Adding a module

1. Workshop: `modules/<slug>/` with `slides.qmd` (copy an existing one for the YAML) and the
   companion script.
2. Repo: `learning/fits/<slug>/` with `index.html`, `strings.js`, `main.js`, `slides.html`,
   `<slug>.py`. Copy the head block (noindex, trailing-slash fix, theme snippet, fonts) from an
   existing module.
3. Title and description: `mod<Key>Title` / `mod<Key>Desc` in `assets/strings-common.js`.
4. Flip `ready: true` for it in `assets/modules.js`. The hub list and every module's prev/next
   links update from that one line.
5. Run the checks below, then the Fable review.

## Checks before pushing

- Serve the repo root (`python -m http.server` or Live Server) and open `/learning` **without**
  the trailing slash: it should land on `/learning/`.
- Each page at 375, 768 and 1280 px, light and dark: no sideways scroll, console clean.
- Every trial control changes its plot and readout; "Draw a new sample" changes the data.
- Slides: the "Try it yourself" slide loads the interactive.
- Open `learning/index.html` straight from disk: module links and the back links still work.
- On the Vercel preview: repeat the `/learning` no-slash check, and view source for `noindex`.

## Fable review prompt (Claude Code, in this repo)

Paste this into Claude Code with the Fable model, on the branch you're about to merge:

```
Review the /learning section of this repo before I merge. First read CLAUDE.md (the
"/learning" section and the main-site rules it overrides), learning/learning-plan.md (plan,
status, decisions) and learning/README.md (structure and conventions). The root plan.md is the
main site's roadmap; it should contain only a short pointer section about /learning.

Then check, and report findings ranked by severity with file and line:

1. Statistics: every claim, formula and number on each module page, its slides and its
   Python script is correct and consistent (e.g. attenuation factor σx²/(σx²+σu²), Deming
   slope, t critical values, confidence-interval coverage). Flag anything misleading for a
   student with no statistics background.
2. Code: run the pages mentally or in a browser; look for JS errors, controls that don't
   update, edge cases at slider extremes (zero noise, max noise), and the offline (file:)
   link fix.
3. Scope: outside learning/, only js/about.js (the Interesting-sites "Learning" entry),
   CLAUDE.md (the /learning section and file-structure lines) and plan.md (the pointer
   section) changed. Nothing else outside learning/ changed.
4. Rules: the /learning rules in CLAUDE.md are followed (noindex, unlisted, own design,
   fixed color meanings, relative links, simulated data).
5. i18n readiness: no hard-coded display text outside strings files; every data-i18n key
   exists; numbers go through LF.num; the EN/ES toggle stays hidden until data-es-ready.
6. Accessibility and layout: labels on every control, aria-labels on charts, visible focus,
   no horizontal scroll at 375 px, both themes readable.
7. Deploy: noindex present on every /learning page including slides.html; relative links
   work at /learning and /learning/; nothing in learning/ that shouldn't be public
   (*.md files are excluded by .vercelignore).

Don't change files; list what you'd change and why.
```
