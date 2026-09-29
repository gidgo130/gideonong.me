# Learning Plan — gideonong.me/learning

A living roadmap for the Learning section. Update it as modules ship or decisions change.
Claude Code: read this file, CLAUDE.md → "/learning" and learning/README.md before working in
learning/. The main site's roadmap is plan.md at the repo root; it only points here.

> Unlisted teaching pages at gideonong.me/learning/. A separate track from the main site's
> plan.md (which only points here). Rules: CLAUDE.md → "/learning". Working manual + Fable
> review prompt: learning/README.md.
> Workshop (slide sources, figures, dev tools): `learning/workshop/`, tracked in git but never
> deployed (.vercelignore).
> Decisions: see the Decisions log at the end of this file.

Series "Reading Your Fits" — six modules, in this order:

| # | Module | Slug | Status |
| --- | --- | --- | --- |
| 1 | Why R² isn't enough (Anscombe's quartet, what R² hides) | r-squared | **Built** (EN, ES), reviewed |
| 2 | Reading a residual plot (four patterns; curvature and the cooling-curve shape example) | residual-plots | **Built** (EN, ES), reviewed |
| 3 | Uneven scatter (heteroskedasticity, weighted fits, honest error bars) | uneven-scatter | **Built** (EN, ES), reviewed |
| 4 | Time-ordered data (autocorrelation, drift, cooling-curve log trap as the worked example) | time-order | **Built** (EN, ES), reviewed |
| 5 | The Invisible Bias (endogeneity: noise in x, unmeasured drift, fixes) | invisible-bias | **Built** (EN, ES), reviewed |
| 6 | Using and reporting a fit (CI vs PI, error in units, checklist, Excel/MATLAB/Python) | reporting | **Built** (EN, ES), reviewed |

Every module ships: interactive page (index.html + strings.js + main.js), Quarto slides
(slides.html, source in learning/workshop/), companion Python script (<slug>.py, Colab-ready).
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
- [X] Gideon: Live Server check → push to a branch → Vercel preview → check `/learning` with
  and without the trailing slash → Fable review (prompt in learning/README.md) → merge
- [X] Old workshop prototype `module3_invisible_bias` gone (the workshop moved into
  learning/workshop/ on 2026-09-28)

## Phase B — Remaining modules (EN), one at a time
For each: 3-line outline for Gideon's OK → build page + slides + script → verify (375 / 768 /
1280, light / dark, console clean, numbers sanity-checked by simulation) → Fable review → push.
Order: 2 → 1 → 3 → 4 → 6.
- [X] Module 2 — Reading a residual plot (built 2026-09-28: pattern gallery + "Name that pattern"
  quiz, cooling-curve shape trial, one-point influence trial; engine gained LF.r2,
  LF.influence, LF.expFit)
- [X] Fable review of Module 2 (2026-09-28): 10 findings, all fixed except #9 (English comments
  inside the "make it yourself" code blocks, same in Module 5), deferred to Phase S
- [X] Build 1, 3, 4, 6 (2026-09-28). Engine gained LF.solve, polyfit, wls, hc3se, bands, ar1, acf,
  durbinWatson, and chart options xticks / xfmt. Every deck's embedded frame is now 520 px tall.
- [X] Fable review of Modules 1, 3, 4, 6 (2026-09-28): 11 findings, all fixed. Notes now follow
  the setting where the sample statistic is too noisy (M3 Trial 1), the Both-ends pattern has
  its own wording, M4 has a middle note for mild carry-over, the M1 quiz asks which fit you can
  trust as it stands, M1's curve is "R² with unlimited data", the M6 report flags predictions
  outside the tested range, expFit is ~3× faster, and decks no longer mark the embedded
  interactive as an image (see the workshop README's rebuild steps).
- [X] Module 1 — Why R² isn't enough (Anscombe's quartet, R² vs test range, polynomial degree)
- [X] Module 3 — Uneven scatter (fan, band/slope coverage incl. "both ends" pattern, weighted fit)
- [X] Module 4 — Time-ordered data (AR(1) residuals, cooling-curve log trap, runs vs samples)
- [X] Module 6 — Using and reporting a fit (CI vs PI, zero-crossing delta method, report line)

