// reflections.js — the ONE registry of the Reflections section (learning/reflections/):
// the 11 books in Professor Donnell's order, each with its reflections. The hub's Reflections
// block, the all-books page and every book page render from it, the way modules.js drives
// Reading Your Fits. Book and reflection titles are English everywhere (the hub marks them
// lang="en"); the section itself is English only (learning-plan.md, Reflections → R3).
//
// A book:        { slug, title, authors, year, edition?, about?, reflections: [] }
//                `edition` = the copy Gideon read; `about` = a line he writes (empty → not shown).
// A reflection:  { slug, title, date: "YYYY-MM-DD", summary, ready }
//                ready: false → listed nowhere until it is. A reflection lives at
//                learning/reflections/<book>/<slug>/ (index.html, main.js, <slug>.py, <slug>.ipynb).
// Excluded from the offline app (build.ps1 $Exclude); the hub loads this file only when it is
// not the installed copy, and hides its block when the file is missing.
window.LEARN_BOOKS = [
  {
    slug: "the-goal", title: "The Goal: A Process of Ongoing Improvement",
    authors: "Eliyahu M. Goldratt & Jeff Cox", year: 1984, edition: "2nd revised edition", about: "",
    reflections: [
      {
        slug: "balanced-plant", title: "The Balanced Plant Theorem", date: "2026-10-13", ready: true,
        summary: "Jonah says a mathematical proof shows that trimming capacity to match demand cuts throughput and sends inventory through the roof. Here is that proof, from queueing theory."
      }
    ]
  },
  { slug: "machine-that-changed-the-world", title: "The Machine That Changed the World",
    authors: "James P. Womack, Daniel T. Jones & Daniel Roos", year: 1990, about: "", reflections: [] },
  { slug: "good-to-great", title: "Good to Great", authors: "Jim Collins", year: 2001, about: "", reflections: [] },
  { slug: "you-already-know-how-to-be-great", title: "You Already Know How to Be Great",
    authors: "Alan Fine with Rebecca R. Merrill", year: 2010, about: "", reflections: [] },
  { slug: "how-the-mighty-fall", title: "How the Mighty Fall", authors: "Jim Collins", year: 2009, about: "", reflections: [] },
  { slug: "reengineering-the-corporation", title: "Reengineering the Corporation",
    authors: "Michael Hammer & James Champy", year: 1993, about: "", reflections: [] },
  { slug: "practice-of-management", title: "The Practice of Management", authors: "Peter F. Drucker", year: 1954, about: "", reflections: [] },
  { slug: "functions-of-the-executive", title: "The Functions of the Executive", authors: "Chester I. Barnard", year: 1938, about: "", reflections: [] },
  { slug: "human-side-of-enterprise", title: "The Human Side of Enterprise", authors: "Douglas McGregor", year: 1960, about: "", reflections: [] },
  { slug: "strategic-technology-management", title: "Strategic Technology Management", authors: "Frederick Betz", year: 1993, about: "", reflections: [] },
  { slug: "new-economics", title: "The New Economics for Industry, Government, Education",
    authors: "W. Edwards Deming", year: 1993, about: "", reflections: [] }
];

// Renderers. Paths are relative to the page that calls them, so they work on the site and from
// disk (learning.js's LF.fixFileLinks rewrites folder links when opened from file:).
(function () {
  "use strict";
  var BOOKS = window.LEARN_BOOKS;
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); }
  // "YYYY-MM-DD" → a date in words, from its parts (never new Date(string): that is UTC midnight
  // and shows the previous day west of Greenwich). lang "es" → "13 de octubre de 2026".
  function fmtDate(iso, lang) {
    var p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!p) return iso || "";
    var d = new Date(Date.UTC(+p[1], +p[2] - 1, +p[3]));
    return d.toLocaleDateString(lang === "es" ? "es" : "en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });
  }
  function ready(b) { return b.reflections.filter(function (r) { return r.ready; }); }
  function fix(el) { if (window.LF && LF.fixFileLinks) LF.fixFileLinks(el); }

  // Hub block (learning/index.html): every ready reflection, newest first, then nothing else
  // (the "All 11 books" link is static markup). `t` = LI18N.t for the hub's words.
  function hubList(el, lang, t) {
    var rows = [];
    BOOKS.forEach(function (b) {
      ready(b).forEach(function (r) { rows.push({ b: b, r: r }); });
    });
    rows.sort(function (x, y) { return x.r.date < y.r.date ? 1 : x.r.date > y.r.date ? -1 : 0; });
    el.innerHTML = rows.map(function (x) {
      return '<li><a class="module-row ref-row" href="reflections/' + x.b.slug + '/' + x.r.slug + '/">' +
        '<span class="ref-book" lang="en">' + esc(x.b.title) + '</span>' +
        '<span class="m-title" lang="en">' + esc(x.r.title) + '</span>' +
        '<span class="ref-date">' + esc(fmtDate(x.r.date, lang)) + '</span>' +
        '<span class="m-desc" lang="en">' + esc(x.r.summary) + '</span></a></li>';
    }).join("");
    fix(el);
  }

  // All-books page (learning/reflections/index.html): the 11 books in order. A book with ready
  // reflections links to its page and shows the count; the others say "Not yet" with no link.
  function bookList(el) {
    el.innerHTML = BOOKS.map(function (b, i) {
      var n = ready(b).length;
      var inner = '<span class="b-num">' + String(i + 1).padStart(2, "0") + '</span>' +
        '<span class="b-title"><i>' + esc(b.title) + '</i></span>' +
        '<span class="b-meta">' + esc(b.authors) + ', ' + b.year + (b.edition ? ' · ' + esc(b.edition) : '') + '</span>' +
        '<span class="b-count' + (n ? ' has' : '') + '">' + (n ? n + (n === 1 ? ' reflection' : ' reflections') : 'Not yet') + '</span>' +
        (b.about ? '<span class="b-about">' + esc(b.about) + '</span>' : '');
      return '<li>' + (n ? '<a class="book-row" href="' + b.slug + '/">' + inner + '</a>'
        : '<div class="book-row is-soon">' + inner + '</div>') + '</li>';
    }).join("");
    fix(el);
  }

  // Book page (learning/reflections/<book>/index.html): its ready reflections, newest first.
  // `about` goes into the element with id "book-about" when it is set.
  function bookPage(el, slug) {
    var b = BOOKS.filter(function (x) { return x.slug === slug; })[0];
    if (!b) return;
    var about = document.getElementById("book-about");
    if (about && b.about) { about.textContent = b.about; about.hidden = false; }
    var rows = ready(b).slice().sort(function (x, y) { return x.date < y.date ? 1 : x.date > y.date ? -1 : 0; });
    el.innerHTML = rows.map(function (r) {
      return '<li><a class="module-row ref-row" href="' + r.slug + '/">' +
        '<span class="m-title">' + esc(r.title) + '</span>' +
        '<span class="ref-date">' + esc(fmtDate(r.date, "en")) + '</span>' +
        '<span class="m-desc">' + esc(r.summary) + '</span></a></li>';
    }).join("");
    fix(el);
  }

  window.LEARN_REFLECTIONS = { hubList: hubList, bookList: bookList, bookPage: bookPage, fmtDate: fmtDate };
}());
