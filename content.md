# Site Content — gideonong.me

Claude Code: read this file alongside CLAUDE.md when building or filling any page.

**`js/translations.js` is the single source of display strings.** This file records each
page's status, the keys that exist, and the non-string fields the data files need — it does
not hold copies of the strings. Do not invent or paraphrase content; mark gaps `TODO`.

---

## How to read this file

Every page section carries a status line. Respect it.

| Status | Meaning |
|---|---|
| **VERIFIED** | Checked against the built page. Strings here match what ships. Safe to rely on. |
| **INTAKE** | The page is built and waiting for content. Every slot is listed below — fill them in, don't restructure. |
| **NEEDS REVIEW** | This section has NOT been checked against the built page and may be stale. Do not trust it as-is. |

**Updated 2026-09-27** for the pre-fair code session: translatable `dates`, clickable tags (no
filter row), phrase chips (`js/chips.js`), project sub-pages (`page` field +
`projects/<slug>.html`), and the hidden About blocks. See plan.md → Decisions log [2026-09-27].

**Reconciled 2026-09-26.** The experience.html and projects.html sections are status + field
reference only (the strings themselves moved out — translations.js is the source), each with
a framework briefing to paste at the start of its interview, updated for the 2026-09-26 data
conventions (listing tiers, project ↔ role links, context, sortDate, shared tag ids). The
about.html section was only partially reconciled and is still marked NEEDS REVIEW — see the
note in it.

### Where content actually goes

Strings and fields have different homes. Nothing is typed into HTML.

| Kind of content | Lives in | Format |
|---|---|---|
| EN/ES display strings | `js/translations.js` | `key: "string"` under `en` and `es` |
| Tag vocabulary (shared) | `js/tags-data.js` | `{ id, key }` — ids in the data files, labels `tag<IdCamel>` in translations.js |
| Experience entries (non-string fields) | `js/experience-data.js` | slug, dates ({ from, to }), sortDate, tags (ids), imageSrc, subpageUrl, layout, status, color, visible |
| about.html books / FAQ / sites | `js/about.js` | **inline** `titleEN`/`titleES` pairs — NOT i18n keys (see about.html note). All three blocks are HIDDEN for the fair (2026-09-27). |
| Project entries (non-string fields) | `js/projects-data.js` | slug, dates ({ from, to }), sortDate, context, tags (ids), imageSrc, subpageUrl, featured, pinned, listing, experience, homeLayout, gallery, page |
| Project sub-pages | `projects/<slug>.html` (shell) + `page` on the entry | one shell file per page; strings are proj<SlugCamel>Section/Fact/Photo/Credit keys |
| Phrase chips (inline links) | `js/chips.js` | `{ phrase, urls: { en, es } }` — strings stay plain text; the linker adds the chip |
| Document PDFs | `assets/pdfs/<type>/` + generated `js/docs-data.js` | dated filenames — see Document links below |

Non-string fields (dates, sort month, context, tag ids, image paths, colors, layout presets,
listing tier, linked role) are listed in this file as intake prompts so the interview collects
them, but they are typed into the data array, not into `translations.js`. Conventions:
CLAUDE.md → Data conventions.

---

## GLOBAL — Nav & UI labels

**Status: VERIFIED**

### Navbar

Logo text: "Gideon A. Ong"
Nav links (in order): Projects · Experience · About
Language toggle: EN | ES (always the rightmost element at every breakpoint)

### "Under development" banner

EN: "This site is under development."
ES: "Este sitio está en desarrollo."
[key: banner]

### Nav link labels

EN: "Projects" / "Experience" / "About"   [keys: navProjects, navExperience, navAbout]
ES: "Proyectos" / "Experiencia" / "Sobre mí"

### Footer

EN resume button: "Download Resume"
ES resume button: "Descargar Currículum"
[key: resumeBtn]

> The ES label is deliberately the long form, not "Descargar CV". This is an explicit
> exception to CLAUDE.md's compact-element rule — see the note there. Do not shorten it.

Footer contact: gao9819@utulsa.edu   [key: footerContact]
Footer copyright: "© 2026 Gideon A. Ong"   [key: footerCopyright]

### Document links (resume / CV / transcript)

Do **not** hardcode PDF paths. Elements opt in with `data-doc-link="resume" | "cv" | "transcript"`
and `js/main.js` resolves the href from the generated manifest `js/docs-data.js` (`const DOCS`):
active language → the other language → the element's existing href. A type with no file at
all has its buttons hidden. No probing, no network requests, no localStorage (2026-09-26).

