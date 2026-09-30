# Development Plan — gideonong.me

A living roadmap. Update this file as phases complete or change.
Claude Code: read this file at the start of each session alongside CLAUDE.md.

---

## Phase 0 — Setup (in progress)

- [X] Buy domain: gideonong.me (Porkbun)
- [X] Create GitHub repository (empty)
- [X] Create Vercel account
- [X] Install Git on local machine (git-scm.com)
- [X] Clone GitHub repo to local machine
- [X] Install Node.js (nodejs.org LTS) and Claude Code VS Code extension
- [X] Create initial project structure: CLAUDE.md, plan.md, index.html placeholder,
  css/style.css, js/main.js, js/translations.js, assets/ folders
- [X] Push initial structure to GitHub
- [X] Import GitHub repo into Vercel → auto-deploy on push
- [X] Connect gideonong.me in Vercel → update DNS A record and CNAME in Porkbun
- [X] Confirm site is live at gideonong.me (placeholder page)
- [X] Create Claude Project at claude.ai → upload CLAUDE.md, plan.md, resume, CV
  as project knowledge → move future chats to the project

---

## Phase 1 — Desktop Foundation

Goal: site is live on desktop with correct structure, confirmed palette, real content.

Design decisions to finalize first:

- ~~ Confirm color palette: Warm Neutral vs Bluebonnet vs Winecup Prairie~~
- [X] Confirm name display: "Gideon A. Ong" vs "Gideon Ong" (currently leaning A.)
- [X] Write EN hero description (capabilities-focused, not majors-focused)
- [X] Write ES hero description (translated/adapted, not just machine-translated)

Build:

> Checkbox convention: a Build box is ticked when the **structure and behavior** exist.
> Placeholder copy does not block the tick — final content is tracked in content.md and in
> Phase 3. Where a line below describes something different from what was actually built, the
> annotation says so rather than the line being quietly rewritten.

- [X] css/style.css: define all CSS custom property tokens, Google Fonts import
- [X] js/translations.js: initial EN + ES strings for home page
- [X] index.html: navbar (white, sticky), dev banner, hero, featured work, dark footer
- [X] about.html: built per Page Spec — about.html (§1–§6) below, which superseded the section
  list originally written on this line. The education / skills by category / honors / languages
  (EN/ES/FR) / interests content has **not** been placed on the page yet — §2–§6 are placeholders.
- [X] experience.html: Baker Hughes internship, McElroy Prototyping Lab, TURC research,
  Dr. Schultz grader role — scaffold built (2026-09-20). Roles, orgs, and dates are real;
  bullets, tags, photos, and employer band colors are still TODO. TURC is in the array with
  `visible: false` pending open decision #4 on that page.
- [X] projects.html: scaffold built (2026-09-20) per Page Spec — projects.html below: search
  band (§1, live keyword search since 2026-09-26), featured entries (§2), index + tag filter
  (§3), all rendered from `js/projects-data.js`. Six **placeholder** entries — the "real
  descriptions" this line originally called for come from the projects content interview,
  not from the scaffold.
- [X] js/main.js: language toggle (instant DOM swap, localStorage, navigator.language default)
- [X] Social link chips in hero: GitHub (gidgo130), LinkedIn (gideon-a-ong), email
- [X] "Download resume" button → new tab. Note: the flat `assets/pdfs/resume.pdf` path on this
  line is not what shipped — main.js links the newest `assets/pdfs/<type>/<lang> Gideon Ong
  <Label> <YYYYMMDD>.pdf` from the generated manifest `js/docs-data.js` (2026-09-26; the
  earlier date-probing is gone — see the decisions log).
- [X] Featured work section: image-forward layout, 1-2 projects — done 2026-09-26: `js/home.js`
  renders every `featured: true` + `listing: "index"` entry from `js/projects-data.js` with the
  projects.html §2 builders (shared via `js/data-helpers.js`). The hardcoded placeholder card
  and its keys are gone; a project's copy exists in exactly one place. Layout is a per-project
  `homeLayout` preset (stacked default, imageLeft, imageRight, collage) — see the schema.
- [ ] Deploy to gideonong.me → review on desktop (Chrome, Firefox, Safari) — auto-deploys from
  GitHub on push; the three-browser desktop review has not been done.

---

### Page Spec — about.html

> Drafted: 2026-09-17. Resolve all TBD items before handing to Claude Code for full build.
> Scaffold build (structure + JS behaviors, placeholder content) may proceed without TBD content.

**Purpose:** A personal-feeling page that progressively reveals who Gideon is — credentials,
biography, intellectual interests, interview preparation, AI philosophy, and visitor preferences.

#### §1 — Hero (name + identifiers + photo)

**Layout:** Two-column. Left: name (large, Lora serif) + dot-separated identifiers in
var(--bronze) below. Right: headshot photo, position: sticky so it stays fixed on right
as user scrolls into §2. Below photo: one "Download Resume" button (same style as index.html).

**Identifiers:**
- EN: `Engineer · Geographer · Federalist · Philomath`
- ES: `Ingeniero · Geógrafo · Federalista · Aprendiz eterno`
- Color: var(--bronze). Font: Lora, smaller than name. EN and ES versions are independent.

**Background:** var(--bg)

#### §2 — "Who am I?"

**Layout:** Two-column continues. Left: biographical text (2–3 paragraphs). Right: same
sticky photo, still fixed — appears to stay in place as section background changes around it.

**Background:** Distinct from §1 (var(--bg-section) or a new about-specific token — TBD).
Transition between §1 and §2 backgrounds is a smooth scroll-driven cross-fade, not abrupt.

**Button morph:** As scroll crosses from §1 into §2, the single "Download Resume" button
below the photo fades out and two stacked buttons fade in: **Download Full CV** and
**Download Transcript**. Same visual style as index.html resume button. Scroll-threshold
triggered — old button opacity → 0, two new buttons opacity → 1, stacked vertically.

**Content:** TBD — biographical paragraph(s), EN + ES via data-i18n.

#### §3 — "What have I been reading?"

**Layout:** Left column: vertically stacked book covers in an inset container. One cover
fully visible; adjacent covers peek slightly above/below (try both slight-peek and no-peek
variants — build slight-peek first). Right side (general page background, no card/block):
book title + description text.

**Scroll behavior:** Page scroll drives book stepping. Each book has a scroll distance
threshold — crossing it at sufficient velocity commits to the next book. Slow or
intermittent scrolling within the threshold does NOT trigger stepover (prevents accidental
advances on slow feed). Fast scroll can step multiple books.

**Text animation (CLAUDE.md carve-out — see below):** Exiting text: fades up-and-out
(~8–12px upward translation + opacity → 0). Entering text: starts slightly below rest
position, moves up + opacity → 1. Minimal displacement — subtle, not dramatic.

**Cover treatment:** Active cover at full opacity. Adjacent/inactive covers slightly dimmed.
No rotation or 3D effect. Covers stacked vertically.

**Maintainability:** Books defined in a JS data array. Each entry: cover image path, title
(EN + ES), description (EN + ES), visible: true/false. Reorder by changing array order;
hide by setting visible: false.

**Content:** TBD — list of books with cover images.

#### §4 — Interview FAQ

**Layout:** Full-width accordion stack. Items touch (no gap between them). Outer stack has
rounded corners as a unified block; internal borders divide items. No outer gap or margin
between items.

**Per item:** Left-side chevron (▶ collapsed / ▼ expanded) + question text. Clicking
expands inline, pushing content below down. Multiple items may be open simultaneously.

**Reference style:** TU Transfer Credit Policies accordion — rounded, touching, clean.
Chevrons left-aligned.

**Background:** Own section. Possible maroon/floral accent — TBD in color pass.

