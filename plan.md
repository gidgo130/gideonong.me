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

- [ ] css/style.css: define all CSS custom property tokens, Google Fonts import
- [ ] js/translations.js: initial EN + ES strings for home page
- [ ] index.html: navbar (white, sticky), dev banner, hero, featured work, dark footer
- [ ] about.html: education (IELP program description), skills by category, honors/awards,
  languages (EN/ES/FR), interests
- [ ] experience.html: Baker Hughes internship, McElroy Prototyping Lab, TURC research,
  Dr. Schultz grader role
- [ ] projects.html: 3-5 initial projects with placeholder images and real descriptions
- [ ] js/main.js: language toggle (instant DOM swap, localStorage, navigator.language default)
- [ ] Social link chips in hero: GitHub (gidgo130), LinkedIn (gideon-a-ong), email
- [ ] "Download resume" button → assets/pdfs/resume.pdf in new tab
- [ ] Featured work section: image-forward layout, 1-2 projects
- [ ] Deploy to gideonong.me → review on desktop (Chrome, Firefox, Safari)

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
- Skill tag pills — small, same style as projects.html; placed below bullets
- "View full case study →" link — `var(--entry-accent)`

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

**Maintainability:** All entries defined in `js/experience-data.js`. Each object:
```js
{
  roleKey: "",            // i18n key → EN + ES
  orgKey: "",             // i18n key
  dates: "",              // literal, not translated
  bulletKeys: [],         // i18n keys → EN + ES
  tags: [],
  imageSrc: "",
  subpageUrl: "",
  layout: "imageLeft",    // preset name — see table above
  status: null,           // "current" on at most one entry, else null
  color: {
    light: { bg: "", border: "", accent: "" },
    dark:  { bg: "", border: "", accent: "" }
  },
  visible: true
}
```
Reorder by changing array order; hide with `visible: false`.

**Current entries (reverse chronological):**
1. Baker Hughes — Engineering Intern, ALS R&D (Summer 2026, Claremore OK)
2. McElroy Prototyping Lab — Machine Shop Technician (Spring 2026 – present)
3. Dr. Joshua Schultz — Grader & Data Analyst (Spring 2026)
4. TURC research — TBD (confirm whether to include before build)

**Sub-pages:** Each entry links to `/experience/[slug].html` (e.g.,
`/experience/baker-hughes.html`). Sub-pages are full case studies with flexible sections
per role. Structure TBD per role — spec separately before building sub-pages.

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
5. Skill tags per entry — TBD per role
6. Sub-page structure — spec separately per role before building sub-pages
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

**Status:** Structure and styles are built in Phase 1 but the element is **hidden**
(`display: none` via a single class on the band). It is revealed in Phase 3 when semantic
search ships. Do not ship a visible search box that does not work.

**Layout:** Full-bleed band directly below the nav/dev-banner. Search input + submit button,
horizontally centered. Closed off at the bottom by a 2px accent rule in `var(--bronze)` —
the rule is the transition into the featured section.

**Background:** Visually distinct from both `var(--bg)` and `var(--bg-section)` — this is the
"innovative background" in the outline. Candidate treatments to compare in the color pass:
a) `var(--footer-bg)` dark band with light text (bookends the dark footer)
b) `var(--bg-section)` with a subtle texture or gradient
c) A bronze-tinted wash
**TBD** — build (b) first as the safe default; (a) is the more striking option.

**Placeholder text:** EN "Search my projects" / ES "Buscar proyectos" — via `data-i18n`.
Keep EN and ES close in character length per the CLAUDE.md compact-element rule.

**Phase 3 behavior:** TF-IDF + cosine similarity over each project's `searchText`, run in
vanilla JS. Results reorder/filter the §3 index in place — no separate results page, no reload.
The markup written in Phase 1 must not need to change when the search function is swapped in.

#### §2 — Featured projects

**Count:** 2–3 entries. Sourced from the same data array as §3 via `featured: true` — never a
second copy of a project's content.

**Layout:** Full-width image as the visual anchor, per entry. Arrangement alternates:
entry 1 image-left / text-right, entry 2 text-left / image-right, matching the outline.
Alternation here is fine because the set is small and fixed; this is the one place a global
alternating rule applies.

**Per entry:** Image → title (Lora) → description (DM Sans) → tag pills → "View project →" link.
**Tags go below the description, never above the title** (CLAUDE.md).

**Background:** `var(--bg-section)`, per the index.html featured-work convention.

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