**To publish a document:** drop the PDF into its folder with the right name and commit — the
pre-commit hook (`.githooks/pre-commit`, one-time `git config core.hooksPath .githooks` per
clone) regenerates and stages the manifest. Preview with `node scripts/build-docs-manifest.js`.

Naming convention (anything else is ignored with a warning):
- `assets/pdfs/resume/<en|es> Gideon Ong Resume <YYYYMMDD>.pdf`
- `assets/pdfs/cv/<en|es> Gideon Ong CV <YYYYMMDD>.pdf`
- `assets/pdfs/transcript/Gideon Ong Transcript <YYYYMMDD>.pdf` — one file, no language prefix

Files today: one EN resume (20260915). No ES resume, CV or transcript yet, so the CV and
transcript buttons on about.html are hidden and the resume button stays static. Once ONE of
CV / transcript exists the button morphs into Resume + that document; with both it morphs
into CV + Transcript (2026-09-27).

---

## index.html — Top section

**Status: VERIFIED**

### Name

Display: "Gideon A. Ong"
(Lora serif, large — no label or subtitle above it)

### IEL chip

Chip text: IEL
URL: https://utulsa.edu/academics/interdisciplinary-programs/international-engineering-science-language/
Placement: auto-linked wherever the word "IEL" appears (hero, bio, bullets, sub-pages) by
the phrase table in `js/chips.js` — it is never written into the HTML or into a string. The
ES link goes through the Google-translate proxy URL. Same mechanism links "Zohaib Sheikh" →
zohaibsheikh.dev. To add a phrase: one line in `CHIPS`.
Style: tonsky.me-style small bordered chip (same style as social chips, but inline in text)

### Description (top section)

EN [key: heroDesc]:
"Bilingual mechanical engineering IEL student with experience in automation, fabrication,
and research; currently looking for summer internships for 2027. Interested in statistics,
manufacturing, data analysis for applied engineering, and automating the boring stuff."

ES [key: heroDesc]:
"Estudiante bilingüe de ingeniería mecánica IEL con experiencia en automatización,
fabricación e investigación; actualmente buscando pasantías para el verano de 2027.
Interesado en estadística, manufactura, análisis de datos para aplicaciones de ingeniería,
y automatizar lo aburrido."

Bilingual display behavior: active language is normal weight/size; inactive language
renders in Lora italic, ~13px, var(--muted), directly below the active paragraph.
Both are always in the DOM; JS swaps their roles.

### Social chips (in order)

```
[LinkedIn]  gideon-a-ong   → https://www.linkedin.com/in/gideon-a-ong
[GitHub]    gidgo130       → https://github.com/gidgo130
[✉]         say hello      → mailto:gao9819@utulsa.edu
```
[key for the email chip label: sayHello — EN "say hello" / ES "escríbeme"]

### Resume button (below social chips)

Uses the global `resumeBtn` key and `data-doc-link="resume"`.

---

## index.html — Featured work section

**Status: VERIFIED (structure) — shows placeholder projects until the projects interview.**

Section heading key: `featuredWork` (written, EN/ES).

Since 2026-09-26 the block is rendered by `js/home.js` from `js/projects-data.js` — every entry
with `featured: true` and `listing: "index"` — using the same builders as projects.html §2
(image, title, "Context · dates", paragraph, tags, "Part of" link, "View project →"). There
are no home-specific project keys; the old `featuredCardTitle` / `featuredCardDesc` placeholder
card is gone. A project's copy exists in exactly one place.

**To fill:** nothing here — featured projects come from the projects content interview.

---

## experience.html — Status + field reference

**Status: VERIFIED (2026-09-27) — content loaded verbatim from staging/copy-en.md and
copy-es.md; checked against the built page in EN and ES at 375 / 768 / 1280, light and dark.**

Pending (not blocking the fair):
- The three hidden pre-college roles (`esl-tutor`, `church-media`, `senior-patrol-leader`,
  all `visible: false`) carry only the EN role title. Their `orgKey` strings and ES titles are
  `TODO`, their `dates` a placeholder year. They are the ONLY `TODO` strings left in the site
  and nothing can render them.
