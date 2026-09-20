// translations.js
// All EN/ES display strings for the bare-bones build.
// Keys match the [key] annotations in content.md where given.
// Source of truth: content.md — do not edit strings here without updating there.

const translations = {
  en: {
    // Navbar — nav link labels (same words as the page headings below;
    // content.md does not give separate ES nav strings, so these reuse the
    // exact translations already provided for aboutHeading/expHeading/projectsHeading)
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

    // index.html — Featured work section
    featuredWork: "Featured work",
    featuredCardTitle: "Featured project coming soon",
    featuredCardDesc: "Project descriptions are being finalized.",

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

    // about.html stub
    aboutHeading: "About",
    aboutBody: "Full about page coming soon.",

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

    // projects.html stub
    projectsHeading: "Projects",
    projectsBody: "Full projects page coming soon.",

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
    featuredCardTitle: "Proyecto destacado próximamente",
    featuredCardDesc: "Las descripciones de proyectos están siendo finalizadas.",

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

    // about.html stub
    aboutHeading: "Sobre mí",
    aboutBody: "Página completa en construcción.",

    // experience.html — §1 hero
    // Same key pair as EN — see the comment in the en block above.
    expHeroStatus: "TODO Actualmente estudiante de Ingeniería Mecánica y Español IEL en la Universidad de Tulsa — buscando pasantías de verano de 2027 en ingeniería y español.",
    expHeroStatusCurrent: "TODO Actualmente {role} en {org}, y estudiante de Ingeniería Mecánica y Español IEL en la Universidad de Tulsa — buscando pasantías de verano de 2027 en ingeniería y español.",
    expHeroPara: "TODO párrafo de introducción — más sobre la dirección profesional actual (ES).",

    // experience.html — §2 entries
    expCaseStudyLink: "Ver caso completo →",
    expCurrentLabel: "Actual",

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

    // projects.html stub
    projectsHeading: "Proyectos",
    projectsBody: "Página completa en construcción.",

    // Footer
    footerContact: "gao9819@utulsa.edu",
    footerCopyright: "© 2026 Gideon A. Ong",
  },
};
