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