- Employer band colors are still neutral grey placeholders (plan.md open decision #9).
- McElroy band image is the pump lathe photo until Gideon supplies a shop photo.

Built 2026-09-20 as full-width bands per plan.md → Page Spec — experience.html; data
conventions revised 2026-09-26 (CLAUDE.md → Data conventions). Structure, CSS, and JS are
done. Nothing below requires a code change to fill.

**Strings live in `js/translations.js` only** — this section names the keys and their status,
never the text. Find every unfilled slot with: `grep "TODO " js/translations.js`.

### Framework briefing — paste this at the start of the interview

**How the page works.** experience.html is a stack of full-width colored bands, one per role,
newest first. Each band carries a restrained tint of its employer's color — the color change
between bands *is* the divider. Inside a band: an image and a text column (role title,
org · dates, bullets, tag pills, a "Projects from this role" list when any project is linked
to the role, and a "View full case study →" link once a sub-page exists). One role may be
flagged `current`, which writes the hero's status sentence and marks that band. Every visible
string is an EN/ES pair in `js/translations.js`; everything else — dates, sort month, tags,
images, colors, layout — is a field in `js/experience-data.js`. Adding, hiding, reordering
(by sort month) or recoloring a role is a data edit, not a code change.

**Fixed — assume these; don't redesign them mid-interview:**
- Full-width bands, stacked with no gaps; the tint change is the divider
- Per-entry color is a 12–20% tint of the employer color over the section background, mixed
  separately for light and dark mode. Body text must clear 4.5:1 on it, role titles 3:1.
  If a brand color can't manage that, the tint gets weaker — the text never gets lighter.
- Every display string is EN + ES. No hardcoded text in the HTML.
- At most one role flagged `current`, set by the author — it is not a visitor-facing toggle.
- Tags come from ONE shared vocabulary used by both projects and experience; each tag has an
  EN and an ES label. Ask for tag names that read well in both languages.
- A project is linked to a role from the project's side (the projects interview asks "which
  role was this part of?"). The band then lists it automatically.
- Content fades in on scroll; band backgrounds never animate.

**Free to change — just say so, it's a data edit:**
- Which roles appear, their order (a sort month per role), and whether one is hidden
- All wording, EN and ES
- Bullet count per role — 2–3 is the guideline, but the renderer takes any number. Same for tags.
- Layout per role: `imageLeft` (current default), `imageRight`, `fullBleed`, `textOnly`.
  All four are built and switching is one word.
- Images — one per role, or none. A role with no image renders clean, not broken.
- Employer colors. All four entries are neutral grey placeholders today.

**Possible, but costs a small code change — flag it rather than assuming:**
- A fifth layout preset (one CSS class plus one line in the renderer)
- A new per-role field, e.g. location, a second link, or an employer logo
- Switching the hero from the photo-collage overlay to the 2-column backup — already built,
  it's one class on the section

**Out of scope here:** the case-study sub-pages at `/experience/<slug>.html` (specced
separately, none built yet — every `subpageUrl` is blank until one ships), and anything
belonging to projects.html.

### Resolved in the 2026-09-27 interview

1. **ES role titles** — translated; employer names untranslated; the university is
   "Universidad de Tulsa" (content-intake.md Round 0).
2. **Tag vocabulary** — the 11 tags in `js/tags-data.js` (copy-en.md § Tags).
3. **Bullet length** — no fixed ceiling; Baker Hughes carries five bullets, the others 2–3.
4. **TURC entry** — included, `visible: true`.

### §1 — Hero: keys and status

| Key | Role | EN | ES |
|---|---|---|---|
| `expHeroStatus` | fallback status sentence (no `current` entry) | written | written |
| `expHeroStatusCurrent` | template when an entry is `current`; must keep `{role}` and `{org}` | written ("Currently {role} at {org}.") | written |
| `expHeroPara` | paragraph under the status sentence | written | written |

**Hero tiles (2026-09-27)** — three captioned `<figure>` tiles in `experience.html` beside
the solid text panel: scanner-fixture (tall), lathe-tile, eagle-tile (stacked). Captions
`expHeroTile1Cap…3Cap`, alts `expHeroTile1Alt…3Alt` — all written EN/ES. Under 768px the text
comes first and the tiles stack below it. No scrim: nothing sits under the text.

### §2 — Field reference (`js/experience-data.js`)

```
slug         unique id → band id (experience.html#<slug>); projects link to it via `experience`
roleKey      exp<SlugCamel>Role     → EN + ES in translations.js
orgKey       exp<SlugCamel>Org      → EN + ES (employer names usually identical)
bulletKeys   [exp<SlugCamel>Bullet1, …]  (2–3; any number works)
dates        { from: <point>, to?: "present" | <point> } — <point> is { season: "spring"|"summer"|
             "fall"|"winter", year } or { month: 1–12, year } or { year }. Renders per language
             ("Summer 2026" / "Verano 2026", "Spring 2026 – present" / "Primavera 2026 – presente").
sortDate     "YYYY-MM" — the only thing ordering reads; newest first. Array order is ignored.
             Must agree with `dates` (the dev check warns otherwise).
tags         [tag ids from js/tags-data.js] — each pill links to projects.html?tag=<id>
imageSrc     path, or "" for no image (renders text-only, no broken image)
imageAltKey  i18n key for the band image's alt text (exp<SlugCamel>ImageAlt)
imageLink    OPTIONAL — where the band image links (site-root-relative, e.g. "projects.html?part=<slug>");
             absent → the image is plain, no hover
subpageUrl   "/experience/<slug>.html" once the page exists, else "" (link omitted)
layout       imageLeft | imageRight | fullBleed | textOnly
status       "current" on AT MOST ONE entry across the whole array, else null
color.light  { bg, border, accent }  — see the color contract below
color.dark   { bg, border, accent }  — mixed separately, never reuse the light value
visible      true | false  (false also makes the role an invalid link target for projects)
```

**Entries in the array** (role/org/dates are real; bullets, tags and colors are not):

| slug | Entry | Key prefix | dates | sortDate | visible | status |
|---|---|---|---|---|---|---|
| `baker-hughes` | Baker Hughes — Engineering Intern, ALS R&D | `expBakerHughes` | summer 2026 | 2026-06 | true | null |
| `machine-shop` | McElroy Prototyping Lab — Machine Shop Technician | `expMachineShop` | spring 2026 – present | 2026-02 | true | **"current"** |
| `schultz-grader` | Dr. Joshua Schultz — Grader & Data Analyst | `expSchultz` | spring 2026 | 2026-01 | true | null |
| `turc` | TURC / TMTC (Edmonds) — role TBD | `expTurc` | summer 2025 (placeholder) | 2025-08 (placeholder) | **false** | null |

All four visible entries are fully written in EN and ES: roles, orgs (with location:
"Baker Hughes, Claremore OK", "…, University of Tulsa" / "Universidad de Tulsa"), short orgs
for "Part of" links, bullets (5 / 3 / 2 / 3), tags, image alts. `turc` is now `visible: true`.
Layouts: imageLeft / imageRight / textOnly / imageLeft.

### §2 — Chrome keys (written, VERIFIED)

`expCaseStudyLink`, `expCurrentLabel` (eyebrow on the flagged entry — compact element, keep
EN/ES close in length, not ALL CAPS), `expRelatedHeading` ("Projects from this role" heading,
2026-09-26). Tag labels: `tag<IdCamel>` in `js/translations.js`, one per id in
`js/tags-data.js`.

### §2 — Employer color contract

Each entry needs a light and a dark set. Collect the employer's brand colors during the
interview; **do not use a raw brand color as a band background.**

- `bg` — employer primary mixed **12–20% over `var(--bg-section)`** for that mode.
  Light mixes over `#EDE6D5`; dark mixes over `#211C14`.
- `border` — employer secondary at full or near-full strength. Band hairline + rule under the role title.
- `accent` — employer secondary, darkened if needed. Case-study link, tag pill borders, current-entry left edge.
- Body text must clear **4.5:1** against `bg`; large role titles **3:1**. If a color can't
  satisfy that at 20%, **reduce the tint — never lighten the text.**

All four entries currently carry neutral grey placeholder tints with the mix percentage noted
in a comment beside each. plan.md open decision #9.

### Still open on this page (plan.md)

- #3 overlay vs. 2-column backup — decide once real photos are in
- #6 sub-page structure — `/experience/<slug>.html` does not exist yet; every `subpageUrl` is
  "" (blanked 2026-09-26) until the sub-pages ship
- #7 layout preset per entry — all four are `imageLeft` today
- #10 hero-to-first-band transition — breather strip or direct butt join

---

## about.html — NEEDS REVIEW

**Status: VERIFIED for the fair (2026-09-27) — bio 1–3 (EN/ES) loaded verbatim, headshot
in place, §3 / §4 / interesting sites hidden. The hidden blocks' arrays are still placeholders
and the inline-string question below is still open for after the fair.**

> **What this section is and isn't.** about.html is **fully built** (hero, who-am-I, reading,
> FAQ, AI statement, viewing settings). The old stub entry that used to live here was wrong and
> has been removed. What follows is a partial, unverified inventory assembled from a quick pass
> during the experience.html work — it has **not** been checked section by section against the
> built page. A session focused on about.html should verify every line, promote it to INTAKE or
> VERIFIED, and expand it into a full intake sheet like the experience.html one above.