**Maintainability:** Questions defined in JS data array. Each entry: question (EN + ES),
answer (EN + ES), visible: true/false. Reorder by changing array order.

**Content:** TBD — brainstorm session in progress.
Confirmed candidates: Why mechanical engineering? What is the IELP program? Why Spanish?
Study abroad plans? Geography championships background? Career goals?

#### §5 — Statement on AI

**Layout:** Text-forward, long-form personal essay. Optional photo (TBD).
Tone: direct, personal, no corporate hedging.
Reference: sive.rs/ai, bydamo.la/p/ai-manifesto.

**Background:** Own section, subtle differentiation from §4.

**Content:** TBD — draft separately before full build. Use placeholder text for scaffold.

#### §6 — Viewing settings + Interesting sites

**Viewing settings (visitor-facing):**
- "Show pre-college" toggle — reveals Geography Championships, IGO medals, pre-college
  honors. Eagle Scout is always visible regardless of toggle state.
- Readability mode — larger text, increased line-height
- Colorblind mode — palette adjustment
- Dark mode toggle — CSS class swap (data-theme="dark" on <html>). Explicit exception to
  CLAUDE.md's no-toggle rule: that rule targets nav/footer; this is a dedicated settings
  panel. Overrides prefers-color-scheme. Existing dark-mode CSS token block handles styling.

**Interesting sites:** Manually curated external links. Eclectic, personally meaningful.
Tone reference: Atomic Rockets (projectrho.com). Per-link descriptions: TBD.

**Content:** TBD — site list, descriptions, toggle UI style (switches/checkboxes/pills).

#### Animation carve-outs (about.html only)

The following override CLAUDE.md's "opacity-only, no movement" animation rule.
They apply ONLY to about.html. State these explicitly in every Claude Code prompt for this page.

| Section | Effect | Implementation note |
|---------|--------|---------------------|
| §1→§2 boundary | Background cross-fade | Scroll-driven, not IntersectionObserver |
| §2 photo | Sticky parallax | position: sticky; top: [nav height] |
| §2 button swap | Resume → CV+Transcript morph | Scroll-threshold opacity transition |
| §3 text | Fade up-and-in / up-and-out | ~8–12px translateY allowed |
| §3 book covers | Active/inactive opacity states | Opacity variation across covers |

#### Open decisions for about.html

1. §2 background color token — same as var(--bg-section) or a new about-specific token?
2. §3 book covers — slight-peek vs. no-peek (build slight-peek first, compare)
3. §4 FAQ content — brainstorm session in progress
4. §5 AI statement — content draft TBD (placeholder for scaffold)
5. §6 interesting sites — list and descriptions TBD
6. §6 viewing settings — exact toggle UI style (switches? checkboxes? pills?)
7. Headshot photo — which photo? Placeholder OK for scaffold.
8. §4 section accent color — maroon/floral tones TBD in color pass

---

### Page Spec — experience.html

> Drafted: 2026-09-17. Resolve all TBD items before handing to Claude Code for full build.
> Scaffold build (structure + JS behaviors, placeholder content) may proceed without TBD content.

**Purpose:** A visual table of contents for Gideon's professional experience — each entry is
an expanded resume card linking to a dedicated full case-study sub-page. Larger and more
image-forward than projects.html; layout can vary per entry.

#### §1 — Hero

**Layout:** Photo collage fills the full hero background. Text overlays the left portion
via a gradient scrim. Collage photos sit on the right, visible and unobscured.

**Gradient scrim:** Left-to-right linear gradient using `var(--footer-bg)` (`#1C1510`) —
opaque on the far left where text sits, fading to fully transparent by the center-right.
Ensures readable text contrast while preserving the photos on the right side.

**Text content (foreground, left side):**
- Status sentence (EN): "Currently a Mechanical Engineering and Spanish IEL student at the
  University of Tulsa — seeking summer 2027 internships in engineering and Spanish."
  (ES: TBD — via `data-i18n`)
- Short paragraph below: more on current professional direction. (EN + ES: TBD content)
- Text color: `var(--footer-text)` (`#D4C9BB`) — readable against the dark scrim.

**Collage (background):** 3–5 photos in a CSS grid mosaic — some tall cells, some wide.
Representative of current professional life (machine shop, Baker Hughes, lab work).
Photos defined as `<img>` tags in HTML; updating = swapping image files and src attributes.

**Backup plan (if overlay reads poorly with actual photos):** Toggle to a 2-column layout
via a single CSS class — text left on `var(--bg)`, collage right, no overlay. Implemented
by adding/removing a `.hero--overlay` class on the section element. Build overlay first;
backup requires no new JS.

**Background:** The photo collage itself — no flat section background color.

**Size:** Taller and more visually prominent than hero sections on other pages.

#### §2 — Experience entries

**Order:** Mostly reverse chronological (most recent at top). Exceptions at content author's
discretion.

> **REVISED 2026-09-20.** The original spec described neutral-background cards with dotted
> dividers. Per the 2026-09-20 hand-drawn outline, entries are now **full-width bands**, each
> carrying a restrained tint of its employer's color. The per-entry content list below is
> unchanged; the container and color treatment are what changed.

**Band layout (default):** Each entry is a full-bleed section spanning the viewport width,
stacked vertically with no gap between bands — the background color change *is* the divider.
Inside the band, content sits in the standard centered content container (max-width, never a
fixed pixel width). Default inner arrangement: image left (~40%), text right (~60%).

**Per-entry color contract:** Each entry declares four tokens, scoped to its own section via
inline `style` on the band element (set from the data array, not hardcoded in CSS):

| Token | Purpose | Rule |
|-------|---------|------|
| `--entry-bg` | Band background | Employer primary mixed **12–20% over `var(--bg-section)`** — a tint, never the raw brand color |
| `--entry-border` | Top/bottom hairline and rule under the role title | Employer secondary at full or near-full strength |
| `--entry-accent` | "View full case study →" link, tag pill borders | Employer secondary, darkened if needed for contrast |
| `--entry-ink` | Body text within the band | Defaults to `var(--ink)`; overridden only if a tint forces it |

Rules that override any employer color:
- Body text must clear **4.5:1** against `--entry-bg`; large role titles must clear **3:1**.
  If an employer's color can't satisfy this at 20% tint, reduce the tint — do not lighten the text.
- Never use raw brand color as a full-strength background. The page must still read as one site.
- Employer **logos** are out of scope for this spec — color only. Revisit separately if wanted.
- Dark mode: `--entry-bg` re-mixes over the dark `--bg-section` token rather than reusing the
  light-mode value. Each entry needs both a light and a dark mix defined in the data array.

**Per entry:**
- Role title — large, Lora serif
- Organization + dates — DM Sans, `var(--muted)`
- 2–3 bullet highlights — DM Sans body
- Skill tag pills — small, same style as projects.html; placed below bullets. Tag IDS from
  the shared `js/tags-data.js` vocabulary, labels translated.
- "Projects from this role" (2026-09-26) — after the tags, only when at least one
  `listing: "index"` project in `js/projects-data.js` points at this band via `experience`.
  Title (→ `projects.html#<slug>`) + one-line description per project, in project sort order.
- "View full case study →" link — `var(--entry-accent)`; omitted while `subpageUrl` is ""

**Layout presets:** Layout variation is a named preset on the data object, not bespoke HTML.
Each preset maps to a single CSS class on the band. Initial set:

| `layout` value | Class | Description |
|---------------|-------|-------------|
| `"imageLeft"` | `.exp-band--image-left` | Default. Image ~40% left, text ~60% right. |
| `"imageRight"` | `.exp-band--image-right` | Mirrored. Used to break rhythm, not to alternate globally. |
| `"fullBleed"` | `.exp-band--full-bleed` | Wide image above, text below. For entries with strong photography. |
| `"textOnly"` | `.exp-band--text-only` | No image. Text sits in a narrower measure, centered. |