## Phase S — Spanish (REQUIRED, after the English set)
- [X] ES strings for strings-common.js, the hub and every module (general Latin American
  Spanish; decimal comma through LF.num). Done 2026-09-28; see decision 13.
- [ ] Spanish slides (slides.es.html per module, or one deck with both — decide at the time).
  Not in the 2026-09-28 pass: the ES pages label the link "Diapositivas (en inglés)".
- [X] Add `data-es-ready` to each page as its ES is complete (un-hides the toggle): the hub
  and all six modules, 2026-09-28
- [X] Spanish Python comments? Decided no: the .py scripts stay English (decision 13)
- [X] Code blocks inside pages ("Show the Python", "Make these plots yourself"): accepted as
  English code and comments (Fable M2 #9); the ES summaries say "el código está en inglés"

## Phase C — Go public
- [ ] Content review by a professor
- [ ] Remove `noindex` from every /learning page and the slides.qmd header; re-render decks
- [ ] Unhide About → Interesting sites (replace or remove the placeholder sites first)
- [ ] Optional: Open Graph tags, Google Search Console

## Phase D — Offline Windows app
- [ ] Inno Setup script (in learning/workshop/offline/, build output git-ignored) that installs learning/ and a
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
6. **Workshop vs repo.** Slide sources, figures and dev tools live in learning/workshop/: tracked
   in git so GitHub backs them up, excluded from Vercel by .vercelignore (moved from a separate
   folder outside the repo on 2026-09-28, after that folder was lost). The site gets only what
   visitors load. The repo is the single source of truth for the pages.
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
10. **Modules 1, 3, 4, 6 built** (2026-09-28), one Fable review for the four. Design choices
   worth knowing: Module 1 uses Anscombe's published quartet (cited on the page); Module 3's
   Trial 2 has a "both ends" noise pattern because with noise growing at one end the slope's
   default range happens to hold up, which would have taught the wrong lesson; Module 6's
   derived-quantity trial moves the data away from x = 0, since that (not the distance to the
   crossing) is what makes ignoring the slope–intercept covariance go wrong.
11. **Reference chips** (2026-09-28). A page's strings.js may carry `chips: [{ phrase: { en, es },
   href }]`; learning-i18n.js links the first whole-word match per element as a quiet
   `a.ref-chip` (new tab), like the main site's js/chips.js. Module 1: "Francis Anscombe" →
   the paper (anscombe-1973.pdf, next to the page), the footnote's title → its DOI. The PDF is
   the 2026 JSTOR copy (it has an OCR text layer; the 2007 copy doesn't), scrubbed of the
   per-page download stamp (IP + time), Info/XMP metadata, the whole-issue bookmarks and the
   cover's support link; the JSTOR cover and "All use subject to" line stay. Same treatment,
   same day, for every module: Cook 1977 and Cook & Weisberg 1982 (Module 2), Long & Ervin
   2000 and MacKinnon & White 1985 (3), Durbin & Watson 1950/1951 and Newey & West 1987 (4),
   the GUM, unmodified as BIPM publishes it (6). Deming 1943 and Fuller 1987 (5) are books:
   Open Library pages. The NIST/SEMATECH e-Handbook is linked from Modules 2 and 6. A chip
   links once per page; each module's footer has a "Further reading" line (`footRead`).
   White 1980 (HC0) joined Module 3's reading list the same day.
12. **No author on the decks** (2026-09-28). The `author:` line is gone from every slides.qmd
   and the rendered title slides. Claude built most of the series; Gideon's name stays on the
   hub and the main site, but the modules don't carry a byline.
13. **Spanish pass (Phase S)** (2026-09-28). The hub and all six modules are `data-es-ready`.
   - **Register.** General Latin American Spanish with **tú**, written the way a professor would
     explain it to students, in short, plain sentences like the English. Sentence-case titles,
     decimal comma in every number written into a string (runtime numbers go through LF.num).
   - **Series name: "Cómo leer tus ajustes de curvas".** "Cómo leer tus ajustes" alone can read
     as "settings"; "ajuste de curvas" is the standard engineering term. Other options weighed:
     "Interpretar tus ajustes", "Lo que dice tu ajuste". "Learning" = "Aprendizaje".
   - **Code stays English.** Slides, the .py scripts and the code blocks on the pages ("Show the
     Python", "Make these plots yourself", the Excel/MATLAB/Python cells of Module 6's tools
     table) keep English code and comments. ES pages say so: "Diapositivas (en inglés)", the
     hub's slides blurb ("Por ahora, solo en inglés") and the code summaries ("el código está en
     inglés").
   - **Excel names.** In ES prose, the Spanish function with the English name after it and ";"
     as the argument separator: =COEF.DE.CORREL(D3:D101; D2:D100) (CORREL en Excel en inglés),
     ESTIMACION.LINEAL (LINEST), INV.T.2C (T.INV.2T), TRUE → VERDADERO, 0,05. Module 6's
     toolsNote maps the table's English names: PENDIENTE (SLOPE), INTERSECCION.EJE (INTERCEPT),
     ESTIMACION.LINEAL (LINEST). All checked on Microsoft's es-ES function pages.
   - **Glossary.** fit / fitted line = ajuste / recta ajustada; residual = residuo; slope /
     intercept = pendiente / ordenada al origen; OLS = mínimos cuadrados ordinarios; weighted
     fit / WLS = ajuste ponderado / mínimos cuadrados ponderados; heteroskedasticity =
     heterocedasticidad; autocorrelation = autocorrelación; endogeneity = endogeneidad; errors
     in x = errores en x; attenuation = atenuación; leverage = apalancamiento (a lever point =
     punto de alto apalancamiento); Cook's distance = distancia de Cook; standard error = error
     estándar; robust standard errors = errores estándar robustos; confidence interval / range =
     intervalo de confianza (readouts: "intervalo del 95%"); prediction interval = intervalo de
     predicción; time constant = constante de tiempo; overfitting = sobreajuste; sample (one
     reading) = muestra; run (a whole repeat of the experiment) = corrida; carry-over = arrastre
     entre muestras; bootstrap = bootstrap; Trial 1 of 3 = Prueba 1 de 3; lag = retardo; residual
     SD = desviación estándar de los residuos ("desv. est." in tight labels); plot = gráfica;
     report = reportar; outlier (button) = Atípico; leftovers = lo que sobra.
   - **Word choices that follow from the glossary.** Run order / measurement order = "orden de
     medición", never "corrida" (in Module 4 a corrida is a whole repeat). Same-sign streaks of
     residuals = "rachas". "Draw a new sample" = "Generar datos nuevos", so "muestra" always
     means one reading. Takeaways heading = "Para recordar". Quiz answers use a colon
     ("Correcto: curva." / "La respuesta era: atípico.") to avoid gender agreement.
   - **Chips.** Every page's `chips` has `es` phrases: paper and book titles stay in English;
     "Distancia de Cook", "regresión de Deming", "parte I (1950)" / "parte II (1951)".
   - **Small fixes made on the way.** learning-i18n.js runs its markup-vs-EN dev check only on
     the first render (switching ES→EN on localhost used to warn on every key). learning.css:
     `section.trial > * { min-width: 0; }`, so an open code block scrolls instead of widening
     its trial at 375 px (an EN bug too; Modules 2 and 5); layout checked unchanged everywhere
     else at 1280 / 375, EN / ES. Some ES readouts use `\u00A0` so "x = 2", "(por defecto)" and
     "10 de 100" never split across lines.
   - **Left as is.** The "Problema oculto" control in Module 2 wraps to two rows in ES (32
     characters of labels vs 24); the `<meta name="description">` of each page stays English.
   - **Check.** `learning/workshop/tools/check-es.js` compares every strings file's `en` and
     `es`: same keys, same {placeholders}, same tag counts in *Html keys, an `es` phrase on every
     chip. Run from the repo root: `node learning/workshop/tools/check-es.js`.