**Known-real strings** (written, not placeholder):
- [aboutIdentifiersEN] "Engineer · Geographer · Federalist · Philomath"
- [aboutIdentifiersES] "Ingeniero · Geógrafo · Federalista · Aprendiz eterno"
  (EN and ES are independent, not translations of each other — plan.md 2026-09-17)
- [aiPara1] — the AI statement is written, as plain text. "Zohaib Sheikh" becomes a link chip
  through `js/chips.js` (2026-09-27); there is no HTML in translations.js any more.
- Section headings and viewing-settings toggle labels are all written.
- [cvBtn] / [transcriptBtn] — "Download Full CV" / "Download Transcript".

- [whoamiBio1] / [whoamiBio2] / [whoamiBio3] — §2 biographical paragraphs, written EN/ES
  (2026-09-27); "IEL" in bio 1 gets the chip automatically.

**Known-placeholder, hidden for the fair:**
- §3 books — 5 entries in `js/about.js` — **HIDDEN for the fair** (`hidden` on `#about-reading`)
- §4 FAQ — 4 entries in `js/about.js` — **HIDDEN for the fair** (`hidden` on `#about-faq`)
- §6 interesting sites — 3 entries in `js/about.js` — **HIDDEN for the fair** (`hidden` on
  `#about-sites`)
