// project-page.js
// The ONE renderer for project sub-pages (projects/<slug>.html). Each page is
// a tiny HTML shell whose <body> carries data-slug="<slug>" and
// data-root="../"; everything visible is rendered here from the entry in
// js/projects-data.js and its optional `page` object:
//
//   page: {
//     sections: [{ headingKey, bodyKey }],   // in order
//     facts:    [{ labelKey, valueKey }],    // quick-facts box
//     photos:   [{ src, altKey }],           // grid; click opens the full image
//     reportPdf: "",                         // optional "Read the report" link
//     creditKey: ""                          // optional photo credit line
//   }
//
// Layout: hero image (imageSrc, 16:9) → title → meta line (context · dates) →
// "Part of" link if any → sections → photo grid → quick-facts box → report
// link → credit → tags → "← All projects". Every missing piece renders
// nothing — never an empty box.
//
// Listing tiers: "index" and "unlisted" entries render for everyone (unlisted
// is exactly the direct-URL case). A "hidden" entry renders only on localhost,
// so a scaffold page can exist in the repo without ever showing on the live
// site. The static <title> / meta description in the HTML are English
// fallbacks; they are replaced on every render.

(function () {
  var main = document.getElementById("project-page");
  var slug = document.body.getAttribute("data-slug");
  if (!main || !slug || typeof siteData === "undefined") return;

  var text = siteData.text;
  var root = siteData.root;

  var entry = siteData.projectBySlug(slug);
  if (!entry) {
    if (siteData.isDev() && console && console.warn) console.warn("[project page] no entry with slug \"" + slug + "\" in js/projects-data.js");
    return;
  }
  if (entry.listing === "hidden" && !siteData.isDev()) return;

  var page = (entry.page && typeof entry.page === "object") ? entry.page : {};

  function el(tag, className) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    return node;
  }

  function buildHero() {
    if (!entry.imageSrc) return null;
    var figure = el("figure", "project-page-hero");
    figure.appendChild(siteData.buildImage(entry, "project-page-hero-image"));
    return figure;
  }

  function buildSections() {
    var list = Array.isArray(page.sections) ? page.sections : [];
    var frag = document.createDocumentFragment();
    list.forEach(function (s) {
      if (!s || !s.headingKey || !s.bodyKey) return;
      var section = el("section", "project-page-section");
      var h = el("h2", "project-page-section-heading");
      h.setAttribute("data-i18n", s.headingKey);
      h.textContent = text(s.headingKey);
      section.appendChild(h);
      var p = el("p", "project-page-section-body");
      p.setAttribute("data-i18n", s.bodyKey);
      siteData.fillText(p, text(s.bodyKey));
      section.appendChild(p);
      frag.appendChild(section);
    });
    return frag;
  }

  // 2-up on desktop, 1-up on phones (style.css). Each photo links to its
  // full-size file in a new tab.
  function buildPhotos() {
    var list = (Array.isArray(page.photos) ? page.photos : [])
      .filter(function (ph) { return ph && ph.src && ph.altKey; });
    if (!list.length) return null;
    var grid = el("div", "project-page-photos");
    list.forEach(function (ph) {
      var a = el("a", "project-page-photo");
      a.href = root + ph.src;
      a.target = "_blank";
      a.rel = "noopener";
      var img = el("img", "project-page-photo-image");
      img.src = root + ph.src;
      img.alt = text(ph.altKey);
      img.loading = "lazy";
      a.appendChild(img);
      grid.appendChild(a);
    });
    return grid;
  }

  function buildFacts() {
    var list = (Array.isArray(page.facts) ? page.facts : [])
      .filter(function (f) { return f && f.labelKey && f.valueKey; });
    if (!list.length) return null;
    var box = el("dl", "project-page-facts");
    list.forEach(function (f) {
      var row = el("div", "project-page-fact");
      var dt = el("dt");
      dt.setAttribute("data-i18n", f.labelKey);
      dt.textContent = text(f.labelKey);
      var dd = el("dd");
      dd.setAttribute("data-i18n", f.valueKey);
      siteData.fillText(dd, text(f.valueKey));
      row.appendChild(dt);
      row.appendChild(dd);
      box.appendChild(row);
    });
    return box;
  }

  function buildReport() {
    if (!page.reportPdf || typeof page.reportPdf !== "string") return null;
    var a = el("a", "project-link project-page-report");
    a.href = root + page.reportPdf;
    a.target = "_blank";
    a.rel = "noopener";
    a.setAttribute("data-i18n", "projReportLink");
    a.textContent = text("projReportLink");
    return a;
  }

  function buildCredit() {
    if (!page.creditKey) return null;
    var p = el("p", "project-page-credit");
    p.setAttribute("data-i18n", page.creditKey);
    siteData.fillText(p, text(page.creditKey));
    return p;
  }

  function buildBack() {
    var a = el("a", "project-page-back");
    a.href = root + "projects.html";
    a.setAttribute("data-i18n", "projAllProjects");
    a.textContent = text("projAllProjects");
    return a;
  }

  function render() {
    var title = text(entry.titleKey);
    document.title = title + " — Gideon A. Ong";
    var metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute("content", text(entry.descKey));

    main.innerHTML = "";
    var parts = [];

    parts.push(buildHero());

    var h1 = el("h1", "project-page-title");
    h1.setAttribute("data-i18n", entry.titleKey);
    h1.textContent = title;
    parts.push(h1);

    var meta = el("p", "project-page-meta");
    meta.textContent = siteData.metaLine(entry);
    parts.push(meta);

    parts.push(siteData.buildPartOfLink(entry));
    parts.push(buildSections());
    parts.push(buildPhotos());
    parts.push(buildFacts());
    parts.push(buildReport());
    parts.push(buildCredit());
    if (entry.tags && entry.tags.length) parts.push(siteData.buildTagRow(entry));
    parts.push(buildBack());

    parts.forEach(function (node) { if (node) main.appendChild(node); });
  }

  siteData.checkData();
  document.addEventListener("langchange", render);
  render();
}());
