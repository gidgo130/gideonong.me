// experience.js
// Renders §2 of experience.html as full-width colored bands from
// js/experience-data.js (sortDate descending), re-rendering on language
// change, and fades each band's CONTENT in on scroll (IntersectionObserver,
// opacity 0→1, no movement — standard CLAUDE.md rule, no carve-out here).
//
// Each band carries id="<slug>" so experience.html#<slug> lands on it, and
// lists the listing: "index" projects that point at it via `experience`
// ("Projects from this role"). Lookups go through js/data-helpers.js.
//
// The band BACKGROUND is painted at first render and never animates. Fading a
// band background in would flash the page color through it — that is a bug, so
// only .exp-band-inner carries the fade.
//
// Per-entry colors are written as inline custom properties on the band element
// from entry.color. That is deliberate: per-entry values cannot live in :root.
// Do not move them into style.css.

(function () {
  var list = document.getElementById("experience-list");
  if (!list || typeof siteData === "undefined") return;

  var text = siteData.text;

  // layout preset → CSS class. Adding a preset = one entry here + one class in
  // style.css. Unknown or absent values fall back to the default preset.
  var LAYOUT_CLASSES = {
    imageLeft: "exp-band--image-left",
    imageRight: "exp-band--image-right",
    fullBleed: "exp-band--full-bleed",
    textOnly: "exp-band--text-only"
  };
  var DEFAULT_LAYOUT = "imageLeft";

  // Light vs dark colors come from the same data object. The no-flash script in
  // <head> sets data-theme before first paint, so the first render already picks
  // the right mix.
  function currentMode() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  // At most one entry may carry status: "current". If none does (or the flagged
  // one is hidden), this returns null and every current-role behavior no-ops.
  function currentEntry() {
    var found = siteData.visibleExperience().filter(function (entry) { return entry.status === "current"; });
    return found.length ? found[0] : null;
  }

  /* ---- Per-entry color contract -------------------------------------------
     Writes --entry-bg / --entry-border / --entry-accent (and optional
     --entry-ink) onto the band. Called at render and again whenever the theme
     changes, so dark mode re-mixes rather than reusing the light values. */
  function paintBand(band, entry) {
    var palette = (entry.color && entry.color[currentMode()]) || null;
    if (!palette) return; // no color defined → band falls back to var(--bg)
    band.style.setProperty("--entry-bg", palette.bg);
    band.style.setProperty("--entry-border", palette.border);
    band.style.setProperty("--entry-accent", palette.accent);
    if (palette.ink) {
      band.style.setProperty("--entry-ink", palette.ink);
    } else {
      band.style.removeProperty("--entry-ink");
    }
  }

  // Band image; wrapped in an image link (hover scale) only when the entry has
  // an `imageLink` destination — otherwise plain.
  function buildMedia(entry) {
    var media = document.createElement("div");
    media.className = "exp-band-media";
    var img = document.createElement("img");
    img.className = "exp-band-image";
    img.src = siteData.root + entry.imageSrc;
    // Alt from the entry's imageAltKey (image-manifest text); fallback role — org.
    img.alt = entry.imageAltKey ? text(entry.imageAltKey) : text(entry.roleKey) + " — " + text(entry.orgKey);
    img.loading = "lazy";
    media.appendChild(siteData.linkImage(img, entry.imageLink, text(entry.roleKey)));
    return media;
  }

  /* "Projects from this role": every listing: "index" project whose
     `experience` is this slug, in project sort order, as title (→
     projects.html#<slug>) + one-line description. Nothing at all if none. */
  function buildRelated(entry) {
    var related = siteData.projectsForExperience(entry.slug);
    if (!related.length) return null;

    var block = document.createElement("div");
    block.className = "exp-related";

    var heading = document.createElement("h3");
    heading.className = "exp-related-heading";
    heading.setAttribute("data-i18n", "expRelatedHeading");
    heading.textContent = text("expRelatedHeading");
    block.appendChild(heading);

    var ul = document.createElement("ul");
    ul.className = "exp-related-list";
    related.forEach(function (project) {
      var li = document.createElement("li");
      var link = document.createElement("a");
      link.className = "exp-related-title";
      link.href = "projects.html#" + project.slug;
      link.setAttribute("data-i18n", project.titleKey);
      link.textContent = text(project.titleKey);
      li.appendChild(link);
      var desc = document.createElement("span");
      desc.className = "exp-related-desc";
      desc.setAttribute("data-i18n", project.descKey);
      siteData.fillText(desc, text(project.descKey));
      li.appendChild(desc);
      ul.appendChild(li);
    });
    block.appendChild(ul);
    return block;
  }

  function buildBody(entry, isCurrent) {
    var body = document.createElement("div");
    body.className = "exp-band-body";

    if (isCurrent) {
      var eyebrow = document.createElement("p");
      eyebrow.className = "exp-band-eyebrow";
      eyebrow.setAttribute("data-i18n", "expCurrentLabel");
      eyebrow.textContent = text("expCurrentLabel");
      body.appendChild(eyebrow);
    }

    var role = document.createElement("h2");
    role.className = "exp-band-role";
    role.setAttribute("data-i18n", entry.roleKey);
    role.textContent = text(entry.roleKey);
    body.appendChild(role);

    var meta = document.createElement("p");
    meta.className = "exp-band-meta";
    var org = document.createElement("span");
    org.setAttribute("data-i18n", entry.orgKey);
    org.textContent = text(entry.orgKey);
    meta.appendChild(org);
    // Language-neutral dates ({ from, to }) rendered per language.
    var dates = siteData.formatDates(entry.dates);
    if (dates) meta.appendChild(document.createTextNode(" · " + dates));
    body.appendChild(meta);

    var bullets = document.createElement("ul");
    bullets.className = "exp-band-bullets";
    (entry.bulletKeys || []).forEach(function (key) {
      var li = document.createElement("li");
      li.setAttribute("data-i18n", key);
      siteData.fillText(li, text(key)); // phrase chips (js/chips.js)
      bullets.appendChild(li);
    });
    body.appendChild(bullets);

    // Tag ids → translated labels (js/tags-data.js via data-helpers); each
    // pill links to projects.html?tag=<id>.
    if (entry.tags && entry.tags.length) {
      body.appendChild(siteData.buildTagRow(entry));
    }

    var related = buildRelated(entry);
    if (related) body.appendChild(related);

    if (entry.subpageUrl) {
      var link = document.createElement("a");
      link.className = "exp-band-link";
      link.href = entry.subpageUrl;
      link.setAttribute("data-i18n", "expCaseStudyLink");
      link.textContent = text("expCaseStudyLink");
      body.appendChild(link);
    }

    return body;
  }

  function buildBand(entry, isCurrent) {
    var band = document.createElement("section");
    var layout = LAYOUT_CLASSES[entry.layout] || LAYOUT_CLASSES[DEFAULT_LAYOUT];
    band.className = "exp-band " + layout + (isCurrent ? " exp-band--current" : "");
    if (entry.slug) band.id = entry.slug;
    paintBand(band, entry);

    var inner = document.createElement("div");
    inner.className = "exp-band-inner";

    // textOnly renders no image; neither does an entry with an empty imageSrc —
    // no broken image, no grey placeholder box.
    if (entry.layout !== "textOnly" && entry.imageSrc) {
      inner.appendChild(buildMedia(entry));
    }
    inner.appendChild(buildBody(entry, isCurrent));

    band.appendChild(inner);
    return band;
  }

  /* ---- Hero status sentence ------------------------------------------------
     With a current entry: fill the expHeroStatusCurrent template with its role
     and org. Without one: leave the element alone — main.js has already painted
     the expHeroStatus fallback from the element's data-i18n attribute. */
  function renderHeroStatus() {
    var statusEl = document.getElementById("exp-hero-status");
    if (!statusEl) return;
    var entry = currentEntry();
    if (!entry) return;
    statusEl.textContent = text("expHeroStatusCurrent")
      .replace("{role}", text(entry.roleKey))
      .replace("{org}", text(entry.orgKey));
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  // Bands are kept paired with their data entry so a theme change can re-paint
  // them in place, without re-rendering (a re-render restarts the content fade).
  var painted = [];

  function render() {
    observer.disconnect();
    painted = [];
    list.innerHTML = "";

    var current = currentEntry();
    siteData.visibleExperience().forEach(function (entry) {
      var band = buildBand(entry, entry === current);
      list.appendChild(band);
      painted.push({ band: band, entry: entry });
      observer.observe(band.querySelector(".exp-band-inner"));
    });

    renderHeroStatus();
    // Re-mark the deep-link target after a re-render, without scrolling.
    siteData.targetFromHash(".exp-band", false);
  }

  function repaint() {
    painted.forEach(function (pair) { paintBand(pair.band, pair.entry); });
  }

  // The viewing-settings panel flips data-theme on <html>; the OS setting can
  // also change mid-session. Either way, re-mix the band colors in place.
  new MutationObserver(repaint).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"]
  });

  siteData.checkData();

  // main.js fires langchange at the end of applyTranslations, so this listener
  // runs after the data-i18n elements are swapped and always wins on the hero.
  document.addEventListener("langchange", render);
  window.addEventListener("hashchange", function () { siteData.targetFromHash(".exp-band", true); });
  render();
  siteData.targetFromHash(".exp-band", true);
}());
