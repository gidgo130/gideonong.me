# Site Content — gideonong.me

Claude Code: read this file alongside CLAUDE.md when building or filling any page.

All display text comes from here. Do not invent or paraphrase — use exact strings.
EN/ES pairs are for `js/translations.js`. Keys are noted in brackets.

---

## How to read this file

Every page section carries a status line. Respect it.

| Status | Meaning |
|---|---|
| **VERIFIED** | Checked against the built page. Strings here match what ships. Safe to rely on. |
| **INTAKE** | The page is built and waiting for content. Every slot is listed below — fill them in, don't restructure. |
| **NEEDS REVIEW** | This section has NOT been checked against the built page and may be stale. Do not trust it as-is. |

**Reconciled 2026-09-20.** The experience.html and projects.html sections were rewritten as
intake sheets and verified against the code — both carry a framework briefing to paste at the
start of their interview. The about.html section was only partially reconciled and is still
marked NEEDS REVIEW — see the note in it.

### Where content actually goes

This file is the source of truth for **display strings**. It is not the only destination.

| Kind of content | Lives in | Format |
|---|---|---|
| EN/ES display strings | `js/translations.js` | `key: "string"` under `en` and `es` |
| Experience entries (non-string fields) | `js/experience-data.js` | dates, tags, imageSrc, subpageUrl, layout, status, color |
| about.html books / FAQ / sites | `js/about.js` | **inline** `titleEN`/`titleES` pairs — NOT i18n keys (see about.html note) |
| Project entries (non-string fields) | `js/projects-data.js` | slug, dates, tags, imageSrc, subpageUrl, featured, pinned, visible, unlisted — plus the `PROJECT_TAGS` vocabulary at the top |

Non-string fields (dates, tags, image paths, colors, layout presets) are listed in this file
as intake prompts so the interview collects them, but they are typed into the data array, not
into `translations.js`.

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
and `js/main.js` resolves the newest file by probing dates backward from today.

Naming convention: `assets/pdfs/<type>/<lang> Gideon Ong <Label> <YYYYMMDD>.pdf`
e.g. `assets/pdfs/resume/en Gideon Ong Resume 20260915.pdf`

The transcript is `bilingual: false` — one file, no `<lang>` prefix. See `DOC_TYPES` in
`js/main.js` for the authoritative definition before changing anything here.

---

## index.html — Top section

**Status: VERIFIED**

### Name

Display: "Gideon A. Ong"
(Lora serif, large — no label or subtitle above it)

### IEL chip

Chip text: IEL
URL: https://utulsa.edu/academics/interdisciplinary-programs/international-engineering-science-language/
Placement: auto-linked inside the hero description by `HERO_CHIPS` in `js/main.js` —
it is not written into the HTML. The ES link goes through the Google-translate proxy URL.
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

**Status: INTAKE — placeholder cards are shipping. Do not invent project content.**

Section heading:
EN [key: featuredWork]: "Featured work"
ES [key: featuredWork]: "Proyectos destacados"

Placeholder card currently live:
- Title [key: featuredCardTitle] — EN "Featured project coming soon" / ES "Proyecto destacado próximamente"
- Description [key: featuredCardDesc] — EN "Project descriptions are being finalized." / ES "Las descripciones de proyectos están siendo finalizadas."

**To fill:** real featured projects come from the projects content interview, not this one.
Featured work on the home page should be sourced from the same project list as projects.html
so a project's copy exists in exactly one place.

---

## experience.html — Content intake sheet

**Status: INTAKE — page is fully built and verified; every slot below is waiting for content.**

Built 2026-09-20 as full-width bands per plan.md → Page Spec — experience.html (2026-09-20
revision). Structure, CSS, and JS are done. Nothing below requires a code change to fill.

Find every unfilled slot with: `grep "TODO " js/translations.js` (33 hits at time of writing).

### Framework briefing — paste this at the start of the interview

**How the page works.** experience.html is a stack of full-width colored bands, one per role,
newest first. Each band carries a restrained tint of its employer's color — the color change
between bands *is* the divider. Inside a band: an image and a text column (role title,
org · dates, bullets, tag pills, a "View full case study →" link). One role may be flagged
`current`, which writes the hero's status sentence and marks that band. Every visible string is
an EN/ES pair in `js/translations.js`; everything else — dates, tags, images, colors, layout —
is a field in `js/experience-data.js`. Adding, reordering, hiding or recoloring a role is a
data edit, not a code change.

