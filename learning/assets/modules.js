// modules.js — the ONE registry of /learning series and modules.
// Order in the array = order in the series. `ready: false` shows "In progress" and no link.
// Titles and descriptions live in strings-common.js as mod<Key>Title / mod<Key>Desc.
// A module's page lives at learning/fits/<slug>/index.html.
window.LEARN_MODULES = [
  { key: "RSquared",      slug: "r-squared",      ready: true  },
  { key: "Residuals",     slug: "residual-plots", ready: true  },
  { key: "UnevenScatter", slug: "uneven-scatter", ready: true  },
  { key: "TimeOrder",     slug: "time-order",     ready: true  },
  { key: "InvisibleBias", slug: "invisible-bias", ready: true  },
  { key: "Reporting",     slug: "reporting",      ready: true  }
];
