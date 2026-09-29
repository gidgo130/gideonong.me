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
      2026-09-29: the block was unhidden with Atomic Rockets in place of the Learning entry
      (js/about-data.js); /learning has no link from the site until an entry is added back.
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
- [X] Spanish slides: one `slides.es.html` per module (2026-09-29; decision 17). The ES pages'
  Slides link opens it; the "(en inglés)" labels are gone.
- [X] Add `data-es-ready` to each page as its ES is complete (un-hides the toggle): the hub
  and all six modules, 2026-09-28
- [X] Spanish Python comments? Decided no: the .py scripts stay English (decision 13)
- [X] Code blocks inside pages ("Show the Python", "Make these plots yourself"): accepted as
  English code and comments (Fable M2 #9); the ES summaries say "el código está en inglés"

## Phase C — Go public
- [ ] Content review by a professor
- [X] Keep `noindex` on every /learning page and deck, even once public (Gideon, 2026-09-28).
  The section is shared by link, not searched for: the About link and the OG cards are how
  people find it. Nothing to remove, nothing to re-render.
- [X] Unhide About → Interesting sites — done 2026-09-29, without a Learning entry (see above)
- [ ] Repo public (decision 18): papers purged from history, force push, GitHub visibility
  → public, then the Colab links work
- [X] Open Graph / Twitter-card tags on the hub, all six modules and their decks, with a
  1200×630 card per page in learning/assets/og/ (2026-09-28; decision 14). Pages stay noindex.
- [ ] Optional: Google Search Console (only for the main site; /learning stays out of search)

## Phase D — Offline Windows app
- [ ] Inno Setup script (in learning/workshop/offline/, build output git-ignored) that installs learning/ and a
  Start Menu shortcut. Pages already work from disk; fonts fall back to system fonts offline.

## Optional later
- [X] marimo "Play with the code" notebooks per module (served from the site over HTTP).
  Pilot for residual-plots 2026-09-28 (decision 16: cost numbers, Colab comparison); the
  other five 2026-09-29, same style, NumPy + Matplotlib only, repeat-the-experiment loops
  vectorized for Pyodide. Source learning/workshop/modules/<slug>/notebook.py, export
  learning/workshop/tools/export-play.py → learning/fits/<slug>/play/index.html.
- [X] Honor About's readability / colorblind settings on /learning pages (2026-09-28, decision 15)

---

## Decisions log

[2026-09-28] Learning section (/learning) — "Reading Your Fits". Built in a Cowork session.
1. **Unlisted, own design.** gideonong.me/learning/ hosts interactive teaching pages in their
   own "lab notebook" look (not the main-site palette or fonts). Not in the nav; since
   2026-09-29 no link from the site either (reached by URL and shared cards). CLAUDE.md →
   /learning holds the rules.
2. **noindex, permanently.** Every page and deck carries robots noindex. Originally "until the
   series is finished and reviewed"; on 2026-09-28 Gideon decided it stays for good (Phase C):
   /learning is reached by link, not by search. robots.txt deliberately not used.
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
   **Amended 2026-09-29:** the hosted PDFs left the repo: untracked and gitignored (they stay
   on disk next to their pages) and, before the repo went public, purged from git history; the
   repo never hosts a paper again. Chips link the DOI (Anscombe
   1973, Cook 1977, Long & Ervin 2000, MacKinnon & White 1985, White 1980, Durbin & Watson
   1950/1951, Newey & West 1987), BIPM's own GUM PDF, or the Open Library page for Cook &
   Weisberg 1982. The scrubbed copies stay in the gitignored references/ folder.
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
     ("Correcto: curva." / "La respuesta era: atípico.") to avoid gender agreement. A piece of
     evidence = "dato" (never "prueba", which is Trial). A catch / drawback = "inconveniente".
     Reviewed 2026-09-29.
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
14. **Link-preview cards** (2026-09-28). Every /learning page and deck has static Open Graph +
   Twitter-card meta (og:title / og:description from the EN title and lead, absolute og:url with
   a trailing slash, og:site_name "Gideon A. Ong", og:image with width / height / alt,
   twitter:card summary_large_image). Cards are 1200×630 PNGs in learning/assets/og/ in the
   lab-notebook look: the hub draws its own chart in the series colors; each module shows a crop
   of its first workshop figure. Generator: learning/workshop/tools/make-og-cards.py (Pillow +
   matplotlib; fetches the three web fonts into a git-ignored tools/fonts/). The decks get the
   tags through `include-in-header` in slides.qmd, so a re-render keeps them; the tracked
   slides.html copies were patched by hand to match. The description stays English (as the meta
   description does). Verified locally: every og:image answers HEAD 200 and is under 60 KB;
   noindex still on every page. After a deploy, check with LinkedIn Post Inspector and
   opengraph.xyz (both fetch the live URL; the Post Inspector also clears LinkedIn's cache).
15. **About's viewing settings on /learning** (2026-09-28). The head snippet on every page (hub
   and six modules) now reads all three main-site keys before first paint and sets the same
   <html> attributes the main site uses: `viewTheme` → data-theme (as before), `viewReadability`
   = "1" → data-readability, `viewColorblind` = "1" → data-colorblind. No UI on /learning; the
   switches stay on About. Styles: learning.css → "Viewing settings" (last section).
   - **Readability.** Body 17 → 19 px, line-height 1.55 → 1.8, letter-spacing .01em, darker
     --muted (#44524a light / #b4c2b9 dark), and every fixed-size text element one step up
     (readouts, labels, notes, captions, code, nav). Readout rows may wrap. Charts are untouched
     on purpose: SVG text scales with the viewBox, so nothing inside a plot changes.
   - **Colorblind.** Red/blue → orange/blue: --fit #b85000 / --fix #0072b2 (light), #ff9a4a /
     #63b3f0 (dark). Chosen with a Machado (2009) simulation: fit/fix stay ΔE ≥ 87 apart under
     protan, deutan and tritan vision, and the orange readout text keeps 4.6:1 on the paper
     background. Every red/blue distinction has a second cue from CSS alone: --fix lines and
     bars dotted (legend swatch too), .pt-hi points and .bar-hi bars with an ink ring, ✕ / ✓
     before .v.bad / .v.good, and a dotted underline on the two corner labels that name the
     corrected estimate (new class .lbl-fix: Module 3 "weighted", Module 6 "with correlation";
     they used to be .lbl-truth with an inline fill). The two colors share a luminance, so
     under achromatopsia the cues do all the work; that's intended.
   - **Dotted corrected line, always on** (same day, Gideon's call after seeing the mode). The
     dotted --fix treatment (lines, bars, legend swatch, .lbl-fix underline) moved out of the
     colorblind block into the base rules, so the two fits tell apart in grayscale for everyone;
     colorblind mode now adds only the tokens, the rings and the ✕ / ✓ marks. Also fixed on the
     way: `input[type=range] { margin-inline: 0 }` removes Chromium's default 2 px side margin
     that let every slider overhang its control column.
   - **Checked** with Playwright against Live Server: 7 pages × light / dark × readability /
     colorblind / both × 375 / 1280 px (84 loads): attributes and tokens applied, no console
     messages, no horizontal scroll, no readout label/value collision, sliders full width,
     charts in place. Chrome's vision-deficiency emulation (protanopia, deuteranopia,
     tritanopia, achromatopsia) over CDP on Module 3 (band misses, coverage bars, slope
     histograms), 4 (ACF bars, CI bars), 5 (OLS vs Deming lines, slope histogram), 6 (crossing
     bars, readout marks), 2 (with / without point, Cook bars) and 1 (LOO chart), with the
     mode off and on.
   - **Not covered.** The slide decks (Quarto) keep their own colors and ignore the settings.
16. **marimo "Play with the code" pilot** (2026-09-28, residual-plots only; the other five wait
   for Gideon's review). The module's Python as a marimo notebook (short markdown cells, marimo
   sliders for the page's knobs, the same figures), exported with `marimo export html-wasm
   --mode edit --single-file` to learning/fits/residual-plots/play/index.html by
   learning/workshop/tools/export-play.py,
   which also adds noindex, the trailing-slash fix, the title, and turns on cell auto-run
   (marimo 0.25 bakes it off and ignores config files), since marimo rewrites index.html on every
   export. Linked as "Play with the code" beside Slides / Python script (`takePlay`, ES "Juega
   con el código (en inglés)"); the link carries `data-http-only` and learning.js hides it when
   the page is opened from disk (the page needs a CDN, so the offline app can't run it).
   - **Packages.** numpy and matplotlib run under Pyodide. scipy runs too but is a 14 MB
     download, so the notebook fits the exponential with numpy alone (a plain sweep over τ,
     coarse then fine, written for beginners; matches `curve_fit` to three decimals). The module's .py script keeps `curve_fit`.
   - **Cost, measured 2026-09-28 (Chromium, fast home connection).** First load: about 37 MB,
     of which 22.6 MB Pyodide + wheels from cdn.jsdelivr.net (matplotlib 6.9, Pyodide core 3.5,
     numpy 2.9, stdlib 2.5, jedi/pygments/fonttools/pillow/docutils ~5), 11.5 MB of marimo's
     editor (from the site in the first export; from jsDelivr since `--single-file`), ~2.8 MB
     of marimo's own wheels from PyPI. All four figures drawn
     11–15 s after opening, on desktop and at 375 px. Warm reload (browser cache): ~7 MB, figures
     at ~10 s. With scipy it would be ~51 MB. Repo: play/ is one ~80 KB index.html. The first
     export was 481 files / 27 MB per module (marimo's whole editor bundle, of which a visitor
     fetches ~90 files); Gideon chose `--single-file` the same day, so the editor comes from
     jsDelivr, version-pinned, like Pyodide: the same download for the visitor, and nothing to
     bloat git history on a marimo upgrade.
   - **Compared with "Open in Colab".** Colab's open-from-GitHub link needs an .ipynb in a public
     GitHub repo (`marimo export ipynb notebook.py`, or one made from the .py), not a .py, so
     the lighter option is one .ipynb per module plus a badge link: nothing to host, nothing to
     download, but a Google login, no sliders (edit a value, rerun), and Colab's own load time.
     The marimo page gives sliders and instant edits at the price of ~37 MB and 10–15 s per
     first visit on a good connection; on a phone over cellular expect a minute or more.
   - **Known noise.** marimo's edit mode logs "Language server initialization failed" errors
     about 35 s after load (its in-browser language server times out); harmless. The Pyodide
     interrupt warning ("not running in a secure context") is because the page isn't
     cross-origin isolated; also harmless.
   - **Verify after deploy.** Open /learning/fits/residual-plots/play/ on the Vercel preview: the
     editor appears within ~5 s and four figures within ~15 s; try /play without the slash; view
     source for noindex. Vercel serves .wasm as application/wasm and needs no headers for this.
17. **Both ways to run the code, on every module** (2026-09-29). Gideon's call after the pilot:
   marimo for everyone who can afford the ~37 MB first load, Colab as the light option, and
   both links on every page. The five remaining marimo notebooks follow the pilot's style
   (decision 16); all six export as one small index.html (`--single-file`). The Colab
   notebooks are GENERATED from the companion scripts by learning/workshop/tools/make-ipynb.py
   (the scripts carry "# %%" cell markers and a knobs cell per trial; `--check` proves the
   cells print what the script prints) and live at learning/fits/<slug>/<slug>.ipynb, opened
   from GitHub, so the repo goes public (decision 18). Which link leads is decided by
   learning.js once at load: `data-lite` on <html> for a narrow or coarse-pointer screen,
   save-data, or 4 GB of device memory or less puts Colab first and primary; otherwise marimo.
   Both are always visible. `deviceMemory` is Chromium-only and coarse pointers include touch
   laptops; accepted as a one-shot rule.
18. **The repo goes public** (2026-09-29, in progress). Needed for the Colab links, and Gideon
   intended it anyway. Done before the flip: the ten cited-paper PDFs left the tree (2dc3a4b:
   untracked, gitignored, chips link DOIs), LICENSE (MIT, code) and LICENSE-CONTENT (CC BY-SA
   4.0, learning content) with a Licensing section in README.md that excludes personal
   material (ef7aa1a). Still to do, in order: the other session commits and the tree is clean;
   `git filter-repo` drops `learning/fits/*/*.pdf` from every commit (after a mirror backup);
   force push; GitHub → visibility public, secret scanning and push protection on, wiki off;
   Vercel: delete deployments older than 2dc3a4b (their URLs still serve the PDFs); then open
   every Colab link and Run all. Kept in history on purpose: scripts/transcript/*.json (the
   transcript PDF is public on the site) and the five `visible: false` experience entries.
17. **Spanish slides** (2026-09-29). Gideon chose one deck per language per module over a
   bilingual deck.
   - **Files.** `learning/workshop/modules/<slug>/slides.es.qmd` → rendered, `role="img"`
     stripped, copied to `learning/fits/<slug>/slides.es.html`. Same YAML as slides.qmd plus
     `lang: es` (Quarto's own UI words in Spanish); OG tags point at slides.es.html with the ES
     page lead and `og:locale` es_LA. The OG card image stays the English one, and its alt text says
     so. noindex as everywhere.
   - **Content.** Slide text and speaker notes follow decision 13 (tú, glossary, decimal commas,
     "orden de medición", "corrida" only for a whole repeat). Code stays English: the Module 2
     "make them yourself" block keeps English code and says so in its heading, with the Spanish
     Excel names (PENDIENTE, INTERSECCION.EJE) under it. Module 6's "what to write down" block
     is a report template, not code, so it's Spanish, matching the page's report text.
   - **Figures without touching the public scripts.** `workshop/tools/figures-es.py <slug>` runs
     `learning/fits/<slug>/<slug>.py` unchanged (same seeds, same data) and translates every
     drawn text through `modules/<slug>/figures-es.json`, keyed by the English text with numbers
     as `#`, with decimal commas. It sets the Spanish before tight_layout and saving, so the
     layout fits the Spanish, and it fails on any text missing from the table. Output goes to
     `figures-es/` (tracked, like figures/). This keeps decision 13's "the .py scripts stay
     English" while the decks get Spanish figures. Long Spanish was shortened in the table
     where it hit an edge (five labels/titles and one note).
   - **Link.** learning-i18n.js: on a `data-i18n` link, a `<key>Href` string also sets the href.
     `takeSlidesHref` (strings-common.js) is slides.html / slides.es.html, so the Slides link
     follows the language, live on a switch; the HTML keeps slides.html as the no-JS fallback.
     No index.html changed. Supersedes decision 13's "Diapositivas (en inglés)" label and the
     hub's "Por ahora, solo en inglés".
   - **The embedded interactive** in a Spanish deck follows the visitor's saved language, like
     the page itself: Spanish for anyone who chose ES (or whose browser is Spanish), English for a
     visitor whose saved choice is EN.
   - **Quarto 1.10.18** (installed 2026-09-28, with TinyTeX and Jupyter; QUARTO_PYTHON points at
     the pythoncore-3.14 Python). The English decks were re-rendered with it in the same pass so
     both languages come from one version: every English slide is pixel-identical to its 1.7.32
     render (a ~38-line diff per deck, Quarto's own CSS and generator tag).
   - **Checked.** Every slide of all 12 decks at 1280×720: nothing overflows the slide, every
     figure loads, console clean, the embedded interactive renders in the deck's language when
     that language is saved. The Slides link was checked on all six pages, EN and ES, before and
     after a language switch.
