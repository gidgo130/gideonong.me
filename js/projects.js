// projects.js
// Renders §2 (featured) and §3 (index) of projects.html from the ONE array in
// js/projects-data.js, and runs the §3 tag filter. Both sections read the same
// entries — `featured: true` promotes an entry into §2 and it still appears in
// §3. There is no second data source anywhere on this page.
//
// §1 (the search band) is intentionally untouched here beyond filling its
// placeholder text: the band ships hidden (.search-band.is-hidden) and its input
// is inert until the Phase 3 semantic search is written. When that lands, it
// reorders/filters the same rows this file renders — the markup does not change.
//
// Animation, per CLAUDE.md (no carve-outs on this page):
//   - featured entries fade in on scroll (IntersectionObserver, opacity only)
//   - the filter transitions opacity only; filtered-out rows are display:none so
//     the list closes up. Rows never slide or animate position.

(function () {
  var featuredList = document.getElementById("featured-list");
  var indexList = document.getElementById("project-index");
  if (!featuredList || !indexList || typeof projectsData === "undefined") return;

  var filterRow = document.getElementById("tag-filter");
  var countEl = document.getElementById("index-count");
  var emptyEl = document.getElementById("index-empty");

  // Active tag filters. AND logic: an entry must carry EVERY active tag.
  // Lives outside render() so a language switch (which re-renders everything)
  // does not silently reset the filter the visitor set.
  var activeTags = [];

  // Rows are kept paired with their entry so filtering reads the data rather
  // than scraping the DOM for tag names.
  var rows = [];

  function currentLang() {
    return document.documentElement.getAttribute("lang") === "es" ? "es" : "en";
  }

  function text(key) {
    var dict = (typeof translations !== "undefined") ? translations[currentLang()] : null;
    return (dict && dict[key] !== undefined) ? dict[key] : key;
  }

  /* ---- Entry selection ------------------------------------------------------
     `unlisted` entries are excluded from every listing (and, later, from search)
     while still living in the array so their sub-page can be generated. */
  function listedEntries() {
    return projectsData.filter(function (entry) {
      return entry.visible && !entry.unlisted;
    });
  }

  function featuredEntries() {
    return listedEntries().filter(function (entry) { return entry.featured; });
  }

  // Array order is the reverse-chronological order the author maintains by hand;
  // `pinned: true` lifts an entry above the rest without disturbing that order.
  function indexEntries() {
    var all = listedEntries();
    return all.filter(function (e) { return e.pinned; })
      .concat(all.filter(function (e) { return !e.pinned; }));
  }

  /* ---- Shared builders ----------------------------------------------------- */

  function buildTagRow(entry) {
    var row = document.createElement("div");
    row.className = "tag-row";
    (entry.tags || []).forEach(function (tag) {
      var pill = document.createElement("span");
      pill.className = "tag-pill";
      pill.textContent = tag;
      row.appendChild(pill);
    });
    return row;
  }

  // Returns null when subpageUrl is "" — no sub-page yet means no link at all,
  // never a link that goes nowhere.
  function buildViewLink(entry) {
    if (!entry.subpageUrl) return null;
    var link = document.createElement("a");
    link.className = "project-link";
    link.href = entry.subpageUrl;
    link.setAttribute("data-i18n", "projViewLink");
    link.textContent = text("projViewLink");
    return link;
  }

  function buildImage(entry, className) {
    var img = document.createElement("img");
    img.className = className;
    img.src = entry.imageSrc;
    img.alt = entry.imageAlt ? text(entry.imageAlt) : "";
    img.loading = "lazy";
    return img;
  }

  /* ---- §2 Featured ---------------------------------------------------------
     Image → title → description → tags → link. Tags sit BELOW the description,
     never above the title (CLAUDE.md). Arrangement alternates image-left /
     image-right; the set is 2-3 entries and fixed, which is the one place a
     global alternating rule is appropriate. */
  function buildFeatured(entry, i) {
    var article = document.createElement("article");
    article.className = "featured-entry " +
      (i % 2 === 0 ? "featured-entry--image-left" : "featured-entry--image-right");

    if (entry.imageSrc) {
      var media = document.createElement("div");
      media.className = "featured-entry-media";
      media.appendChild(buildImage(entry, "featured-entry-image"));
      article.appendChild(media);
    }

    var body = document.createElement("div");
    body.className = "featured-entry-body";

    var title = document.createElement("h3");
    title.className = "featured-entry-title";
    title.setAttribute("data-i18n", entry.titleKey);
    title.textContent = text(entry.titleKey);
    body.appendChild(title);

    var meta = document.createElement("p");
    meta.className = "featured-entry-meta";
    meta.textContent = entry.dates; // literal, never translated
    body.appendChild(meta);

    var desc = document.createElement("p");
    desc.className = "featured-entry-desc";
    desc.setAttribute("data-i18n", entry.longDescKey);
    desc.textContent = text(entry.longDescKey);
    body.appendChild(desc);

    body.appendChild(buildTagRow(entry));

    var link = buildViewLink(entry);
    if (link) body.appendChild(link);

    article.appendChild(body);
    return article;
  }

  /* ---- §3 Index rows -------------------------------------------------------
     Identical markup under both .project-index--rows and .project-index--grid —
     switching views later is a class swap on the container, with no change to
     this function or to the data array.

     An entry with no imageSrc gets .project-row--no-image and no <img> node at
     all: the text takes the full row width. Not a broken image, not a grey box,
     not a placeholder icon. */
  function buildRow(entry) {
    var row = document.createElement("article");
    row.className = "project-row" + (entry.imageSrc ? "" : " project-row--no-image");

    if (entry.imageSrc) {
      var thumb = document.createElement("div");
      thumb.className = "project-thumb";
      thumb.appendChild(buildImage(entry, "project-thumb-image"));
      row.appendChild(thumb);
    }

    var body = document.createElement("div");
    body.className = "project-row-body";

    var heading = document.createElement("h3");
    heading.className = "project-row-title";
    var titleText = document.createElement("span");
    titleText.setAttribute("data-i18n", entry.titleKey);
    titleText.textContent = text(entry.titleKey);
    heading.appendChild(titleText);
    var dates = document.createElement("span");
    dates.className = "project-row-dates";
    dates.textContent = entry.dates; // literal, never translated
    heading.appendChild(dates);
    body.appendChild(heading);

    var desc = document.createElement("p");
    desc.className = "project-row-desc";
    desc.setAttribute("data-i18n", entry.descKey);
    desc.textContent = text(entry.descKey);
    body.appendChild(desc);

    body.appendChild(buildTagRow(entry));

    var link = buildViewLink(entry);
    if (link) body.appendChild(link);

    row.appendChild(body);
    return row;
  }

  /* ---- Tag filter ----------------------------------------------------------
     Pills come from PROJECT_TAGS (the controlled vocabulary) in vocabulary
     order, narrowed to tags at least one listed entry actually carries — a pill
     that can only ever return zero results is noise, not a filter.
     Multi-select, AND logic. The "Clear" pill resets. */
  function tagsInUse() {
    var used = {};
    listedEntries().forEach(function (entry) {
      (entry.tags || []).forEach(function (tag) { used[tag] = true; });
    });
    var vocabulary = (typeof PROJECT_TAGS !== "undefined") ? PROJECT_TAGS : [];
    return vocabulary.filter(function (tag) { return used[tag]; });
  }

  function toggleTag(tag) {
    var at = activeTags.indexOf(tag);
    if (at === -1) {
      activeTags.push(tag);
    } else {
      activeTags.splice(at, 1);
    }
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
      pill.textContent = tag;
      pill.setAttribute("data-tag", tag);
      pill.addEventListener("click", function () { toggleTag(tag); });
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
  function matchesFilter(entry) {
    return activeTags.every(function (tag) {
      return (entry.tags || []).indexOf(tag) !== -1;
    });
  }

  function applyFilter() {
    var shown = 0;
    rows.forEach(function (pair) {
      var visible = matchesFilter(pair.entry);
      // display:none removes the row from flow so the list closes up rather
      // than leaving a gap. Only opacity is transitioned — never position.
      pair.row.classList.toggle("is-filtered-out", !visible);
      if (visible) shown++;
    });
    updateCount(shown);
    if (emptyEl) emptyEl.hidden = shown !== 0;
  }

  function updateCount(n) {
    if (!countEl) return;
    var key = n === 1 ? "projCountOne" : "projCount";
    countEl.textContent = text(key).replace("{n}", n);
  }

  /* ---- §1 search band ------------------------------------------------------
     The band is hidden and the input is inert; this only keeps its placeholder
     in the right language so nothing is left in the wrong language when the
     band is revealed in Phase 3. main.js handles data-i18n and data-i18n-alt
     but not placeholders, so it is done here. */
  function renderSearchPlaceholder() {
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.setAttribute("placeholder", text(el.getAttribute("data-i18n-placeholder")));
    });
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
    featuredEntries().forEach(function (entry, i) {
      var article = buildFeatured(entry, i);
      featuredList.appendChild(article);
      observer.observe(article);
    });

    indexList.innerHTML = "";
    rows = [];
    indexEntries().forEach(function (entry) {
      var row = buildRow(entry);
      indexList.appendChild(row);
      rows.push({ row: row, entry: entry });
    });

    renderFilter();
    renderSearchPlaceholder();
    applyFilter(); // also paints the count and the empty state
  }

  // main.js fires langchange at the end of applyTranslations, so this runs after
  // the data-i18n elements are swapped and always wins on JS-rendered content.
  document.addEventListener("langchange", render);
  render();
}());
