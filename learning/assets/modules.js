// modules.js — the ONE registry of /learning series and modules.
// Order in the array = order in the series. `ready: false` shows "In progress" and no link.
// Titles and descriptions live in strings-common.js as mod<Key>Title / mod<Key>Desc.
// A module's page lives at learning/fits/<slug>/index.html.
window.LEARN_MODULES = [
  { key: "RSquared",      slug: "r-squared",      ready: false },
  { key: "Residuals",     slug: "residual-plots", ready: false },
  { key: "UnevenScatter", slug: "uneven-scatter", ready: false },
  { key: "TimeOrder",     slug: "time-order",     ready: false },
  { key: "InvisibleBias", slug: "invisible-bias", ready: true  },
  { key: "Reporting",     slug: "reporting",      ready: false }
];
