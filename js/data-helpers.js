// data-helpers.js
// Read-side helpers shared by js/projects.js, js/experience.js, js/home.js and
// js/project-page.js: string lookup, tag and context labels, date formatting,
// listing/sort selectors, the project markup builders, hash deep-link
// targeting, and the dev-only data check.
//
// Load order on every page that uses it:
//   translations.js → chips.js → main.js → tags-data.js → experience-data.js →
//   projects-data.js → data-helpers.js → <page script>
//
// Everything is exposed on window.siteData. Nothing here touches the DOM at
// load time — the page scripts decide what to render and when.

(function () {
  function currentLang() {
    return document.documentElement.getAttribute("lang") === "es" ? "es" : "en";
  }

  // Pages in a subfolder (projects/<slug>.html) carry data-root="../" on
  // <body>. Every relative href/src built here is prefixed with it, so the
  // same builders work from the site root and from /projects/.
  var ROOT = (document.body && document.body.getAttribute("data-root")) || "";

  // Dev-only behavior (the data check, HEAD probes) runs on localhost only —
  // a real visitor never pays for an extra request.
  function isDev() {
    var h = location.hostname;
    return h === "localhost" || h === "127.0.0.1" || h === "[::1]" || h === "::1" || location.protocol === "file:";
  }

  // text(key)        → string in the active language
  // text(key, "es")  → string in that language (the search corpus uses both)
  // A missing key falls back to the key itself so the page never renders blank.
  function text(key, lang) {
    var dict = (typeof translations !== "undefined") ? translations[lang || currentLang()] : null;
    return (dict && dict[key] !== undefined) ? dict[key] : key;
  }

  // Fill an element with text, linking phrase chips (js/chips.js).
  function fillText(el, str, lang) {
    if (typeof siteChips !== "undefined") siteChips.fill(el, str, lang);
    else el.textContent = str;
    return el;
  }

  /* ---- Tags ---------------------------------------------------------------
     Data files store tag IDS (js/tags-data.js). The label is looked up here so
     pills translate, and the ?tag= filter state can stay id-based. */
  var TAG_BY_ID = {};
  (typeof TAGS !== "undefined" ? TAGS : []).forEach(function (tag) { TAG_BY_ID[tag.id] = tag; });

  function tagLabel(id, lang) {
    var tag = TAG_BY_ID[id];
    return tag ? text(tag.key, lang) : id;
  }

  function tagExists(id) {
    return !!TAG_BY_ID[id];
  }

  function tagVocabulary() {
    return (typeof TAGS !== "undefined") ? TAGS : [];
  }

  // Every tag pill links to the filtered index. Same URL from every page.
  function tagUrl(id) {
    return ROOT + "projects.html?tag=" + encodeURIComponent(id);
  }

  /* ---- Context ---------------------------------------------------------- */
  var CONTEXT_KEYS = {
    industry: "ctxIndustry",
    coursework: "ctxCoursework",
    personal: "ctxPersonal",
    service: "ctxService",
    research: "ctxResearch"
  };

  function contextLabel(context, lang) {
    var key = CONTEXT_KEYS[context];
    return key ? text(key, lang) : "";
  }

  /* ---- Dates ----------------------------------------------------------------
     `dates` on projects and experience entries is language-neutral:
       { from: <point> }                     "Summer 2026" / "Verano 2026"
       { from: <point>, to: "present" }      "Spring 2026 – present"
       { from: <point>, to: <point> }        "Fall 2025 – Spring 2026"
     where <point> is one of
       { season: "spring"|"summer"|"fall"|"winter", year: 2026 }
       { month: 1..12, year: 2022 }          "July 2022" / "julio de 2022"
       { year: 2025 }                        "2025"
     Rendered through translations.js: dateSpring… / dateMonth1… / datePresent /
     dateSeasonYear / dateMonthYear / dateRange. */
  var SEASON_KEYS = { spring: "dateSpring", summer: "dateSummer", fall: "dateFall", winter: "dateWinter" };

  function formatPoint(p, lang) {
    if (p === "present") return text("datePresent", lang);
    if (!p || typeof p !== "object") return "";
    var year = (p.year !== undefined && p.year !== null) ? String(p.year) : "";
    if (p.season && SEASON_KEYS[p.season]) {
      return text("dateSeasonYear", lang)
        .replace("{season}", text(SEASON_KEYS[p.season], lang))
        .replace("{year}", year);
    }
    if (p.month >= 1 && p.month <= 12) {
      return text("dateMonthYear", lang)
        .replace("{month}", text("dateMonth" + p.month, lang))
        .replace("{year}", year);
    }
    return year;
  }

  function formatDates(dates, lang) {
    if (!dates) return "";
    if (typeof dates === "string") return dates; // legacy literal — the dev check warns
    var from = formatPoint(dates.from, lang);
    if (dates.to === undefined || dates.to === null || dates.to === "") return from;
    return text("dateRange", lang)
      .replace("{from}", from)
      .replace("{to}", formatPoint(dates.to, lang));
  }

  // "<Context> · <dates>"
  function metaLine(entry, lang) {
    var label = contextLabel(entry.context, lang);
    var dates = formatDates(entry.dates, lang);
    return label ? (dates ? label + " · " + dates : label) : dates;
  }

  /* ---- Ordering -----------------------------------------------------------
     sortDate ("YYYY-MM") descending. Array order in the data files is
     irrelevant. `pinned` lifts a project above everything else. Array.sort is
     stable, so equal dates keep their relative order. */
  function bySortDateDesc(a, b) {
    return (b.sortDate || "").localeCompare(a.sortDate || "");
  }

  function sortProjects(list) {
    return list.slice().sort(function (a, b) {
      if (!!a.pinned !== !!b.pinned) return a.pinned ? -1 : 1;
      return bySortDateDesc(a, b);
    });
  }

  /* ---- Experience selectors --------------------------------------------- */
  function allExperience() {
    return (typeof experienceData !== "undefined") ? experienceData : [];
  }

  function visibleExperience() {
    return allExperience().filter(function (e) { return e.visible; }).sort(bySortDateDesc);
  }

  // Only a VISIBLE role is a valid link target. Returns null otherwise, and
  // every caller treats null as "render no link".
  function experienceBySlug(slug) {
    if (!slug) return null;
    var found = visibleExperience().filter(function (e) { return e.slug === slug; });
    return found.length ? found[0] : null;
  }

  /* ---- Project selectors --------------------------------------------------
     Listing tiers: "index" is the only tier that appears in any listing.
     "unlisted" and "hidden" never reach one; "nested" is reserved and also
     renders nothing (the dev check warns about it). A sub-page renders an
     "index" or "unlisted" entry; a "hidden" one only on localhost. */
  function allProjects() {
    return (typeof projectsData !== "undefined") ? projectsData : [];
  }

  function indexProjects() {
    return sortProjects(allProjects().filter(function (e) { return e.listing === "index"; }));
  }

  // Featured blocks (home + projects.html §2): entries with a numeric
  // `featuredOrder` come first, ascending; the rest follow in sortDate order.
  function featuredProjects() {
    return indexProjects().filter(function (e) { return e.featured; }).sort(function (a, b) {
      var ao = typeof a.featuredOrder === "number", bo = typeof b.featuredOrder === "number";
      if (ao && bo) return a.featuredOrder - b.featuredOrder;
      if (ao !== bo) return ao ? -1 : 1;
      return 0; // stable: keeps sortDate order
    });
  }

  function projectsForExperience(slug) {
    if (!slug) return [];
    return indexProjects().filter(function (e) { return e.experience === slug; });
  }

  // Any listing tier — the sub-page renderer decides what to do with it.
  function projectBySlug(slug) {
    if (!slug) return null;
    var found = allProjects().filter(function (e) { return e.slug === slug; });
    return found.length ? found[0] : null;
  }

  /* ---- Shared builders ----------------------------------------------------
     One set of markup for projects.html §2/§3, the index.html featured block,
     experience bands and the project sub-pages. Tags always sit BELOW the
     description, never above the title. */

  // Tag pills are links to projects.html?tag=<id>. Pointer cursor only — no
  // hover effect, no enlarged tap target (style.css .tag-pill).
  function buildTagRow(entry) {
    var row = document.createElement("div");
    row.className = "tag-row";
    (entry.tags || []).forEach(function (id) {
      var pill = document.createElement("a");
      pill.className = "tag-pill";
      pill.href = tagUrl(id);
      pill.textContent = tagLabel(id);
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

  // "Part of: <org> →" → experience.html#<slug>. {org} is the role's short
  // organization name (orgShortKey, falling back to orgKey). Null when the
  // entry has no `experience`, or it points at a role that is unknown or hidden.
  function buildPartOfLink(entry) {
    var role = experienceBySlug(entry.experience);
    if (!role) return null;
    var link = document.createElement("a");
    link.className = "project-part-of";
    link.href = ROOT + "experience.html#" + role.slug;
    link.textContent = text("projPartOf")
      .replace("{role}", text(role.roleKey))
      .replace("{org}", text(role.orgShortKey || role.orgKey));
    return link;
  }

  function buildImage(entry, className) {
    var img = document.createElement("img");
    img.className = className;
    img.src = ROOT + entry.imageSrc;
    img.alt = entry.imageAlt ? text(entry.imageAlt) : "";
    img.loading = "lazy";
    return img;
  }

  /* ---- Featured layout presets ---------------------------------------------
     One class per preset. projects.html §2 alternates imageLeft / imageRight
     from the index (the set is 2-3 entries and fixed, which is the one place a
     global alternating rule is appropriate). index.html passes
     options.layout = entry.homeLayout, default "stacked". Same markup order and
     data for every preset; one builder. */
  var FEATURED_LAYOUTS = {
    stacked: "featured-entry--stacked",
    imageLeft: "featured-entry--image-left",
    imageRight: "featured-entry--image-right",
    collage: "featured-entry--collage"
  };
  var GALLERY_MAX = 3;

  // Extra images for the collage preset: items with both src and altKey, capped
  // at GALLERY_MAX. Invalid items are skipped here and reported by checkData().
  function validGallery(entry) {
    return (entry.gallery || [])
      .filter(function (g) { return g && g.src && g.altKey; })
      .slice(0, GALLERY_MAX);
  }

  // Cells = imageSrc first, then the gallery. 2 → two columns; 3 → large left +
  // two stacked right; 4 → 2×2 (style.css .featured-collage--N).
  function buildCollage(entry, gallery) {
    var media = document.createElement("div");
    var cells = [{ src: entry.imageSrc, altKey: entry.imageAlt }].concat(gallery);
    media.className = "featured-entry-media featured-collage featured-collage--" + cells.length;
    cells.forEach(function (cell) {
      var img = document.createElement("img");
      img.className = "featured-collage-image";
      img.src = ROOT + cell.src;
      img.alt = cell.altKey ? text(cell.altKey) : "";
      img.loading = "lazy";
      media.appendChild(img);
    });
    return media;
  }

  /* Featured entry: image → title → meta → description → tags → "Part of" →
     link. options.layout (a FEATURED_LAYOUTS key) overrides the alternation.
     Fallbacks, never an error: collage with no usable gallery → stacked; any
     preset with no imageSrc → text only (no empty frame). */
  function buildFeatured(entry, i, options) {
    var layout = options && options.layout;
    if (!layout) layout = i % 2 === 0 ? "imageLeft" : "imageRight";
    if (!FEATURED_LAYOUTS[layout]) layout = "stacked";
    var gallery = layout === "collage" ? validGallery(entry) : [];
    if (layout === "collage" && !gallery.length) layout = "stacked";

    var article = document.createElement("article");
    article.className = "featured-entry " +
      (entry.imageSrc ? FEATURED_LAYOUTS[layout] : "featured-entry--text-only");

    if (entry.imageSrc && layout === "collage") {
      article.appendChild(buildCollage(entry, gallery));
    } else if (entry.imageSrc) {
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
    meta.textContent = metaLine(entry);
    body.appendChild(meta);

    var desc = document.createElement("p");
    desc.className = "featured-entry-desc";
    desc.setAttribute("data-i18n", entry.longDescKey);
    fillText(desc, text(entry.longDescKey));
    body.appendChild(desc);

    body.appendChild(buildTagRow(entry));

    var partOf = buildPartOfLink(entry);
    if (partOf) body.appendChild(partOf);

    var link = buildViewLink(entry);
    if (link) body.appendChild(link);

    article.appendChild(body);
    return article;
  }

  /* Index row. Identical markup under both .project-index--rows and
     .project-index--grid — switching views later is a class swap on the
     container. The row carries id="<slug>" so projects.html#<slug> lands on it.

     An entry with no imageSrc gets .project-row--no-image and no <img> node at
     all: the text takes the full row width. Not a broken image, not a grey
     box, not a placeholder icon. */
  function buildRow(entry) {
    var row = document.createElement("article");
    row.className = "project-row" + (entry.imageSrc ? "" : " project-row--no-image");
    row.id = entry.slug;

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
    var meta = document.createElement("span");
    meta.className = "project-row-dates";
    meta.textContent = metaLine(entry);
    heading.appendChild(meta);
    body.appendChild(heading);

    var desc = document.createElement("p");
    desc.className = "project-row-desc";
    desc.setAttribute("data-i18n", entry.descKey);
    fillText(desc, text(entry.descKey));
    body.appendChild(desc);

    body.appendChild(buildTagRow(entry));

    var partOf = buildPartOfLink(entry);
    if (partOf) body.appendChild(partOf);

    var link = buildViewLink(entry);
    if (link) body.appendChild(link);

    row.appendChild(body);
    return row;
  }

  /* ---- Deep links ---------------------------------------------------------
     Index rows and experience bands carry id="<slug>". targetFromHash() marks
     the element location.hash names with .is-target (a static left rule — no
     animation) and, when asked, scrolls it into view. scroll-margin-top in
     style.css keeps it clear of the sticky nav and the dev banner.

     Callers pass scroll: true on load and on hashchange only. A language
     switch re-renders and re-marks WITHOUT scrolling, so the visitor's scroll
     position is preserved exactly (CLAUDE.md). */
  function targetFromHash(selector, scroll) {
    var hash = (location.hash || "").replace(/^#/, "");
    document.querySelectorAll(selector + ".is-target").forEach(function (el) {
      el.classList.remove("is-target");
    });
    if (!hash) return null;
    var el = null;
    try { el = document.getElementById(decodeURIComponent(hash)); } catch (e) { el = null; }
    if (!el || !el.matches(selector)) return null;
    el.classList.add("is-target");
    if (scroll) el.scrollIntoView({ block: "start" }); // instant — never smooth
    return el;
  }

  /* ---- Dev-only data check ------------------------------------------------
     console.warn only. Never renders anything, never throws. Runs on
     localhost ONLY (isDev) — including the HEAD probes at the end — so real
     visitors never see it or pay for it. Called once on load by the page
     scripts. */
  var LISTINGS = ["index", "unlisted", "hidden"];
  var SORT_DATE = /^\d{4}-\d{2}$/;
  // Plausible sortDate months for a season point (spring can end in May, etc.).
  var SEASON_MONTHS = { spring: [1, 2, 3, 4, 5], summer: [5, 6, 7, 8], fall: [8, 9, 10, 11, 12], winter: [11, 12, 1, 2] };

  function checkData() {
    if (!isDev()) return;
    if (typeof console === "undefined" || !console.warn) return;
    function warn(msg) { console.warn("[data check] " + msg); }

    var en = (typeof translations !== "undefined" && translations.en) || {};
    var es = (typeof translations !== "undefined" && translations.es) || {};
    function checkKey(owner, field, key) {
      if (!key) { warn(owner + ": " + field + " is empty"); return; }
      if (en[key] === undefined) warn(owner + ": " + field + " \"" + key + "\" has no EN string");
      if (es[key] === undefined) warn(owner + ": " + field + " \"" + key + "\" has no ES string");
    }
    function checkTags(owner, tags) {
      (tags || []).forEach(function (id) {
        if (!TAG_BY_ID[id]) warn(owner + ": unknown tag id \"" + id + "\" (not in js/tags-data.js)");
      });
    }

    // A date point: { season, year } | { month, year } | { year }
    function checkPoint(owner, field, p) {
      if (!p || typeof p !== "object") { warn(owner + ": " + field + " must be an object like { season: \"summer\", year: 2026 } or { month: 7, year: 2022 }"); return false; }
      var ok = true;
      if (!Number.isInteger(p.year)) { warn(owner + ": " + field + ".year must be an integer"); ok = false; }
      if (p.season !== undefined && !SEASON_KEYS[p.season]) { warn(owner + ": " + field + ".season \"" + p.season + "\" (expected spring | summer | fall | winter)"); ok = false; }
      if (p.month !== undefined && !(Number.isInteger(p.month) && p.month >= 1 && p.month <= 12)) { warn(owner + ": " + field + ".month must be 1–12"); ok = false; }
      if (p.season !== undefined && p.month !== undefined) { warn(owner + ": " + field + " has both season and month — use one"); ok = false; }
      return ok;
    }

    // dates shape, then sortDate consistency: the reference point is `to` when
    // it is a point (sort by when it finished), else `from`. Year must match;
    // a month must match exactly; a season must contain the sortDate month.
    function checkDates(owner, dates, sortDate) {
      if (!dates || typeof dates !== "object") { warn(owner + ": dates must be { from, to? } — literal strings are no longer supported"); return; }
      var fromOk = checkPoint(owner, "dates.from", dates.from);
      var toOk = true;
      if (dates.to !== undefined && dates.to !== null && dates.to !== "" && dates.to !== "present") toOk = checkPoint(owner, "dates.to", dates.to);
      if (!fromOk || !toOk || !SORT_DATE.test(sortDate || "")) return;
      var ref = (dates.to && typeof dates.to === "object") ? dates.to : dates.from;
      var y = parseInt(sortDate.slice(0, 4), 10), m = parseInt(sortDate.slice(5, 7), 10);
      if (ref.year !== y) warn(owner + ": sortDate " + sortDate + " does not match the dates year " + ref.year);
      else if (ref.month !== undefined && ref.month !== m) warn(owner + ": sortDate " + sortDate + " does not match dates month " + ref.month);
      else if (ref.season !== undefined && SEASON_MONTHS[ref.season] && SEASON_MONTHS[ref.season].indexOf(m) === -1) warn(owner + ": sortDate " + sortDate + " is outside " + ref.season);
    }

    // Tags
    var seenTag = {};
    tagVocabulary().forEach(function (tag) {
      if (seenTag[tag.id]) warn("tags: duplicate id \"" + tag.id + "\"");
      seenTag[tag.id] = true;
      checkKey("tag \"" + tag.id + "\"", "key", tag.key);
    });

    // Experience
    var expSlugs = {};
    var currentCount = 0;
    allExperience().forEach(function (e, i) {
      var owner = "experience \"" + (e.slug || "#" + i) + "\"";
      if (!e.slug) warn(owner + ": missing slug");
      else if (expSlugs[e.slug]) warn("experience: duplicate slug \"" + e.slug + "\"");
      expSlugs[e.slug] = true;
      checkKey(owner, "roleKey", e.roleKey);
      checkKey(owner, "orgKey", e.orgKey);
      if (e.orgShortKey) checkKey(owner, "orgShortKey", e.orgShortKey);
      if (e.imageSrc && e.layout !== "textOnly") {
        if (!e.imageAltKey) warn(owner + ": imageSrc set without imageAltKey — alt falls back to role — org");
        else checkKey(owner, "imageAltKey", e.imageAltKey);
      }
      (e.bulletKeys || []).forEach(function (k, n) { checkKey(owner, "bulletKeys[" + n + "]", k); });
      checkTags(owner, e.tags);
      if (!SORT_DATE.test(e.sortDate || "")) warn(owner + ": missing or malformed sortDate (expected \"YYYY-MM\")");
      checkDates(owner, e.dates, e.sortDate);
      if (e.status === "current" && e.visible) currentCount++;
    });
    if (currentCount > 1) warn("experience: more than one visible entry has status \"current\"");

    // Projects
    var projSlugs = {};
    var featuredCount = 0;
    var subpageUrls = [];
    allProjects().forEach(function (p, i) {
      var owner = "project \"" + (p.slug || "#" + i) + "\"";
      if (!p.slug) warn(owner + ": missing slug");
      else if (projSlugs[p.slug]) warn("projects: duplicate slug \"" + p.slug + "\"");
      projSlugs[p.slug] = true;

      if (p.listing === "nested") {
        warn(owner + ": listing \"nested\" is reserved and not implemented — the entry will not render");
      } else if (LISTINGS.indexOf(p.listing) === -1) {
        warn(owner + ": unknown listing \"" + p.listing + "\" (expected index | unlisted | hidden) — the entry will not render");
      }

      checkKey(owner, "titleKey", p.titleKey);
      checkKey(owner, "descKey", p.descKey);
      // longDesc is the featured-card paragraph: required when featured,
      // otherwise "" is fine (index rows only show desc).
      if (p.featured || p.longDescKey) checkKey(owner, "longDescKey", p.longDescKey);
      checkKey(owner, "searchTextKey", p.searchTextKey);
      if (p.imageSrc && !p.imageAlt) warn(owner + ": imageSrc set without imageAlt");
      else if (p.imageSrc) checkKey(owner, "imageAlt", p.imageAlt);

      checkTags(owner, p.tags);

      if (p.experience) {
        if (!expSlugs[p.experience]) warn(owner + ": experience \"" + p.experience + "\" matches no experience slug");
        else if (!experienceBySlug(p.experience)) warn(owner + ": experience \"" + p.experience + "\" is not visible — the link will be omitted");
      }

      if (p.featured && p.listing !== "index") warn(owner + ": featured on a non-index entry (listing \"" + p.listing + "\") — it will not be featured");
      if (p.featured && p.listing === "index") featuredCount++;
      if (p.featuredOrder !== undefined && typeof p.featuredOrder !== "number") warn(owner + ": featuredOrder must be a number");

      if (!SORT_DATE.test(p.sortDate || "")) warn(owner + ": missing or malformed sortDate (expected \"YYYY-MM\")");
      checkDates(owner, p.dates, p.sortDate);
      if (!p.context) warn(owner + ": missing context");
      else if (!CONTEXT_KEYS[p.context]) warn(owner + ": unknown context \"" + p.context + "\"");

      // Home featured presets (optional fields)
      if (p.homeLayout !== undefined && !FEATURED_LAYOUTS[p.homeLayout]) {
        warn(owner + ": unknown homeLayout \"" + p.homeLayout + "\" (expected stacked | imageLeft | imageRight | collage) — falls back to stacked");
      }
      if (p.gallery !== undefined) {
        if (!Array.isArray(p.gallery)) {
          warn(owner + ": gallery must be an array of { src, altKey }");
        } else {
          if (p.homeLayout !== "collage") warn(owner + ": gallery is set but homeLayout is not \"collage\" — the gallery is ignored");
          if (p.gallery.length > GALLERY_MAX) warn(owner + ": gallery has " + p.gallery.length + " items (max " + GALLERY_MAX + ") — extras are dropped");
          p.gallery.forEach(function (g, n) {
            var item = owner + ": gallery[" + n + "]";
            if (!g || !g.src) warn(item + " is missing src — skipped");
            if (!g || !g.altKey) warn(item + " is missing altKey — skipped");
            else checkKey(item, "altKey", g.altKey);
          });
        }
      }

      // Sub-page content (optional `page` object — js/project-page.js)
      if (p.page !== undefined) {
        if (!p.page || typeof p.page !== "object") {
          warn(owner + ": page must be an object { sections, facts, photos, reportPdf, creditKey }");
        } else {
          var pg = p.page;
          if (!p.subpageUrl) warn(owner + ": page content is set but subpageUrl is \"\" — nothing links to it");
          if (pg.sections !== undefined) {
            if (!Array.isArray(pg.sections)) warn(owner + ": page.sections must be an array of { headingKey, bodyKey }");
            else pg.sections.forEach(function (s, n) {
              var item = owner + ": page.sections[" + n + "]";
              if (!s) { warn(item + " is empty"); return; }
              checkKey(item, "headingKey", s.headingKey);
              checkKey(item, "bodyKey", s.bodyKey);
            });
          }
          if (pg.facts !== undefined) {
            if (!Array.isArray(pg.facts)) warn(owner + ": page.facts must be an array of { labelKey, valueKey }");
            else pg.facts.forEach(function (f, n) {
              var item = owner + ": page.facts[" + n + "]";
              if (!f) { warn(item + " is empty"); return; }
              checkKey(item, "labelKey", f.labelKey);
              checkKey(item, "valueKey", f.valueKey);
            });
          }
          if (pg.photos !== undefined) {
            if (!Array.isArray(pg.photos)) warn(owner + ": page.photos must be an array of { src, altKey }");
            else pg.photos.forEach(function (ph, n) {
              var item = owner + ": page.photos[" + n + "]";
              if (!ph || !ph.src) warn(item + " is missing src — skipped");
              if (!ph || !ph.altKey) warn(item + " is missing altKey — skipped");
              else checkKey(item, "altKey", ph.altKey);
            });
          }
          if (pg.reportPdf !== undefined && typeof pg.reportPdf !== "string") warn(owner + ": page.reportPdf must be a path string or \"\"");
          if (pg.creditKey) checkKey(owner, "page.creditKey", pg.creditKey);
        }
      }

      if (p.subpageUrl) subpageUrls.push({ owner: owner, url: p.subpageUrl });
    });
    if (featuredCount > 3) warn("projects: " + featuredCount + " featured entries (max 3)");

    checkDocs(warn);
    checkSubpages(warn, subpageUrls);
  }

  // Documents manifest (js/docs-data.js): one HEAD per listed file, warn on a
  // non-2xx. Dev check only — the buttons themselves never make a request.
  function checkDocs(warn) {
    if (typeof DOCS === "undefined" || typeof fetch !== "function") return;
    Object.keys(DOCS).forEach(function (type) {
      Object.keys(DOCS[type]).forEach(function (lang) {
        var p = DOCS[type][lang];
        if (!p) return;
        var url = ROOT + p.split("/").map(encodeURIComponent).join("/");
        fetch(url, { method: "HEAD" }).then(function (res) {
          if (!res.ok) warn("docs: " + type + "." + lang + " \"" + p + "\" returned HTTP " + res.status);
        }).catch(function () {
          warn("docs: " + type + "." + lang + " \"" + p + "\" could not be fetched");
        });
      });
    });
  }

  // One HEAD per non-empty subpageUrl: a "View project →" link must land on a
  // real file. Dev check only.
  function checkSubpages(warn, list) {
    if (typeof fetch !== "function") return;
    list.forEach(function (item) {
      fetch(item.url, { method: "HEAD" }).then(function (res) {
        if (!res.ok) warn(item.owner + ": subpageUrl \"" + item.url + "\" returned HTTP " + res.status);
      }).catch(function () {
        warn(item.owner + ": subpageUrl \"" + item.url + "\" could not be fetched");
      });
    });
  }

  window.siteData = {
    root: ROOT,
    isDev: isDev,
    currentLang: currentLang,
    text: text,
    fillText: fillText,
    tagLabel: tagLabel,
    tagExists: tagExists,
    tagUrl: tagUrl,
    tagVocabulary: tagVocabulary,
    contextLabel: contextLabel,
    formatDates: formatDates,
    metaLine: metaLine,
    visibleExperience: visibleExperience,
    experienceBySlug: experienceBySlug,
    indexProjects: indexProjects,
    featuredProjects: featuredProjects,
    projectsForExperience: projectsForExperience,
    projectBySlug: projectBySlug,
    buildTagRow: buildTagRow,
    buildViewLink: buildViewLink,
    buildPartOfLink: buildPartOfLink,
    buildImage: buildImage,
    buildFeatured: buildFeatured,
    buildRow: buildRow,
    targetFromHash: targetFromHash,
    checkData: checkData
  };
}());
