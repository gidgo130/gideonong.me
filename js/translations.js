// translations.js
// All EN/ES display strings. THIS FILE is the single source of display
// strings — content.md records status and field references, not copies of
// the strings. Placeholders are prefixed "TODO " in both languages.
//
// Per-entry keys are named by slug: proj<SlugCamel><Field> for projects
// (Title / Desc / LongDesc / Alt / Search) and exp<SlugCamel><Field> for
// experience (Role / Org / Bullet1…). Tag labels are tag<IdCamel>, context
// labels ctx<Context>. See CLAUDE.md → Data conventions.

const translations = {
  en: {
    // Navbar — nav link labels
    navProjects: "Projects",
    navExperience: "Experience",
    navAbout: "About",

    // "Under development" banner
    banner: "This site is under development.",

    // index.html — top section
    heroDesc: "Bilingual mechanical engineering IEL student with experience in automation, fabrication, and research; currently looking for summer internships for 2027. Interested in statistics, manufacturing, data analysis for applied engineering, and automating the boring stuff.",

    // Social chips
    sayHello: "say hello",

    // Resume button
    resumeBtn: "Download Resume",

    // index.html — Featured work section. The entries themselves render from
    // js/projects-data.js (featured: true, listing: "index") with the same
    // per-entry keys projects.html uses — nothing project-specific lives here.
    featuredWork: "Featured work",

    // Shared tag labels (js/tags-data.js). Pills and filter buttons show these;
    // the data files store the tag ID, never the label. Compact elements — keep
    // EN and ES close in length. todo-a … todo-f are the project placeholders;
    // the rest carried over from experience.html's former free-string tags.
    tagTodoA: "TODO Tag A",
    tagTodoB: "TODO Tag B",
    tagTodoC: "TODO Tag C",
    tagTodoD: "TODO Tag D",
    tagTodoE: "TODO Tag E",
    tagTodoF: "TODO Tag F",
    tagEngineering: "Engineering",
    tagRd: "R&D",
    tagAls: "ALS",
    tagMachining: "Machining",
    tagPrototyping: "Prototyping",
    tagFabrication: "Fabrication",
    tagDataAnalysis: "Data Analysis",
    tagGrading: "Grading",
    tagDynamics: "Dynamics",
    tagResearch: "Research",

    // Project context labels — the `context` field in js/projects-data.js,
    // rendered as "<Context> · <dates>" in every project meta line. Short.
    ctxIndustry: "Industry",
    ctxCoursework: "Coursework",
    ctxPersonal: "Personal",
    ctxService: "Service",
    ctxResearch: "Research",

    // about.html — §1 hero
    aboutIdentifiersEN: "Engineer · Geographer · Federalist · Philomath",
    aboutIdentifiersES: "Ingeniero · Geógrafo · Federalista · Aprendiz eterno",
    headshotAlt: "Portrait of Gideon A. Ong",

    // about.html — §2 "Who am I?"
    whoamiHeading: "Who am I?",
    whoamiBio1: "[Bio paragraph 1 — EN]",
    whoamiBio2: "[Bio paragraph 2 — EN]",
    whoamiBio3: "[Bio paragraph 3 — EN]",
    cvBtn: "Download Full CV",
    transcriptBtn: "Download Transcript",

    // about.html — §3 "What have I been reading?"
    readingHeading: "What have I been reading?",

    // about.html — §4 Interview FAQ
    faqHeading: "Interview FAQ",

    // about.html — §5 Statement on AI
    aiHeading: "Statement on AI",
    aiPara1: 'This website was inspired by <a class="iel-chip" href="https://zohaibsheikh.dev" target="_blank" rel="noopener">Zohaib Sheikh</a>, who I had the great pleasure of working together with at Baker Hughes in Claremore the summer of 2026. I have used Claude heavily to help develop and flesh out this website. Nearly all of the code, HTML and otherwise, has been written by AI. Claude has also assisted in grammar-checking and reorganizing content as I have populated this site with my projects and experiences.',

    // about.html — §6 Viewing settings + Interesting sites
    settingsHeading: "Viewing settings",
    togglePreCollege: "Show pre-college achievements",
    toggleReadability: "Readability mode",
    toggleColorblind: "Colorblind mode",
    toggleDarkMode: "Dark mode",
    interestingSitesHeading: "Interesting sites",

    // experience.html — §1 hero
    // Key pair for the status sentence. expHeroStatus is the FALLBACK, shown
    // when no entry in js/experience-data.js carries status: "current".
    // expHeroStatusCurrent is the template used when one does — {role} and
    // {org} are substituted from that entry by js/experience.js.
    expHeroStatus: "Currently a Mechanical Engineering and Spanish IEL student at the University of Tulsa — seeking summer 2027 internships in engineering and Spanish.",
    expHeroStatusCurrent: "Currently {role} at {org}, and a Mechanical Engineering and Spanish IEL student at the University of Tulsa — seeking summer 2027 internships in engineering and Spanish.",
    expHeroPara: "TODO hero paragraph — more on current professional direction (EN).",

    // experience.html — §2 entries
    expCaseStudyLink: "View full case study →",
    expCurrentLabel: "Current",
    // Heading of the "Projects from this role" list a band shows when at least
    // one listing: "index" project points at it via `experience`.
    expRelatedHeading: "Projects from this role",

    expBakerHughesRole: "Engineering Intern, ALS R&D",
    expBakerHughesOrg: "Baker Hughes",
    expBakerHughesBullet1: "TODO bullet 1 (EN)",
    expBakerHughesBullet2: "TODO bullet 2 (EN)",
    expBakerHughesBullet3: "TODO bullet 3 (EN)",

    expMachineShopRole: "Machine Shop Technician",
    expMachineShopOrg: "McElroy Prototyping Lab",
    expMachineShopBullet1: "TODO bullet 1 (EN)",
    expMachineShopBullet2: "TODO bullet 2 (EN)",
    expMachineShopBullet3: "TODO bullet 3 (EN)",

    expSchultzRole: "Grader & Data Analyst",
    expSchultzOrg: "Dr. Joshua Schultz",
    expSchultzBullet1: "TODO bullet 1 (EN)",
    expSchultzBullet2: "TODO bullet 2 (EN)",
    expSchultzBullet3: "TODO bullet 3 (EN)",

    expTurcRole: "TURC Research — TODO role (EN)",
    expTurcOrg: "TURC / TMTC (Edmonds)",
    expTurcBullet1: "TODO bullet 1 (EN)",
    expTurcBullet2: "TODO bullet 2 (EN)",
    expTurcBullet3: "TODO bullet 3 (EN)",

    // projects.html — §1 search band (live keyword search over the index)
    projSearchPlaceholder: "Search my projects",
    projSearchBtn: "Search",
    projSearchClear: "Clear search",       // aria-label on the × control

    // projects.html — §2 featured + §3 index chrome
    projFeaturedHeading: "Featured projects",
    projIndexHeading: "All projects",
    projViewLink: "View project →",
    // {role} and {org} are filled from the linked experience entry's keys.
    // Shown below the tags on any entry whose `experience` field is set.
    projPartOf: "Part of: {role}, {org} →",
    projFilterLabel: "Filter by tag",      // aria-label on the filter row
    projFilterClear: "Clear",              // resets every active tag
    projCount: "{n} projects",             // {n} filled by js/projects.js
    projCountOne: "{n} project",
    projEmpty: "No projects match those tags.",
    projEmptySearch: "No projects match “{q}”.",   // {q} = the search query

    // projects.html — placeholder entries (js/projects-data.js).
    // Every string here is a stand-in. Real project copy comes from the
    // projects content interview — do not invent any of it.
    projTodoProject1Title: "TODO Project 1 title",
    projTodoProject1Desc: "TODO one-line index description for project 1.",
    projTodoProject1LongDesc: "TODO fuller featured description for project 1 — one short paragraph, used in the featured block and on the sub-page.",
    projTodoProject1Alt: "TODO image description for project 1",
    projTodoProject1Search: "TODO search text blob for project 1",

    projTodoProject2Title: "TODO Project 2 title",
    projTodoProject2Desc: "TODO one-line index description for project 2.",
    projTodoProject2LongDesc: "TODO fuller featured description for project 2 — one short paragraph, used in the featured block and on the sub-page.",
    projTodoProject2Alt: "TODO image description for project 2",
    projTodoProject2Search: "TODO search text blob for project 2",

    projTodoProject3Title: "TODO Project 3 title",
    projTodoProject3Desc: "TODO one-line index description for project 3.",
    projTodoProject3LongDesc: "TODO fuller description for project 3.",
    projTodoProject3Alt: "TODO image description for project 3",
    projTodoProject3Search: "TODO search text blob for project 3",

    // Entry 4 has no image — its imageSrc is "" and it carries no alt key.
    projTodoProject4Title: "TODO Project 4 title (no image)",
    projTodoProject4Desc: "TODO one-line index description for project 4 — this entry has no thumbnail, so its text runs the full row width.",
    projTodoProject4LongDesc: "TODO fuller description for project 4.",
    projTodoProject4Search: "TODO search text blob for project 4",

    projTodoProject5Title: "TODO Project 5 title (no sub-page)",
    projTodoProject5Desc: "TODO one-line index description for project 5 — this entry has no sub-page yet, so no link is shown.",
    projTodoProject5LongDesc: "TODO fuller description for project 5.",
    projTodoProject5Alt: "TODO image description for project 5",
    projTodoProject5Search: "TODO search text blob for project 5",

    projTodoProject6Title: "TODO Project 6 title",
    projTodoProject6Desc: "TODO one-line index description for project 6.",
    projTodoProject6LongDesc: "TODO fuller description for project 6.",
    projTodoProject6Alt: "TODO image description for project 6",
    projTodoProject6Search: "TODO search text blob for project 6",

    // Footer
    footerContact: "gao9819@utulsa.edu",
    footerCopyright: "© 2026 Gideon A. Ong",
  },

  es: {
    // Navbar
    navProjects: "Proyectos",
    navExperience: "Experiencia",
    navAbout: "Sobre mí",

    // "Under development" banner
    banner: "Este sitio está en desarrollo.",

    // index.html — top section
    heroDesc: "Estudiante bilingüe de ingeniería mecánica IEL con experiencia en automatización, fabricación e investigación; actualmente buscando pasantías para el verano de 2027. Interesado en estadística, manufactura, análisis de datos para aplicaciones de ingeniería, y automatizar lo aburrido.",

    // Social chips
    sayHello: "escríbeme",

    // Resume button
    resumeBtn: "Descargar Currículum",

    // index.html — Featured work section
    featuredWork: "Proyectos destacados",

    // Shared tag labels — see the note in the en block. ES labels for the
    // carried-over experience tags are provisional ("TODO ") until the
    // vocabulary is settled in the content interviews.
    tagTodoA: "TODO Etiqueta A",
    tagTodoB: "TODO Etiqueta B",
    tagTodoC: "TODO Etiqueta C",
    tagTodoD: "TODO Etiqueta D",
    tagTodoE: "TODO Etiqueta E",
    tagTodoF: "TODO Etiqueta F",
    tagEngineering: "TODO Engineering",
    tagRd: "TODO R&D",
    tagAls: "TODO ALS",
    tagMachining: "TODO Machining",
    tagPrototyping: "TODO Prototyping",
    tagFabrication: "TODO Fabrication",
    tagDataAnalysis: "TODO Data Analysis",
    tagGrading: "TODO Grading",
    tagDynamics: "TODO Dynamics",
    tagResearch: "TODO Research",

    // Project context labels — kept short (meta line).
    ctxIndustry: "Industria",
    ctxCoursework: "Curso",
    ctxPersonal: "Personal",
    ctxService: "Servicio",
    ctxResearch: "Investigación",

    // about.html — §1 hero
    aboutIdentifiersEN: "Engineer · Geographer · Federalist · Philomath",
    aboutIdentifiersES: "Ingeniero · Geógrafo · Federalista · Aprendiz eterno",
    headshotAlt: "Retrato de Gideon A. Ong",

    // about.html — §2 "¿Quién soy?"
    whoamiHeading: "¿Quién soy?",
    whoamiBio1: "[Párrafo de biografía 1 — ES]",
    whoamiBio2: "[Párrafo de biografía 2 — ES]",
    whoamiBio3: "[Párrafo de biografía 3 — ES]",
    cvBtn: "Descargar CV Completo",
    transcriptBtn: "Descargar Historial Académico",

    // about.html — §3 "¿Qué he estado leyendo?"
    readingHeading: "¿Qué he estado leyendo?",

    // about.html — §4 Preguntas de entrevista
    faqHeading: "Preguntas frecuentes de entrevista",

    // about.html — §5 Declaración sobre la IA
    aiHeading: "Declaración sobre la IA",
    aiPara1: 'Este sitio web fue inspirado por <a class="iel-chip" href="https://zohaibsheikh.dev" target="_blank" rel="noopener">Zohaib Sheikh</a>, con quien tuve el gran placer de trabajar juntos en Baker Hughes en Claremore el verano de 2026. He usado Claude ampliamente para desarrollar y dar cuerpo a este sitio web; casi todo el código fue escrito por IA. Claude también me asistió en corregir mi gramática y mis traducciones, y en reorganizar mis experiencias y proyectos mientras los iba añadiendo a este sitio.',

    // about.html — §6 Preferencias de visualización + Sitios interesantes
    settingsHeading: "Preferencias de visualización",
    togglePreCollege: "Mostrar logros preuniversitarios",
    toggleReadability: "Modo de lectura fácil",
    toggleColorblind: "Modo daltónico",
    toggleDarkMode: "Modo oscuro",
    interestingSitesHeading: "Sitios interesantes",

    // experience.html — §1 hero
    // Same key pair as EN — see the comment in the en block above.
    expHeroStatus: "TODO Actualmente estudiante de Ingeniería Mecánica y Español IEL en la Universidad de Tulsa — buscando pasantías de verano de 2027 en ingeniería y español.",
    expHeroStatusCurrent: "TODO Actualmente {role} en {org}, y estudiante de Ingeniería Mecánica y Español IEL en la Universidad de Tulsa — buscando pasantías de verano de 2027 en ingeniería y español.",
    expHeroPara: "TODO párrafo de introducción — más sobre la dirección profesional actual (ES).",

    // experience.html — §2 entries
    expCaseStudyLink: "Ver caso completo →",
    expCurrentLabel: "Actual",
    expRelatedHeading: "Proyectos de este puesto",

    expBakerHughesRole: "TODO Engineering Intern, ALS R&D",
    expBakerHughesOrg: "Baker Hughes",
    expBakerHughesBullet1: "TODO bullet 1 (ES)",
    expBakerHughesBullet2: "TODO bullet 2 (ES)",
    expBakerHughesBullet3: "TODO bullet 3 (ES)",

    expMachineShopRole: "TODO Machine Shop Technician",
    expMachineShopOrg: "McElroy Prototyping Lab",
    expMachineShopBullet1: "TODO bullet 1 (ES)",
    expMachineShopBullet2: "TODO bullet 2 (ES)",
    expMachineShopBullet3: "TODO bullet 3 (ES)",

    expSchultzRole: "TODO Grader & Data Analyst",
    expSchultzOrg: "Dr. Joshua Schultz",
    expSchultzBullet1: "TODO bullet 1 (ES)",
    expSchultzBullet2: "TODO bullet 2 (ES)",
    expSchultzBullet3: "TODO bullet 3 (ES)",

    expTurcRole: "TODO TURC Research — role (ES)",
    expTurcOrg: "TURC / TMTC (Edmonds)",
    expTurcBullet1: "TODO bullet 1 (ES)",
    expTurcBullet2: "TODO bullet 2 (ES)",
    expTurcBullet3: "TODO bullet 3 (ES)",

    // projects.html — §1 search band
    projSearchPlaceholder: "Buscar proyectos",
    projSearchBtn: "Buscar",
    projSearchClear: "Borrar búsqueda",

    // projects.html — §2 featured + §3 index chrome.
    // projSearchBtn and projFilterClear sit inside fixed-shape controls, so the
    // ES strings are kept the same length as the EN ones (CLAUDE.md compact
    // element rule) — the pill must not resize when the language toggles.
    projFeaturedHeading: "Proyectos destacados",
    projIndexHeading: "Todos los proyectos",
    projViewLink: "Ver proyecto →",
    projPartOf: "Parte de: {role}, {org} →",
    projFilterLabel: "Filtrar por etiqueta",
    projFilterClear: "Todos",
    projCount: "{n} proyectos",
    projCountOne: "{n} proyecto",
    projEmpty: "Ningún proyecto coincide con esas etiquetas.",
    projEmptySearch: "Ningún proyecto coincide con «{q}».",

    // projects.html — placeholder entries (js/projects-data.js).
    // Same TODO convention as EN — real copy comes from the content interview.
    projTodoProject1Title: "TODO título del proyecto 1",
    projTodoProject1Desc: "TODO descripción de una línea para el proyecto 1.",
    projTodoProject1LongDesc: "TODO descripción ampliada del proyecto 1 — un párrafo corto, usado en el bloque destacado y en la subpágina.",
    projTodoProject1Alt: "TODO descripción de la imagen del proyecto 1",
    projTodoProject1Search: "TODO texto de búsqueda para el proyecto 1",

    projTodoProject2Title: "TODO título del proyecto 2",
    projTodoProject2Desc: "TODO descripción de una línea para el proyecto 2.",
    projTodoProject2LongDesc: "TODO descripción ampliada del proyecto 2 — un párrafo corto, usado en el bloque destacado y en la subpágina.",
    projTodoProject2Alt: "TODO descripción de la imagen del proyecto 2",
    projTodoProject2Search: "TODO texto de búsqueda para el proyecto 2",

    projTodoProject3Title: "TODO título del proyecto 3",
    projTodoProject3Desc: "TODO descripción de una línea para el proyecto 3.",
    projTodoProject3LongDesc: "TODO descripción ampliada del proyecto 3.",
    projTodoProject3Alt: "TODO descripción de la imagen del proyecto 3",
    projTodoProject3Search: "TODO texto de búsqueda para el proyecto 3",

    // La entrada 4 no tiene imagen — imageSrc es "" y no lleva clave alt.
    projTodoProject4Title: "TODO título del proyecto 4 (sin imagen)",
    projTodoProject4Desc: "TODO descripción de una línea para el proyecto 4 — esta entrada no tiene miniatura, así que su texto ocupa todo el ancho de la fila.",
    projTodoProject4LongDesc: "TODO descripción ampliada del proyecto 4.",
    projTodoProject4Search: "TODO texto de búsqueda para el proyecto 4",

    projTodoProject5Title: "TODO título del proyecto 5 (sin subpágina)",
    projTodoProject5Desc: "TODO descripción de una línea para el proyecto 5 — esta entrada todavía no tiene subpágina, así que no se muestra enlace.",
    projTodoProject5LongDesc: "TODO descripción ampliada del proyecto 5.",
    projTodoProject5Alt: "TODO descripción de la imagen del proyecto 5",
    projTodoProject5Search: "TODO texto de búsqueda para el proyecto 5",

    projTodoProject6Title: "TODO título del proyecto 6",
    projTodoProject6Desc: "TODO descripción de una línea para el proyecto 6.",
    projTodoProject6LongDesc: "TODO descripción ampliada del proyecto 6.",
    projTodoProject6Alt: "TODO descripción de la imagen del proyecto 6",
    projTodoProject6Search: "TODO texto de búsqueda para el proyecto 6",

    // Footer
    footerContact: "gao9819@utulsa.edu",
    footerCopyright: "© 2026 Gideon A. Ong",
  },
};
