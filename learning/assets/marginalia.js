// marginalia.js — the ONE registry of the Marginalia series (learning/marginalia/): side
// questions that come up while Gideon studies, one page each, usually with an interactive.
// The hub's Marginalia band and the series index render from it, the way reflections.js drives
// Reflections. English only (titles are marked lang="en" on the hub).
//
// An entry: { slug, title, sub?, subject, date: "YYYY-MM-DD", summary, ready }
//   Order in this array = the order the questions were asked (oldest first). That order is the
//   entry number shown on the index ("01", "02", …) and the order on the hub. Never renumber:
//   append. URLs use the slug only: learning/marginalia/<slug>/ (index.html, main.js, <slug>.py,
//   GENERATED <slug>.ipynb).
//   `subject` groups entries on the index; keep the wording identical across entries.
//   ready: false → listed nowhere until it is.
// Excluded from the offline app (build.ps1 $Exclude); the hub loads this file only when it is
// not the installed copy, and hides its band when the file is missing.
window.LEARN_MARGINALIA = [
  {
    slug: "markov-memory", title: "Does a Markov chain forget where it started?",
    subject: "Probability & statistics", date: "2026-10-27", ready: true,
    summary: "For a two-state chain the whole answer is one number, λ = 1 − a − b. It sets how fast the start is forgotten, and whether it ever is."
  },
  {
    slug: "clt-sample-size", title: "How big does n have to be?", sub: "Reading skewness from the CLT",
    subject: "Probability & statistics", date: "2026-10-27", ready: true,
    summary: "The practical rule n > 28 + 25γ₁² for a 95% interval on a mean, what to do when you can't reach it, and why the skewness of your data sets it."
  }
];

// Renderers. Paths are relative to the page that calls them, so they work on the site and from
// disk (learning.js's LF.fixFileLinks rewrites folder links when opened from file:).
(function () {
  "use strict";
  var E = window.LEARN_MARGINALIA;
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); }
  // "YYYY-MM-DD" → a date in words, from its parts with timeZone UTC (never new Date(string)).
  function fmtDate(iso, lang) {
    var p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!p) return iso || "";
    var d = new Date(Date.UTC(+p[1], +p[2] - 1, +p[3]));
    return d.toLocaleDateString(lang === "es" ? "es" : "en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });
  }
  function num(i) { return String(i + 1).padStart(2, "0"); }
  function ready() { return E.map(function (e, i) { return { e: e, i: i }; }).filter(function (x) { return x.e.ready; }); }
  function fix(el) { if (window.LF && LF.fixFileLinks) LF.fixFileLinks(el); }
  function title(e) { return esc(e.title) + (e.sub ? ' <span class="e-sub">' + esc(e.sub) + '</span>' : ''); }

  // Hub band (learning/index.html): the HUB_MAX most recent ready entries, in asked order.
  var HUB_MAX = 4;
  function hubList(el, lang) {
    var rows = ready().slice(-HUB_MAX);
    el.innerHTML = rows.map(function (x) {
      return '<li><a class="module-row marg-row" href="marginalia/' + x.e.slug + '/">' +
        '<span class="m-num">' + num(x.i) + '</span>' +
        '<span class="m-title" lang="en">' + title(x.e) + '</span>' +
        '<span class="m-desc" lang="en">' + esc(x.e.summary) + '</span></a></li>';
    }).join("");
    fix(el);
  }

  // Series index (learning/marginalia/index.html): one section per subject, in the order each
  // subject first appears; entries in asked order with their number and date.
  function indexList(el) {
    var subjects = [];
    ready().forEach(function (x) { if (subjects.indexOf(x.e.subject) < 0) subjects.push(x.e.subject); });
    el.innerHTML = subjects.map(function (s, si) {
      var rows = ready().filter(function (x) { return x.e.subject === s; });
      return '<section class="marg-subject" aria-labelledby="subj-' + si + '"><h2 id="subj-' + si + '">' + esc(s) + '</h2>' +
        '<ol class="entry-list">' + rows.map(function (x) {
          return '<li><a class="entry-row" href="' + x.e.slug + '/">' +
            '<span class="e-num">' + num(x.i) + '</span>' +
            '<span class="e-title">' + title(x.e) + '</span>' +
            '<span class="e-date">' + esc(fmtDate(x.e.date, "en")) + '</span>' +
            '<span class="e-desc">' + esc(x.e.summary) + '</span></a></li>';
        }).join("") + '</ol></section>';
    }).join("");
    fix(el);
  }

  window.LEARN_MARG = { hubList: hubList, indexList: indexList, fmtDate: fmtDate };
}());
