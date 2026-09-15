// main.js
// Language toggle: instant DOM swap, localStorage persistence,
// navigator.language default. No page reload, no scroll jump.

(function () {
  const IEL_URL = "https://utulsa.edu/academics/interdisciplinary-programs/international-engineering-science-language/";
  const STORAGE_KEY = "lang";

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

    document.querySelectorAll("[data-resume-link]").forEach(function (el) {
      el.setAttribute("href", "assets/pdfs/resume-" + lang + ".pdf");
    });

    document.querySelectorAll("[data-lang-btn]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-lang-btn") === lang);
    });

    document.documentElement.setAttribute("lang", lang);
    updateHeroActiveState(lang);
  }

  function setLang(lang) {
    localStorage.setItem(STORAGE_KEY, lang);
    applyTranslations(lang);
  }

  document.querySelectorAll("[data-lang-btn]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setLang(btn.getAttribute("data-lang-btn"));
    });
  });

  renderHeroParagraphs();
  applyTranslations(detectDefaultLang());
})();