Adding a preset later means one new class — never a one-off markup fork for a single entry.

**Current-role flag:** Exactly one entry may carry `status: "current"`. The page reads this
flag and does two things automatically:
1. Sets the hero status sentence from that entry (role + org), via a `data-i18n` key pair.
2. Applies `.exp-band--current` to that band — a `--entry-accent` left edge rule and a small
   "Current" eyebrow label above the role title (EN/ES via `data-i18n`).

This is an **author-side flag**, not a visitor-facing toggle. Changing jobs = editing one
field. If no entry has `status: "current"`, the hero falls back to the student status sentence
and no band gets the current treatment — this fallback must work, not error.

**Maintainability:** All entries defined in `js/experience-data.js`. Each object
(schema as of 2026-09-26 — see CLAUDE.md → Data conventions):
```js
{
  slug: "",               // unique; band id (experience.html#<slug>) and the target of a
                          // project's `experience` field. Keys: exp<SlugCamel>Role / Org / BulletN
  roleKey: "",            // i18n key → EN + ES
  orgKey: "",             // i18n key — full string, band + hero ("…, University of Tulsa")
  orgShortKey: "",        // OPTIONAL i18n key — short form for "Part of: <org> →" links
  imageAltKey: "",        // i18n key for the band image's alt (required with imageSrc)
  dates: { from: { season: "summer", year: 2026 } },   // language-neutral (2026-09-27):
                          //   from/to points are { season, year } | { month, year } | { year };
                          //   to may be "present" or a point. Rendered per language.
  sortDate: "YYYY-MM",    // the ONLY thing ordering reads — newest first; array order is ignored.
                          //   The dev check flags a sortDate that disagrees with `dates`.
  bulletKeys: [],         // i18n keys → EN + ES
  tags: [],               // tag IDS from js/tags-data.js — every pill links to projects.html?tag=<id>
  imageSrc: "",
  subpageUrl: "",         // "" = no case-study page yet → link omitted (all "" today: none exist)
  layout: "imageLeft",    // preset name — see table above
  status: null,           // "current" on at most one entry, else null
  color: {
    light: { bg: "", border: "", accent: "" },
    dark:  { bg: "", border: "", accent: "" }
  },
  visible: true           // false → hidden, and no longer a valid `experience` link target
}
```
Hide with `visible: false`. Related projects are not stored here — a band lists every
`listing: "index"` project whose `experience` equals its slug.

**Current entries (sortDate order, content loaded 2026-09-27):**
1. `baker-hughes` — Baker Hughes, Claremore OK — Engineering Intern, ALS R&D (Summer 2026), imageLeft
2. `machine-shop` — McElroy Prototyping Lab, University of Tulsa — Machine Shop Technician
   (Spring 2026 – present, `current`), imageRight
3. `schultz-grader` — Dr. Joshua Schultz, University of Tulsa — Grader & Data Analyst
   (Spring 2026 – present), textOnly
4. `turc` — Dr. Janica Edmonds, University of Tulsa — Undergraduate Research Assistant, TURC
   (Summer 2025), imageLeft
5. `esl-tutor`, `church-media`, `senior-patrol-leader` — pre-college, `visible: false`, EN role
   title only (org / dates / ES pending)

**Sub-pages:** Each entry may link to `/experience/[slug].html` (e.g.,
`/experience/baker-hughes.html`). Sub-pages are full case studies with flexible sections
per role. Structure TBD per role — spec separately before building sub-pages. Every
`subpageUrl` is "" as of 2026-09-26 because none of the pages exist; fill it in when one ships.

**Background:** Per-band `--entry-bg` (see color contract above). The entries section as a
whole has no single background — each band supplies its own. `var(--bg)` remains the fallback
for any entry with no color defined.

#### Animation

No CLAUDE.md carve-outs required for experience.html. Standard rules apply:
- Scroll-triggered fade-in on band content: IntersectionObserver, opacity 0→1, ~300ms, no movement.
  The band background itself does NOT fade in — it is painted at first render, so there is no
  color flash on scroll.
- Hover on links and tags: color transition only, ~150ms ease.

#### Open decisions for experience.html

1. Hero text — status sentence + paragraph (EN + ES) — TBD content before full build
2. Hero collage photos — TBD; placeholder images OK for scaffold build
3. Overlay vs. backup — build overlay first; evaluate once real photos are in place
4. TURC research — include as an entry? Confirm before build
5. Skill tags per entry — TBD per role. The vocabulary question is settled structurally
   (one shared list in `js/tags-data.js`, 2026-09-26); the real tag names are still open.
6. Sub-page structure — spec separately per role before building sub-pages. `subpageUrl`
   values are blank until then, so the 404 links are gone.
7. Layout preset per entry — which entry uses which preset? Decided at content time
8. Hero text color in dark mode — verify `var(--footer-text)` contrast in dark token block
9. Employer color values (light + dark mix) per entry — TBD; scaffold uses neutral tints
10. Hero-to-first-band transition — does the collage hero butt directly against Band 1, or is
    there a neutral breather strip between them? Evaluate once real photos are in.

---

### Page Spec — projects.html

> Drafted: 2026-09-20 from Gideon's hand-drawn outline. Resolve all TBD items before handing
> to Claude Code for full build. Scaffold build (structure + JS behaviors, placeholder content)
> may proceed without TBD content.

**Purpose:** The complete record of Gideon's technical work. Three zones in descending order of
visual weight: a search band, a small curated **featured** set, and a complete **index** of
everything. Featured shows depth; the index shows range. The page must not read as one repeating
layout loop top to bottom — the index is deliberately more compact than the featured block above it.

#### §1 — Search band

**Status:** LIVE — keyword search (2026-09-26). The band was built hidden on 2026-09-20 and
unhidden once the search worked.

**Layout:** Full-bleed band directly below the nav/dev-banner. Search input (with a × clear
control shown only while it has text — aria-label `projSearchClear`) + search button,
horizontally centered. Closed off at the bottom by a 2px accent rule in `var(--bronze)` —
the rule is the transition into the featured section.

The band is a `<div>`, **not a `<form>`**, and the button is `type="button"`: Enter is handled
by `js/projects.js` and can never navigate. The placeholder is set from
`data-i18n-placeholder` by `js/projects.js`, because `main.js` handles `data-i18n` and
`data-i18n-alt` but not placeholders.

**Behavior (built):**
- Runs as the visitor types (debounced ~150ms); Enter and the button run it at once; × clears.
- Matching: the query is split on whitespace and every token must appear (AND) as a
  substring of the entry's corpus. Both sides are lowercased and diacritic-stripped
  (`normalize("NFD")` + remove combining marks), so "diseño" and "diseno" match each other.
- Corpus per entry, built once from BOTH languages regardless of the active one: title, desc,
  longDesc, searchText, tag labels, context label, and the linked experience's role + org.
  A Spanish word matches while the page is in English and vice versa.
- Combines with the tag filter (AND). The count and the empty state reflect both:
  `projEmpty` when only tags are active, `projEmptySearch` ("No projects match "{q}"." /
  "Ningún proyecto coincide con «{q}».") when a query is active.
- Query state lives outside `render()` like the tag state, so a language switch keeps the
  query, the result set and the count.
- Only `listing: "index"` entries are searchable. Featured §2 is never filtered.
- All matching sits behind one function, `searchEntries(query, entries) → entries`.

