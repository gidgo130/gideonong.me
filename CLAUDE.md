# Gideon A. Ong — Personal Website

## What this project is
Personal portfolio and career site for Gideon A. Ong, a Mechanical Engineering student at the University of Tulsa in the International Engineering and Language Program (5-year).
Expected degrees: Mechanical Engineering B.S.M.E. and Spanish B.A.; additional minors TBD.
Audience: engineering recruiters and hiring managers.
Domain: gideonong.me. See plan.md for the development roadmap.

## Stack
Plain HTML + CSS + vanilla JavaScript. No frameworks, no build tools, no npm.
External resources: Google Fonts only (Lora + DM Sans).

## File structure
index.html          Home page
about.html          About / education / skills / honors / languages
experience.html     Work experience and research roles
projects.html       Technical projects with photos, tags, descriptions
css/style.css       All styles (single file, organized by section)
js/main.js          Nav behavior, language toggle, scroll interactions
js/translations.js  All EN and ES text strings for the bilingual toggle
js/tags-data.js     The one shared tag vocabulary (id + i18n key)
js/projects-data.js Project entries (feeds projects.html and the home featured block)
js/experience-data.js  Experience entries (feeds experience.html)
js/data-helpers.js  Shared selectors, builders, deep-link targeting, dev data check
js/projects.js      projects.html renderer: featured, index, tag filter, search
js/experience.js    experience.html renderer: bands + related projects
js/home.js          index.html featured block renderer
js/about.js         about.html behaviors
assets/images/      Project photos and diagrams
assets/pdfs/        Resume and project reports (resume.pdf goes here)
assets/videos/      Project video clips
CLAUDE.md           This file
plan.md             Development roadmap

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
"Download Resume" opens assets/pdfs/resume.pdf in a new tab.

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
   "Featured work" as a readable section heading (~15px Lora, near-black)
   Rendered by js/home.js from js/projects-data.js (featured: true, listing: "index")
   with the same builders and markup as projects.html §2: 16:9 image as the anchor,
   title, "<Context> · <dates>" meta, description, tags below description (not
   above), "Part of: <role>, <org> →" when linked to a role, "View project →" link.
   No project copy lives in index.html. 1-5 projects, dynamic over time.
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
- Dynamic tag filter: clicking a tag filters visible projects (vanilla JS, no reload)
- Keyword search band (§1): live, debounced, AND over whitespace tokens, diacritic-
  insensitive, both languages indexed. Combines with the tag filter (AND). Only the
  index is filtered; featured is not.
- Tag pills placed BELOW description text, not above the title
- Unlinked pages: exist at a URL, not listed in nav or project list
  (for politically-sensitive or selectively shared work) — `listing: "unlisted"` in
  js/projects-data.js. List filenames here as sub-pages are added.

## Data conventions
Data files: js/tags-data.js, js/projects-data.js, js/experience-data.js. Read-side
helpers in js/data-helpers.js. Array order never matters — everything sorts by `sortDate`
("YYYY-MM") descending; `pinned: true` lifts a project to the top of the index.

- Listing tiers (`listing` on every project):
    "index"    — in the §3 index, the tag filter, search, and its role's "Projects from
                 this role" list; may be `featured` (max 3)
    "unlisted" — direct URL only; excluded from index, bands, filter, featured, search
    "hidden"   — excluded everywhere
    "nested"   — RESERVED, not implemented. Intended for role-bound minor projects shown
                 on their band and surfaced in the index only under an active filter or
                 search. An entry set to it does not render and the dev check warns.
                 Build trigger: the index passes ~30 rows, or 4+ minor role-bound items
                 exist. Experience entries keep a `visible` boolean.
- Two-way project ↔ experience links come from ONE field: project `experience` holds an
  experience `slug` (or ""). Project → role: "Part of: <role>, <org> →" (key projPartOf)
  below the tags, to experience.html#<slug>. Role → projects: the band lists every
  listing:"index" project pointing at it (key expRelatedHeading), titles linking to
  projects.html#<slug>. Index rows and bands carry id="<slug>"; a matching location.hash
  clears filter/query, scrolls clear of the nav, and adds `.is-target` (static bronze
  left rule). Only a visible role is a valid link target.
- Tags are IDS from js/tags-data.js (`{ id, key }`); pills and filter buttons show the
  translated label; filter state stores ids. Never store a label in a data file.
- `context` on every project: industry | coursework | personal | service | research —
  rendered as "<Context> · <dates>" (keys ctxIndustry …).
- Key naming by slug: proj<SlugCamel>Title / Desc / LongDesc / Alt / Search
  (slug "todo-project-1" → projTodoProject1Title); exp<SlugCamel>Role / Org / Bullet1…;
  tag<IdCamel>; ctx<Context>. translations.js is the single source of display strings.
- searchEntries(query, entries) → entries in js/projects.js is the ONE place matching
  happens. Phase 3 (TF-IDF) replaces its body only — same signature, same return shape,
  may reorder by score; no markup or caller changes.
- Dev data check (siteData.checkData, console.warn only) runs on load of projects.html
  and experience.html: unknown tag id, missing EN/ES key, duplicate slug, bad `experience`
  target, featured on non-index, >3 featured, imageSrc without imageAlt, missing
  sortDate/context, reserved "nested". Keep the console clean.

## Animation and scroll behavior
- NO page-load animations — no rising text, no fading on arrival
- Scroll-triggered fades only: IntersectionObserver, opacity 0→1, ~300ms, no movement
- Hover: color transitions only, ~150ms ease
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

## What NOT to do
- Do not make navbar anything other than white (#FFFFFF) in light mode
  (dark mode overrides --nav-bg to a dark warm background, which is expected)
- Do not hardcode display text in HTML — use data-i18n attributes
- Do not animate on page load or cause layout shift
- Do not use dark mode toggle
- Do not use fixed pixel widths on containers
- Do not use ALL CAPS section labels or numbered decorators (01, 02, 03)
- Do not put tag pills above the project title
- Do not use rose/--rose on structural elements — it belongs only on "say hello" chip
- Do not add npm packages, build steps, or frameworks without explicit instruction
- Do not make section backgrounds compete visually with project images
