// chips.js
// The ONE auto-linker for phrase chips. Rendered content (project and
// experience strings, the bio, the AI statement, the hero paragraphs) is
// written as plain text — translations.js holds no HTML — and this file turns
// known phrases into the existing .iel-chip style at render time.
//
//   CHIPS  [{ phrase, urls: { en, es } }]  — phrase is a plain string, matched
//          as a whole word (no letter or digit on either side). One link per
//          phrase per element: only the FIRST occurrence is linked.
//
//   siteChips.fill(el, text, lang)  → el
//          Replaces el's content with `text`, linking phrases. Builds DOM
//          nodes (text nodes + <a class="iel-chip">) — never innerHTML.
//          Headings, links and buttons (and anything inside a link or button)
//          get plain text, so a chip can never nest inside another <a>.
//          Idempotent: it always starts from the string, so a language
//          switch that calls it again produces the same result.
//
// Loaded on every page right after translations.js and before main.js.
// Adding a phrase = one line in CHIPS.

(function () {
  var IEL_URL_EN = "https://utulsa.edu/academics/interdisciplinary-programs/international-engineering-science-language/";
  var IEL_URL_ES = "https://utulsa-edu.translate.goog/academics/interdisciplinary-programs/international-engineering-science-language/?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=en";
  var BOTS_URL_EN = "https://automatetheboringstuff.com/";
  var BOTS_URL_ES = "https://automatetheboringstuff-com.translate.goog/?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=en";

  var CHIPS = [
    { phrase: "Zohaib Sheikh", urls: { en: "https://zohaibsheikh.dev", es: "https://zohaibsheikh.dev" } },
    { phrase: "IEL", urls: { en: IEL_URL_EN, es: IEL_URL_ES } },
    { phrase: "automating the boring stuff", urls: { en: BOTS_URL_EN, es: BOTS_URL_ES } },
    { phrase: "automatizar lo aburrido", urls: { en: BOTS_URL_EN, es: BOTS_URL_ES } }
  ];

  // Elements that never get chips: headings and anything that is, or sits
  // inside, a link or button.
  var SKIP_TAGS = /^(A|BUTTON|H1|H2|H3|H4|H5|H6)$/;

  var WORD = /[\p{L}\p{N}_]/u;
  function isWordChar(ch) { return !!ch && WORD.test(ch); }

  // Index of the first whole-word occurrence of `phrase` in `text`, or -1.
  function findWhole(text, phrase) {
    var from = 0;
    while (from <= text.length) {
      var i = text.indexOf(phrase, from);
      if (i === -1) return -1;
      if (!isWordChar(text.charAt(i - 1)) && !isWordChar(text.charAt(i + phrase.length))) return i;
      from = i + 1;
    }
    return -1;
  }

  function currentLang() {
    return document.documentElement.getAttribute("lang") === "es" ? "es" : "en";
  }

  function fill(el, text, lang) {
    text = (text === undefined || text === null) ? "" : String(text);
    lang = lang || currentLang();
    el.textContent = "";

    if (SKIP_TAGS.test(el.tagName) || (el.closest && el.closest("a, button"))) {
      el.textContent = text;
      return el;
    }

    // One match per chip (first whole-word occurrence), non-overlapping,
    // in text order.
    var matches = [];
    CHIPS.forEach(function (chip) {
      var url = chip.urls[lang] || chip.urls.en;
      if (!url) return;
      var start = findWhole(text, chip.phrase);
      if (start === -1) return;
      var end = start + chip.phrase.length;
      var overlaps = matches.some(function (m) { return start < m.end && end > m.start; });
      if (!overlaps) matches.push({ start: start, end: end, url: url });
    });
    matches.sort(function (a, b) { return a.start - b.start; });

    var pos = 0;
    matches.forEach(function (m) {
      if (m.start > pos) el.appendChild(document.createTextNode(text.slice(pos, m.start)));
      var a = document.createElement("a");
      a.className = "iel-chip";
      a.href = m.url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = text.slice(m.start, m.end);
      el.appendChild(a);
      pos = m.end;
    });
    if (pos < text.length) el.appendChild(document.createTextNode(text.slice(pos)));
    return el;
  }

  window.siteChips = { CHIPS: CHIPS, fill: fill };
}());
