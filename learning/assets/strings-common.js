// strings-common.js — text shared by every /learning page (series name, module titles, nav words).
// Page-specific text lives in each page's own strings.js; the two are merged by learning-i18n.js.
// `es` is filled in when the Spanish pass happens. Until then every key falls back to English.
// Keys ending in "Html" may hold light markup (<b>, <i>, <code>); all other keys are plain text.
window.LEARN_STRINGS_COMMON = {
  en: {
    seriesName: "Reading Your Fits",
    learningHome: "Learning",
    siteHome: "gideonong.me",
    langToggleAria: "Toggle language (EN/ES)",
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
  es: {}
};