- Headshot — `<img src="assets/images/about/headshot.jpg">` in about.html, alt from
  `headshotAlt` (EN/ES written). Swap the file in place.

**Flag for the about.html session — a real inconsistency:**
The §3/§4/§6 data arrays in `js/about.js` carry **inline** `titleEN`/`titleES`/`descEN`/`descES`
strings. They do **not** use i18n keys, unlike `js/experience-data.js`, which stores keys and
resolves them through `translations.js`. Two different patterns for the same job. Decide which
one wins before the about content interview, because it changes where every book, FAQ, and site
string gets typed.

(The stub-page keys `aboutHeading` / `aboutBody` were deleted on 2026-09-26.)

---

## projects.html — Status + field reference

**Status: VERIFIED (2026-09-27) — 16 projects loaded verbatim from staging/copy-en.md and
copy-es.md, images and alt text from staging/image-manifest.md; checked against the built
pages (projects.html, index.html, the three sub-pages) in EN and ES at 375 / 768 / 1280.**

Loaded: 3 featured with sub-pages (`pump-cylinder-failure` stacked, `eagle-pathway` collage,
`g-view` imageRight; `featuredOrder` 1–3), 13 index rows, `uk-crash-hotspots` pinned, 11-tag
vocabulary. Deferred (LATER in content-intake.md): Arduino robot, R crash models, ESL
peer-connection system, Spinelli translations (unlisted).

> **What this section is and isn't.** projects.html is **built** per plan.md → Page Spec —
> projects.html: live keyword search band (§1, since 2026-09-26), featured entries (§2), and
> the index with its tag filter (§3), rendered by `js/projects.js` from `js/projects-data.js`.
> The same array feeds the index.html featured block (`js/home.js`) and the sub-pages
> (`js/project-page.js`). Content loaded 2026-09-27 — see the entries table below.

**Strings live in `js/translations.js` only** — this section names the keys and their status,
never the text. `grep "TODO " js/translations.js js/projects-data.js js/tags-data.js` returns
nothing for projects.

### Framework briefing — copy the whole block below into the projects interview

Written to stand on its own: an interview chat has no access to this repo, so the block below
references no file, no other section, and no line of code. Copy it between the two markers.

<!-- ============================ COPY FROM HERE ============================ -->

**Your job in this conversation.** Interview Gideon about his engineering projects and produce
the filled-in content described under "What to hand back" at the end. You are not writing code
and not designing the page — both already exist. A separate session with the codebase will
implement whatever this interview produces. Never invent, embellish, or infer a project
detail: if something is missing, mark it `TODO` and move on.

**The page your answers fill.** It has three zones:

- a **search band** at the top — a working keyword search over the index. It indexes every
  project's title, descriptions, tags, context, linked role and a hidden "search keywords"
  field, in both languages.
- a **featured** set of 2–3 projects — large image, title, a "Context · dates" line, a
  paragraph, tags, a "Part of: <role> →" link when the project belongs to a job or research
  role, a link. On the home page each featured project also picks a layout: a wide image
  with the text below (default), image left, image right, or a collage of up to four photos.
- an **index** of every project — one compact row each: small thumbnail, title, "Context ·
  dates", one-line description, tag pills, the same "Part of" link. A live project count sits
  above it. Clicking any tag pill anywhere on the site shows the index filtered to that tag,
  with a removable chip beside the count — there is no separate filter row. While any filter
  or search is active the featured set folds away so the results sit right under the search
  band.

Both zones read one list, and so does the home page's "Featured work" block. Marking a
project "featured" promotes it into the featured blocks and it still appears in the index —
its text is never duplicated. Everything displayed exists in both English and Spanish.

**Collect per project:**

