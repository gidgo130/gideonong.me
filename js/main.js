// main.js
// Language toggle: instant DOM swap, localStorage persistence,
// navigator.language default. No page reload, no scroll jump.

(function () {
  const IEL_URL_EN = "https://utulsa.edu/academics/interdisciplinary-programs/international-engineering-science-language/";
  const IEL_URL_ES = "https://utulsa-edu.translate.goog/academics/interdisciplinary-programs/international-engineering-science-language/?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=en";
  const STORAGE_KEY = "lang";

  // Document naming convention: "assets/pdfs/<type>/<lang> Gideon Ong <Label> <YYYYMMDD>.pdf"
  // e.g. "assets/pdfs/resume/en Gideon Ong Resume 20260915.pdf". Doc types with
  // bilingual: false (the transcript — one file regardless of language) drop the
  // "<lang> " prefix and are probed/cached once, not once per language.
  // Static hosting has no directory listing, so the "latest" file is found by probing
  // dates backward from today (HEAD request) until one exists — drop a new PDF in with
  // today's date and no code change is needed. Elements opt in with
  // data-doc-link="resume" | "cv" | "transcript".
  const DOC_TYPES = {
    resume: { dir: "assets/pdfs/resume/", label: "Resume", bilingual: true },
    cv: { dir: "assets/pdfs/cv/", label: "CV", bilingual: true },
    transcript: { dir: "assets/pdfs/transcript/", label: "Transcript", bilingual: false }
  };
  const DOC_SEARCH_DAYS = 60; // how far back to probe before giving up (~2 months)
  const DOC_PROBE_BATCH = 30; // dates checked in parallel per round
  const DOC_CACHE_PREFIX = "docUrl_";
  const DOC_CACHE_TTL_MS = 24 * 60 * 60 * 1000; // re-probe at most once a day, hit or miss

  function formatYYYYMMDD(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return "" + y + m + day;
  }

  function docUrlForDate(docType, lang, yyyymmdd) {
    const type = DOC_TYPES[docType];
    const prefix = type.bilingual ? lang + " " : "";
    return type.dir + encodeURIComponent(prefix + "Gideon Ong " + type.label + " " + yyyymmdd + ".pdf");
  }

  // Non-bilingual doc types (the transcript) share one cache entry across languages
  // instead of one per language — same file, so no reason to probe/cache it twice.
  function docCacheKey(docType, lang) {
    return DOC_TYPES[docType].bilingual ? docType + "_" + lang : docType;
  }

  // Cache entry shape: { url: string|null, checkedAt: number }. url === null means
  // "probed recently, nothing found" — still a cache hit, so a missing doc (e.g. no
  // Spanish resume yet, or CV/transcript not uploaded yet) doesn't get re-probed on
  // every single page load.
  function readDocCache(docType, lang) {
    try {
      const cached = JSON.parse(localStorage.getItem(DOC_CACHE_PREFIX + docCacheKey(docType, lang)) || "null");
      if (cached && Date.now() - cached.checkedAt < DOC_CACHE_TTL_MS) return cached;
    } catch (e) { /* ignore malformed/unavailable storage */ }
    return null;
  }

  function writeDocCache(docType, lang, url) {
    try {
      localStorage.setItem(DOC_CACHE_PREFIX + docCacheKey(docType, lang), JSON.stringify({ url: url, checkedAt: Date.now() }));
    } catch (e) { /* ignore unavailable storage */ }
  }

  async function findLatestDocUrl(docType, lang) {
    if (!DOC_TYPES[docType]) return null;

    const cached = readDocCache(docType, lang);
    if (cached) return cached.url;

    const today = new Date();
    for (let start = 0; start <= DOC_SEARCH_DAYS; start += DOC_PROBE_BATCH) {
      const batch = [];
      for (let i = start; i < start + DOC_PROBE_BATCH && i <= DOC_SEARCH_DAYS; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        batch.push(docUrlForDate(docType, lang, formatYYYYMMDD(d)));
      }
      const results = await Promise.all(batch.map(function (url) {
        return fetch(url, { method: "HEAD" })
          .then(function (res) { return res.ok ? url : null; })
          .catch(function () { return null; });
      }));
      const hit = results.find(Boolean);
      if (hit) {
        writeDocCache(docType, lang, hit);
        return hit;
      }
    }
    writeDocCache(docType, lang, null); // cache the miss too — see comment above
    return null;
  }

  function updateResumeLinks(lang) {
    const docTypes = new Set();
    document.querySelectorAll("[data-doc-link]").forEach(function (el) {
      docTypes.add(el.getAttribute("data-doc-link"));
    });

    docTypes.forEach(function (docType) {
      findLatestDocUrl(docType, lang).then(function (url) {
        if (!url) return; // keep whatever href is already on the element
        document.querySelectorAll('[data-doc-link="' + docType + '"]').forEach(function (el) {
          el.setAttribute("href", url);
        });
      });
    });
  }

  function detectDefaultLang() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "es") return stored;

    const nav = (navigator.language || "en").toLowerCase();
    // Spanish-locale or Portuguese (lusophone) → ES default. Else EN.
    if (nav.startsWith("es") || nav.startsWith("pt")) return "es";
    return "en";
  }

  function withIelChip(text, lang) {
    const url = lang === "es" ? IEL_URL_ES : IEL_URL_EN;
    const chip = '<a class="iel-chip" href="' + url + '" target="_blank" rel="noopener">IEL</a>';
    return text.replace(/\bIEL\b/, chip);
  }

  function renderHeroParagraphs() {
    document.querySelectorAll("[data-hero-lang]").forEach(function (el) {
      const lang = el.getAttribute("data-hero-lang");
      const dict = translations[lang];
      if (dict && dict.heroDesc) {
        el.innerHTML = withIelChip(dict.heroDesc, lang);
      }
    });
  }

  function updateHeroActiveState(lang) {
    document.querySelectorAll("[data-hero-lang]").forEach(function (el) {
      const isActive = el.getAttribute("data-hero-lang") === lang;
      el.classList.toggle("is-active", isActive);
      el.classList.toggle("is-inactive", !isActive);
    });
  }

  function applyTranslations(lang) {
    const dict = translations[lang];
    if (!dict) return;

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      const key = el.getAttribute("data-i18n");
      if (dict[key] === undefined) return;
      el.textContent = dict[key];
    });

    document.querySelectorAll("[data-i18n-alt]").forEach(function (el) {
      const key = el.getAttribute("data-i18n-alt");
      if (dict[key] === undefined) return;
      el.setAttribute("alt", dict[key]);
    });

    updateResumeLinks(lang);

    document.querySelectorAll(".lang-toggle .lang-btn").forEach(function (span) {
      span.classList.toggle("is-active", span.getAttribute("data-lang") === lang);
    });

    document.documentElement.setAttribute("lang", lang);
    updateHeroActiveState(lang);

    // Lets page-specific scripts (e.g. js/about.js) refresh content that is
    // rendered from JS data arrays rather than driven directly by data-i18n.
    document.dispatchEvent(new CustomEvent("langchange", { detail: { lang: lang } }));
  }

  function setLang(lang) {
    localStorage.setItem(STORAGE_KEY, lang);
    applyTranslations(lang);
  }

  const langToggleBtn = document.querySelector("[data-lang-toggle]");
  if (langToggleBtn) {
    langToggleBtn.addEventListener("click", function () {
      const current = document.documentElement.getAttribute("lang") === "es" ? "es" : "en";
      setLang(current === "en" ? "es" : "en");
    });
  }

  // Mobile hamburger — open/close nav dropdown
  (function () {
    var hamburger = document.getElementById("hamburger");
    var dropdown = document.getElementById("nav-dropdown");
    if (!hamburger || !dropdown) return;

    function openMenu() {
      dropdown.classList.add("is-open");
      hamburger.classList.add("is-open");
      hamburger.setAttribute("aria-expanded", "true");
      dropdown.setAttribute("aria-hidden", "false");
    }

    function closeMenu() {
      dropdown.classList.remove("is-open");
      hamburger.classList.remove("is-open");
      hamburger.setAttribute("aria-expanded", "false");
      dropdown.setAttribute("aria-hidden", "true");
    }

    hamburger.addEventListener("click", function (e) {
      e.stopPropagation();
      if (dropdown.classList.contains("is-open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    // Close when a nav link is tapped
    dropdown.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMenu);
    });

    // Close when clicking outside the dropdown or hamburger
    document.addEventListener("click", function (e) {
      if (!hamburger.contains(e.target) && !dropdown.contains(e.target)) {
        closeMenu();
      }
    });

    // Close on Escape key
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });
  }());

  renderHeroParagraphs();
  applyTranslations(detectDefaultLang());
})();