**Fixed — assume these; don't redesign them mid-interview:**
- Full-width bands, stacked with no gaps; the tint change is the divider
- Per-entry color is a 12–20% tint of the employer color over the section background, mixed
  separately for light and dark mode. Body text must clear 4.5:1 on it, role titles 3:1.
  If a brand color can't manage that, the tint gets weaker — the text never gets lighter.
- Every display string is EN + ES. No hardcoded text in the HTML.
- At most one role flagged `current`, set by the author — it is not a visitor-facing toggle.
- Content fades in on scroll; band backgrounds never animate.

**Free to change — just say so, it's a data edit:**
- Which roles appear, what order they sit in, and whether one is hidden
- All wording, EN and ES
- Bullet count per role — 2–3 is the guideline, but the renderer takes any number. Same for tags.
- Layout per role: `imageLeft` (current default), `imageRight`, `fullBleed`, `textOnly`.
  All four are built and switching is one word.
- Images — one per role, or none. A role with no image renders clean, not broken.
- The case-study link — point it at a sub-page, or leave it blank and the link disappears.
- Employer colors. All four entries are neutral grey placeholders today.

**Possible, but costs a small code change — flag it rather than assuming:**
- A fifth layout preset (one CSS class plus one line in the renderer)
- A new per-role field, e.g. location, a second link, or an employer logo
- Switching the hero from the photo-collage overlay to the 2-column backup — already built,
  it's one class on the section

**Out of scope here:** the case-study sub-pages at `/experience/<slug>.html` (specced
separately, none built yet), and anything belonging to projects.html.

### Resolve these four first — they change what the interview asks

1. **ES role titles** — translate job titles into Spanish, or keep the English title inside
   Spanish surrounding text? Employer names (Baker Hughes, McElroy Prototyping Lab) presumably
   stay untranslated either way. Currently the ES titles are English behind a `TODO ` marker.
2. **Tag vocabulary** — projects.html now has a controlled list, `PROJECT_TAGS` at the top of
   `js/projects-data.js` (placeholder values, awaiting its own interview). Should experience.html
   draw from that same vocabulary, or keep its own? Today its tags are free strings
   (`"Engineering"`, `"R&D"`, `"ALS"`, …). Both files note the question and neither has decided
   it — whichever interview runs second should not settle it unilaterally.
3. **Bullet length target** — the spec says 2–3 bullets per role but sets no length. Bullets sit
   in the ~60% text column of a band, and ES runs ~20% longer. Agree a rough ceiling (e.g. one
   to two lines each at 1280px) so bands stay visually even.
4. **TURC entry** — include it at all? It is in the array with `visible: false` and its role is
   still `[role TBD]`. plan.md open decision #4.

### §1 — Hero

**Status sentence — a key PAIR.** `js/experience.js` picks one automatically:

- [key: expHeroStatus] — the **fallback**, used when no entry carries `status: "current"`.
  EN (approved, from plan.md): "Currently a Mechanical Engineering and Spanish IEL student at
  the University of Tulsa — seeking summer 2027 internships in engineering and Spanish."
  ES: TODO — currently a provisional translation marked `TODO `. Confirm or replace.

- [key: expHeroStatusCurrent] — the **template**, used when an entry IS flagged current.
  Must contain the literal placeholders `{role}` and `{org}`; they are filled from the flagged
  entry at render time.
  EN: TODO — confirm the current provisional wording.
  ES: TODO.

**Hero paragraph** [key: expHeroPara] — more on current professional direction.
EN: TODO. ES: TODO.
Renders directly under the status sentence in `var(--footer-text)` over the scrim.

**Collage photos** — 3–5 images, currently all `assets/images/placeholder.jpg`.
Written as plain `<img>` tags in `experience.html`; updating means swapping files and `src`.
Representative of current professional life (machine shop, Baker Hughes, lab work).
Needed: which photos, in which of the 5 grid slots (slot 1 is the large left cell; slot 5
only appears at 1024px and up).

### §2 — Per-entry intake

One block per entry. **Strings** go to `js/translations.js`; **fields** go to
`js/experience-data.js`. Entry order in the array is display order (reverse chronological).

Repeat this block for every entry:

