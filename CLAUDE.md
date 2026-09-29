# Gideon A. Ong — Personal Website

## What this project is
Personal portfolio and career site for Gideon A. Ong, a Mechanical Engineering student at the University of Tulsa in the International Engineering and Language Program (5-year).
Expected degrees: Mechanical Engineering B.S.M.E. and Spanish B.A.; additional minors TBD.
Audience: engineering recruiters and hiring managers.
Domain: gideonong.me. See plan.md for the development roadmap.

## Stack
Plain HTML + CSS + vanilla JavaScript. No frameworks, no build tools, no npm.
External resources: Google Fonts only (Lora + DM Sans).
/learning is the one exception: it also loads Barlow Semi Condensed, Source Serif 4 and
JetBrains Mono (see /learning below).

## File structure
index.html          Home page
about.html          About / education / skills / honors / languages
experience.html     Work experience and research roles
projects.html       Technical projects with photos, tags, descriptions
projects/<slug>.html  One tiny shell per project sub-page (body data-slug + data-root="../")
css/style.css       All styles (single file, organized by section)
js/chips.js         The one phrase auto-linker (IEL, Zohaib Sheikh, …) — see Phrase chips
js/site-config.js   Author-side switches (home featured side-by-side flag); index.html only
js/main.js          Nav behavior, language toggle, document links
js/translations.js  All EN and ES text strings for the bilingual toggle (plain text, no HTML)
js/tags-data.js     The one shared tag vocabulary (id + i18n key)
js/projects-data.js Project entries (feeds projects.html and the home featured block)
js/experience-data.js  Experience entries (feeds experience.html)
js/data-helpers.js  Shared selectors, builders, date formatter, deep-link targeting, dev data check
js/projects.js      projects.html renderer: featured, index, ?tag= filter, search
js/project-page.js  projects/<slug>.html renderer (one renderer for every sub-page)
js/experience.js    experience.html renderer: bands + related projects
js/home.js          index.html featured block renderer
js/about.js         about.html behaviors
js/docs-data.js     GENERATED documents manifest (see Documents below) — never edit by hand
scripts/build-docs-manifest.js  Dev-side generator for js/docs-data.js (Node built-ins only)
scripts/transcript/  Dev-side transcript PDF generator (Python; see its README) — never deployed
scripts/editor/      Dev-side local content editor (Python/Flask + vanilla-JS pages; see its
                     README and staging/editor-plan.md) — never deployed. Phase 1 edits
                     js/translations.js in place, losslessly. Phase 1b (core/cv/) checks and
                     publishes the CV/résumé PDFs from staging/cv-masters/ into assets/pdfs/
                     (export through a private Word instance; one-line fit, one-page résumé,
                     blocklist scans; never edits a master). Phase 3 (core/transcript/) runs
                     scripts/transcript/ as subprocesses, edits its JSON inputs losslessly,
                     builds PDFs into staging/transcript-out/ and publishes them. Phase 2
                     (core/site/, core/spans.py) edits projects-data.js, experience-data.js,
                     tags-data.js and the matching translations keys in place with span edits
                     (keys named by the conventions below, never shown), creates/deletes
                     projects/<slug>.html shells, and gates saves with a Python port of
                     siteData.checkData (core/site/datacheck.py — keep the two in step). Its .local/
                     (backups, logs, drafts, WebView2 storage) is gitignored. It never runs
                     git write commands.
.githooks/pre-commit  Runs the generator and stages the manifest on every commit
assets/images/      Project photos and diagrams
assets/pdfs/        resume/, cv/, transcript/ — dated PDFs (see Documents below)
assets/videos/      Project video clips
learning/           UNLISTED Learning section (own design, noindex) — see /learning below and
                    learning/README.md. Linked only from About → Interesting sites.
learning/assets/    Shared CSS/JS for /learning (learning.css, learning.js, learning-i18n.js,
                    strings-common.js, modules.js) and og/ (link-preview cards, generated)
learning/learning-plan.md  Roadmap, status and decisions for /learning (dev-only, not deployed)
learning/fits/<slug>/  One "Reading Your Fits" module: index.html, strings.js, main.js,
                    slides.html, slides.es.html, <slug>.py (papers are never hosted: chips
                    link DOIs)
CLAUDE.md           This file
plan.md             Development roadmap
README.md           Public front page of the repo (what it is, layout, licensing)
LICENSE             MIT, for the code
LICENSE-CONTENT     CC BY-SA 4.0, for the teaching content under learning/ (personal material
                    is not licensed; README.md lists it)

