// projects.js
// Renders §2 (featured) and §3 (index) of projects.html from the ONE array in
// js/projects-data.js, runs the §3 tag filter (from the URL) and the §1
// keyword search, and handles projects.html#<slug> deep links. Markup
// builders and selectors are shared with index.html and the sub-pages via
// js/data-helpers.js (window.siteData).
//
// Only listing: "index" entries exist as far as this file is concerned —
// siteData.indexProjects() has already dropped unlisted / hidden / reserved
// entries, so nothing below can leak one into the index, the filter, search
// or the featured block.
//
// Filters (2026-09-27): there is no filter row. Every tag pill on the site is
// a link to projects.html?tag=<id>, and a band image on experience.html can
// link to projects.html?part=<experience slug>. This page reads both on load,
// filters the index (AND with each other and with the search), and shows each
// active filter as a "<Label> ✕" chip beside the count. ✕ clears that filter
// and rewrites the URL (history.replaceState), so a filtered view is always
// linkable. An unknown id / slug is ignored.
//
// Animation, per CLAUDE.md:
//   - the featured section collapses (height + opacity, 300ms) while any
//     filter is active — a recorded movement exception (see updateFeaturedCollapse)
//   - featured entries fade in on scroll (IntersectionObserver, opacity only)
//   - the filter transitions opacity only; filtered-out rows are display:none so
//     the list closes up. Rows never slide or animate position.
//   - the deep-link target gets a static left rule — no animation, no scroll
//     effect beyond the initial jump.