```
ENTRY: <name>
  Strings → js/translations.js
    [key: exp<Name>Role]    EN: ________  ES: ________
    [key: exp<Name>Org]     EN: ________  ES: ________   (employer names usually identical)
    [key: exp<Name>Bullet1] EN: ________  ES: ________
    [key: exp<Name>Bullet2] EN: ________  ES: ________
    [key: exp<Name>Bullet3] EN: ________  ES: ________   (2–3 bullets; drop key 3 if only 2)

  Fields → js/experience-data.js
    dates        literal, never translated (e.g. "Summer 2026")
    tags         [ ... ]  — see decision #2 above
    imageSrc     path, or "" for no image (renders text-only, no broken image)
    subpageUrl   "/experience/<slug>.html", or "" to omit the link entirely
    layout       imageLeft | imageRight | fullBleed | textOnly
    status       "current" on AT MOST ONE entry across the whole array, else null
    color.light  { bg, border, accent }  — see the color contract below
    color.dark   { bg, border, accent }  — mixed separately, never reuse the light value
    visible      true | false
```

**Entries currently in the array** (role/org/dates are already real; bullets and tags are not):

| # | Entry | Role key prefix | Dates | visible | status |
|---|---|---|---|---|---|
| 1 | Baker Hughes — Engineering Intern, ALS R&D | `expBakerHughes` | Summer 2026 | true | null |
| 2 | McElroy Prototyping Lab — Machine Shop Technician | `expMachineShop` | Spring 2026 – present | true | **"current"** |
| 3 | Dr. Joshua Schultz — Grader & Data Analyst | `expSchultz` | Spring 2026 | true | null |
| 4 | TURC / TMTC (Edmonds) — role TBD | `expTurc` | TBD | **false** | null |

### §2 — Shared strings

- [key: expCaseStudyLink] — EN "View full case study →" / ES "Ver caso completo →" — VERIFIED
- [key: expCurrentLabel] — EN "Current" / ES "Actual" — VERIFIED
  Eyebrow above the role title on the flagged entry. Compact element: keep EN and ES close in
  length. Not ALL CAPS (CLAUDE.md).

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
- #6 sub-page structure — `/experience/<slug>.html` does not exist yet; all four `subpageUrl`
  values currently 404. Blank them until the sub-pages ship, or ship the sub-pages.
- #7 layout preset per entry — all four are `imageLeft` today
- #10 hero-to-first-band transition — breather strip or direct butt join

---

## about.html — NEEDS REVIEW

**Status: NEEDS REVIEW — reconcile this section in a chat focused on about.html.**

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
- [aiPara1] — the AI statement is written and contains inline HTML (an `<a>` to zohaibsheikh.dev).
  It is listed in `HTML_I18N_KEYS` in `js/main.js` so it injects as HTML, not escaped text.
- Section headings and viewing-settings toggle labels are all written.
- [cvBtn] / [transcriptBtn] — "Download Full CV" / "Download Transcript".

**Known-placeholder, awaiting content:**
- [whoamiBio1] / [whoamiBio2] / [whoamiBio3] — §2 biographical paragraphs
- §3 books — 5 entries in `js/about.js`
- §4 FAQ — 4 entries in `js/about.js`
- §6 interesting sites — 3 entries in `js/about.js`

**Flag for the about.html session — a real inconsistency:**
The §3/§4/§6 data arrays in `js/about.js` carry **inline** `titleEN`/`titleES`/`descEN`/`descES`
strings. They do **not** use i18n keys, unlike `js/experience-data.js`, which stores keys and
resolves them through `translations.js`. Two different patterns for the same job. Decide which
one wins before the about content interview, because it changes where every book, FAQ, and site
string gets typed.

**Dead keys to clean up:** `aboutHeading` and `aboutBody` are still defined in `translations.js`
but no longer referenced by any HTML — leftovers from the stub page.

---

## projects.html — INTAKE

**Status: INTAKE — the scaffold is built; every project string below is a placeholder.
Do not invent project content.**

> **What this section is and isn't.** As of 2026-09-20 projects.html is **built as a scaffold**
> per plan.md → Page Spec — projects.html: hidden search band (§1), featured entries (§2), and
> the index with its tag filter (§3), rendered by `js/projects.js` from `js/projects-data.js`.
> Structure and behavior are real; **all content is placeholder**. Six `TODO` entries are in the
> array — two featured, one deliberately with `imageSrc: ""` to exercise the no-thumbnail path,
> one with `subpageUrl: ""` to exercise the omitted link, one `pinned`. The content interview
> replaces the entries and the tag vocabulary; the markup does not need to change.

