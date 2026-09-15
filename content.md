# Site Content — gideonong.me

# Claude Code: read this file alongside CLAUDE.md when building any page.

# All display text comes from here. Do not invent or paraphrase — use exact strings.

# EN/ES pairs are for translations.js. Keys are noted in brackets.

---

## GLOBAL — Nav & UI labels

### Navbar

Logo text: "Gideon A. Ong"
Nav links (in order): Projects · Experience · About
Language toggle: EN | ES

### "Under development" banner

EN: "This site is under development."
ES: "Este sitio está en desarrollo."
[key: banner]

### Footer

EN resume button: "Download Resume"
ES resume button: "Descargar CV"
[key: resumeBtn]
Resume EN path: assets/pdfs/resume-en.pdf
Resume ES path: assets/pdfs/resume-es.pdf
(open in new tab)

Footer contact: gao9819@utulsa.edu
Footer copyright: "© 2026 Gideon A. Ong"

---

## index.html — Top section

### Name

Display: "Gideon A. Ong"
(Lora serif, large — no label or subtitle above it)

### IEL chip

Chip text: IEL
URL: https://utulsa.edu/academics/interdisciplinary-programs/international-engineering-science-language/
Placement: between "mechanical engineering" and "student" in the description sentence
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

[LinkedIn]  gideon-a-ong   → https://www.linkedin.com/in/gideon-a-ong
[GitHub]    gidgo130       → https://github.com/gidgo130
[✉]         say hello      → mailto:gao9819@utulsa.edu

### Resume button (below social chips)

EN: "Download Resume"
ES: "Descargar CV"
Opens: active-language resume PDF in new tab

---

## index.html — Featured work section

# STATUS: PLACEHOLDER — real project content coming after project list is finalized.

# For bare-bones build: render 1–2 placeholder cards with this structure visible,

# image slot gray (#DDD5C8), title/description/tags marked [Project coming soon].

# Do not invent project content.

Section heading:
EN [key: featuredWork]: "Featured work"
ES [key: featuredWork]: "Proyectos destacados"

Placeholder card 1:
Title: "Featured project coming soon"
Description: "Project descriptions are being finalized."
Tags: (none)
Link: (none)

---

## about.html — Stub (bare-bones build)

Page heading:
EN [key: aboutHeading]: "About"
ES [key: aboutHeading]: "Sobre mí"

Body placeholder:
EN: "Full about page coming soon."
ES: "Página completa en construcción."

---

## experience.html — Stub (bare-bones build)

Page heading:
EN [key: expHeading]: "Experience"
ES [key: expHeading]: "Experiencia"

Body placeholder:
EN: "Experience page coming soon."
ES: "Página en construcción."

---

## projects.html — Stub (bare-bones build)

Page heading:
EN [key: projectsHeading]: "Projects"
ES [key: projectsHeading]: "Proyectos"

Body placeholder:
EN: "Full projects page coming soon."
ES: "Página completa en construcción."

---

## Notes for Claude Code

- Use data-i18n="[key]" on every element whose text is listed above.
- All strings go into js/translations.js — never hardcode display text in HTML.
- The IEL chip is inline in the description paragraph, not in the social chip row.
- For the bare-bones build, stub pages (about, experience, projects) need:
  working navbar, dev banner, a centered heading, placeholder body text, and footer.
  They do not need full content — that comes in Phase 1.
- Both resume PDFs may not exist in assets/pdfs/ yet; link the button anyway.
  The button will work once the files are added.
- Visual reference available at: references/mockup-v2-brass.html (gitignored, local only)
