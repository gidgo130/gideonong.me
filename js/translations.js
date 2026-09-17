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
    aiPara1: "[AI statement paragraph 1 — EN]",
    aiPara2: "[AI statement paragraph 2 — EN]",
    aiPara3: "[AI statement paragraph 3 — EN]",

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
    expHeroStatus: "Currently a Mechanical Engineering and Spanish IEL student at the University of Tulsa — seeking summer 2027 internships in engineering and Spanish.",
    expHeroPara: "[Hero paragraph — more on current professional direction — EN]",

    // experience.html — §2 entries
    expCaseStudyLink: "View full case study →",

    expBakerHughesRole: "Engineering Intern, ALS R&D",
    expBakerHughesOrg: "Baker Hughes",
    expBakerHughesBullet1: "[Bullet 1 — EN]",
    expBakerHughesBullet2: "[Bullet 2 — EN]",
    expBakerHughesBullet3: "[Bullet 3 — EN]",

    expMachineShopRole: "Machine Shop Technician",
    expMachineShopOrg: "McElroy Prototyping Lab",
    expMachineShopBullet1: "[Bullet 1 — EN]",
    expMachineShopBullet2: "[Bullet 2 — EN]",
    expMachineShopBullet3: "[Bullet 3 — EN]",

    expSchultzRole: "Grader & Data Analyst",
    expSchultzOrg: "Dr. Joshua Schultz",
    expSchultzBullet1: "[Bullet 1 — EN]",
    expSchultzBullet2: "[Bullet 2 — EN]",
    expSchultzBullet3: "[Bullet 3 — EN]",

    expTurcRole: "TURC Research — [role TBD]",
    expTurcOrg: "TURC / TMTC (Edmonds)",
    expTurcBullet1: "[Bullet 1 — EN]",
    expTurcBullet2: "[Bullet 2 — EN]",
    expTurcBullet3: "[Bullet 3 — EN]",

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
    resumeBtn: "Descargar CV",

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
    cvBtn: "Descargar CV completo",
    transcriptBtn: "Descargar transcripción",

    // about.html — §3 "¿Qué he estado leyendo?"
    readingHeading: "¿Qué he estado leyendo?",

    // about.html — §4 Preguntas de entrevista
    faqHeading: "Preguntas frecuentes de entrevista",

    // about.html — §5 Declaración sobre la IA
    aiHeading: "Declaración sobre la IA",
    aiPara1: "[Párrafo de declaración sobre IA 1 — ES]",
    aiPara2: "[Párrafo de declaración sobre IA 2 — ES]",
    aiPara3: "[Párrafo de declaración sobre IA 3 — ES]",

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
    expHeroStatus: "[ES TBD] Currently a Mechanical Engineering and Spanish IEL student at the University of Tulsa — seeking summer 2027 internships in engineering and Spanish.",
    expHeroPara: "[ES TBD] [Hero paragraph — more on current professional direction]",

    // experience.html — §2 entries
    expCaseStudyLink: "Ver caso completo →",

    expBakerHughesRole: "[ES TBD] Engineering Intern, ALS R&D",
    expBakerHughesOrg: "Baker Hughes",
    expBakerHughesBullet1: "[ES TBD] [Bullet 1]",
    expBakerHughesBullet2: "[ES TBD] [Bullet 2]",
    expBakerHughesBullet3: "[ES TBD] [Bullet 3]",

    expMachineShopRole: "[ES TBD] Machine Shop Technician",
    expMachineShopOrg: "McElroy Prototyping Lab",
    expMachineShopBullet1: "[ES TBD] [Bullet 1]",
    expMachineShopBullet2: "[ES TBD] [Bullet 2]",
    expMachineShopBullet3: "[ES TBD] [Bullet 3]",

    expSchultzRole: "[ES TBD] Grader & Data Analyst",
    expSchultzOrg: "Dr. Joshua Schultz",
    expSchultzBullet1: "[ES TBD] [Bullet 1]",
    expSchultzBullet2: "[ES TBD] [Bullet 2]",
    expSchultzBullet3: "[ES TBD] [Bullet 3]",

    expTurcRole: "[ES TBD] TURC Research — [role TBD]",
    expTurcOrg: "TURC / TMTC (Edmonds)",
    expTurcBullet1: "[ES TBD] [Bullet 1]",
    expTurcBullet2: "[ES TBD] [Bullet 2]",
    expTurcBullet3: "[ES TBD] [Bullet 3]",

    // projects.html stub
    projectsHeading: "Proyectos",
    projectsBody: "Página completa en construcción.",

    // Footer
    footerContact: "gao9819@utulsa.edu",
    footerCopyright: "© 2026 Gideon A. Ong",
  },
};
