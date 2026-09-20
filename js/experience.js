// experience.js
// Renders §2 of experience.html as full-width colored bands from
// js/experience-data.js, re-rendering on language change, and fades each band's
// CONTENT in on scroll (IntersectionObserver, opacity 0→1, no movement —
// standard CLAUDE.md rule, no carve-out on this page).
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
  if (!list || typeof experienceData === "undefined") return;

  // layout preset → CSS class. Adding a preset = one entry here + one class in
  // style.css. Unknown or absent values fall back to the default preset.
  var LAYOUT_CLASSES = {
    imageLeft: "exp-band--image-left",
    imageRight: "exp-band--image-right",
    fullBleed: "exp-band--full-bleed",
    textOnly: "exp-band--text-only"
  };
  var DEFAULT_LAYOUT = "imageLeft";

  function currentLang() {
    return document.documentElement.getAttribute("lang") === "es" ? "es" : "en";
  }

  // Light vs dark colors come from the same data object. The no-flash script in
  // <head> sets data-theme before first paint, so the first render already picks
  // the right mix.
  function currentMode() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function text(key) {
    var dict = (typeof translations !== "undefined") ? translations[currentLang()] : null;
    return (dict && dict[key] !== undefined) ? dict[key] : key;
  }

  function visibleEntries() {
    return experienceData.filter(function (entry) { return entry.visible; });
  }

  // At most one entry may carry status: "current". If none does (or the flagged
  // one is hidden), this returns null and every current-role behavior no-ops.
  function currentEntry() {
    var found = visibleEntries().filter(function (entry) { return entry.status === "current"; });
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

  function buildMedia(entry) {
    var media = document.createElement("div");
    media.className = "exp-band-media";
    var img = document.createElement("img");
    img.className = "exp-band-image";
    img.src = entry.imageSrc;
    img.alt = text(entry.roleKey) + " — " + text(entry.orgKey);
    img.loading = "lazy";
    media.appendChild(img);
    return media;
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
    meta.appendChild(document.createTextNode(" · " + entry.dates)); // dates are literal, never translated
    body.appendChild(meta);

    var bullets = document.createElement("ul");
    bullets.className = "exp-band-bullets";
    (entry.bulletKeys || []).forEach(function (key) {
      var li = document.createElement("li");
      li.setAttribute("data-i18n", key);
      li.textContent = text(key);
      bullets.appendChild(li);
    });
    body.appendChild(bullets);

    if (entry.tags && entry.tags.length) {
      var tagRow = document.createElement("div");
      tagRow.className = "tag-row";
      entry.tags.forEach(function (tag) {
        var pill = document.createElement("span");
        pill.className = "tag-pill";
        pill.textContent = tag;
        tagRow.appendChild(pill);
      });
      body.appendChild(tagRow);
    }

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
    visibleEntries().forEach(function (entry) {
      var band = buildBand(entry, entry === current);
      list.appendChild(band);
      painted.push({ band: band, entry: entry });
      observer.observe(band.querySelector(".exp-band-inner"));
    });

    renderHeroStatus();
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

  // main.js fires langchange at the end of applyTranslations, so this listener
  // runs after the data-i18n elements are swapped and always wins on the hero.
  document.addEventListener("langchange", render);
  render();
}());
