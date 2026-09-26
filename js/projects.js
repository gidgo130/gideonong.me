// projects.js
// Renders §2 (featured) and §3 (index) of projects.html from the ONE array in
// js/projects-data.js, runs the §3 tag filter and the §1 keyword search, and
// handles projects.html#<slug> deep links. Markup builders and selectors are
// shared with index.html via js/data-helpers.js (window.siteData).
//
// Only listing: "index" entries exist as far as this file is concerned —
// siteData.indexProjects() has already dropped unlisted / hidden / reserved
// entries, so nothing below can leak one into the index, the filter, search
// or the featured block.
//
// Animation, per CLAUDE.md (no carve-outs on this page):
//   - featured entries fade in on scroll (IntersectionObserver, opacity only)
//   - the filter transitions opacity only; filtered-out rows are display:none so
//     the list closes up. Rows never slide or animate position.
//   - the deep-link target gets a static left rule — no animation, no scroll
//     effect beyond the initial jump.

(function () {
  var featuredList = document.getElementById("featured-list");
  var indexList = document.getElementById("project-index");
  if (!featuredList || !indexList || typeof siteData === "undefined") return;

  var text = siteData.text;

  var filterRow = document.getElementById("tag-filter");
  var countEl = document.getElementById("index-count");
  var emptyEl = document.getElementById("index-empty");
  var searchInput = document.getElementById("project-search");
  var searchBtn = document.getElementById("project-search-btn");
  var searchClear = document.getElementById("project-search-clear");
  var searchField = document.getElementById("project-search-field");

  // Visitor state. Both live OUTSIDE render() so a language switch (which
  // re-renders everything) keeps the active filter and the query exactly.
  var activeTags = [];   // tag IDS (never labels) — AND logic
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
     at once. The × clears and refocuses. Filter state and query state combine
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
  // aria-labels on the search chrome, so they are refreshed here each render.
  function renderSearchChrome() {
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.setAttribute("placeholder", text(el.getAttribute("data-i18n-placeholder")));
    });
    if (searchClear) searchClear.setAttribute("aria-label", text("projSearchClear"));
  }

  /* ---- Tag filter ----------------------------------------------------------
     Pills come from the shared vocabulary (js/tags-data.js) in vocabulary
     order, narrowed to tags at least one index entry actually carries — a pill
     that can only ever return zero results is noise, not a filter.
     Multi-select, AND logic, state stored as ids. The "Clear" pill resets. */
  function tagsInUse() {
    var used = {};
    siteData.indexProjects().forEach(function (entry) {
      (entry.tags || []).forEach(function (id) { used[id] = true; });
    });
    return siteData.tagVocabulary().filter(function (tag) { return used[tag.id]; });
  }

  function toggleTag(id) {
    var at = activeTags.indexOf(id);
    if (at === -1) activeTags.push(id); else activeTags.splice(at, 1);
    syncFilterPills();
    applyFilter();
  }

  function renderFilter() {
    if (!filterRow) return;
    filterRow.innerHTML = "";
    filterRow.setAttribute("aria-label", text("projFilterLabel"));

    var clear = document.createElement("button");
    clear.type = "button";
    clear.className = "tag-filter-pill tag-filter-pill--clear";
    clear.setAttribute("data-i18n", "projFilterClear");
    clear.textContent = text("projFilterClear");
    clear.addEventListener("click", function () {
      activeTags = [];
      syncFilterPills();
      applyFilter();
    });
    filterRow.appendChild(clear);

    tagsInUse().forEach(function (tag) {
      var pill = document.createElement("button");
      pill.type = "button";
      pill.className = "tag-filter-pill";
      pill.textContent = siteData.tagLabel(tag.id);
      pill.setAttribute("data-tag", tag.id);
      pill.addEventListener("click", function () { toggleTag(tag.id); });
      filterRow.appendChild(pill);
    });

    syncFilterPills();
  }

  // Pill visual state is derived from activeTags, never stored on the element —
  // so a re-render (language switch) restores it for free.
  function syncFilterPills() {
    if (!filterRow) return;
    filterRow.querySelectorAll(".tag-filter-pill[data-tag]").forEach(function (pill) {
      var isActive = activeTags.indexOf(pill.getAttribute("data-tag")) !== -1;
      pill.classList.toggle("is-active", isActive);
      pill.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
    var clear = filterRow.querySelector(".tag-filter-pill--clear");
    if (clear) clear.classList.toggle("is-active", activeTags.length === 0);
  }

  // AND logic: the entry must carry EVERY active tag, not any of them.
  function matchesTags(entry) {
    return activeTags.every(function (id) {
      return (entry.tags || []).indexOf(id) !== -1;
    });
  }

  /* ---- Combine tags + search ----------------------------------------------
     A row stays visible only if it passes BOTH the tag filter and the search.
     The count and the empty state reflect the combination. Visible rows are
     re-appended in the order searchEntries() returned them (identical to index
     order today; a ranking search later reorders for free). Featured §2 is
     never filtered. */
  function applyFilter() {
    var matched = searchEntries(activeQuery, rows.map(function (pair) { return pair.entry; }))
      .filter(matchesTags);
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
  }

  function updateCount(n) {
    if (!countEl) return;
    var key = n === 1 ? "projCountOne" : "projCount";
    countEl.textContent = text(key).replace("{n}", n);
  }

  // projEmptySearch when a query is active (with or without tags), projEmpty
  // when only tags are. Text is set here, not via data-i18n, because it
  // depends on state.
  function updateEmpty(shown) {
    if (!emptyEl) return;
    emptyEl.hidden = shown !== 0;
    if (shown !== 0) return;
    emptyEl.textContent = activeQuery.trim()
      ? text("projEmptySearch").replace("{q}", activeQuery.trim())
      : text("projEmpty");
  }

  /* ---- Deep links ---------------------------------------------------------
     projects.html#<slug>: clear any active tags and query (a hidden target is
     useless), scroll the row clear of the nav, mark it. Re-run on hashchange.
     A language re-render re-marks without scrolling. */
  function goToHash(scroll) {
    if (!location.hash) return;
    if (scroll) {
      activeTags = [];
      setQuery("");
      syncFilterPills();
      applyFilter();
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

    renderFilter();
    renderSearchChrome();
    applyFilter(); // also paints the count and the empty state
    goToHash(false);
  }

  siteData.checkData();
  buildCorpus();
  wireSearch();

  // main.js fires langchange at the end of applyTranslations, so this runs after
  // the data-i18n elements are swapped and always wins on JS-rendered content.
  document.addEventListener("langchange", render);
  window.addEventListener("hashchange", function () { goToHash(true); });
  render();
  goToHash(true);
}());
