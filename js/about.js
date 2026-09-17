// about.js
// Page-specific behavior for about.html only:
//   - §1→§2 scroll-driven background crossfade + resume/CV/transcript button morph
//   - §3 velocity-threshold book stepper
//   - §4 FAQ accordion (rendered from a data array)
//   - §6 viewing-settings toggles + interesting-sites list (rendered from a data array)
// Content arrays here hold EN/ES text directly (not translations.js keys) per plan.md's
// Page Spec — about.html, so they re-render on the "langchange" event main.js dispatches.

(function () {
  function currentLang() {
    return document.documentElement.getAttribute("lang") === "es" ? "es" : "en";
  }

  /* ------------------------------------------------------------------------
     §1 → §2 background crossfade + resume button morph
     ------------------------------------------------------------------------ */
  (function () {
    var whoami = document.getElementById("about-s2");
    var overlay = whoami && whoami.querySelector(".whoami-bg-overlay");
    var resumeBtn = document.querySelector('[data-btn="resume"]');
    var btnGroup = document.querySelector("[data-btn-group]");
    if (!whoami || !overlay || !resumeBtn || !btnGroup) return;

    var thresholds = [];
    for (var i = 0; i <= 1; i += 0.05) thresholds.push(i);

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var ratio = entry.intersectionRatio;
        overlay.style.opacity = String(1 - ratio);
        var revealed = ratio > 0.35;
        resumeBtn.classList.toggle("is-hidden", revealed);
        btnGroup.classList.toggle("is-visible", revealed);
      });
    }, { threshold: thresholds });

    observer.observe(whoami);
  }());

  /* ------------------------------------------------------------------------
     §3 — "What have I been reading?" book stepper
     ------------------------------------------------------------------------ */
  var books = [
    {
      coverSrc: "assets/images/book-placeholder-1.jpg",
      titleEN: "[Book title 1 — EN]",
      titleES: "[Título del libro 1 — ES]",
      descEN: "[Book description 1 — EN]",
      descES: "[Descripción del libro 1 — ES]",
      visible: true
    },
    {
      coverSrc: "assets/images/book-placeholder-2.jpg",
      titleEN: "[Book title 2 — EN]",
      titleES: "[Título del libro 2 — ES]",
      descEN: "[Book description 2 — EN]",
      descES: "[Descripción del libro 2 — ES]",
      visible: true
    },
    {
      coverSrc: "assets/images/book-placeholder-3.jpg",
      titleEN: "[Book title 3 — EN]",
      titleES: "[Título del libro 3 — ES]",
      descEN: "[Book description 3 — EN]",
      descES: "[Descripción del libro 3 — ES]",
      visible: true
    }
  ];

  (function () {
    var section = document.getElementById("about-reading");
    var wrap = document.getElementById("book-covers-wrap");
    var coversEl = document.getElementById("book-covers");
    var textWrap = document.getElementById("book-text");
    var titleEl = document.getElementById("book-title");
    var descEl = document.getElementById("book-desc");
    if (!section || !wrap || !coversEl || !textWrap || !titleEl || !descEl) return;

    var visibleBooks = books.filter(function (b) { return b.visible; });
    if (!visibleBooks.length) return;

    var currentIndex = 0;
    var VH_PER_BOOK = 90; // vh of scroll runway per book, gives room for the velocity gesture
    section.style.height = (visibleBooks.length * VH_PER_BOOK) + "vh";

    visibleBooks.forEach(function (book, i) {
      var img = document.createElement("img");
      img.className = "book-cover";
      img.src = book.coverSrc;
      img.alt = "";
      img.dataset.index = String(i);
      coversEl.appendChild(img);
    });

    function updateCovers() {
      Array.prototype.forEach.call(coversEl.children, function (img, i) {
        img.classList.toggle("is-active", i === currentIndex);
      });
      var coverEl = coversEl.children[0];
      var coverHeight = coverEl ? coverEl.offsetHeight : 0;
      var containerHeight = wrap.offsetHeight;
      var centerOffset = (containerHeight - coverHeight) / 2;
      coversEl.style.transform = "translateY(" + (centerOffset - currentIndex * coverHeight) + "px)";
    }

    function renderText(animate) {
      var book = visibleBooks[currentIndex];
      var lang = currentLang();
      var title = lang === "es" ? book.titleES : book.titleEN;
      var desc = lang === "es" ? book.descES : book.descEN;

      if (!animate) {
        titleEl.textContent = title;
        descEl.textContent = desc;
        return;
      }

      textWrap.classList.add("is-exiting");
      window.setTimeout(function () {
        titleEl.textContent = title;
        descEl.textContent = desc;
        textWrap.classList.remove("is-exiting");
        textWrap.classList.add("is-entering");
        void textWrap.offsetWidth; // force reflow so the entering transition runs
        textWrap.classList.remove("is-entering");
      }, 250);
    }

    renderText(false);
    updateCovers();
    window.addEventListener("resize", updateCovers);
    window.addEventListener("load", updateCovers);

    var lastScrollY = window.scrollY;
    var lastTime = performance.now();
    var zoneAccum = 0;
    var VELOCITY_THRESHOLD = 0.4; // px/ms — below this, scrolling is treated as slow/browsing
    var DISTANCE_THRESHOLD = 90; // px accumulated at sufficient velocity to commit to a step

    window.addEventListener("scroll", function () {
      // Covers may not have had a measurable offsetHeight yet (e.g. placeholder
      // images still loading) when this handler first ran — recompute once one is available.
      var firstCover = coversEl.children[0];
      if (firstCover && firstCover.offsetHeight === 0) updateCovers();

      var rect = section.getBoundingClientRect();
      var inZone = rect.top < window.innerHeight && rect.bottom > 0;
      var now = performance.now();
      var deltaY = window.scrollY - lastScrollY;
      var deltaT = Math.max(now - lastTime, 1);
      var velocity = Math.abs(deltaY) / deltaT;

      if (inZone) {
        zoneAccum += deltaY;
        if (velocity > VELOCITY_THRESHOLD && Math.abs(zoneAccum) > DISTANCE_THRESHOLD) {
          var direction = zoneAccum > 0 ? 1 : -1;
          var steps = Math.min(
            visibleBooks.length - 1,
            Math.floor(Math.abs(zoneAccum) / DISTANCE_THRESHOLD)
          );
          var newIndex = Math.max(0, Math.min(visibleBooks.length - 1, currentIndex + direction * steps));
          if (newIndex !== currentIndex) {
            currentIndex = newIndex;
            renderText(true);
            updateCovers();
          }
          zoneAccum = 0;
        }
      } else {
        zoneAccum = 0;
      }

      lastScrollY = window.scrollY;
      lastTime = now;
    }, { passive: true });

    document.addEventListener("langchange", function () { renderText(false); });
  }());

  /* ------------------------------------------------------------------------
     §4 — Interview FAQ accordion
     ------------------------------------------------------------------------ */
  var faqItems = [
    { questionEN: "[FAQ question 1 — EN]", questionES: "[Pregunta 1 — ES]", answerEN: "[FAQ answer 1 — EN]", answerES: "[Respuesta 1 — ES]", visible: true },
    { questionEN: "[FAQ question 2 — EN]", questionES: "[Pregunta 2 — ES]", answerEN: "[FAQ answer 2 — EN]", answerES: "[Respuesta 2 — ES]", visible: true },
    { questionEN: "[FAQ question 3 — EN]", questionES: "[Pregunta 3 — ES]", answerEN: "[FAQ answer 3 — EN]", answerES: "[Respuesta 3 — ES]", visible: true },
    { questionEN: "[FAQ question 4 — EN]", questionES: "[Pregunta 4 — ES]", answerEN: "[FAQ answer 4 — EN]", answerES: "[Respuesta 4 — ES]", visible: true }
  ];

  (function () {
    var container = document.getElementById("faq-accordion");
    if (!container) return;
    var visibleItems = faqItems.filter(function (item) { return item.visible; });

    // Which items are open survives a re-render triggered by a language switch.
    var openState = visibleItems.map(function () { return false; });

    function render() {
      var lang = currentLang();
      container.innerHTML = "";

      visibleItems.forEach(function (item, i) {
        var wrapper = document.createElement("div");
        wrapper.className = "faq-item";
        wrapper.classList.toggle("is-open", openState[i]);

        var button = document.createElement("button");
        button.type = "button";
        button.className = "faq-question";
        button.setAttribute("aria-expanded", String(openState[i]));
        button.setAttribute("aria-controls", "faq-answer-" + i);

        var chevron = document.createElement("span");
        chevron.className = "faq-chevron";
        chevron.setAttribute("aria-hidden", "true");
        chevron.textContent = openState[i] ? "▼" : "▶";

        var questionText = document.createElement("span");
        questionText.textContent = lang === "es" ? item.questionES : item.questionEN;

        button.appendChild(chevron);
        button.appendChild(questionText);

        var answer = document.createElement("div");
        answer.className = "faq-answer";
        answer.id = "faq-answer-" + i;
        var answerP = document.createElement("p");
        answerP.textContent = lang === "es" ? item.answerES : item.answerEN;
        answer.appendChild(answerP);

        button.addEventListener("click", function () {
          openState[i] = !openState[i];
          wrapper.classList.toggle("is-open", openState[i]);
          button.setAttribute("aria-expanded", String(openState[i]));
          chevron.textContent = openState[i] ? "▼" : "▶";
        });

        wrapper.appendChild(button);
        wrapper.appendChild(answer);
        container.appendChild(wrapper);
      });
    }

    render();
    document.addEventListener("langchange", render);
  }());

  /* ------------------------------------------------------------------------
     §6 — Viewing settings toggles
     ------------------------------------------------------------------------ */
  (function () {
    var THEME_KEY = "aboutTheme";

    var preCollege = document.getElementById("toggle-pre-college");
    var readability = document.getElementById("toggle-readability");
    var colorblind = document.getElementById("toggle-colorblind");
    var darkMode = document.getElementById("toggle-dark-mode");

    if (preCollege) {
      preCollege.addEventListener("change", function () {
        document.body.classList.toggle("hide-pre-college", !preCollege.checked);
      });
    }

    if (readability) {
      readability.addEventListener("change", function () {
        document.body.classList.toggle("readability-mode", readability.checked);
      });
    }

    if (colorblind) {
      colorblind.addEventListener("change", function () {
        document.documentElement.classList.toggle("colorblind-mode", colorblind.checked);
      });
    }

    if (darkMode) {
      var stored = null;
      try { stored = localStorage.getItem(THEME_KEY); } catch (e) { /* storage unavailable */ }
      if (stored === "dark") {
        darkMode.checked = true;
        document.documentElement.setAttribute("data-theme", "dark");
      }

      darkMode.addEventListener("change", function () {
        if (darkMode.checked) {
          document.documentElement.setAttribute("data-theme", "dark");
          try { localStorage.setItem(THEME_KEY, "dark"); } catch (e) { /* storage unavailable */ }
        } else {
          document.documentElement.removeAttribute("data-theme");
          try { localStorage.removeItem(THEME_KEY); } catch (e) { /* storage unavailable */ }
        }
      });
    }
  }());

  /* ------------------------------------------------------------------------
     §6 — Interesting sites list
     ------------------------------------------------------------------------ */
  var interestingSites = [
    { url: "#", labelEN: "[Site 1 — EN]", labelES: "[Sitio 1 — ES]", descEN: "[Site 1 description — EN]", descES: "[Descripción del sitio 1 — ES]" },
    { url: "#", labelEN: "[Site 2 — EN]", labelES: "[Sitio 2 — ES]", descEN: "[Site 2 description — EN]", descES: "[Descripción del sitio 2 — ES]" },
    { url: "#", labelEN: "[Site 3 — EN]", labelES: "[Sitio 3 — ES]", descEN: "[Site 3 description — EN]", descES: "[Descripción del sitio 3 — ES]" }
  ];

  (function () {
    var list = document.getElementById("interesting-sites-list");
    if (!list) return;

    function render() {
      var lang = currentLang();
      list.innerHTML = "";
      interestingSites.forEach(function (site) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = site.url;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = lang === "es" ? site.labelES : site.labelEN;
        var desc = document.createElement("p");
        desc.className = "site-desc";
        desc.textContent = lang === "es" ? site.descES : site.descEN;
        li.appendChild(a);
        li.appendChild(desc);
        list.appendChild(li);
      });
    }

    render();
    document.addEventListener("langchange", render);
  }());
}());
