// main.js
// Language toggle: instant DOM swap, localStorage persistence,
// navigator.language default. No page reload, no scroll jump.

(function () {
  const IEL_URL = "https://utulsa.edu/academics/interdisciplinary-programs/international-engineering-science-language/";
  const STORAGE_KEY = "lang";

  // Resume file naming convention: "assets/pdfs/<lang> Gideon Ong Resume <YYYYMMDD>.pdf"
  // e.g. "assets/pdfs/en Gideon Ong Resume 20260915.pdf".
  // Static hosting has no directory listing, so the "latest" file is found by
  // probing dates backward from today (HEAD request) until one exists — drop a
  // new PDF in with today's date and no code change is needed.
  const RESUME_DIR = "assets/pdfs/";
  const RESUME_SEARCH_DAYS = 730; // how far back to probe before giving up (~2 years)
  const RESUME_PROBE_BATCH = 30; // dates checked in parallel per round
  const RESUME_CACHE_PREFIX = "resumeUrl_";
  const RESUME_CACHE_TTL_MS = 24 * 60 * 60 * 1000; // re-probe at most once a day

  function formatYYYYMMDD(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return "" + y + m + day;
  }

  function resumeUrlForDate(lang, yyyymmdd) {
    return RESUME_DIR + encodeURIComponent(lang + " Gideon Ong Resume " + yyyymmdd + ".pdf");
  }

  function readResumeCache(lang) {
    try {
      const cached = JSON.parse(localStorage.getItem(RESUME_CACHE_PREFIX + lang) || "null");
      if (cached && Date.now() - cached.checkedAt < RESUME_CACHE_TTL_MS) return cached.url;
    } catch (e) { /* ignore malformed/unavailable storage */ }
    return null;
  }

  function writeResumeCache(lang, url) {
    try {
      localStorage.setItem(RESUME_CACHE_PREFIX + lang, JSON.stringify({ url: url, checkedAt: Date.now() }));
    } catch (e) { /* ignore unavailable storage */ }
  }

  async function findLatestResumeUrl(lang) {
    const cached = readResumeCache(lang);
    if (cached) return cached;

    const today = new Date();
    for (let start = 0; start <= RESUME_SEARCH_DAYS; start += RESUME_PROBE_BATCH) {
      const batch = [];
      for (let i = start; i < start + RESUME_PROBE_BATCH && i <= RESUME_SEARCH_DAYS; i++) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        batch.push(resumeUrlForDate(lang, formatYYYYMMDD(d)));
      }
      const results = await Promise.all(batch.map(function (url) {
        return fetch(url, { method: "HEAD" })
          .then(function (res) { return res.ok ? url : null; })
          .catch(function () { return null; });
      }));
      const hit = results.find(Boolean);
      if (hit) {
        writeResumeCache(lang, hit);
        return hit;
      }
    }
    return null;
  }

  function updateResumeLinks(lang) {
    findLatestResumeUrl(lang).then(function (url) {
      if (!url) return; // keep whatever href is already on the element
      document.querySelectorAll("[data-resume-link]").forEach(function (el) {
        el.setAttribute("href", url);
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

  function withIelChip(text) {
    const chip = '<a class="iel-chip" href="' + IEL_URL + '" target="_blank" rel="noopener">IEL</a>';
    return text.replace(/\bIEL\b/, chip);
  }

  function renderHeroParagraphs() {
    document.querySelectorAll("[data-hero-lang]").forEach(function (el) {
      const lang = el.getAttribute("data-hero-lang");
      const dict = translations[lang];
      if (dict && dict.heroDesc) {
        el.innerHTML = withIelChip(dict.heroDesc);
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

    updateResumeLinks(lang);

    document.querySelectorAll(".lang-toggle .lang-btn").forEach(function (span) {
      span.classList.toggle("is-active", span.getAttribute("data-lang") === lang);
    });

    document.documentElement.setAttribute("lang", lang);
    updateHeroActiveState(lang);
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

  renderHeroParagraphs();
  applyTranslations(detectDefaultLang());
})();
