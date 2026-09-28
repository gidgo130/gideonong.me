# Learning Plan — gideonong.me/learning

A living roadmap for the Learning section. Update it as modules ship or decisions change.
Claude Code: read this file, CLAUDE.md → "/learning" and learning/README.md before working in
learning/. The main site's roadmap is plan.md at the repo root; it only points here.

> Unlisted teaching pages at gideonong.me/learning/. A separate track from the main site's
> plan.md (which only points here). Rules: CLAUDE.md → "/learning". Working manual + Fable
> review prompt: learning/README.md.
> Workshop (slide sources, figures, study notes; NOT in the repo):
> `C:\Users\gidgo\Documents\dev\statistics and error plots for engineers\`.
> Decisions: see the Decisions log at the end of this file.

Series "Reading Your Fits" — six modules, in this order:

| # | Module | Slug | Status |
| --- | --- | --- | --- |
| 1 | Why R² isn't enough (Anscombe's quartet, what R² hides) | r-squared | Planned |
| 2 | Reading a residual plot (four patterns; curvature and the cooling-curve shape example) | residual-plots | **Built** (EN), reviewed |
| 3 | Uneven scatter (heteroskedasticity, weighted fits, honest error bars) | uneven-scatter | Planned |
| 4 | Time-ordered data (autocorrelation, drift, cooling-curve log trap as the worked example) | time-order | Planned |
| 5 | The Invisible Bias (endogeneity: noise in x, unmeasured drift, fixes) | invisible-bias | **Built** (EN) |
| 6 | Using and reporting a fit (CI vs PI, error in units, checklist, Excel/MATLAB/Python) | reporting | Planned |

Every module ships: interactive page (index.html + strings.js + main.js), Quarto slides
(slides.html, source in the workshop), companion Python script (<slug>.py, Colab-ready).
Interactives stay abstract (generic x and y); the cooling curve is the one worked example.
Audience: engineering students with no statistics background, some Excel/MATLAB.

## Phase A — Foundation (2026-09-28)
- [X] learning/ structure, shared assets (learning.css, learning.js, learning-i18n.js,
  strings-common.js, modules.js)
- [X] Module 5 "The Invisible Bias" ported into learning/fits/invisible-bias/ (renumbered from
  the prototype's "Module 3"), strings extracted for EN/ES, series bar + prev/all/next
- [X] Hub page learning/index.html (module list from modules.js)
- [X] noindex on every page and deck; theme follows `viewTheme`; trailing-slash fix; offline
  (file:) link fix
- [X] EN/ES toggle scaffold in every page, hidden until `data-es-ready`
- [X] About → Interesting sites: "Learning" entry (js/about.js). Block still `hidden`.
- [X] Docs: CLAUDE.md /learning section, this file (learning/learning-plan.md), learning/README.md;
  plan.md keeps only a pointer section
- [X] Fable review (2026-09-28): 15 findings; wording, readouts, script t-value, favicon,
  seed generator, histogram range, aria-label strings and heading levels fixed the same day
- [ ] Decide: `vercel.json` with `"trailingSlash": true` (Fable #14) so `/learning` redirects
  before the page loads, instead of the in-page fix that logs a few 404s first. Affects the
  whole site, so it's Gideon's call; the current behavior works.
- [ ] Gideon: Live Server check → push to a branch → Vercel preview → check `/learning` with
  and without the trailing slash → Fable review (prompt in learning/README.md) → merge
- [ ] Gideon: delete the old workshop folder `module3_invisible_bias` (superseded by
  `modules/invisible-bias`)

## Phase B — Remaining modules (EN), one at a time
For each: 3-line outline for Gideon's OK → build page + slides + script → verify (375 / 768 /
1280, light / dark, console clean, numbers sanity-checked by simulation) → Fable review → push.
Order: 2 → 1 → 3 → 4 → 6.
- [X] Module 2 — Reading a residual plot (built 2026-09-28: pattern gallery + "Name that pattern"
  quiz, cooling-curve shape trial, one-point influence trial; engine gained LF.r2,
  LF.influence, LF.expFit)
- [X] Fable review of Module 2 (2026-09-28): 10 findings, all fixed except #9 (English comments
  inside the "make it yourself" code blocks, same in Module 5), deferred to Phase S
- [ ] Build 1, 3, 4, 6, then one Fable review for the four
- [ ] Module 1 — Why R² isn't enough
- [ ] Module 3 — Uneven scatter
- [ ] Module 4 — Time-ordered data
- [ ] Module 6 — Using and reporting a fit

## Phase S — Spanish (REQUIRED, after the English set)
- [ ] ES strings for strings-common.js, the hub and every module (general Latin American
  Spanish; decimal comma through LF.num)
- [ ] Spanish slides (slides.es.html per module, or one deck with both — decide at the time)
- [ ] Add `data-es-ready` to each page as its ES is complete (un-hides the toggle)
- [ ] Spanish Python comments? (decide at the time)
- [ ] Code blocks inside pages ("Show the Python", "Make these plots yourself") hold English
  comments in the HTML; move them to strings or accept English code comments (Fable M2 #9)

## Phase C — Go public
- [ ] Content review by a professor
- [ ] Remove `noindex` from every /learning page and the slides.qmd header; re-render decks
- [ ] Unhide About → Interesting sites (replace or remove the placeholder sites first)
- [ ] Optional: Open Graph tags, Google Search Console

## Phase D — Offline Windows app
- [ ] Inno Setup script (kept in the workshop, not the repo) that installs learning/ and a
  Start Menu shortcut. Pages already work from disk; fonts fall back to system fonts offline.

## Optional later
- [ ] marimo "play with the code" notebooks per module (served from the site over HTTP)
- [ ] Honor About's readability / colorblind settings on /learning pages

---

## Decisions log

[2026-09-28] Learning section (/learning) — "Reading Your Fits". Built in a Cowork session.
1. **Unlisted, own design.** gideonong.me/learning/ hosts interactive teaching pages in their
   own "lab notebook" look (not the main-site palette or fonts). Not in the nav; the only link
   in is About → Interesting sites (currently hidden). CLAUDE.md → /learning holds the rules.
2. **noindex now, index later.** Every page and deck carries robots noindex until the series is
   finished and reviewed (Phase C). robots.txt deliberately not used.
3. **Bilingual required, English first.** Strings files + learning-i18n.js from day one; the
   EN/ES toggle (shared "lang" key) is present but hidden until a page is `data-es-ready`.
4. **Plain HTML/JS interactives, Python as a companion.** Chosen over marimo browser exports:
   instant load, works offline from disk, no server needed, fits the no-build site. Each
   module still ships a Colab-ready .py script. marimo stays an optional extra.
5. **Module order** R² → residual plots → uneven scatter → time order → invisible bias →
   reporting. The first built module (invisible bias) became Module 5. Slugs, not numbers, in
   URLs.
6. **Workshop vs repo.** Slide sources, figures and notes stay in the workshop folder; the repo
   gets only what visitors load. The repo is the single source of truth for the pages.
7. **Review.** Fable (Claude Code, on the repo) reviews each module before merge; prompt in
   learning/README.md.
8. **Own plan file.** This plan lives in learning/learning-plan.md, not plan.md, so the main
   site's roadmap stays about the main site. plan.md keeps a short pointer section.
9. **Fable review fixes.** The intro now says x is *read* off an instrument, with one line on
   setpoint (Berkson) error, which does not bias the slope. The rule of thumb names the
   standard deviation of x, not its range. The errors-in-x readout is neutral (it's unbiased
   but noisier) and Trial 4 warns when the correction itself is unreliable (λ < 0.3). The
   Trial 2 note only claims "more data makes you more certain of the wrong answer" when
   coverage is below 85%. The Python script uses the t critical value like the page.
