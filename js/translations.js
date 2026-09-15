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
    sayHello: "say hello", // content.md gives no separate ES string for this chip

    // Resume button
    resumeBtn: "Download Resume",

    // index.html — Featured work section
    featuredWork: "Featured work",
    featuredCardTitle: "Featured project coming soon", // content.md gives no ES string for placeholder card
    featuredCardDesc: "Project descriptions are being finalized.", // content.md gives no ES string for placeholder card

    // about.html stub
    aboutHeading: "About",
    aboutBody: "Full about page coming soon.",

    // experience.html stub
    expHeading: "Experience",
    expBody: "Experience page coming soon.",

    // projects.html stub
    projectsHeading: "Projects",
    projectsBody: "Full projects page coming soon.",

    // Footer
    footerContact: "gidgo130@gmail.com",
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
    sayHello: "say hello", // pending ES translation — not specified in content.md

    // Resume button
    resumeBtn: "Descargar CV",

    // index.html — Featured work section
    featuredWork: "Proyectos destacados",
    featuredCardTitle: "Featured project coming soon", // pending ES translation — not specified in content.md
    featuredCardDesc: "Project descriptions are being finalized.", // pending ES translation — not specified in content.md

    // about.html stub
    aboutHeading: "Sobre mí",
    aboutBody: "Página completa en construcción.",

    // experience.html stub
    expHeading: "Experiencia",
    expBody: "Página en construcción.",

    // projects.html stub
    projectsHeading: "Proyectos",
    projectsBody: "Página completa en construcción.",

    // Footer
    footerContact: "gidgo130@gmail.com",
    footerCopyright: "© 2026 Gideon A. Ong",
  },
};