Find every unfilled slot with: `grep "TODO " js/translations.js js/projects-data.js`
(29 project string keys × 2 languages, plus 6 placeholder tags and 6 `dates`, at time of writing).

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

- a **search band** at the top — built, but hidden until a search feature ships later. Ignore it.
- a **featured** set of 2–3 projects — large image, title, a paragraph, tags, a link
- an **index** of every project — one compact row each: small thumbnail, title, one-line
  description, tag pills. A tag filter and a live project count sit above it.

Both zones read one list. Marking a project "featured" promotes it into the featured block and
it still appears in the index — its text is never duplicated. Everything displayed exists in
both English and Spanish.

**Collect per project:**

| What | Notes | Rough length |
|---|---|---|
| Name | | a few words |
| Dates | free text — "Spring 2026", "2025–2026" | short |
| One-line description | shown in the index row | one line |
| Fuller description | featured block; strictly needed only for the 2–3 featured projects | a short paragraph |
| Tags | from the agreed vocabulary; any number | |
| Photo | one, or none. "No photo" is a perfectly good answer — the row then renders clean, with the text at full width | |
| Alt text | what the photo shows, for screen readers; only if there is a photo | one line |
| Search keywords | never displayed; feeds the later search feature | any |
| Sub-page | a deeper page per project, not built yet. "Later" is fine — the link simply doesn't appear | |
| Listing | normal / hide for now / exists but unlisted (sensitive or selectively shared work) | |

**Collect for the list as a whole:** the running order (newest first by default), which 2–3 are
featured, whether any one project should be pinned to the top of the index, and the **tag
vocabulary** — one controlled list of roughly 5–10 tags that every project draws from. Draft the
vocabulary *after* hearing the whole list, never before: the list is what reveals the right axis.
A controlled list is what stops "CAD", "cad" and "SolidWorks" becoming three separate filter
pills that each match a third of the work.

**Fixed — assume these; don't redesign them mid-interview:**

- One list feeds both zones. Featured promotes an entry; it never copies its text.
- Tag pills sit below the description, never above the title.
- The index is rows, not a card grid.
- Every thumbnail is the same shape (4:3, cropped to fill); featured images are wider (16:9).
- Everything displayed is English **and** Spanish.
- Filtering on several tags is AND — a project must carry all of them to stay visible.
- Animation is opacity only: never movement, never on page load.

**Flexible — offer these freely; each is a one-line data edit:**

- Which projects appear, in what order, which are featured, which one is pinned
- All wording in both languages, including the section headings and the filter labels
- How many tags a project carries
- A project with no photo, no sub-page, or no Spanish text yet
- Hiding a project, or keeping it reachable by direct link but out of every listing

**Costs a small code change — flag it, don't promise it:**

- Translating the tags themselves (today a tag shows as the same string in both languages)
- Showing the index as a card grid instead of rows
- A new field per project — a report PDF, a video, a second link, a collaborator credit
- Two-line descriptions in the index rows

**Out of scope for this interview:** the deeper per-project sub-pages (not designed yet), the
home page, and anything about jobs, internships or research roles — that is a separate interview.

**Settle these five early — they change what you ask for:**

1. **Spanish** — does Gideon write it himself, or do you draft it for him to correct? Either is
   fine, but it decides whether you collect Spanish during the interview or after it.
2. **Tag vocabulary axis** — skill ("CAD", "Python"), domain ("Thermal", "Robotics"), type of
   work ("Research", "Coursework"), or a deliberate mix.
3. **Do the tags need translating?** "CAD" and "Python" read fine in Spanish; a phrase like
   "Heat Transfer" does not. Either choose tag names that work in both languages, or flag it as
   the code change it is.
4. **One description or two?** If the featured paragraph genuinely says more than the index
   line, collect both. If it would only be the same thing at greater length, say so.
5. **How many projects are there?** A long list changes what the index rows have to do; a very
   short one may not need a tag filter at all.

**What to hand back.** For each project, in this shape — the implementing session types it
straight into the site's data files:

```
Project: <name>
Slug: <url-safe-name>
Dates: <free text>
Tags: <from the vocabulary>
Featured: yes / no     Pinned: yes / no     Listing: normal / hidden / unlisted
Photo: <filename, or "none">
Alt (EN):              Alt (ES):
One-line (EN):
One-line (ES):
Paragraph (EN):        [featured projects only]
Paragraph (ES):
Search keywords (EN / ES):
Sub-page: <planned / later>
```