| What | Notes | Rough length |
|---|---|---|
| Name | | a few words |
| Dates | a season or month + year, optionally to another one or "present" — "Summer 2026", "July 2022", "Spring 2026 – present". The site translates them itself. | short |
| Sort month | the year-month the project should sort by (newest first); usually when it finished | YYYY-MM |
| Context | one of: industry / coursework / personal / service / research | one word |
| One-line description | shown in the index row | one line |
| Fuller description | featured block; strictly needed only for the 2–3 featured projects | a short paragraph |
| Tags | from the agreed vocabulary; any number | |
| Part of a role? | which job, internship or research role it belonged to, if any — the site links the two both ways | role name or "none" |
| Photo | one, or none. "No photo" is a perfectly good answer — the row then renders clean, with the text at full width | |
| Alt text | what the photo shows, for screen readers; only if there is a photo | one line |
| Search keywords | never displayed; feeds the search — synonyms, tools, acronyms, Spanish terms | any |
| Sub-page | a deeper page per project (featured projects only, for now). Collect: 2–5 titled sections of a paragraph each, a quick-facts list (team, role, course, methods, award…), extra photos with alt text, whether a report PDF may be linked, and a photo credit if any. "Later" is fine — the link simply doesn't appear | 250–400 words |
| Linked names | any person or program in the text that should become a link (e.g. a collaborator's site) — the site links them by phrase | name + URL |
| Listing | normal / hide for now / exists but unlisted (sensitive or selectively shared work — reachable by direct link only, never in any list, search or role) | |
| Home layout | featured projects only — how it sits on the home page: stacked (default: wide image, text below) / image left / image right / collage | one word |
| Extra photos | collage only — 1–3 more photos shown with the main one, each with alt text | |

**Collect for the list as a whole:** which 2–3 are featured (at most 3), whether any one project
should be pinned to the top of the index, and the **tag vocabulary** — one controlled list of
roughly 5–10 tags that every project draws from, each with an English and a Spanish label
that read well in a small pill. The same list is used by the experience page. Draft the
vocabulary *after* hearing the whole list, never before: the list is what reveals the right
axis. A controlled list is what stops "CAD", "cad" and "SolidWorks" becoming three separate
filter pills that each match a third of the work.

**Fixed — assume these; don't redesign them mid-interview:**

- One list feeds every project listing. Featured promotes an entry; it never copies its text.
- Order is by sort month, newest first; no manual ordering.
- Tag pills sit below the description, never above the title.
- The index is rows, not a card grid.
- Every thumbnail is the same shape (4:3, cropped to fill); featured images are wider (16:9).
- Everything displayed is English **and** Spanish, tags included.
- Filtering on several tags is AND — a project must carry all of them to stay visible. Search
  and the filter combine with AND too.
- Animation is opacity only: never movement, never on page load.

**Flexible — offer these freely; each is a one-line data edit:**

- Which projects appear, which are featured, which one is pinned, which role each belongs to
- All wording in both languages, including the section headings and the filter labels
- How many tags a project carries
- A project with no photo, no sub-page, or no Spanish text yet
- Hiding a project, or keeping it reachable by direct link but out of every listing

**Costs a small code change — flag it, don't promise it:**

- A new context beyond the five above
- Showing the index as a card grid instead of rows
- A new field per project beyond the sub-page set — a video, a second link (report PDF and
  photo credit are already fields on the sub-page)
- Two-line descriptions in the index rows
- Minor projects that should show on a role's band but stay out of the index unless someone
  searches or filters for them (planned, not built — note them as "nested" and move on)

**Out of scope for this interview:** the deeper per-project sub-pages (not designed yet), the
home page, and anything about jobs, internships or research roles — that is a separate interview.

**Settle these early — they change what you ask for:**

1. **Spanish** — does Gideon write it himself, or do you draft it for him to correct? Either is
   fine, but it decides whether you collect Spanish during the interview or after it.
2. **Tag vocabulary axis** — skill ("CAD", "Python"), domain ("Thermal", "Robotics"), type of
   work, or a deliberate mix. Note that the *type of work* is already captured by the context
   field (industry / coursework / personal / service / research), so tags need not repeat it.
3. **One description or two?** If the featured paragraph genuinely says more than the index
   line, collect both. If it would only be the same thing at greater length, say so.
4. **How many projects are there?** A long list changes what the index rows have to do; a very
   short one may not need a tag filter at all.

**What to hand back.** For each project, in this shape — the implementing session types it
straight into the site's data files:

```
Project: <name>
Slug: <url-safe-name>
Dates: <season|month> <year> [– <season|month> <year> | present]     Sort month: <YYYY-MM>
Context: industry / coursework / personal / service / research
Tags: <from the vocabulary>
Part of role: <role name, or none>
Featured: yes / no     Pinned: yes / no     Listing: index / hidden / unlisted
Home layout: stacked / imageLeft / imageRight / collage      [featured projects only]
Photo: <filename, or "none">
Alt (EN):              Alt (ES):
Extra photos (collage only, 1–3):
  - <filename>   Alt (EN):   Alt (ES):
One-line (EN):
One-line (ES):
Paragraph (EN):        [featured projects only]
Paragraph (ES):
Search keywords (EN / ES):
Linked names: <phrase → URL, or none>
Sub-page: <planned / later>
  Sections (2–5):  <Heading (EN) / (ES)> — <paragraph (EN)> / <(ES)>
  Quick facts:     <Label (EN/ES)> — <value (EN/ES)>   (team, role, course, methods, award…)
  Photos:          <filename>   Alt (EN):   Alt (ES):
  Report PDF:      <filename, or "do not link">
  Photo credit:    <text (EN/ES), or none>
```

Then the tag vocabulary as a final list of `id — EN label / ES label`, and any wording changes
to the page chrome (search placeholder, "Search", "Clear search", "Featured projects",
"All projects", "View project →", "Part of: {role}, {org} →", "Clear tag filter" (the ✕ label),
"{n} projects" / "{n} project", the two empty-state lines, "Read the report →", "← All
projects", the five context labels, and the season / month / "present" words used in dates).
Mark anything still unknown as `TODO` rather than filling it with a guess.

<!-- ============================= COPY TO HERE ============================= -->

### Field reference (`js/projects-data.js`)

```
slug           URL slug → /projects/<slug>.html; also the index row id (projects.html#<slug>)
titleKey       proj<SlugCamel>Title      → EN + ES  (slug "todo-project-1" → projTodoProject1Title)
descKey        proj<SlugCamel>Desc       one line, index row
longDescKey    proj<SlugCamel>LongDesc   paragraph, featured blocks + sub-page
imageAlt       proj<SlugCamel>Alt        required whenever imageSrc is set; "" otherwise
searchTextKey  proj<SlugCamel>Search     never displayed; folded into the search corpus
dates          { from: <point>, to?: "present" | <point> }; <point> = { season, year } |
               { month: 1–12, year } | { year }. Rendered per language (never a literal string).
sortDate       "YYYY-MM" — the only thing ordering reads; newest first. Array order is ignored.
               Must agree with `dates` (dev check warns).
context        industry | coursework | personal | service | research  → ctx<Context> label
tags           [tag ids from js/tags-data.js] — each pill links to projects.html?tag=<id>
imageSrc       path, or "" (row renders text-only). Featured image / sub-page hero.
thumbSrc       OPTIONAL — index-row thumbnail (4:3 crop); falls back to imageSrc
thumbAltKey    OPTIONAL — alt key for thumbSrc; falls back to imageAlt
subpageUrl     "/projects/<slug>.html" once projects/<slug>.html exists, or "" (link
               omitted; the images then stay plain — they link to the sub-page only when
               one exists)
featured       true → also in projects.html §2 and the index.html featured block (max 3)
pinned         true → top of the index regardless of sortDate
listing        "index" | "unlisted" | "hidden"   ("nested" is reserved — see CLAUDE.md)
experience     experience slug (baker-hughes, machine-shop, schultz-grader, turc) or ""
homeLayout     OPTIONAL — index.html featured block only: "stacked" (default) | "imageLeft" |
               "imageRight" | "collage". projects.html §2 ignores it.
gallery        OPTIONAL, collage only — [{ src, altKey }] × 2–4: the collage cells themselves
               (imageSrc is NOT a cell); altKey = proj<SlugCamel>Gallery<N>Alt (EN + ES)
page           OPTIONAL — sub-page content (projects/<slug>.html, rendered by js/project-page.js):
                 sections:  [{ headingKey, bodyKey }]   proj<SlugCamel>Section<N>Heading / Body
                 facts:     [{ labelKey, valueKey }]    proj<SlugCamel>Fact<N>Label / Value
                 photos:    [{ src, altKey }]           proj<SlugCamel>Photo<N>Alt
                 reportPdf: "assets/pdfs/projects/<file>.pdf"   ("" = no link)
                 creditKey: proj<SlugCamel>Credit       ("" = no credit line)
               Every part optional. To publish a sub-page: copy projects/todo-project-2.html to
               projects/<slug>.html, set data-slug, the static <title> and meta description, then
               set subpageUrl on the entry.
```

Tags: `js/tags-data.js` holds `{ id, key }` pairs; the label is `tag<IdCamel>` in
`js/translations.js`. Data files store ids only.

**Entries in the array** (all strings written, EN + ES):

| slug | dates | sortDate | context | featured | pinned | experience | image |
|---|---|---|---|---|---|---|---|
| `pump-cylinder-failure` | Spring 2026 | 2026-05 | coursework | 1 (stacked) | — | — | pin-assembly.jpg + 5 sub-page photos + report PDF |
| `eagle-pathway` | July 2022 | 2022-07 | service | 2 (collage) | — | — | directing-volunteers + 2 collage + 3 sub-page photos, credit |
| `g-view` | Summer 2026 | 2026-07 | industry | 3 (imageRight) | — | baker-hughes | g-view-demo.png |
| `velora` | Summer 2026 | 2026-07 | industry | — | — | baker-hughes | none |
| `autoscan` | Summer 2026 | 2026-07 | industry | — | — | baker-hughes | scanner-station.jpg |
| `dynamics-pdf-unifier` | Fall 2026 | 2026-09 | personal | — | — | schultz-grader | none |
| `keplinger-heating` | Spring 2026 | 2026-05 | coursework | — | — | — | none |
| `music-notes-matlab` | Spring 2026 | 2026-05 | coursework | — | — | — | trumpet-notes.png |
| `gender-employment-cs` | Spring 2026 | 2026-05 | coursework | — | — | — | none |
| `chilled-water-pipeline` | Fall 2025 | 2025-12 | coursework | — | — | — | route-a.jpg |
| `notched-beam-stress-relief` | Fall 2025 | 2025-12 | coursework | — | — | — | fea-spline.png |
| `diesel-dual-cycle` | Fall 2025 | 2025-11 | coursework | — | — | — | pv-diagram.png |
| `mechanical-fuse` | Fall 2025 | 2025-10 | coursework | — | — | — | broken-links.jpg |
| `bicycle-crash-severity` | Spring 2025 | 2025-05 | coursework | — | — | — | shap.png |
| `uk-crash-hotspots` | Spring 2025 | 2025-04 | coursework | — | **yes** | — | qgis-england.jpg |
| `landmine-classification` | Spring 2025 | 2025-03 | coursework | — | — | — | none |

Sort months for Velora, AutoScan and Dynamics PDF Unifier were derived from their season
(the intake gave none). Search keywords (`proj…Search`) list only tools and names that appear
in the copy or content-intake.md.

### Chrome keys (written, VERIFIED)

`projSearchPlaceholder`, `projSearchBtn`, `projSearchClear` (× aria-label), `projFeaturedHeading`,
`projIndexHeading`, `projViewLink`, `projPartOf` (must keep `{role}` and `{org}`),
`projTagClear` (aria-label on the ✕ of the "<Tag> ✕" chip), `projCount` / `projCountOne`
(`{n}`), `projEmpty` (tag-only empty state), `projEmptySearch` (`{q}`, query empty state),
`projReportLink` / `projAllProjects` (sub-page chrome), `ctxIndustry`, `ctxCoursework`,
`ctxPersonal`, `ctxService`, `ctxResearch`, and the date keys `dateSpring…dateWinter`,
`dateMonth1…12`, `datePresent`, `dateSeasonYear`, `dateMonthYear`, `dateRange`. The placeholder
is set via `data-i18n-placeholder` by `js/projects.js`. (`projFilterLabel` / `projFilterClear`
were deleted with the filter row on 2026-09-27.)

### Still to fill

- Nothing for the fair. Sub-pages for the 13 index projects (later); the four deferred
  projects above; employer band colors.

---

## Notes for Claude Code

- Use `data-i18n="[key]"` on every element whose text is keyed here.
- All display strings go into `js/translations.js` — never hardcode display text in HTML.
  Elements may be left empty in the HTML and filled entirely from `translations.js`.
- Per-entry keys are named by slug (`proj<SlugCamel>Title`, `exp<SlugCamel>Role`, …); tag
  labels are `tag<IdCamel>`; context labels `ctx<Context>`. See CLAUDE.md → Data conventions.
- Placeholder strings are prefixed `TODO ` in **both** languages so they stay greppable.
  Keep that convention when adding new unfilled slots.
- Per-entry colors on experience.html bands are written as **inline styles** from the data
  array. That is a deliberate, documented exception to the "tokens live in `:root`" rule —
  per-entry values cannot live in `:root`. Do not "fix" it.
- If a status or field note here disagrees with the code, the **code is not automatically
  wrong** — this file has drifted before. Check which one was updated more recently, reconcile,
  and update the status line at the top of that section.
- Visual reference available at: `references/mockup-v2-brass.html` (gitignored, local only)