================================================================================
PALETTE LIBRARY
All four palettes are documented here for experimentation. To activate a palette,
copy its token values into the :root block at the top of css/style.css.
The navbar is WHITE (#FFFFFF) in all palettes — never change that.
The footer is dark in all palettes (see individual footer-bg values).
================================================================================

## PALETTE A — Oenothera
Inspired by Oenothera speciosa (Texas Evening Primrose), Gideon's favorite flower.
Stamen gold → deep bronze primary. Mid petal desaturated → rose-gold on contact element only. Page bg is neutral white with no visible pink tint. Images take center stage; the palette stays out of their way. All section backgrounds are warm-neutral, not pink.

--bg:           #FAFAF8    neutral off-white (no visible pink tint — images breathe here)
--bg-section:   #EDE7E4    warm neutral (featured work and alternate sections — not pink)
--nav-bg:       #FFFFFF    white
--ink:          #1C1810    warm near-black
--muted:        #6E6560    warm neutral grey
--bronze:       #714A14    deep rich bronze (primary accent)
--bronze-mid:   #9B7340    lighter bronze (hover states, tag borders)
--rose:         #B87A7A    muted rose-gold (ONLY on "say hello" email chip — nowhere else)
--rose-light:   #E8D0D4    very soft rose (border on "say hello" chip only)
--border:       #DDD5C8    warm neutral divider
--footer-bg:    #1C1510    very dark warm near-black
--footer-text:  #D4C9BB    warm light text on footer
--search-bg:    #E1D7CF    projects.html search band (bronze ≈10% over bg-section)

## PALETTE B — Warm Neutral (CURRENT ACTIVE)
The original warm brass direction. Warmer and more golden than A, with a more noticeably cream-tinted background. Good if the site feels too cold or clinical.

--bg:           #FAFAF8    barely warm off-white
--bg-section:   #EDE6D5    warm parchment-tan (alternate sections)
--nav-bg:       #FFFFFF    white
--ink:          #1A1A17    warm near-black
--muted:        #6B6963    warm grey
--bronze:       #6B4F1A    brass-gold (slightly warmer/brighter than Palette A)
--bronze-mid:   #9B7340    lighter brass
--rose:         (not used in this palette)
--border:       #DDD5C8    warm neutral divider
--footer-bg:    #1A1510    dark warm
--footer-text:  #D4C9BB    warm light text
--search-bg:    #E0D7C2    projects.html search band (bronze ≈10% over bg-section; dark #32291A)

## PALETTE C — Bluebonnet
Inspired by Lupinus texensis (Texas state flower). Cool blue accent.
Professional, calm, distinctive. Very different from AI warm-cream default.
Good if the site should feel more technical, precise, and engineering-forward.

--bg:           #F5F7FC    very light blue-tinted white
--bg-section:   #EBF0FA    light blue-tint (alternate sections)
--nav-bg:       #FFFFFF    white
--ink:          #1A1F2E    cool near-black (blue undertone)
--muted:        #5A6880    cool grey-blue
--blue:         #2E4D7B    deep bluebonnet blue (primary accent)
--blue-mid:     #5A7AAB    lighter blue (hover states)
--border:       #D4D8E4    cool blue-grey divider
--footer-bg:    #1A1F2E    dark blue-charcoal
--footer-text:  #C8D4E4    cool light text
--search-bg:    #D8E0ED    projects.html search band (blue ≈10% over bg-section)

## PALETTE D — Winecup Prairie
Inspired by Callirhoe involucrata (Texas Winecup). Warm rose-burgundy primary, sage green secondary. The most botanical and personal of the four. Good if the site should feel warmer and more openly personal/expressive.

--bg:           #FAF6F5    very light rose-tinted white
--bg-section:   #F0E8E5    warm rose-tint (alternate sections)
--nav-bg:       #FFFFFF    white
--ink:          #1A1018    warm near-black (slight rose undertone)
--muted:        #7A5868    rose-warm grey
--wine:         #7A3050    deep rose-burgundy (primary accent)
--wine-mid:     #A86070    lighter wine (hover states)
--sage:         #5C7A56    sage green (secondary accent — optional, use sparingly)
--border:       #DDD0CE    warm rose-tinted divider
--footer-bg:    #1A1018    dark rose-near-black
--footer-text:  #D8C8C4    warm rose-light text
--search-bg:    #E4D6D6    projects.html search band (wine ≈10% over bg-section)

================================================================================
DESIGN TOKENS IN USE (copy from active palette above into style.css)
================================================================================

## Site-wide elements

### Navigation bar (sticky, always fully opaque white)
- Background: #FFFFFF at all times, all scroll positions — never transparent
- Logo: "Gideon A. Ong" (left), Lora serif ~17px, near-black
  Middle initial is intentional — do not remove
- Nav links order (right): Projects · Experience · About ("About" always rightmost)
  Link color: #4A4945, hover to near-black
- EN/ES language toggle: rightmost, after nav links
  Active: dark fill (#1C1810 bg). Inactive: muted text.

### "Under development" banner
Thin bar (~32px) directly below navbar. Background: #8B3A2A. Text: near-white.
Easy to show/hide via a single CSS class or display property.

### Footer (dark, full-width)
See active palette for --footer-bg and --footer-text values.
Contents: resume download button (bronze/accent border), contact links, copyright.
"Download Resume" opens the newest resume PDF (from js/docs-data.js) in a new tab.

### Documents (resume / CV / transcript)
- Buttons opt in with data-doc-link="resume" | "cv" | "transcript". js/main.js resolves
  the href from the generated manifest js/docs-data.js (const DOCS): active language →
  the other language → the element's existing href. A type with no file in any language
  gets its buttons hidden (hidden attribute). No network requests, no localStorage.
- To publish a new document: drop a dated PDF into assets/pdfs/<type>/ and commit. The
  pre-commit hook regenerates and stages js/docs-data.js. Filenames must match
    "<en|es> Gideon Ong Resume <YYYYMMDD>.pdf"   (assets/pdfs/resume/)
    "<en|es> Gideon Ong CV <YYYYMMDD>.pdf"       (assets/pdfs/cv/)
    "<en|es> Gideon Ong Transcript <YYYYMMDD>.pdf" (assets/pdfs/transcript/)
  Anything else is ignored with a warning. Transcript PDFs are generated by
  scripts/transcript/ (Python, dev-only, see scripts/transcript/README.md); its .docx
  scratch output (scripts/transcript/output/) is gitignored. To preview before committing:
    node scripts/build-docs-manifest.js
- One-time setup per clone (the hook lives in the repo, but git must be pointed at it):
    git config core.hooksPath .githooks
  If node is not on PATH the hook prints a warning and the commit still goes through;
  run the script by hand afterwards.
- This is dev-side tooling, not a site build step: the site still deploys as plain
  static files, and js/docs-data.js is committed like any other file.
- Dev files are excluded from deploys by .vercelignore (*.md, scripts/, .githooks/,
  .gitattributes, references/, staging/). Add any new dev-only path there.
- about.html's resume → CV + transcript morph (js/about.js), by what the manifest holds:
  both CV and transcript → resume morphs into CV + Transcript; exactly one → resume morphs
  into Resume + that document (a clone of the resume button fills the top slot); neither →
  no morph, the resume button stays static.

### Experience hero (2026-09-27)
A solid `--footer-bg` text panel (min(540px, 52%) wide) and three captioned photo tiles
that start where the panel ends — nothing sits under the text, so there is no scrim.
Height min(80vh, 640px). Desktop: tile 1 (scanner-fixture) tall, tiles 2–3 (lathe, eagle)
stacked, 4px gap; captions in a dark translucent bar along each tile's bottom
(`expHeroTile<N>Cap`), alts `expHeroTile<N>Alt`. Under 768px: text first, tiles stacked
below at 4:3, captions still shown. Images live in assets/images/experience/hero/.

### About page — hidden sections (career fair, 2026-09-27)
§3 books (`#about-reading`), §4 FAQ (`#about-faq`) and the interesting-sites block of §6
(`#about-sites`) carry the `hidden` attribute in about.html. That attribute is the ONE
flag: remove it to show the block again. js/about.js skips each block's setup while it is
hidden (no scroll runway, no FAQ items), and .section-settings uses an auto-fit grid so
the settings panel takes the full row on its own. The AI statement and viewing settings
stay. The headshot is a plain `<img src="assets/images/about/headshot.jpg"
data-i18n-alt="headshotAlt">` in about.html — swap the file or the src there.

## Home page (index.html) structure
1. Sticky white navbar
2. Under-development banner (easily removable)
3. Hero section (var(--bg)):
   a. Name: "Gideon A. Ong" — large Lora serif. No subtitle or label above it.
   b. Thin horizontal rule (~40px wide, 2px, color: primary accent)
   c. Description (English, primary): capabilities-focused — research experience,
      adaptability, automation/fabrication/ML skills. NOT a list of majors/degrees.
   d. Same description in Spanish (inactive): Lora italic, ~13px, var(--muted), below.
      On language switch: Spanish becomes primary; English drops to italic/small/muted.
   e. Social link row — small bordered chips, icon + username (tonsky.me-inspired):
        ORDER: [LinkedIn] gideon-a-ong   [GitHub] gidgo130   [✉] say hello
   f. "Download resume" button — primary accent border and text, border-radius: 2px
4. Featured work section (image-forward, eater.net-inspired):
   Background: var(--bg-section). Top border: 1px solid var(--border).
   "Featured work" is an <h2 class="list-heading"> — Lora 600, clamp(1.5rem, 1.2rem + 1.2vw,
   2rem), left on the column edge — the same element and size as "Featured projects" /
   "All projects" on projects.html. (.section-heading, 15px, is for small panel labels only.)
   The column is centered (margin-inline: auto) at the projects.html index width (1000px,
   1120px at 1440+), heading aligned to it.
   Wide-screen option: js/site-config.js → `homeFeaturedSideBySide: true` lays the entries
   out side by side at ≥1200px (image one side, text the other, alternating; a collage
   keeps its grid in the image column) and stacks them below 1200px. Default OFF. That flag
   is the only switch; no data or markup changes.
   Rendered by js/home.js from js/projects-data.js (featured: true, listing: "index")
   with the same builders and markup as projects.html §2: image, title,
   "<Context> · <dates>" meta, description, tags below description (not above),
   "Part of: <role>, <org> →" when linked to a role, "View project →" link.
   No project copy lives in index.html. 1-5 projects, dynamic over time.
   Layout is a per-project preset, `homeLayout` (index.html only — projects.html §2
   keeps its alternating layout and ignores it):
     "stacked"    DEFAULT — full-width 16:9 image (object-fit: cover), text below
     "imageLeft"  image ~55% left, text right (the projects.html §2 style)
     "imageRight" text left, image right
     "collage"    full-width 16:9 grid of the `gallery` images (2–4; imageSrc is NOT a
                  cell): 2 → two equal columns; 3 → first cell large left (2/3), two
                  stacked right; 4 → 2×2. Below 768px: 2 side by side, 3 large on top +
                  two below, 4 → 2×2. Every cell object-fit: cover, alt from its altKey.
   Fallbacks, never an error: collage with fewer than 2 gallery items → stacked; no
   imageSrc → text only.
5. Footer (dark)

## Bilingual support (EN/ES)
- ALL display text via translations.js — use data-i18n="key" on elements
- Language toggle: instant DOM swap, no reload, scroll position preserved exactly
- Active language: normal size/color. Inactive: Lora italic, ~13px, muted, below.
- Both EN + ES versions always present in hero, swapping primary/secondary roles.
- Default on first visit: navigator.language → Spanish-locale (or lusophone) → ES. Else: EN.
- Store user choice in localStorage. Spanish can run ~20% (read: a little bit) longer — no fixed widths.
- Exception: button/pill/chip labels (nav, tag filters, toggles) should stay close in
  character length between EN and ES so the element doesn't visibly resize when the language
  toggles. Prefer a shorter, still-natural ES synonym over a literal translation when the
  literal one runs much longer. This only applies to compact fixed-shape UI elements, not
  body/paragraph text.
- The resume button is a deliberate exception to that rule: ES is "Descargar Currículum",
  not "Descargar CV". Gideon's call — the full word is what he wants on the button, and the
  footer/hero layouts absorb the extra width. Do not "shorten" it back to CV.

## Projects (projects.html)
- Clickable tags, no filter row (2026-09-27): every tag pill anywhere on the site (index
  rows, featured entries, experience bands, sub-pages) is a link to
  `projects.html?tag=<id>`. projects.html reads `?tag=` on load, filters the index (AND with
  the search), and shows a "<Tag label> ✕" chip beside the count; ✕ clears it and rewrites
  the URL with history.replaceState. One tag at a time. Unknown id → ignored. A language
  switch keeps it. A `#<slug>` deep link clears it. Pills: pointer cursor ONLY — no hover
  effect, no enlarged tap target (the global a:hover bronze is cancelled on .tag-pill).
  A pill click on projects.html itself is a plain link (page reloads).
- Role filter (2026-09-27): `projects.html?part=<experience slug>` works the same way — its
  own chip beside the count showing the role's short org name + ✕ (aria-label
  `projPartClear`), ANDed with the tag filter and the search, unknown or hidden slugs
  ignored, `#<slug>` clears both filters. The Baker Hughes band image links here.
- Keyword search band (§1): live, debounced, AND over whitespace tokens, diacritic-
  insensitive, both languages indexed. Combines with the tag filter (AND). Only the
  index is filtered; featured is not — instead the whole featured section COLLAPSES
  (`.is-collapsed`, aria-hidden) while any filter is active (search text, ?tag=, ?part=),
  so results sit directly under the search band, and returns when all are cleared. The ×
  inside the field (bordered chip, shown only with text) clears the query.
- Tag pills placed BELOW description text, not above the title
- Unlinked pages: exist at a URL, not listed in nav or project list
  (for politically-sensitive or selectively shared work) — `listing: "unlisted"` in
  js/projects-data.js. List filenames here as sub-pages are added.
- Sub-pages (projects/<slug>.html): see "Project sub-pages" under Data conventions.
  Files today: projects/pump-cylinder-failure.html, eagle-pathway.html, g-view.html.

## Data conventions
Data files: js/tags-data.js, js/projects-data.js, js/experience-data.js. Read-side
helpers in js/data-helpers.js. Array order never matters — everything sorts by `sortDate`
("YYYY-MM") descending; `pinned: true` lifts a project to the top of the index.

- Listing tiers (`listing` on every project):
    "index"    — in the §3 index, the tag filter, search, and its role's "Projects from
                 this role" list; may be `featured` (max 3). Optional `featuredOrder`
                 (number) orders the featured blocks; entries without it follow by sortDate.
                 `longDescKey` (the featured-card paragraph) is required only when featured.
    "unlisted" — direct URL only; excluded from index, bands, filter, featured, search
    "hidden"   — excluded everywhere
    "nested"   — RESERVED, not implemented. Intended for role-bound minor projects shown
                 on their band and surfaced in the index only under an active filter or
                 search. An entry set to it does not render and the dev check warns.
                 Build trigger: the index passes ~30 rows, or 4+ minor role-bound items
                 exist. Experience entries keep a `visible` boolean.
- Two-way project ↔ experience links come from ONE field: project `experience` holds an
  experience `slug` (or ""). Project → role: "Part of: <org short> →" (key projPartOf, {org}
  = the role's `orgShortKey`, falling back to `orgKey`) below the tags, to
  experience.html#<slug>. `orgKey` is the full string shown on the band and in the hero
  status ("McElroy Prototyping Lab, University of Tulsa"); `orgShortKey` the short form
  ("McElroy Prototyping Lab"). Experience entries with an image also carry `imageAltKey`. Role → projects: the band lists every
  listing:"index" project pointing at it (key expRelatedHeading), titles linking to
  projects.html#<slug>. Index rows and bands carry id="<slug>"; a matching location.hash
  clears filter/query, scrolls clear of the nav, and adds `.is-target` (static bronze
  left rule). Only a visible role is a valid link target.
- Tags are IDS from js/tags-data.js (`{ id, key }`); pills show the translated label and
  link to projects.html?tag=<id>; the filter state is the id in the URL. Never store a
  label in a data file.
- `context` on every project: industry | coursework | personal | service | research —
  rendered as "<Context> · <dates>" (keys ctxIndustry …).
- Dates (2026-09-27): `dates` on projects AND experience entries is language-neutral,
  never a literal string. Shape: `{ from: <point> }`, `{ from, to: "present" }`, or
  `{ from, to: <point> }`, where a point is `{ season: "spring"|"summer"|"fall"|"winter",
  year }`, `{ month: 1–12, year }` or `{ year }`. Rendered per language by
  siteData.formatDates via keys dateSpring…dateWinter, dateMonth1…12, datePresent,
  dateSeasonYear ("{season} {year}"), dateMonthYear (EN "{month} {year}", ES
  "{month} de {year}"), dateRange ("{from} – {to}"). Seasons capitalized in both
  languages; ES month names lowercase. `sortDate` stays the only ordering input; the dev
  check flags a sortDate that disagrees with the dates (against `to` when it is a point,
  else `from`: year must match, a month must match, a season must contain the month).
- Home featured presets: optional `homeLayout` ("stacked" default | "imageLeft" |
  "imageRight" | "collage") and, for collage only, `gallery: [{ src, altKey }]` — the 2–4
  collage cells themselves (imageSrc is not one). Ignored by projects.html §2. Gallery alt
  keys: proj<SlugCamel>Gallery<N>Alt.
- Thumbnails (2026-09-27): optional `thumbSrc` + `thumbAltKey` on a project. Index rows use
  them and fall back to imageSrc / imageAlt; featured blocks and sub-pages always use
  imageSrc.
- Image links (2026-09-27): a project's thumbnail / featured image / collage links to its
  `subpageUrl` when one exists (else plain); a band image links to the experience entry's
  optional `imageLink` (site-root-relative, e.g. "projects.html?part=baker-hughes" or
  "projects/pump-cylinder-failure.html"; absent → plain). See the animation exception.
- Project sub-pages (2026-09-27): one renderer, js/project-page.js, plus one shell per page
  at projects/<slug>.html whose <body> carries `data-slug="<slug>"` and `data-root="../"`.
  The shell has the same nav / dev banner / footer / toggle as every page with `../` paths,
  a static English <title> + meta description (replaced from the entry on every render),
  and an empty `<main id="project-page">`. `data-root` is read by main.js (document links)
  and data-helpers.js (images, tag links, "Part of" links), so the shared builders work
  from /projects/. Optional `page` object on the entry:
    page: { sections: [{ headingKey, bodyKey }], facts: [{ labelKey, valueKey }],
            photos: [{ src, altKey }], reportPdf: "", creditKey: "" }
  Layout: hero image (imageSrc, 16:9) → title → "<Context> · <dates>" → "Part of" link →
  sections → photo grid (2-up, 1-up below 768px) → quick-facts box → "Read the report →"
  (new tab) → credit → tags → "← All projects".
  Lightbox (2026-09-27): clicking a photo opens it in a native <dialog class="lightbox">
  (image ≤ 92vw × 88vh, caption = alt text, ✕ with `projLightboxClose`, prev/next with
  `projLightboxPrev` / `projLightboxNext`, ← → keys, Esc and backdrop click close, page
  scroll locked, focus returns to the photo, opacity-only fade). The anchor keeps its href
  as the no-JS fallback (new tab). No libraries.
  Any missing piece renders nothing. `gallery` stays collage-only; sub-page photos use
  page.photos. `subpageUrl` = "/projects/<slug>.html" once the file exists, else "" (link
  omitted). Listing: index + unlisted entries render for everyone; a hidden entry renders
  only on localhost. Keys: proj<SlugCamel>Section<N>Heading / Section<N>Body /
  Fact<N>Label / Fact<N>Value / Photo<N>Alt / Credit.
- Phrase chips (2026-09-27): js/chips.js holds ONE table `CHIPS = [{ phrase, urls: { en,
  es } }]` (Zohaib Sheikh → zohaibsheikh.dev, IEL → the IEL URLs, "automating the boring
  stuff" / "automatizar lo aburrido"). `siteChips.fill(el, text, lang)` builds text nodes +
  `<a class="iel-chip">` — never innerHTML. Whole-word matches, first occurrence per
  phrase per element, headings / links / buttons (and anything inside a link or button)
  get plain text, idempotent across language switches. main.js runs it on every data-i18n
  element and both hero paragraphs; the builders run it on descriptions, bullets, section
  bodies, fact values and credits. translations.js therefore holds NO HTML (the old
  HTML_I18N_KEYS / HERO_CHIPS in main.js are gone). Adding a phrase = one line in CHIPS.
- Key naming by slug: proj<SlugCamel>Title / Desc / LongDesc / Alt / Search / Gallery<N>Alt
  / Section<N>Heading / Section<N>Body / Fact<N>Label / Fact<N>Value / Photo<N>Alt / Credit
  (slug "todo-project-1" → projTodoProject1Title); exp<SlugCamel>Role / Org / Bullet1…;
  tag<IdCamel>; ctx<Context>. translations.js is the single source of display strings.
- searchEntries(query, entries) → entries in js/projects.js is the ONE place matching
  happens. Phase 3 (TF-IDF) replaces its body only — same signature, same return shape,
  may reorder by score; no markup or caller changes.
- Dev data check (siteData.checkData, console.warn only) runs on load of projects.html,
  experience.html and every sub-page — on LOCALHOST ONLY (siteData.isDev: localhost,
  127.0.0.1, ::1, file:), so real visitors never get its HEAD probes. Checks: unknown tag
  id, missing EN/ES key, duplicate slug, bad `experience` target, featured on non-index,
  >3 featured, imageSrc without imageAlt, missing sortDate/context, malformed `dates` or a
  sortDate that disagrees with them, reserved "nested", unknown homeLayout, gallery
  problems (on a non-collage entry, >3 items, item missing src/altKey, altKey with no
  EN/ES string), `page` problems (bad shape, missing keys, page set with subpageUrl ""),
  one HEAD per js/docs-data.js path and one HEAD per non-empty subpageUrl that returns
  non-2xx. Keep the console clean. (Live Server answers HEAD with a body; Chromium logs
  those as aborted network requests, not console messages — ignore them.) The local editor
  (scripts/editor/core/site/datacheck.py) ports this list to Python and blocks a save on the
  error-level items; when a rule is added here, add it there too (and vice versa).

## Animation and scroll behavior
- NO page-load animations — no rising text, no fading on arrival
- Scroll-triggered fades only: IntersectionObserver, opacity 0→1, ~300ms, no movement
- Hover: color transitions only, ~150ms ease
- DELIBERATE EXCEPTION (2026-09-27): images that link somewhere (index thumbnails,
  featured images and collages → their sub-page; band images → `imageLink`) are wrapped in
  `<a class="image-link">`, a clipped frame in which the image scales to 1.03 on hover and
  :focus-visible, 250ms ease, pointer cursor. Images with no destination are never wrapped
  and never move. Off under prefers-reduced-motion. Nothing else may scale or move.
- The sub-page lightbox fades in with opacity only (200ms); no other motion.
- SECOND EXCEPTION (2026-09-27, may revert): on projects.html the featured section
  collapses — grid row 1fr → 0fr plus padding, with an opacity fade — over 300ms while any
  filter is active, and expands the same way when cleared. Gideon chose the animated
  collapse over fade-then-instant "for now"; to revert, drop grid-template-rows / padding /
  border-top-width from the two `.featured-projects` transitions in style.css. Off under
  prefers-reduced-motion. The section starts with `.is-settling` (transitions off) and
  js/projects.js removes it one frame after the first render, so a page opened already
  filtered never animates on load.
- Sticky nav: position: sticky, always opaque

## Mobile / responsive (Phase 2)
- Primary breakpoint: 768px
- Below 768px: .nav-links hidden; hamburger (☰) appears between logo area and the EN/ES toggle.
  EN/ES toggle is always the rightmost element on the navbar at every breakpoint.
- Hamburger opens a dropdown panel that appears fixed below the navbar (top: 56px).
  Dropdown closes on link tap, outside click, or Escape.
  Full-screen overlay is an option to consider if the dropdown feels too small on certain devices.
- NEVER use fixed pixel widths on layout containers — always max-width + width: 100%
- Test at 375px (iPhone SE), 768px (iPad), 1280px (desktop)

## Wide-screen scaling (1440px+)
- @media (min-width: 1440px) block in style.css bumps up body, nav link, chip, and
  hero text sizes. Hero layout and proportions stay identical — only text grows.
- Hero name uses clamp(46px, 3.5vw, 72px) at 1440px+.

## Dark mode
- Dark mode IS supported via @media (prefers-color-scheme: dark) in style.css.
- Light mode is the primary design target; dark mode matches the warm palette feel
  but is not expected to look equally polished.
- Palette B (Warm Neutral) has a corresponding dark token block already in style.css.
  When switching active palettes, add a dark-mode :root block for the new palette too.
- Do NOT add a manual dark/light toggle button to the UI.
- Hardcoded hex colors (e.g. #4A4945) must be overridden in the dark-mode block;
  prefer using CSS vars to avoid this need in future additions.
- IEL chip: uses rgba(0,0,0,0.06) in light mode; rgba(255,255,255,0.10) in dark.

## /learning — Learning section (EXCEPTION to main-site styling, 2026-09-28)
gideonong.me/learning/ hosts interactive teaching pages, starting with the series "Reading
Your Fits" (how to check a line fit against lab data). Build plan, status and decisions:
learning/learning-plan.md (plan.md only points there). Working manual (structure, strings,
adding a module, checks, Fable review prompt): learning/README.md. Slide sources, figures and dev tools live in
learning/workshop/ (tracked in git, never deployed: listed in .vercelignore); the site loads only
the rendered slides.html copied into learning/fits/<slug>/.

Rules for /learning (these replace the main-site rules where they conflict):
- Own design, deliberately different from the main site: the "lab notebook" look in
  learning/assets/learning.css. Fonts Barlow Semi Condensed (display), Source Serif 4 (body),
  JetBrains Mono (numbers). Uppercase eyebrows and "Trial 1 of 4" / module numbers ARE allowed
  here because they mark a real sequence. No main-site navbar, banner or footer; each page has
  the thin series bar (gideonong.me / Learning / series) and prev / all / next links.
- Color meaning is fixed across every module: dashed ink = the truth, solid red (--fit) = what
  an ordinary fit reports, dotted blue (--fix) = a corrected estimate, grey dots = measured
  points. The dots on --fix (.fix, .fix-curve, .ci-bar-fix, the .sw.fix legend swatch, the
  dotted underline on a .lbl-fix label) are a permanent second cue, so the two fits tell apart
  in grayscale (decided 2026-09-28).
  Red may also mark a miss or a flag (a reading outside a band, a range that misses the
  truth, a readout that fails its check); when it does, the caption says so.
  Colorblind mode (`data-colorblind` on <html>, see the viewing-settings bullet) swaps the pair
  for orange / blue (--fit #b85000, --fix #0072b2; dark #ff9a4a / #63b3f0) and learning.css adds
  a non-color cue to the red/grey distinctions: highlighted or missed points (.pt-hi) and
  flagged bars (.bar-hi) wear an ink ring; .v.bad readouts are marked ✕ and .v.good ✓ besides
  bold. New charts must reuse those class names so the cues apply without touching JS.
- Unlisted: NOT in the main nav, sitemap or project list. The only link in is the Learning
  entry in about.html's Interesting sites (js/about.js `interestingSites`, `internal: true` =
  same tab); that block is `hidden` for now, so the link shows once `hidden` is removed.
- noindex, permanently: every /learning page (and each deck, via `include-in-header` in
  slides.qmd) has `<meta name="robots" content="noindex">`. Do not remove it: /learning is
  reached by link, not by search (learning-plan.md Phase C, 2026-09-28). Do not use robots.txt.
- Link previews: every page and deck carries static Open Graph + Twitter-card meta (title and
  lead in EN, absolute og:url, og:image = learning/assets/og/<slug>.png, 1200×630, made by
  learning/workshop/tools/make-og-cards.py). Scrapers don't run JS, so they stay in the HTML.
- Bilingual is REQUIRED; English ships first. All display text lives in strings files
  (learning/assets/strings-common.js + each page's strings.js), never hard-coded in JS.
  learning-i18n.js shares the main site's localStorage "lang" key and default rule. The EN/ES
  toggle is in every page's series bar but stays hidden, and the page renders EN, until that
  page's `<html>` gets `data-es-ready` (after its `es` strings are complete). Keys ending in
  "Html" may hold <b>/<i>/<code> (the translations.js no-HTML rule does not apply here).
  Numbers go through LF.num so ES gets a decimal comma.
- Viewing settings follow the main site's saved choices (About → Viewing settings) through the
  head snippet on every page, with the same localStorage keys and <html> attributes as
  js/about.js §6: `viewTheme` → data-theme (else prefers-color-scheme), `viewReadability` → data-
  readability, `viewColorblind` → data-colorblind. learning.css styles all three (section
  "Viewing settings" at the end). Readability enlarges page text only; SVG charts scale with
  their viewBox and are left alone. No settings UI or toggle on /learning pages.
- Module registry: learning/assets/modules.js is the ONE list (order, slug, ready). Titles and
  descriptions: mod<Key>Title / mod<Key>Desc in strings-common.js. URLs use slugs, never
  numbers, so reordering never breaks links.
- Relative links only, so pages work on the site, on previews and from disk (offline app).
  Each page's head adds the trailing slash to folder URLs; LF.fixFileLinks points folder links
  at index.html when opened from disk.
- Simulated data only; each page states its true model.
- Cited papers: a quiet `a.ref-chip` via the page's `chips` table in strings.js (see
  learning/README.md). Never host a paper in the repo or on the site: link its DOI, the
  publisher's page, or a catalog page for a book. Sources stay in the gitignored references/.
  No author byline on module decks.
- Motion: slider-driven redraws only. No page-load or scroll animation.
- Files outside learning/ that /learning touches: js/about.js (the Interesting-sites entry)
  and these docs. Anything else outside learning/ needs Gideon's OK first.

## What NOT to do
(Main site. /learning follows its own rules in the section above.)
- Do not make navbar anything other than white (#FFFFFF) in light mode
  (dark mode overrides --nav-bg to a dark warm background, which is expected)
- Do not hardcode display text in HTML — use data-i18n attributes
- Do not put HTML in translations.js — links come from the js/chips.js phrase table
- Two heading classes, two jobs: `.list-heading` (clamp(1.5rem, 1.2rem + 1.2vw, 2rem)) tops a
  list of entries (home featured, projects §2 / §3); `.section-heading` (15px) labels a small
  panel (About). Do not use one for the other's job.
- Do not store `dates` as a literal string — use the { from, to } shape so it translates
- Do not animate on page load or cause layout shift
- Do not use dark mode toggle
- Do not use fixed pixel widths on containers
- Do not use ALL CAPS section labels or numbered decorators (01, 02, 03)
- Do not put tag pills above the project title
- Do not use rose/--rose on structural elements — it belongs only on "say hello" chip
- Do not add npm packages, build steps, or frameworks without explicit instruction
- Do not make section backgrounds compete visually with project images