**Missing images:** An entry with no `imageSrc` renders with no thumbnail and the text occupying
the full row width. It must not render a broken image, a grey box, or a generic placeholder icon.

**Tag filter:** Row of tag pills above the index. Clicking toggles a tag; multiple tags may be
active simultaneously (AND logic — an entry must carry all active tags). A "Clear"/"Todos" pill
resets. Filtering is instant vanilla JS, no reload. Filtered-out rows are removed from flow
(`display: none`) so the list closes up rather than leaving gaps.

- Active tag pill: filled `var(--bronze)`, light text. Inactive: bordered, `var(--muted)` text.
- A live count ("8 projects" / "8 proyectos") sits beside the filter row and updates on filter.
- If a filter combination yields zero results, show a short empty-state line — never a blank page.

**Order:** Reverse chronological by default. A `pinned: true` field may lift an entry to the top
of the index independently of the featured flag.

**Background:** `var(--bg)`.

#### Maintainability — `js/projects-data.js`

New file, mirroring `js/experience-data.js`. One array, single source of truth for §2 and §3.

```js
{
  slug: "",               // URL slug → /projects/[slug].html
  titleKey: "",           // i18n key → EN + ES
  descKey: "",            // i18n key — one line, used in the index row
  longDescKey: "",        // i18n key — fuller paragraph, used in featured + sub-page
  dates: "",              // literal, not translated
  tags: [],               // must match the tag vocabulary below
  imageSrc: "",           // "" is valid — renders without a thumbnail
  imageAlt: "",           // i18n key — required whenever imageSrc is set
  subpageUrl: "",         // "" = no sub-page yet; the "View project →" link is then omitted
  featured: false,        // true → also rendered in §2
  pinned: false,          // true → lifted to top of §3
  searchTextKey: "",      // i18n key — EN + ES blob indexed by Phase 3 search
  visible: true,          // false → hidden from both §2 and §3 without deleting the entry
  unlisted: false         // true → reachable by direct URL only; excluded from §2, §3 and search
}
```

`unlisted: true` is how the "unlinked pages" decision (politically-sensitive or selectively-shared
work) is implemented — the entry lives in the array so its sub-page can be generated, but it never
appears in any listing.

**Tag vocabulary:** A controlled list, defined once at the top of `projects-data.js`. Entries may
only use tags from it. This prevents "CAD"/"cad"/"SolidWorks" fragmenting the filter.
**TBD** — draft the vocabulary during the content interview, not before.

#### Animation

No CLAUDE.md carve-outs required. Standard rules apply:
- Scroll-triggered fade-in on featured entries: IntersectionObserver, opacity 0→1, ~300ms, no movement.
- Tag filter transitions: opacity only. Rows must not slide or animate position — reflow is instant.
- Hover on rows, links, and tags: color transition only, ~150ms ease.

#### Open decisions for projects.html

1. Search band background treatment — (a) dark, (b) section-tint, (c) bronze wash. Build (b) first.
2. Tag vocabulary — drafted during the content interview
3. Project list — which projects, and which 2–3 are featured? Content interview
4. Thumbnail aspect ratio — 4:3, 16:9, or 1:1? Pick one and enforce it across all rows
5. Index row density — one-line description vs. two. Evaluate once real descriptions exist
6. Sub-page structure — spec separately, after §2/§3 are built and reviewed
7. Whether a visitor-facing rows/grid view switcher is worth building at all (Phase 3, optional)

---

## Phase 2 — Responsive + Polish

Goal: site works cleanly on phone and tablet; typography and visual polish complete.

- [ ] Mobile nav: hamburger menu (☰) at 768px breakpoint → vertical link dropdown
- [ ] Review all pages at 375px (iPhone SE), 768px (iPad), 1280px (desktop)
- [ ] Typography pass: review practicaltypography.com Line Length, Font Size, Bold/Italic
  sections before adjusting any font sizes or line heights
- [ ] Scroll-triggered fade-ins: IntersectionObserver on project cards and sections
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
- [ ] Add Open Graph metadata tags to all pages (controls LinkedIn/social preview image)

Features:

- [ ] Tag filter system on projects.html (JS, no page reload)
- [ ] Semantic search box ("Search my experience") in hero section:
  Phase 3a: TF-IDF + cosine similarity in vanilla JS (fast, no download)
  Phase 3b (optional upgrade): Transformers.js in-browser embeddings (more semantic)
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