(function () {
  var featuredList = document.getElementById("featured-list");
  var featuredSection = document.getElementById("featured-projects");
  var indexList = document.getElementById("project-index");
  if (!featuredList || !indexList || typeof siteData === "undefined") return;

  var text = siteData.text;

  var countEl = document.getElementById("index-count");
  var emptyEl = document.getElementById("index-empty");
  var chipEl = document.getElementById("tag-chip");
  var chipLabel = document.getElementById("tag-chip-label");
  var chipClear = document.getElementById("tag-chip-clear");
  var partChipEl = document.getElementById("part-chip");
  var partChipLabel = document.getElementById("part-chip-label");
  var partChipClear = document.getElementById("part-chip-clear");
  var searchInput = document.getElementById("project-search");
  var searchBtn = document.getElementById("project-search-btn");
  var searchClear = document.getElementById("project-search-clear");
  var searchField = document.getElementById("project-search-field");

  // Visitor state. Both live OUTSIDE render() so a language switch (which
  // re-renders everything) keeps the active tag and the query exactly.
  var activeTag = null;  // one tag ID (never a label), from ?tag=
  var activePart = null; // one visible experience slug, from ?part=
  var activeQuery = "";  // raw text as typed

  // Rows are kept paired with their entry so filtering reads the data rather
  // than scraping the DOM.
  var rows = [];

  /* ---- Search: corpus ---------------------------------------------------
     One normalized string per index entry, built ONCE from BOTH languages so a
     Spanish word matches while the page is in English and vice versa, and so
     a language switch never changes the result set. Rebuild only if the data
     arrays change (they don't at runtime — call buildCorpus() again if that
     ever becomes true).

     Fields: title, desc, longDesc, searchText, tag labels, context label, and
     the linked experience's role + org. */
  var corpus = {};

  // Lowercase + strip diacritics (NFD, then drop combining marks): "diseño"
  // and "diseno" match each other, in the query and in the corpus alike.
  function normalize(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function buildCorpus() {
    corpus = {};
    siteData.indexProjects().forEach(function (entry) {
      var parts = [];
      ["en", "es"].forEach(function (lang) {
        parts.push(
          text(entry.titleKey, lang),
          text(entry.descKey, lang),
          text(entry.longDescKey, lang),
          text(entry.searchTextKey, lang),
          siteData.contextLabel(entry.context, lang)
        );
        (entry.tags || []).forEach(function (id) { parts.push(siteData.tagLabel(id, lang)); });
        var role = siteData.experienceBySlug(entry.experience);
        if (role) parts.push(text(role.roleKey, lang), text(role.orgKey, lang));
      });
      corpus[entry.slug] = normalize(parts.join(" "));
    });
  }

  /* ---- Search: matching ---------------------------------------------------
     searchEntries(query, entries) → entries
     THE ONE PLACE matching happens. Today: split the query on whitespace and
     keep an entry only if EVERY token is a substring of its corpus (AND).
     Result order is the input order.

     Phase 3 (TF-IDF + cosine over the same corpus) replaces the BODY of this
     function only — same signature, same return shape. It may return the
     entries reordered by score; applyFilter() already lays rows out in the
     order this returns. No markup and no caller changes. */
  function searchEntries(query, entries) {
    var tokens = normalize(query).split(/\s+/).filter(Boolean);
    if (!tokens.length) return entries.slice();
    return entries.filter(function (entry) {
      var doc = corpus[entry.slug] || "";
      return tokens.every(function (token) { return doc.indexOf(token) !== -1; });
    });
  }

  /* ---- Search: band wiring ----------------------------------------------
     Runs as the visitor types (debounced ~150ms); Enter and the button run it
     at once. The × clears and refocuses. Tag state and query state combine
     with AND in applyFilter(). */
  var debounceTimer = null;

  function setQuery(q) {
    activeQuery = q;
    if (searchInput && searchInput.value !== q) searchInput.value = q;
    if (searchField) searchField.classList.toggle("has-text", q.length > 0);
  }

  function runSearch() {
    clearTimeout(debounceTimer);
    setQuery(searchInput ? searchInput.value : "");
    applyFilter();
  }

  function wireSearch() {
    if (!searchInput) return;
    searchInput.addEventListener("input", function () {
      if (searchField) searchField.classList.toggle("has-text", searchInput.value.length > 0);
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(runSearch, 150);
    });
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); runSearch(); }
    });
    if (searchBtn) searchBtn.addEventListener("click", runSearch);
    if (searchClear) {
      searchClear.addEventListener("click", function () {
        clearTimeout(debounceTimer);
        setQuery("");
        applyFilter();
        searchInput.focus();
      });
    }
  }

  // main.js handles data-i18n and data-i18n-alt but not placeholders or
  // aria-labels on the chrome, so they are refreshed here each render.
  function renderSearchChrome() {
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.setAttribute("placeholder", text(el.getAttribute("data-i18n-placeholder")));
    });
    if (searchClear) searchClear.setAttribute("aria-label", text("projSearchClear"));
    if (chipClear) chipClear.setAttribute("aria-label", text("projTagClear"));
    if (partChipClear) partChipClear.setAttribute("aria-label", text("projPartClear"));
  }

  /* ---- Tag + role filters (URL state) --------------------------------------
     ?tag=<id> and ?part=<experience slug> are the whole state. Both are read
     on load; an unknown id / slug (or a hidden role) is ignored. Each has its
     own chip beside the count; ✕ clears that one and rewrites the URL in
     place. They combine with each other and with the search by AND. */
  function readFiltersFromUrl() {
    var params;
    try { params = new URLSearchParams(location.search); } catch (e) { return; }
    var tag = params.get("tag");
    var part = params.get("part");
    activeTag = (tag && siteData.tagExists(tag)) ? tag : null;
    activePart = (part && siteData.experienceBySlug(part)) ? part : null;
  }

  function writeFiltersToUrl() {
    var url;
    try { url = new URL(location.href); } catch (e) { return; }
    if (activeTag) url.searchParams.set("tag", activeTag); else url.searchParams.delete("tag");
    if (activePart) url.searchParams.set("part", activePart); else url.searchParams.delete("part");
    history.replaceState(null, "", url.pathname + url.search + url.hash);
  }

  function setTag(id) {
    activeTag = id || null;
    writeFiltersToUrl();
    renderChips();
    applyFilter();
  }

  function setPart(slug) {
    activePart = slug || null;
    writeFiltersToUrl();
    renderChips();
    applyFilter();
  }

  // The chips beside the count: "<Label> ✕". Each is hidden when its filter
  // is off. Labels are derived from the id / slug each render, so a language
  // switch translates them.
  function renderChips() {
    if (chipEl) {
      chipEl.hidden = !activeTag;
      if (chipLabel) chipLabel.textContent = activeTag ? siteData.tagLabel(activeTag) : "";
    }
    if (partChipEl) {
      var role = siteData.experienceBySlug(activePart);
      partChipEl.hidden = !role;
      if (partChipLabel) partChipLabel.textContent = role ? text(role.orgShortKey || role.orgKey) : "";
    }
  }

  function wireChips() {
    if (chipClear) chipClear.addEventListener("click", function () { setTag(null); });
    if (partChipClear) partChipClear.addEventListener("click", function () { setPart(null); });
  }

  function matchesTag(entry) {
    return !activeTag || (entry.tags || []).indexOf(activeTag) !== -1;
  }

  function matchesPart(entry) {
    return !activePart || entry.experience === activePart;
  }

  /* ---- Combine filters + search -------------------------------------------
     A row stays visible only if it passes the tag filter, the role filter AND
     the search. The count and the empty state reflect the combination. Visible
     rows are re-appended in the order searchEntries() returned them (identical
     to index order today; a ranking search later reorders for free). Featured
     §2 is never filtered. */
  function applyFilter() {
    var matched = searchEntries(activeQuery, rows.map(function (pair) { return pair.entry; }))
      .filter(matchesTag)
      .filter(matchesPart);
    var order = {};
    matched.forEach(function (entry, i) { order[entry.slug] = i; });

    var shownPairs = [];
    rows.forEach(function (pair) {
      var visible = order[pair.entry.slug] !== undefined;
      // display:none removes the row from flow so the list closes up rather
      // than leaving a gap. Only opacity is transitioned — never position.
      pair.row.classList.toggle("is-filtered-out", !visible);
      if (visible) shownPairs.push(pair);
    });
    shownPairs
      .sort(function (a, b) { return order[a.entry.slug] - order[b.entry.slug]; })
      .forEach(function (pair) { indexList.appendChild(pair.row); });

    updateCount(shownPairs.length);
    updateEmpty(shownPairs.length);
    updateFeaturedCollapse();
  }

  /* ---- Featured collapse ---------------------------------------------------
     While ANY filter is active (search text, ?tag=, ?part=) the featured
     section collapses (style.css .featured-projects.is-collapsed: height +
     opacity, 300ms) so the results sit right under the search band. The
     section starts with .is-settling (transitions off) and loses it one frame
     after the first render, so a page opened as ?tag=… starts collapsed with
     no animation even if the browser painted before this script ran.
     Clearing every filter brings it back. */
  function updateFeaturedCollapse() {
    if (!featuredSection) return;
    var filtering = !!activeQuery.trim() || !!activeTag || !!activePart;
    featuredSection.classList.toggle("is-collapsed", filtering);
    if (filtering) featuredSection.setAttribute("aria-hidden", "true");
    else featuredSection.removeAttribute("aria-hidden");
  }

  function updateCount(n) {
    if (!countEl) return;
    var key = n === 1 ? "projCountOne" : "projCount";
    countEl.textContent = text(key).replace("{n}", n);
  }

  // projEmptySearch when a query is active (with or without filters), projEmpty
  // when only the tag / role filters are. Text is set here, not via data-i18n,
  // because it depends on state.
  function updateEmpty(shown) {
    if (!emptyEl) return;
    emptyEl.hidden = shown !== 0;
    if (shown !== 0) return;
    emptyEl.textContent = activeQuery.trim()
      ? text("projEmptySearch").replace("{q}", activeQuery.trim())
      : text("projEmpty");
  }

  /* ---- Deep links ---------------------------------------------------------
     projects.html#<slug>: clear the filters and the query (a hidden target is
     useless), scroll the row clear of the nav, mark it. Re-run on hashchange.
     A language re-render re-marks without scrolling. */
  function goToHash(scroll) {
    if (!location.hash) return;
    if (scroll) {
      setQuery("");
      activeTag = null;
      setPart(null); // drops ?tag= and ?part= from the URL and repaints
    }
    siteData.targetFromHash(".project-row", scroll);
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  function render() {
    observer.disconnect();

    featuredList.innerHTML = "";
    siteData.featuredProjects().forEach(function (entry, i) {
      var article = siteData.buildFeatured(entry, i);
      featuredList.appendChild(article);
      observer.observe(article);
    });

    indexList.innerHTML = "";
    rows = [];
    siteData.indexProjects().forEach(function (entry) {
      var row = siteData.buildRow(entry);
      indexList.appendChild(row);
      rows.push({ row: row, entry: entry });
    });

    renderSearchChrome();
    renderChips();
    applyFilter(); // also paints the count and the empty state
    goToHash(false);
  }

  siteData.checkData();
  buildCorpus();
  wireSearch();
  wireChips();
  readFiltersFromUrl();

  // main.js fires langchange at the end of applyTranslations, so this runs after
  // the data-i18n elements are swapped and always wins on JS-rendered content.
  document.addEventListener("langchange", render);
  window.addEventListener("hashchange", function () { goToHash(true); });
  render();
  goToHash(true);
  // Initial state is painted; from the next frame on, collapse / expand animate.
  if (featuredSection) {
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { featuredSection.classList.remove("is-settling"); });
    });
  }
}());
