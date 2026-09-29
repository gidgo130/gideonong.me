// strings-common.js — text shared by every /learning page (series name, module titles, nav words).
// Page-specific text lives in each page's own strings.js; the two are merged by learning-i18n.js.
// Spanish lives in `es`; a key missing there falls back to English (see learning-i18n.js).
// Keys ending in "Html" may hold light markup (<b>, <i>, <code>); all other keys are plain text.
window.LEARN_STRINGS_COMMON = {
  en: {
    seriesName: "Reading Your Fits",
    learningHome: "Learning",
    siteHome: "gideonong.me",
    langToggleAria: "Toggle language (EN/ES)",
    takeSlidesHref: "slides.html",
    navSiteAria: "Site",
    navSeriesAria: "Series",
    navSeriesNavAria: "Series navigation",
    navAll: "All modules",
    navPrev: "Previous",
    navNext: "Next",
    moduleN: "Module {n}",
    statusReady: "Ready",
    statusSoon: "In progress",

    modRSquaredTitle: "Why R² isn't enough",
    modRSquaredDesc: "Four datasets, one R². What the number hides and what to look at instead.",
    modResidualsTitle: "Reading a residual plot",
    modResidualsDesc: "The leftovers after a fit, and the four patterns that mean something.",
    modUnevenScatterTitle: "Uneven scatter",
    modUnevenScatterDesc: "When the noise grows with the reading: honest error bars and weighted fits.",
    modTimeOrderTitle: "Time-ordered data",
    modTimeOrderDesc: "Drift, sampling too fast, and the cooling-curve log trap.",
    modInvisibleBiasTitle: "The Invisible Bias",
    modInvisibleBiasDesc: "Noise in x and unmeasured drift bend the slope without leaving a trace in the residuals.",
    modReportingTitle: "Using and reporting a fit",
    modReportingDesc: "Confidence vs prediction intervals, error in real units, and a one-page checklist."
  },
  es: {
    seriesName: "Cómo leer tus ajustes de curvas",
    learningHome: "Aprendizaje",
    siteHome: "gideonong.me",
    langToggleAria: "Cambiar idioma (EN/ES)",
    takeSlidesHref: "slides.es.html",
    navSiteAria: "Sitio",
    navSeriesAria: "Serie",
    navSeriesNavAria: "Navegación de la serie",
    navAll: "Todos los módulos",
    navPrev: "Anterior",
    navNext: "Siguiente",
    moduleN: "Módulo {n}",
    statusReady: "Listo",
    statusSoon: "En preparación",

    modRSquaredTitle: "Por qué R² no basta",
    modRSquaredDesc: "Cuatro conjuntos de datos, un mismo R². Lo que el número esconde y qué mirar en su lugar.",
    modResidualsTitle: "Cómo leer una gráfica de residuos",
    modResidualsDesc: "Lo que sobra después de un ajuste, y los cuatro patrones que sí significan algo.",
    modUnevenScatterTitle: "Dispersión desigual",
    modUnevenScatterDesc: "Cuando el ruido crece con la lectura: barras de error honestas y ajustes ponderados.",
    modTimeOrderTitle: "Datos ordenados en el tiempo",
    modTimeOrderDesc: "La deriva, el muestreo demasiado rápido y la trampa del logaritmo en la curva de enfriamiento.",
    modInvisibleBiasTitle: "El sesgo invisible",
    modInvisibleBiasDesc: "El ruido en x y una deriva que no mediste tuercen la pendiente sin dejar rastro en los residuos.",
    modReportingTitle: "Cómo usar y reportar un ajuste",
    modReportingDesc: "Intervalo de confianza frente a intervalo de predicción, el error en unidades reales y una lista de verificación de una página."
  }
};