**Background:** Visually distinct from both `var(--bg)` and `var(--bg-section)` — this is the
"innovative background" in the outline. Candidate treatments to compare in the color pass:
a) `var(--footer-bg)` dark band with light text (bookends the dark footer)
b) `var(--bg-section)` with a subtle texture or gradient
c) A bronze-tinted wash
**RESOLVED 2026-09-27: (c) bronze wash.** Built 2026-09-20 as a `--bg-section` → `--bg`
gradient, briefly a solid `--bg-section` (which matched the featured section under it), now a
per-palette `--search-bg` token: bronze ≈10% over `--bg-section` (light #E0D7C2, dark
#32291A). (a) dark and the page background were weighed and passed over.

**Placeholder text:** EN "Search my projects" / ES "Buscar proyectos" — via `data-i18n`.
Keep EN and ES close in character length per the CLAUDE.md compact-element rule.

**Phase 3 behavior:** TF-IDF + cosine similarity over the same corpus, run in vanilla JS.
Phase 3 now only upgrades the BODY of `searchEntries()` — same signature, same return shape.
It may return the entries reordered by score; `applyFilter()` already lays the rows out in the
order it returns. No markup, no caller, no i18n change.

#### §2 — Featured projects

**Count:** 2–3 entries. Sourced from the same data array as §3 via `featured: true` — never a
second copy of a project's content.

**Layout:** Full-width image as the visual anchor, per entry. Arrangement alternates:
entry 1 image-left / text-right, entry 2 text-left / image-right, matching the outline.
Alternation here is fine because the set is small and fixed; this is the one place a global
alternating rule applies.

**Per entry:** Image → title (Lora) → "<Context> · <dates>" meta → description (DM Sans) →
tag pills → "Part of: <role>, <org> →" (only when `experience` is set) → "View project →" link.
**Tags go below the description, never above the title** (CLAUDE.md).

**Background:** `var(--bg-section)`, per the index.html featured-work convention. The
index.html featured block uses these same builders (`js/data-helpers.js`) since 2026-09-26.

#### §3 — Project index

**Format:** **List rows** (single column), with a grid-view hook reserved for later.

Per row: thumbnail left (~140–180px, fixed aspect ratio, `object-fit: cover`) — title,
one-line description, and tag pills right. Rows separated by a dotted `border-bottom` in
`var(--border)`. No card borders, no drop shadows.

Rationale (recorded so it isn't relitigated): the featured block above is already image-forward,
so the index's job is coverage, not impression. Rows also absorb the ~20% EN→ES length swing
without breaking alignment, and degrade cleanly when an entry has no photograph — both of which
a fixed-height card grid does not.

**Grid toggle hook:** The index container carries a modifier class — `.project-index--rows`
(default) or `.project-index--grid`. Both classes are written in `style.css` in Phase 1; only
rows is used. Switching views later is a class swap, with **no change to the data array or the
generated markup**. A visitor-facing view switcher is Phase 3 at the earliest, and optional.

Both classes are written as of 2026-09-20, and the swap was exercised in-browser: with
`--grid` applied, the six entries render as cards (3-up at 1280px, 1-up at 375px), thumbnails
hold the same 4:3 ratio, and the no-image entry becomes a text card. No data or markup changed.
Grid cards are not forced to a common height — a text-only card is shorter than its neighbors,
which is exactly the fixed-height-grid problem the rows view was chosen to avoid. Decide that
before ever making grid the default.

**Missing images:** An entry with no `imageSrc` renders with no thumbnail and the text occupying
the full row width. It must not render a broken image, a grey box, or a generic placeholder icon.

**Tag filter — REVISED 2026-09-27 (clickable tags, no filter row).** The always-visible row
of filter pills above the index is gone. Instead every tag pill on the site — index rows,
featured entries, experience bands, sub-pages — is a link to `projects.html?tag=<id>`.
projects.html reads `?tag=` on load, filters the index (AND with the keyword search), and
shows a small "<Tag label> ✕" chip beside the count; ✕ clears the tag and rewrites the URL
with `history.replaceState`, so a tag view is always linkable. One tag at a time. An unknown
id is ignored. A language switch keeps it (state lives outside `render()`); a `#<slug>` deep
link clears it. Filtered-out rows are removed from flow (`display: none`) so the list closes
up rather than leaving gaps.

- Pills: pointer cursor ONLY — no hover effect, no enlarged tap target (Gideon: they must not
  distract from the content). `:focus-visible` outlines stay.
- The chip is filled `var(--bronze)` with `var(--bg)` text, not a literal white — in dark mode
  `--bronze` lightens and `--bg` darkens, so the pair stays legible in both themes.
- A live count ("8 projects" / "8 proyectos") sits beside the chip and updates on filter.
- If the tag + search combination yields zero results, show a short empty-state line
  (`projEmpty` tag-only, `projEmptySearch` with a query) — never a blank page.
- A pill click on projects.html itself is a plain link: the page reloads and a typed search
  is lost. Accepted (2026-09-27) for simplicity.

Still true from the 2026-09-20 build:
- The count has separate singular and plural keys (`projCountOne` / `projCount`), so one match
  reads "1 project" / "1 proyecto" rather than "1 projects".

*(The original 2026-09-20 spec — a multi-select AND row of pills with a "Clear"/"Todos" reset,
narrowed to tags in use — shipped and was removed on 2026-09-27; see the decisions log.)*

**Order:** `sortDate` descending (2026-09-26 — array order no longer matters). A `pinned: true`
field lifts an entry to the top of the index independently of the featured flag.

**Deep links (2026-09-26):** every index row carries `id="<slug>"`. Landing on
`projects.html#<slug>` (or a hashchange) clears any active tags and query, scrolls the row
clear of the sticky nav + dev banner (`scroll-margin-top`), and adds `.is-target` — a static
`var(--bronze)` left rule, no animation. A language re-render re-marks without scrolling.

**Background:** `var(--bg)`.

#### Maintainability — `js/projects-data.js`

One array, single source of truth for §2, §3 AND the index.html featured block.
Schema as of 2026-09-26 (see CLAUDE.md → Data conventions):

```js
{
  slug: "",               // URL slug → /projects/[slug].html; also the row id (projects.html#<slug>)
  titleKey: "",           // i18n keys, named by slug: proj<SlugCamel>Title / Desc / LongDesc /
  descKey: "",            //   Alt / Search  (e.g. "todo-project-1" → projTodoProject1Title)
  longDescKey: "",
  dates: { from: { season: "spring", year: 2026 } },   // language-neutral (2026-09-27):
                          //   { from: <point> } | { from, to: "present" } | { from, to: <point> }
                          //   point = { season: spring|summer|fall|winter, year } | { month: 1–12, year } | { year }
  sortDate: "YYYY-MM",    // the ONLY thing ordering reads — newest first. The dev check flags
                          //   a sortDate that disagrees with `dates` (to when a point, else from)
  context: "coursework",  // industry | coursework | personal | service | research
                          //   → "<Context> · <dates>" meta line via ctxIndustry … keys
  tags: [],               // tag IDS from js/tags-data.js — never labels; pills link to ?tag=<id>
  imageSrc: "",           // "" is valid — renders without a thumbnail
  imageAlt: "",           // i18n key — required whenever imageSrc is set
  subpageUrl: "",         // "/projects/<slug>.html" once the file exists, else "" — the
                          //   "View project →" link is then omitted. Dev check HEADs each one.
  featured: false,        // true → also rendered in §2 and on index.html (index tier only; max 3)
  featuredOrder: 1,       // OPTIONAL — order among the featured blocks (home + §2), ascending
  pinned: false,          // true → lifted to top of §3
  searchTextKey: "",      // i18n key — EN + ES blob folded into the search corpus
  listing: "index",       // "index" | "unlisted" | "hidden"  ("nested" reserved — see below)
  experience: "",         // experience slug this project belongs to, or ""
  homeLayout: "stacked",  // OPTIONAL, index.html featured block only (default "stacked"):
                          //   "stacked" | "imageLeft" | "imageRight" | "collage"
  gallery: [              // OPTIONAL, collage only — 1–3 EXTRA images after imageSrc
    { src: "", altKey: "" }   //   altKey = proj<SlugCamel>Gallery<N>Alt
  ],
  page: {                 // OPTIONAL (2026-09-27) — sub-page content for js/project-page.js.
    sections: [{ headingKey: "", bodyKey: "" }],   //   proj<SlugCamel>Section<N>Heading / Body
    facts:    [{ labelKey: "", valueKey: "" }],    //   proj<SlugCamel>Fact<N>Label / Value
    photos:   [{ src: "", altKey: "" }],           //   proj<SlugCamel>Photo<N>Alt
    reportPdf: "",        //   optional "Read the report →" link (new tab)
    creditKey: ""         //   optional photo credit line, proj<SlugCamel>Credit
  }                       // Every part optional; a missing part renders nothing.
}
```

**Sub-pages (2026-09-27):** one renderer, `js/project-page.js`, and one shell per page at
`projects/<slug>.html` — same nav / dev banner / footer / language toggle as every page, all
paths `../`, `<body data-slug="<slug>" data-root="../">`, a static English `<title>` and meta
description that the renderer replaces from the entry on every render (and on language
change), and an empty `<main id="project-page">`. Layout: hero image (imageSrc, 16:9) → title →
"<Context> · <dates>" → "Part of" link → sections → photo grid (2-up desktop, 1-up mobile, each
opens the full image in a new tab) → quick-facts box → report link → credit → tags → "← All
projects". `data-root` is read by `js/main.js` and `js/data-helpers.js` so the shared builders
(document links, images, tag links, "Part of" links) work from `/projects/`. Listing tiers on a
sub-page: `index` and `unlisted` render for everyone; `hidden` renders on localhost only. Scaffold:
`projects/todo-project-2.html` for the hidden `todo-project-2` entry. No sitemap for now.

**Home featured presets (2026-09-26):** `homeLayout` is read by `js/home.js` only; projects.html
§2 keeps its alternating image-left / image-right and ignores it. `siteData.buildFeatured(entry,
i, options)` takes `options.layout` and maps each preset to one class (`.featured-entry--stacked`
/ `--image-left` / `--image-right` / `--collage`); same markup order and data for all four.
stacked = full-width 16:9 image, text below (the CLAUDE.md home spec, now the default).
collage = full-width 16:9 grid, cells = imageSrc then gallery: 2 → two columns; 3 → imageSrc
large left (2/3) + two stacked right; 4 → 2×2; below 768px 3 becomes large on top + two below.
Fallbacks, never an error: collage with no usable gallery → stacked; no imageSrc → text only.

**Listing tiers** (replaced the `visible` + `unlisted` pair on 2026-09-26):
- `"index"` — in the §3 index, the tag filter, search, and its role's "Projects from this
  role" list; may be featured.
- `"unlisted"` — direct URL only. Excluded from the index, bands, filter, featured and search.
  This is how the "unlinked pages" decision (politically-sensitive or selectively-shared work)
  is implemented — the entry lives in the array so its sub-page can be generated, but it never
  appears in any listing.
- `"hidden"` — excluded everywhere.
- `"nested"` — **reserved, not implemented.** For role-bound minor projects: shown on their
  band, and surfaced in the index only under an active filter or search. An entry set to it
  renders nowhere and the dev check warns. Build it when the index passes ~30 rows or 4+ minor
  role-bound items exist.

**Two-way links:** `experience` is the one field. Project → role: "Part of: <role>, <org> →"
(`projPartOf`, placeholders filled from the role's keys) below the tags on featured entries and
index rows, to `experience.html#<slug>`. Role → projects: the band lists every index project
pointing at it. Only a visible role is a valid target; the dev check warns otherwise.

**Tag vocabulary:** ONE controlled list, shared by projects and experience, in `js/tags-data.js`
as `{ id, key }` pairs (2026-09-26 — replaced `PROJECT_TAGS`). Data files store ids; pills and
filter buttons show the translated label; filter state stores ids so a language switch keeps the
active filter. The real tag names are still **TBD** — draft them during the content interview.
Six project placeholders `todo-a` … `todo-f` plus the ten ids carried over from
experience.html's former free-string tags are in the file today.

#### Animation

No CLAUDE.md carve-outs required. Standard rules apply:
- Scroll-triggered fade-in on featured entries: IntersectionObserver, opacity 0→1, ~300ms, no movement.
- Tag filter transitions: opacity only. Rows must not slide or animate position — reflow is instant.
- Hover on rows, links, and tags: color transition only, ~150ms ease.

#### Open decisions for projects.html

1. Search band background treatment — (b) section-tint is **built** and now visible; comparing
   it against (a) dark and (c) bronze wash is still open, deferred to the color pass.
2. Tag vocabulary — drafted during the content interview. Placeholders are in place. The
   shared-or-separate question is **settled**: one list in `js/tags-data.js` for both pages
   (2026-09-26). The names themselves are still open.
3. Project list — which projects, and which 2–3 are featured? Content interview
4. ~~Thumbnail aspect ratio~~ — **RESOLVED 2026-09-20: 4:3**, enforced on every row and every
   grid card via `object-fit: cover`. See the decisions log.
5. Index row density — one-line description vs. two. Evaluate once real descriptions exist
6. ~~Sub-page structure~~ — **RESOLVED 2026-09-27**: one shared renderer + one shell per page
   (see "Sub-pages" under Maintainability). Filling the three featured projects' pages is the
   content session's job. `subpageUrl: ""` still omits the link until a page file exists.
7. Whether a visitor-facing rows/grid view switcher is worth building at all (Phase 3, optional).
   Both view classes now exist and the swap is verified, so this is purely a product question —
   no build risk either way.

---

## Phase 2 — Responsive + Polish

Goal: site works cleanly on phone and tablet; typography and visual polish complete.

- [X] Mobile nav: hamburger menu (☰) at 768px breakpoint → vertical link dropdown — built on
  all four pages; closes on link tap, outside click, and Escape
- [ ] Review all pages at 375px (iPhone SE), 768px (iPad), 1280px (desktop) — projects.html
  verified at all three, light and dark, on 2026-09-20. index / about / experience not
  re-reviewed since their own builds.
- [ ] Typography pass: review practicaltypography.com Line Length, Font Size, Bold/Italic
  sections before adjusting any font sizes or line heights
- [ ] Scroll-triggered fade-ins: IntersectionObserver on project cards and sections — partly
  done: experience.html band content and projects.html featured entries fade in (opacity only,
  ~300ms). index.html has no observer, and about.html uses its own scroll-driven effects under
  the carve-outs. Index rows deliberately do **not** fade on scroll — they only transition
  opacity under the tag filter, so a filter change is never mistaken for a scroll animation.
- [ ] Optimize all images (compress, correct dimensions, add alt text to every image)
- [ ] Add real project photos, diagrams, and embedded PDFs where available
- [ ] Cross-browser test (Chrome, Firefox, Safari desktop + mobile)
- [ ] Review "under development" banner — hide when ready to go live

---

## Phase 3 — Content Complete + Features

Goal: all content live, recruiter-ready, smart search implemented.

Content:

- [ ] All projects with final descriptions, photos, videos, tag lists, and report links
- [ ] Create unlinked project pages (not in nav, accessible by direct URL)
- [ ] Final hero description (both EN and ES) reviewed and edited
- [X] Add Open Graph metadata tags to all pages (controls LinkedIn/social preview image) —
  **done 2026-09-29**: static EN og/twitter block on the 4 main pages and 3 sub-pages, cards
  in assets/images/og/ from scripts/make-og-cards.py (CLAUDE.md → Link previews).

Features:

- [X] Tag filter system on projects.html — **shipped early: built in the Phase 1 scaffold,
  2026-09-20**, then **revised 2026-09-27**: the filter row is gone; every tag pill on the site
  links to `projects.html?tag=<id>`, which filters the index (AND with search) and shows a
  "<Tag> ✕" chip. Live count, zero-result empty state, `display: none` on filtered rows,
  translated labels from `js/tags-data.js`. The real vocabulary drops in without touching
  the filter code.
- [ ] Semantic search on projects.html:
  **Keyword search shipped 2026-09-26** — the band is live, debounced, AND over tokens,
  diacritic-insensitive, both languages indexed, combined with the tag filter (see §1 of the
  page spec). What remains here:
  Phase 3a: TF-IDF + cosine similarity in vanilla JS — replaces the body of
  `searchEntries(query, entries)` in `js/projects.js` only. No markup or caller changes.
  Phase 3b (optional upgrade): Transformers.js in-browser embeddings (more semantic)
- [ ] Clean URLs (`/about`, `/projects/g-view`) — soon; Live Server must keep working.
  Today there is no vercel.json, so only the `.html` form works (`/about` is a 404; checked
  2026-09-29). Candidate routes, decision pending:
  (a) `vercel.json { "cleanUrls": true }`, links left as `.html` — Live Server untouched,
      but every click in production takes a 308 redirect to the clean form;
  (b) the same plus links rewritten to the clean form — plain Live Server can't serve
      `/about`, so local preview needs a small server that emulates cleanUrls;
  (c) folder-per-page (`about/index.html` → `/about/`) — works in Live Server and on Vercel
      with no config, but every page's relative paths and `data-root` change.
  Any route must also update: og:url in all 7 heads (CLAUDE.md → Link previews),
  `subpageUrl` in js/projects-data.js and the dev-check probes, the editor's
  `"/projects/<slug>.html"` convention (create_shell / rename_entry in
  scripts/editor/core/site/service.py, and datacheck.py), CLAUDE.md, and a LinkedIn Post
  Inspector re-scrape of every shared link. Check /learning's folder URLs and its
  trailing-slash script under the chosen route before deploying.
- [ ] Language detection refinement: add IP geolocation (free API) for regional default
- [ ] Flag-based EN/ES toggle (cosmetic — replace pill buttons with small flag icons)

---

## Phase 4 — Long-term / Optional

Goal: site evolves from career tool to broader personal site.

- [ ] Blog or research notes section
- [ ] Research paper page (when first paper is published)
- [ ] "Hire Me" button in footer → template offer letter or contact form
- [ ] Upgrade semantic search to Transformers.js (if TF-IDF proves insufficient)
- [ ] Scroll-driven parallax image clip effects for featured work
- [ ] Remove "under development" banner permanently
- [ ] Transition site tone from student-career to researcher-practitioner as appropriate

---

## Learning section — /learning

A separate track, not planned in this file. The unlisted teaching pages at
gideonong.me/learning/ have their own plan, status and decisions log in
`learning/learning-plan.md`, their rules in CLAUDE.md → "/learning", and their working manual
in `learning/README.md`.

---

## Decisions log

(Add dated entries as design and content decisions are made.)

[2026-09] Palette: brass/gold (#6B4F1A) accent confirmed. Background under discussion —
comparing Warm Neutral (#FAFAF8 base), Bluebonnet (#F5F7FC + #2E4D7B), Winecup Prairie
(#FAF6F5 + #7A3050 + sage #5C7A56). Navbar confirmed white (#FFFFFF) in all palettes.

[2026-09] Nav order: Projects · Experience · About (About rightmost per Gideon's preference).
Home is implicit — clicking the name/logo returns to index.html.

[2026-09] Name: "Gideon A. Ong" as formal display name (middle initial for career context).
"Gideon" used in conversational body copy. No subtitle text above the name in hero.

[2026-09] Bilingual: EN primary default (with ES italic below in hero). Language switches
via toggle — both versions always visible in hero, swapping primary/secondary role.
navigator.language detection on first visit; localStorage saves choice.

[2026-09] Featured work: image-forward (eater.net-inspired), 1-5 projects rotating.
Tags placed below project description, not above title.

[2026-09] Social links: tonsky.me-style small bordered chips in hero row.
GitHub (gidgo130), LinkedIn (gideon-a-ong), email/contact.

[2026-09] Semantic search: planned Phase 3. First pass: TF-IDF + cosine similarity in
vanilla JS. Optional: Transformers.js (in-browser sentence embeddings, no API call).
"Search my experience" button as placeholder in hero from Phase 3 onward.

[2026-09] Unlinked pages: confirmed. Files exist at URL, not linked from nav.
Used for politically-sensitive or selectively-shared projects.

[2026-09-17] about.html page spec drafted and finalized. See Phase 1 → Page Spec — about.html.

[2026-09-17] about.html §1 identifiers confirmed:
EN: "Engineer · Geographer · Federalist · Philomath"
ES: "Ingeniero · Geógrafo · Federalista · Aprendiz eterno"
(EN and ES are independent — not translations of each other.)

[2026-09-17] about.html §6 dark mode toggle: CSS class swap (data-theme="dark" on <html>),
surfaced in the Viewing Settings panel. Explicit exception to CLAUDE.md's no-toggle rule —
the rule targets nav/footer placement; a dedicated settings panel is exempt.

[2026-09-17] experience.html page spec drafted and finalized. See Phase 1 → Page Spec — experience.html.

[2026-09-17] experience.html hero: gradient scrim overlay (--footer-bg left → transparent
right) over photo collage. Backup: 2-column text/collage via .hero--overlay CSS class toggle.

[2026-09-17] experience.html cards: image left (~40%), text right (~60%) as default layout.
Each entry links to a dedicated /experience/[slug].html case-study sub-page. Entries defined
in a JS data array with visible flag for easy maintenance.

[2026-09-20] projects.html scaffold built: §1 hidden search band, §2 featured, §3 index with
tag filter. Structure and behavior are real; all six entries are placeholders. New files:
js/projects-data.js (data + PROJECT_TAGS vocabulary) and js/projects.js (renders §2 and §3,
runs the filter). Content intake sheet is in content.md.

[2026-09-20] projects.html thumbnail aspect ratio: **4:3**, enforced on every index row and
every grid card via object-fit: cover. Closes open decision #4. Chosen because it matches the
4:3 band images on experience.html (one image vocabulary, not two), stays tall enough beside
three lines of text at a 140–180px column where 16:9 reads as a sliver, and crops landscape
shop and CAD photography far less than 1:1.

[2026-09-20] projects.html §2 and §3 read one array. `featured: true` promotes an entry into
the featured block and it still appears in the index. There is no second data source and no
duplicated copy — the same rule content.md asks for on index.html featured work, which is
still outstanding there.

[2026-09-20] projects.html search band ships hidden behind a single class
(.search-band.is-hidden). Background treatment (b) built; (a) still worth comparing. The band
is a div, not a form, so the inert input cannot navigate on Enter. *(Superseded 2026-09-26:
the band is live with keyword search; see that entry.)*

[2026-09-20] projects.html index view: rows are the default; .project-index--grid is written
in style.css but unapplied. Verified in-browser that switching is a class swap with no data or
markup change. Grid cards are not height-matched, which is the fixed-height-grid weakness the
rows view was chosen to avoid — settle that before ever making grid the default.

[2026-09-20] Tag filter shipped in Phase 1 rather than Phase 3. It is annotated in place in the
Phase 3 list rather than moved, so the original phase plan stays readable.

[2026-09-26] Data conventions + keyword search session. No new content; the six placeholder
projects and four experience entries were migrated. Recorded in CLAUDE.md → Data conventions.
1. **Listing tiers.** `visible` + `unlisted` on projects replaced by one field,
   `listing: "index" | "unlisted" | "hidden"`. `"nested"` is RESERVED and not implemented:
   role-bound minor projects shown on their band and surfaced in the index only under an
   active filter or search. Build trigger: the index passes ~30 rows, or 4+ minor role-bound
   items exist. Until then an entry set to it does not render and the dev check warns.
   Experience entries keep their `visible` boolean.
2. **Two-way project ↔ experience links** from a single project field, `experience: "<slug>"`.
   Experience entries gained `slug` (baker-hughes, machine-shop, schultz-grader, turc); bands
   carry `id="<slug>"`, index rows `id="<slug>"`. Project → role: "Part of: <role>, <org> →"
   below the tags (`projPartOf`). Role → projects: "Projects from this role"
   (`expRelatedHeading`) after the band's tags, index-tier projects only. Deep links clear the
   filter/query, scroll clear of the nav, and mark the target with a static bronze left rule.
   Every experience `subpageUrl` was blanked — none of the case-study pages exist.
3. **Keyword search** is live in the §1 band: debounced typing / Enter / button, × to clear,
   whitespace-token AND matching, diacritic-insensitive, corpus built from both languages
   (title, desc, longDesc, searchText, tag labels, context, linked role + org), combined with
   the tag filter by AND, `projEmptySearch` empty state, query preserved across a language
   switch, featured never filtered. All matching is `searchEntries(query, entries)`; Phase 3
   TF-IDF replaces its body only.
4. **Context + sort.** `context: industry | coursework | personal | service | research`
   renders as "<Context> · <dates>". `sortDate: "YYYY-MM"` on projects and experience entries
   is the only ordering input (descending; `pinned` still lifts a project). Array order is
   irrelevant now.
5. **Shared, translatable tags.** `js/tags-data.js` (`TAGS = [{ id, key }]`) replaces
   `PROJECT_TAGS`; both data files store ids; labels come from translations.js; filter state
   stores ids. The ten former free-string experience tags became ids with "TODO "-prefixed ES
   labels pending the vocabulary interview. Settles the shared-or-separate question.
6. **Keys named by slug**: `proj<SlugCamel>Title / Desc / LongDesc / Alt / Search`. Dead keys
   `projectsHeading`, `projectsBody`, `aboutHeading`, `aboutBody`, `featuredCardTitle`,
   `featuredCardDesc` deleted.
7. **Home featured** renders from `js/projects-data.js` (`featured` + `listing: "index"`) via
   `js/home.js`, using the §2 builders shared in `js/data-helpers.js`. Closes the Phase 1 box.
8. **Dev-only data check** (`siteData.checkData`, console.warn only) on projects.html and
   experience.html load. New shared file `js/data-helpers.js` holds selectors, builders,
   deep-link targeting and the check; every page loads `tags-data → experience-data →
   projects-data → data-helpers` before its page script.
   Placeholder `todo-project-6` is set to `listing: "unlisted"` (with a Baker Hughes link) so
   the exclusion path is exercised by the scaffold, like the no-image and no-sub-page cases.

[2026-09-26] Home featured layout presets. The CLAUDE.md home spec (full-width 16:9 image,
text below) is the DEFAULT of a per-project `homeLayout` preset — "stacked" | "imageLeft" |
"imageRight" | "collage" — read only by index.html; projects.html §2 is unchanged and keeps its
alternation. "collage" adds `gallery: [{ src, altKey }]` (1–3 extra images) to `imageSrc` in a
full-width 16:9 grid (2 → two columns, 3 → large left + two stacked right, 4 → 2×2; on phones 3
becomes large on top + two below). One builder for all four; fallbacks never error (collage
without gallery → stacked; no imageSrc → text only). Dev check warns on unknown homeLayout,
gallery on a non-collage entry, >3 items, items missing src/altKey, altKey without EN/ES.
Scaffold state: `todo-project-1` stacked, `todo-project-2` collage with two placeholder images.

[2026-09-26] Documents: date probing replaced by a generated manifest. `js/main.js` no longer
HEAD-probes `assets/pdfs/` dates backward from today (the mechanism behind the 2026-09-17
request-flood outage) and no longer caches anything in localStorage (old `docUrl_*` keys are
removed once on load). `scripts/build-docs-manifest.js` (Node built-ins only) scans
`assets/pdfs/{resume,cv,transcript}` for correctly named files, picks the newest date per type
and language, and writes `js/docs-data.js` (`const DOCS`, sorted keys, rewritten only on
change, exit 0 with warnings for unmatched files). `.githooks/pre-commit` runs it and stages the
result on every commit, or warns and continues if node is missing; `.gitattributes` keeps the
hook LF. One-time per clone: `git config core.hooksPath .githooks`. This is dev-side tooling,
not a build step — the site still deploys as static files. `main.js` resolves each
`data-doc-link` button: active language → other language → existing href; a type with no
file at all has its buttons hidden. about.html's morph is skipped while CV or transcript is
missing (the resume button stays; a lone available document shows in the bottom slot). The
dev check HEADs each manifest path once and warns on non-2xx. Zero requests under
`assets/pdfs/` on a cold load. Verified with a throwaway commit on a temporary branch: the hook
regenerated and staged the manifest for a dummy `20991231` file; branch and file removed, main
restored.

[2026-09-27] Pre-fair code session (content follows in a second session). Placeholder data
migrated; nothing committed by the session itself.
1. **Translatable dates.** `dates` on projects and experience is now `{ from, to? }` with
   points `{ season, year }` / `{ month, year }` / `{ year }` and `to` = "present" or a point.
   Rendered by `siteData.formatDates` through `dateSpring…`, `dateMonth1…12`, `datePresent`,
   `dateSeasonYear`, `dateMonthYear` (EN "{month} {year}", ES "{month} de {year}"), `dateRange`.
   Seasons capitalized; ES months lowercase. Literal strings are no longer accepted. `sortDate`
   stays the ordering input; the dev check flags a sortDate that disagrees with the dates
   (year must match; a month must match; a season must contain the month; `to` wins when it is
   a point). TURC's placeholder sortDate moved 2025-09 → 2025-08 to satisfy that.
2. **Clickable tags, no filter row.** Removed the multi-select row (and `projFilterLabel` /
   `projFilterClear`). Pills are `<a href="projects.html?tag=<id>">` everywhere — pointer cursor
   only, no hover effect, no enlarged tap target, `:focus-visible` kept. projects.html reads
   `?tag=`, ANDs it with search, shows a "<Label> ✕" chip beside the count (✕ has a translated
   aria-label `projTagClear`; `history.replaceState` rewrites the URL). One tag at a time;
   unknown ids ignored; a language switch keeps it; a hash deep link clears it. A pill click on
   projects.html reloads the page (typed search lost) — accepted. `projEmpty` reworded for one
   tag.
3. **Phrase chips.** `js/chips.js` replaces `HERO_CHIPS` + `HTML_I18N_KEYS`: one table
   `{ phrase, urls: { en, es } }` (Zohaib Sheikh, IEL, "automating the boring stuff" pair),
   DOM-built (no innerHTML), whole-word, first occurrence per phrase per element, headings /
   links / buttons get plain text, idempotent. Applied to every `data-i18n` element, both hero
   paragraphs, and every builder-rendered body string. `aiPara1` is plain text now; translations.js
   holds no HTML. Verified: no `<a>` ever nests inside another `<a>`.
4. **Project sub-pages.** `js/project-page.js` + `projects/<slug>.html` shells with
   `data-slug` / `data-root="../"`; optional `page: { sections, facts, photos, reportPdf,
   creditKey }` on the entry; layout per the spec; missing pieces render nothing; static
   `<title>` / meta description replaced on render. Shared scripts read `data-root` so document
   links, images, tag links and "Part of" links resolve from `/projects/`. `hidden` entries
   render on localhost only. Scaffold: `todo-project-2` set to `listing: "hidden"` with a full
   `page` object and `projects/todo-project-2.html`; its featured / collage / Baker Hughes
   featured-link duties moved to `todo-project-3`; the other placeholder `subpageUrl`s blanked
   (their files never existed). No sitemap for now.
5. **Dev checks are localhost-only** (`siteData.isDev`), including the docs HEAD probes and the
   new one-HEAD-per-`subpageUrl` check; `page` shape and date consistency added.
6. **About for the fair.** §3 books, §4 FAQ and the interesting-sites block carry the `hidden`
   attribute (the one flag each; remove to restore); `js/about.js` skips their setup while
   hidden; the settings grid is auto-fit. Headshot src fixed in about.html to
   `assets/images/about/headshot.jpg` (the old path did not exist).
7. **Experience hero scrim** is pixel-based: solid `--footer-bg` to 540px (the text column ends
   at 520px), transparent by 960px; mobile full-cover opacity 0.82 → 0.88. Verified with a pure
   white slot-1 image at 768 / 900 / 1024 / 1280, light and dark: every hero line sits on solid
   scrim.
Tested on Live Server at :5500 with Playwright in the scratchpad (nothing in the repo): dates
EN/ES, `?tag=` from a row, a band and a typed URL, tag + search, ✕, unknown id, hash deep link,
chips, the sub-page in both languages, hidden About blocks, 375 / 768 / 1280 light and dark, no
horizontal overflow, console clean.

[2026-09-27] Content loaded (second session of the day) from staging/copy-en.md, copy-es.md,
content-intake.md and image-manifest.md, verbatim. 11-tag vocabulary; 16 projects (3 featured
with sub-pages: pump-cylinder-failure, eagle-pathway, g-view; pinned uk-crash-hotspots); 4
visible experience bands + 3 hidden pre-college roles; hero status / paragraph / collage; bio
1–3. Placeholder entries, keys and projects/todo-project-2.html removed. Decisions:
- `orgKey` carries the location ("Baker Hughes, Claremore OK", "…, University of Tulsa") for the
  band and the hero status; new optional `orgShortKey` feeds "Part of: {org} →" (`projPartOf`
  no longer includes the role).
- New optional `featuredOrder` fixes the featured order pump → Eagle → G-View (home and §2)
  independent of sortDate; `longDescKey` is required only on featured entries.
- New `imageAltKey` on experience entries (band image alt from the manifest).
- Eagle quick facts use labels My role / Volunteers / Size / Materials / Beneficiary / Rank;
  width and area merged into "Size". Eagle sub-page photos: granite-and-compactor,
  finished-path, group (no names). Pump "Report PDF" is the report link, not a fact row.
- Sort months derived from the season where the intake gave none: Velora and AutoScan
  2026-07, Dynamics PDF Unifier 2026-09.
- Search keywords drawn only from tools named in the copy / intake.
- Employer band colors remain neutral grey placeholders (after the fair).

[2026-09-27] Polish pass (third session of the day). No commit.
1. **Images.** Optional `thumbSrc` / `thumbAltKey` on projects (index rows only; fallback
   imageSrc / imageAlt). Pump: pin-installed-wide (featured) + pin-installed-thumb; Eagle:
   compacting-path (featured) + finished-path thumb; G-View: g-view-thumb; AutoScan and the
   Baker Hughes band: scanner-station. The home collage now reads its 2–4 cells from
   `gallery` alone (imageSrc is not a cell; GALLERY_MAX 4); Eagle's gallery lists
   directing-volunteers, granite-and-compactor, finished-path so the collage is unchanged.
2. **Text-only index rows** keep the two-column grid at ≥768px with the text in column 2,
   so their left edge and width match the image rows. Phones unchanged.
3. **Home featured** centered at the index width (1000 / 1120px), "Featured work" is a real
   `<h2 class="section-heading">` like projects.html. `js/site-config.js` →
   `homeFeaturedSideBySide` (default false) alternates image/text at ≥1200px and stacks
   below; a collage keeps its grid in the image column.
4. **Experience hero** rebuilt: solid text panel (min(540px, 52%)) + three captioned tiles
   (scanner-fixture tall; lathe, eagle stacked) starting at the panel edge, height
   min(80vh, 640px), no scrim; under 768px text first, tiles stacked at 4:3. printer.jpg and
   basket-old-new.jpg deleted (unreferenced). Keys `expHeroTile<N>Cap / Alt`.
5. **Image links + hover.** Images with a destination are wrapped in `<a class="image-link">`
   (clipped frame, image scales 1.03 on hover / :focus-visible, 250ms, pointer; off under
   prefers-reduced-motion) — thumbnails / featured images / collages → subpageUrl; band
   images → new optional `imageLink` (baker-hughes → `projects.html?part=baker-hughes`,
   machine-shop → `projects/pump-cylinder-failure.html`). Recorded as THE motion exception
   in CLAUDE.md. New `?part=<experience slug>` filter on projects.html: own chip (short org
   name + ✕, `projPartClear`), AND with tag + search, unknown slugs ignored, hash clears both;
   `projEmpty` reworded to cover both filters.
6. **Lightbox** on sub-pages: native `<dialog class="lightbox">`, image ≤ 92vw × 88vh,
   caption = alt, ✕ / prev / next (`projLightboxClose / Prev / Next`), ← → keys, Esc and
   backdrop close, scroll locked, focus returned, opacity-only fade; anchors keep their href
   as the no-JS fallback. The dialog is seeded with the first photo so it never holds an
   empty `<img>`.
7. **About morph** by manifest state: neither doc → static resume; one → Resume + that
   document (resume button cloned into the group's top slot); both → CV + Transcript.
   Verified all three by stubbing js/docs-data.js in the scratchpad test.
8. **About alignment.** "Statement on AI" now sits in the same 1100px container (padding
   included) as the §1/§2 grid, so its left edge matches "Who am I?" at every width; on
   phones it takes the §2 side padding. Measured equal at 375 / 768 / 1024 / 1280 / 1440 / 1800.
9. **Featured collapses while filtering** (projects.html). Any active filter — search text,
   `?tag=`, `?part=` — adds `.is-collapsed` + aria-hidden to `#featured-projects`: a one-row
   grid animates 1fr → 0fr with padding and opacity over 300ms so the index glides up under
   the search band; clearing everything expands it. A page opened with a filter starts
   collapsed with no animation; reduced motion → instant. Chosen over "fade, then instant
   collapse" and "instant" after seeing all three described — Gideon may revert (second
   movement exception in CLAUDE.md). The × in the search field became a bordered chip
   (36×28, opacity-only appear) rather than adding a separate Clear button.
10. **List headings + search band color.** New `.list-heading` class (Lora 600,
   clamp(1.5rem, 1.2rem + 1.2vw, 2rem), left on the column edge, margin-bottom
   clamp(20px, 3vw, 28px)) on the three list tops — home "Featured work", projects "Featured
   projects" / "All projects". Chosen over resizing the shared `.section-heading` (which
   would have grown the About panel label too) and over a page-scoped size: two classes,
   two jobs; `.section-heading` stays 15px for panel labels. Experience hero/band headings
   untouched. Search band: `--search-bg` per palette (bronze wash) — see open decision #1.
Verified with Playwright (scratchpad) at 375 / 768 / 1280 / 1440 × EN / ES × light / dark on
every page and the three sub-pages: no overflow, no nested anchors, no broken images, alt on
every image, console clean; hover scale on and off (reduced motion); `?part=` alone, with
`?tag=`, with search, unknown, ES; lightbox keyboard-only (Enter, → ←, Esc, focus return);
side-by-side flag on at 1280 / 1024.