Then the tag vocabulary as a final list, and the order the projects should appear in. Mark
anything still unknown as `TODO` rather than filling it with a guess.

<!-- ============================= COPY TO HERE ============================= -->

**Repo-side notes for whoever implements the result** (not part of the copy block): entries go
in `js/projects-data.js`, strings in `js/translations.js` as EN/ES pairs, and the tag vocabulary
is the `PROJECT_TAGS` constant at the top of the data file. The five per-project string keys are
`projNTitle`, `projNDesc`, `projNLongDesc`, `projNAlt`, `projNSearch`. Question 2 above overlaps
the experience.html tag-vocabulary decision recorded on that sheet — whichever interview runs
second should not settle it unilaterally.

**Page chrome strings** (live):
- [projFeaturedHeading] — EN "Featured projects" / ES "Proyectos destacados"
- [projIndexHeading] — EN "All projects" / ES "Todos los proyectos"
- [projViewLink] — EN "View project →" / ES "Ver proyecto →"
- [projFilterLabel] — EN "Filter by tag" / ES "Filtrar por etiqueta" (aria-label only)
- [projFilterClear] — EN "Clear" / ES "Todos" (compact control — lengths deliberately matched)
- [projCount] / [projCountOne] — EN "{n} projects" / "{n} project", ES "{n} proyectos" /
  "{n} proyecto". `{n}` is substituted by `js/projects.js`; the count updates on every filter.
- [projEmpty] — EN "No projects match those tags." /
  ES "Ningún proyecto coincide con esas etiquetas."

**§1 search band** — built but **hidden** (`.search-band.is-hidden`, `display: none`). Revealed
by deleting that one class in `projects.html` when Phase 3 semantic search ships. The input is
inert and the band is a `<div>`, not a `<form>`, so Enter cannot navigate.
- [projSearchPlaceholder] — EN "Search my projects" / ES "Buscar proyectos"
  (set via `data-i18n-placeholder`, handled in `js/projects.js` — `main.js` does not do
  placeholders)
- [projSearchBtn] — EN "Search" / ES "Buscar"

**Per-entry strings** — five keys per project, all currently `TODO` in both languages:
`projNTitle`, `projNDesc` (one-line, index row), `projNLongDesc` (featured + sub-page),
`projNAlt` (image alt — omitted when the entry has no image), `projNSearch` (Phase 3 blob).

**Non-string fields** live in `js/projects-data.js`: `slug`, `dates`, `tags`, `imageSrc`,
`subpageUrl`, `featured`, `pinned`, `visible`, `unlisted`.

**Still to fill:**
- Tag vocabulary — the controlled list `PROJECT_TAGS` at the top of `js/projects-data.js`,
  currently `TODO Tag A` … `TODO Tag F`. **This is also open decision #2 on the experience.html
  sheet above** — the two pages should agree on whether they share one vocabulary.
- The project list itself, and which 2–3 are featured
- Per-project: title, one-line description, longer description, dates, tags, image, search text
- Thumbnail aspect ratio is settled: **4:3**, enforced on every row via `object-fit: cover`
  (plan.md open decision #4).

**Dead keys to clean up:** `projectsHeading` and `projectsBody` are still defined in
`translations.js` but no longer referenced — leftovers from the stub page, same as
`aboutHeading` / `aboutBody`.

---

## Notes for Claude Code

- Use `data-i18n="[key]"` on every element whose text is listed here.
- All display strings go into `js/translations.js` — never hardcode display text in HTML.
  Elements may be left empty in the HTML and filled entirely from `translations.js`.
- Placeholder strings are prefixed `TODO ` in **both** languages so they stay greppable.
  Keep that convention when adding new unfilled slots.
- Per-entry colors on experience.html bands are written as **inline styles** from the data
  array. That is a deliberate, documented exception to the "tokens live in `:root`" rule —
  per-entry values cannot live in `:root`. Do not "fix" it.
- If a string here disagrees with the code, the **code is not automatically wrong** — this file
  has drifted before. Check which one was updated more recently, reconcile, and update the
  status line at the top of that section.
- Visual reference available at: `references/mockup-v2-brass.html` (gitignored, local only)
