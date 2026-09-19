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
     §1 → §2 — portrait travel + resume→CV/Transcript starburst morph
     Scroll-driven, radial-fan version. The constants below came from the
     live tuner (starburst_tuner.html); tweak them here to re-tune.
     Desktop only; on mobile the buttons show statically (see style.css).
     ------------------------------------------------------------------------ */
  (function () {
    var intro = document.getElementById('about-intro');
    var s1 = document.getElementById('about-s1');
    var s2 = document.getElementById('about-s2');
    var photoCol = document.getElementById('about-photo-col');
    var buttons = document.getElementById('about-buttons');
    var resumeBtn = buttons && buttons.querySelector('[data-btn="resume"]');
    var group = buttons && buttons.querySelector('[data-btn-group]');
    if (!intro || !s1 || !s2 || !photoCol || !buttons || !resumeBtn || !group) return;

    // ---- TUNABLES (from the tuner) ----------------------------------------
    var NTEETH      = 16;     // spike count (more = finer rays)
    var DEPTH_FRAC  = 0.85;   // notch depth as a fraction of the shape's height
    var D0          = 12;     // collapsed solid-dot diameter (px)
    var CORNER      = 8;      // resting corner radius (px)
    var DEAD        = 0.16;   // dead zone at each end (fraction) — undeformed, clickable
    var TEXT_FADE   = 0.10;   // (reserved) label-fade fraction
    var FILL_W      = 42;     // width (px) below which the shape fills to solid
    var TRAVEL_SPAN = 0.40;   // <1 = portrait travels DOWN faster than the page; lower = faster

    var mql = window.matchMedia('(max-width: 767px)');

    // ---- inject the morph SVG once ----------------------------------------
    var NS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'morph-svg'); svg.setAttribute('aria-hidden', 'true');
    var path = document.createElementNS(NS, 'path'); svg.appendChild(path);
    buttons.appendChild(svg);

    var btnW = 200, btnH = 46, gap = 16, boxH = 112;
    function measure() {
      btnW = resumeBtn.offsetWidth || btnW;
      btnH = resumeBtn.offsetHeight || btnH;
      gap = parseFloat(getComputedStyle(buttons).getPropertyValue('--btn-gap')) || gap;
      boxH = 2 * btnH + gap;
      buttons.style.height = boxH + 'px';
      svg.setAttribute('viewBox', '0 0 ' + btnW + ' ' + boxH);
      svg.setAttribute('width', btnW); svg.setAttribute('height', boxH);
    }

    function lerp(a, b, t) { return a + (b - a) * t; }
    function clamp01(x) { return Math.max(0, Math.min(1, x)); }
    function smooth(x) { x = clamp01(x); return x * x * (3 - 2 * x); }
    function vstep(a) { a = clamp01(a); return a * a * (3 - 2 * a); }
    function ball(t) {
      if (t <= 0.5) { var u = t / 0.5; return 0.5 * u * u; }
      var v = (t - 0.5) / 0.5; return 0.5 + 0.5 * (1 - (1 - v) * (1 - v));
    }

    // rounded-rect boundary points + outward normals, centred at origin (y-up)
    function rrectPN(w, h, r) {
      r = Math.max(0.001, Math.min(r, w / 2, h / 2));
      var pts = [], nrm = [], dens = 0.7;
      function edge(p0, p1, n) {
        var L = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]), m = Math.max(2, Math.round(dens * L));
        for (var i = 0; i < m; i++) { var t = i / m; pts.push([lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)]); nrm.push(n); }
      }
      function arc(cx, cy, a0, a1) {
        var m = Math.max(3, Math.round(dens * r * Math.abs(a1 - a0)));
        for (var i = 0; i < m; i++) { var a = lerp(a0, a1, i / m); pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); nrm.push([Math.cos(a), Math.sin(a)]); }
      }
      edge([-w/2+r, 0], [w/2-r, 0], [0,-1]); arc(w/2-r, r, -Math.PI/2, 0);
      edge([w/2, r], [w/2, h-r], [1,0]);     arc(w/2-r, h-r, 0, Math.PI/2);
      edge([w/2-r, h], [-w/2+r, h], [0,1]);  arc(-w/2+r, h-r, Math.PI/2, Math.PI);
      edge([-w/2, h-r], [-w/2, r], [-1,0]);  arc(-w/2+r, r, Math.PI, 3*Math.PI/2);
      for (var i = 0; i < pts.length; i++) pts[i][1] -= h / 2;
      return { pts: pts, nrm: nrm };
    }

    // carve one lobe (radial notches toward the bottom-centre convergence point)
    function carve(c, mirror) {
      var w = lerp(btnW, D0, smooth(c)), h = lerp(btnH, D0, smooth(c)), r = lerp(CORNER, D0/2, c);
      var o = rrectPN(w, h, r), pts = o.pts, nrm = o.nrm, N = pts.length, i, j;
      var bcx = 0, bcy = -h / 2;
      var seg = new Array(N), L = 0;
      for (i = 0; i < N; i++) { j = (i+1) % N; seg[i] = Math.hypot(pts[j][0]-pts[i][0], pts[j][1]-pts[i][1]); L += seg[i]; }
      var s = new Array(N); s[0] = 0; for (i = 1; i < N; i++) s[i] = s[i-1] + seg[i-1];
      var ti = 0, best = -1e9;
      for (i = 0; i < N; i++) { var sc = pts[i][1] - 1e3 * Math.abs(pts[i][0]); if (sc > best) { best = sc; ti = i; } }
      var sn = Math.sin(Math.PI * c), out = new Array(N);
      for (i = 0; i < N; i++) {
        var dd = Math.abs(s[i] - s[ti]); dd = Math.min(dd, L - dd);
        var val = 0.5 - 0.5 * Math.cos(2 * Math.PI * NTEETH * (dd / L));
        var mask = vstep((nrm[i][1] + 0.60) / 0.55);
        var inw = DEPTH_FRAC * h * sn * mask * val;
        var dx = bcx - pts[i][0], dy = bcy - pts[i][1], dn = Math.hypot(dx, dy) || 1e-6;
        var x = pts[i][0] + (dx / dn) * inw, y = pts[i][1] + (dy / dn) * inw;
        if (mirror) y = -y;
        out[i] = [x, y];
      }
      return { out: out, w: w, h: h };
    }

    // one lobe -> SVG path string, placed with its flat edge anchored at Py (y-up from box centre)
    function lobeD(c, Py, mirror) {
      var o = carve(c, mirror), pts = o.out, h = o.h, oy = mirror ? -h/2 : h/2, d = '';
      for (var i = 0; i < pts.length; i++) {
        var fy = Py + pts[i][1] + oy;                 // y-up from box centre
        var X = btnW/2 + pts[i][0], Y = boxH/2 - fy;  // -> svg coords (y-down)
        d += (i ? 'L' : 'M') + X.toFixed(2) + ' ' + Y.toFixed(2) + ' ';
      }
      return d + 'Z';
    }

    function show(el, on) { el.style.opacity = on ? '1' : '0'; el.style.pointerEvents = on ? 'auto' : 'none'; }

    function updateMorph(q) {
      if (q <= 0.0001) { show(resumeBtn, true); show(group, false); svg.style.opacity = '0'; return; }
      if (q >= 0.9999) { show(group, true); show(resumeBtn, false); svg.style.opacity = '0'; return; }
      show(resumeBtn, false); show(group, false);
      var d, wNow;
      if (q <= 0.5) {
        var c = q / 0.5, P = lerp(gap/2, 0, smooth(c));
        d = lobeD(c, P, false);
        wNow = lerp(btnW, D0, smooth(c));
      } else {
        var e = (q - 0.5) / 0.5, c2 = 1 - e, off = lerp(0, gap/2, smooth(e));
        d = lobeD(c2, off, false) + ' ' + lobeD(c2, -off, true);
        wNow = lerp(btnW, D0, smooth(c2));
      }
      path.setAttribute('d', d);
      path.style.fillOpacity = vstep((FILL_W - wNow) / 12);
      svg.style.opacity = '1';
    }

    function frame() {
      if (mql.matches) {                 // mobile: static, morph off
        photoCol.style.transform = ''; svg.style.opacity = '0';
        resumeBtn.style.opacity = ''; resumeBtn.style.pointerEvents = '';
        group.style.opacity = ''; group.style.pointerEvents = '';
        return;
      }
      var scy = window.scrollY || window.pageYOffset;
      var introTop = intro.getBoundingClientRect().top + scy;
      var s1H = s1.offsetHeight, s2H = s2.offsetHeight, colH = photoCol.offsetHeight;
      var start = introTop, end = introTop + s1H * TRAVEL_SPAN;
      var p = clamp01((scy - start) / Math.max(1, end - start));
      var restC = introTop + s1H / 2, finalC = introTop + s1H + s2H / 2, baseC = introTop + colH / 2;
      photoCol.style.transform = 'translateY(' + (lerp(restC, finalC, p) - baseC) + 'px)';
      updateMorph(ball(clamp01((p - DEAD) / (1 - 2 * DEAD))));
    }

    var ticking = false;
    function onScroll() {
      if (ticking) return; ticking = true;
      window.requestAnimationFrame(function () { frame(); ticking = false; });
    }

    // images can change measured button size once fonts/layout settle
    measure(); frame();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () { measure(); frame(); });
    window.addEventListener('load', function () { measure(); frame(); });
    document.addEventListener('langchange', function () { measure(); frame(); });
  }());

  /* ------------------------------------------------------------------------
     §3 — "What have I been reading?"
     Pinned full-screen. Covers sit on a layer behind the page and show through a
     rectangular hole; they slide VERTICALLY as you scroll. SCROLL-DRIVEN: the
     position through the covers tracks how far you've scrolled into the section
     (analog, 1:1 with scroll). To switch to flick-to-step, see the message note.
     Desktop only; mobile falls back to a simple stack (see style.css).
     ------------------------------------------------------------------------ */
  var books = [
    { coverSrc:"assets/images/book-placeholder-1.jpg", titleEN:"[Book title 1 — EN]", titleES:"[Título del libro 1 — ES]", descEN:"[Book description 1 — EN]", descES:"[Descripción del libro 1 — ES]", visible:true },
    { coverSrc:"assets/images/book-placeholder-2.jpg", titleEN:"[Book title 2 — EN]", titleES:"[Título del libro 2 — ES]", descEN:"[Book description 2 — EN]", descES:"[Descripción del libro 2 — ES]", visible:true },
    { coverSrc:"assets/images/book-placeholder-3.jpg", titleEN:"[Book title 3 — EN]", titleES:"[Título del libro 3 — ES]", descEN:"[Book description 3 — EN]", descES:"[Descripción del libro 3 — ES]", visible:true },
    { coverSrc:"assets/images/book-placeholder-4.jpg", titleEN:"[Book title 4 — EN]", titleES:"[Título del libro 4 — ES]", descEN:"[Book description 4 — EN]", descES:"[Descripción del libro 4 — ES]", visible:true },
    { coverSrc:"assets/images/book-placeholder-5.jpg", titleEN:"[Book title 5 — EN]", titleES:"[Título del libro 5 — ES]", descEN:"[Book description 5 — EN]", descES:"[Descripción del libro 5 — ES]", visible:true }
  ];

  (function () {
    var section = document.getElementById('about-reading');
    var strip = document.getElementById('book-covers');
    var holeEl = document.getElementById('reading-hole');
    var textWrap = document.getElementById('book-text');
    var titleEl = document.getElementById('book-title');
    var descEl = document.getElementById('book-desc');
    if (!section || !strip || !textWrap || !titleEl || !descEl) return;

    var READ_STEP_VH = 70;                    // scroll runway (vh) per book
    var mql = window.matchMedia('(max-width: 767px)');
    function clamp01(x){ return Math.max(0, Math.min(1, x)); }

    var vis = books.filter(function(b){ return b.visible; });
    if (!vis.length) return;

    vis.forEach(function(b){
      var c = document.createElement('div');
      c.className = 'reading-cover';
      c.style.backgroundImage = 'url("' + b.coverSrc + '")';
      strip.appendChild(c);
    });

    var idxShown = -1;
    function renderText(i, animate){
      var b = vis[i], lang = (typeof currentLang === 'function' ? currentLang() : 'en');
      var t = lang === 'es' ? b.titleES : b.titleEN;
      var d = lang === 'es' ? b.descES : b.descEN;
      if (!animate){ titleEl.textContent = t; descEl.textContent = d; return; }
      textWrap.classList.add('is-exiting');
      window.setTimeout(function(){
        titleEl.textContent = t; descEl.textContent = d;
        textWrap.classList.remove('is-exiting'); textWrap.classList.add('is-entering');
        void textWrap.offsetWidth; textWrap.classList.remove('is-entering');
      }, 200);
    }

    function layout(){
      if (mql.matches){ section.style.height = ''; strip.style.transform = ''; return; }
      section.style.height = (100 + (vis.length - 1) * READ_STEP_VH) + 'vh';
    }

    function frame(){
      if (mql.matches){ strip.style.transform = ''; return; }
      var vh = window.innerHeight;
      var runway = section.offsetHeight - vh;
      var p = runway > 0 ? clamp01((-section.getBoundingClientRect().top) / runway) : 0;
      var idxF = p * (vis.length - 1);
      var holeH = holeEl ? holeEl.offsetHeight : vh * 0.66;
      strip.style.transform = 'translateY(' + (-idxF * holeH).toFixed(2) + 'px)';
      var i = Math.round(idxF);
      if (i !== idxShown){ renderText(i, idxShown !== -1); idxShown = i; }
    }

    var ticking = false;
    function onScroll(){ if (ticking) return; ticking = true; window.requestAnimationFrame(function(){ frame(); ticking = false; }); }

    layout(); renderText(0, false); idxShown = 0; frame();
    window.addEventListener('scroll', onScroll, { passive:true });
    window.addEventListener('resize', function(){ layout(); frame(); });
    window.addEventListener('load', function(){ layout(); frame(); });
    if (mql.addEventListener) mql.addEventListener('change', function(){ layout(); frame(); });
    document.addEventListener('langchange', function(){ renderText(idxShown, false); });
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
