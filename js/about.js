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
    var cvBtn = buttons && buttons.querySelector('[data-btn="cv"]');
    var transcriptBtn = buttons && buttons.querySelector('[data-btn="transcript"]');
    var group = buttons && buttons.querySelector('[data-btn-group]');
    if (!intro || !s1 || !s2 || !photoCol || !buttons || !resumeBtn || !cvBtn || !transcriptBtn || !group) return;

    // js/main.js (loaded first) hides any document button whose type has no file
    // in the manifest (hidden attribute). The morph needs BOTH CV and transcript;
    // with one or both missing it is skipped: the resume button stays put and an
    // available single document simply shows in the bottom slot. The portrait
    // travel is unaffected.
    var groupCount = (cvBtn.hidden ? 0 : 1) + (transcriptBtn.hidden ? 0 : 1);
    var morphEnabled = groupCount === 2;

    // ---- TUNABLES (from the tuner) ----------------------------------------
    var NTEETH      = 16;     // spike count (more = finer rays)
    var DEPTH_FRAC  = 0.85;   // notch depth as a fraction of the shape's height
    var D0          = 12;     // collapsed solid-dot diameter (px)
    var CORNER      = 8;      // resting corner radius (px)
    var DEAD        = 0.16;   // dead zone at each end (fraction) — undeformed, clickable
    var TEXT_FADE   = 0.10;   // (reserved) label-fade fraction
    var FILL_W      = 42;     // width (px) below which the shape fills to solid
    var HIT_PAD     = 8;      // invisible click padding around the shape (px) — hit stroke = 2 × this
    // Portrait travel speed. <1 = portrait travels DOWN faster than the page; lower = faster.
    // Two values: desktop/iPad (>=768px) and phone (<768px) can be tuned independently.
    var TRAVEL_SPAN_DESKTOP = 0.7;   // computer + iPad
    var TRAVEL_SPAN_MOBILE  = 4.5;   // phone (<768px) — change this alone to retune the phone

    var mql = window.matchMedia('(max-width: 767px)');

    // ---- inject the morph SVG once ----------------------------------------
    // Two visible lobes (top / bottom) plus, over each, an invisible "hit" twin
    // with the same d and a fat transparent stroke (2 × HIT_PAD): the spiky
    // outline and the tiny dot become forgiving click targets. Clicks forward to
    // the real <a> buttons so main.js's probed hrefs and target="_blank" still apply.
    // In the second half each hit path is clipped to its own side of the mirror line.
    var NS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'morph-svg'); svg.setAttribute('aria-hidden', 'true');
    var defs = document.createElementNS(NS, 'defs'); svg.appendChild(defs);
    function clipRect(id) {
      var cp = document.createElementNS(NS, 'clipPath'); cp.setAttribute('id', id);
      var r = document.createElementNS(NS, 'rect'); cp.appendChild(r); defs.appendChild(cp);
      return r;
    }
    var clipTopRect = clipRect('morph-clip-top'), clipBotRect = clipRect('morph-clip-bottom');
    function mkPath(cls) { var p = document.createElementNS(NS, 'path'); p.setAttribute('class', cls); svg.appendChild(p); return p; }
    var pathTop = mkPath('morph-lobe'), pathBot = mkPath('morph-lobe');   // visible
    var hitTop = mkPath('morph-hit'), hitBot = mkPath('morph-hit');       // invisible, on top
    hitTop.style.strokeWidth = hitBot.style.strokeWidth = (2 * HIT_PAD) + 'px';
    buttons.appendChild(svg);

    // click routing: top pad = resume (first half) / CV (second half); bottom pad = transcript
    var qNow = 0;
    hitTop.addEventListener('click', function (e) { e.preventDefault(); (qNow <= 0.5 ? resumeBtn : cvBtn).click(); });
    hitBot.addEventListener('click', function (e) { e.preventDefault(); transcriptBtn.click(); });
    // hover: thicken the targeted visible lobe (style.css .morph-lobe.is-hover)
    function hoverPair(hit, lobe) {
      hit.addEventListener('pointerenter', function () { lobe.classList.add('is-hover'); });
      hit.addEventListener('pointerleave', function () { lobe.classList.remove('is-hover'); });
    }
    hoverPair(hitTop, pathTop); hoverPair(hitBot, pathBot);

    var btnW = 200, btnH = 46, gap = 16, boxH = 112;
    function measure() {
      btnW = resumeBtn.offsetWidth || btnW;
      btnH = resumeBtn.offsetHeight || btnH;
      gap = parseFloat(getComputedStyle(buttons).getPropertyValue('--btn-gap')) || gap;
      boxH = 2 * btnH + gap;
      buttons.style.height = boxH + 'px';
      svg.setAttribute('viewBox', '0 0 ' + btnW + ' ' + boxH);
      svg.setAttribute('width', btnW); svg.setAttribute('height', boxH);
      // half-plane clips for the hit pads: above / below the mirror line (y = boxH/2),
      // oversized sideways so the padded stroke is never cut off at the box edges
      [clipTopRect, clipBotRect].forEach(function (r, i) {
        r.setAttribute('x', -btnW); r.setAttribute('width', 3 * btnW);
        r.setAttribute('y', i ? boxH / 2 : -boxH); r.setAttribute('height', 1.5 * boxH);
      });
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

    // one lobe -> SVG path string, drawn CENTRED at Yc (y-up from box centre).
    // clampSide keeps the lobe on its own side of the mirror line (+1 = y>=0,
    // -1 = y<=0, 0 = no clamp) so the two buttons never cross each other.
    function lobeD(c, Yc, mirror, clampSide) {
      var o = carve(c, mirror), pts = o.out, d = '';
      for (var i = 0; i < pts.length; i++) {
        var fy = Yc + pts[i][1];                      // centred on Yc
        if (clampSide > 0 && fy < 0) fy = 0;
        if (clampSide < 0 && fy > 0) fy = 0;
        var X = btnW/2 + pts[i][0], Y = boxH/2 - fy;  // -> svg coords (y-down)
        d += (i ? 'L' : 'M') + X.toFixed(2) + ' ' + Y.toFixed(2) + ' ';
      }
      return d + 'Z';
    }

    function show(el, on) { el.style.opacity = on ? '1' : '0'; el.style.pointerEvents = on ? 'auto' : 'none'; }

    // at rest the svg is opacity 0, but opacity does NOT stop pointer events —
    // empty the hit pads so they can never sit over a visible real button
    function rest() {
      svg.style.opacity = '0';
      hitTop.setAttribute('d', ''); hitBot.setAttribute('d', '');
      pathTop.classList.remove('is-hover'); pathBot.classList.remove('is-hover');
    }

    function updateMorph(q) {
      qNow = q;
      if (!morphEnabled) { show(resumeBtn, true); show(group, groupCount > 0); rest(); return; }
      if (q <= 0.0001) { show(resumeBtn, true); show(group, false); rest(); return; }
      if (q >= 0.9999) { show(group, true); show(resumeBtn, false); rest(); return; }
      show(resumeBtn, false); show(group, false);
      var Cc = gap/2 + btnH/2;              // each button's CENTRE distance from the mirror line
      var dTop, dBot = '', wNow;
      if (q <= 0.5) {
        var c = q / 0.5, Yc = lerp(Cc, 0, smooth(c));   // resume: top-slot centre -> mirror line
        dTop = lobeD(c, Yc, false, 0);
        wNow = lerp(btnW, D0, smooth(c));
        hitTop.removeAttribute('clip-path'); hitBot.removeAttribute('clip-path');  // one lobe: whole pad = resume
      } else {
        var e = (q - 0.5) / 0.5, c2 = 1 - e, off = lerp(0, Cc, smooth(e));
        dTop = lobeD(c2, off, false, +1);                // grow from the centred dot
        dBot = lobeD(c2, -off, true, -1);
        wNow = lerp(btnW, D0, smooth(c2));
        hitTop.setAttribute('clip-path', 'url(#morph-clip-top)');       // upper half-plane = CV
        hitBot.setAttribute('clip-path', 'url(#morph-clip-bottom)');    // lower half-plane = transcript
      }
      pathTop.setAttribute('d', dTop); pathBot.setAttribute('d', dBot);
      hitTop.setAttribute('d', dTop);  hitBot.setAttribute('d', dBot);
      var fo = vstep((FILL_W - wNow) / 12);
      pathTop.style.fillOpacity = fo; pathBot.style.fillOpacity = fo;
      svg.style.opacity = '1';
    }

    function frame() {
      var scy = window.scrollY || window.pageYOffset;
      var introTop = intro.getBoundingClientRect().top + scy;
      var vh = window.innerHeight;
      var colH = photoCol.offsetHeight;
      var restC, finalC, p;
      if (mql.matches) {
        // MOBILE: single column. The portrait travels down the (tall) header and
        // comes to rest CLEARLY INSIDE "Who am I?" (§2), morphing the buttons on the way.
        var s1Hm = s1.offsetHeight;
        var ids = s1.querySelector('.about-identifiers');
        var nameBottom = ids ? (ids.getBoundingClientRect().bottom + scy - introTop) : (0.18 * vh);
        var landInset = 0.05 * vh;                               // gap below §2's top edge
        restC  = introTop + nameBottom + 0.05 * vh + colH / 2;   // just below the name
        finalC = introTop + s1Hm + landInset + colH / 2;         // inside "Who am I?"
        p = clamp01((scy - introTop) / Math.max(1, (s1Hm - vh) * TRAVEL_SPAN_MOBILE));
        // Push the "Who am I?" text down so it clears where the portrait lands.
        var pad = Math.round(landInset + colH + 28);
        if (s2._padFor !== colH) { s2.style.paddingTop = pad + 'px'; s2._padFor = colH; }
      } else {
        // DESKTOP: portrait rides the right column from header-centre to who-am-i-centre.
        var s1H = s1.offsetHeight, s2H = s2.offsetHeight;
        restC  = introTop + s1H / 2;
        finalC = introTop + s1H + s2H / 2;
        p = clamp01((scy - introTop) / Math.max(1, (s1H * TRAVEL_SPAN_DESKTOP)));
        if (s2.style.paddingTop) { s2.style.paddingTop = ''; s2._padFor = null; }  // clear mobile override
      }
      var baseC = introTop + colH / 2;
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
     Pinned full-screen. Covers show through a rectangular hole and SNAP to whole
     covers: scrolling drags the covers a little (a preview), then a flick OR
     enough accumulated scroll commits to the next/prev book. If you stop between
     books without committing, it settles back onto the nearest cover — you never
     rest showing two covers at once. A little dead scroll after the last book
     before the section unpins. Desktop only; mobile = a stack of cover cards.
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

    // ---- TUNABLES ----------------------------------------------------------
    var COMMIT_VH    = 48;   // scroll (vh) within ONE gesture that commits one book (a flick past this steps;
                             //   short of it, it falls back). Also sizes the pinned runway = (N-1)*this, so it's
                             //   long enough that a normal flick can't overshoot the whole section.
    var DEAD_TAIL_VH = 40;   // dead scroll (vh) held on the last book before the section unpins
    var GESTURE_GAP  = 140;  // ms of scroll-pause that ends a gesture. ONE gesture (one flick/swipe) = at most ONE
                             //   book, no matter how many scroll events the touchpad fires. Flick again to go further.
    var PREVIEW      = 0.34; // how far (fraction of a cover) the covers slide while you drag
    var EASE         = 0.22; // settle easing per frame (higher = snappier)

    var mql = window.matchMedia('(max-width: 767px)');
    function clamp(x,a,b){ return Math.max(a, Math.min(b, x)); }
    function clamp01(x){ return clamp(x,0,1); }
    function nowMs(){ return (window.performance && performance.now) ? performance.now() : Date.now(); }

    var vis = books.filter(function(b){ return b.visible; });
    if (!vis.length) return;
    var N = vis.length;

    // build cover items (+ per-cover captions; captions show only on mobile cards)
    var caps = [];
    vis.forEach(function(b){
      var item = document.createElement('div'); item.className = 'reading-cover-item';
      var cov = document.createElement('div'); cov.className = 'reading-cover'; cov.style.backgroundImage = 'url("' + b.coverSrc + '")';
      var cap = document.createElement('div'); cap.className = 'reading-cover-cap';
      var h = document.createElement('h3'); h.className = 'book-title';
      var p = document.createElement('p'); p.className = 'book-desc';
      cap.appendChild(h); cap.appendChild(p); item.appendChild(cov); item.appendChild(cap); strip.appendChild(item);
      caps.push({ h:h, p:p, b:b });
    });
    function lang(){ return (typeof currentLang === 'function' ? currentLang() : 'en'); }
    function fillCaps(){ var l = lang(); caps.forEach(function(c){ c.h.textContent = l==='es'?c.b.titleES:c.b.titleEN; c.p.textContent = l==='es'?c.b.descES:c.b.descEN; }); }
    fillCaps();

    var index = 0, idxShown = -1;
    function renderText(i, animate){
      var b = vis[i], l = lang(); var t = l==='es'?b.titleES:b.titleEN, d = l==='es'?b.descES:b.descEN;
      if (!animate){ titleEl.textContent = t; descEl.textContent = d; return; }
      textWrap.classList.add('is-exiting');
      window.setTimeout(function(){
        titleEl.textContent = t; descEl.textContent = d;
        textWrap.classList.remove('is-exiting'); textWrap.classList.add('is-entering');
        void textWrap.offsetWidth; textWrap.classList.remove('is-entering');
      }, 180);
    }

    function layout(){
      section.style.height = (100 + (N-1)*COMMIT_VH + DEAD_TAIL_VH) + 'vh';
    }
    function commitPx(){ return COMMIT_VH / 100 * window.innerHeight; }

    // ---- snap / flick state ----
    var acc = 0;                 // scroll (px) accumulated toward the next/prev book since last commit
    var display = 0;             // displayed position in book units (eased -> snaps to `index`)
    var lastY = window.scrollY || 0, lastT = nowMs(), lastScrollT = 0, armed = true, raf = 0;

    function onScroll(){
      var y = window.scrollY || 0, t = nowMs();
      var dy = y - lastY;
      if (t - lastScrollT >= GESTURE_GAP){ armed = true; acc = 0; }   // a pause = a new gesture -> re-arm
      lastY = y; lastT = t; lastScrollT = t;

      var runway = Math.max(1, section.offsetHeight - window.innerHeight);
      var pPos = clamp01((-section.getBoundingClientRect().top) / runway);
      if (pPos <= 0){ index = 0; acc = 0; armed = true; }
      else if (pPos >= 1){ index = N - 1; acc = 0; armed = true; }
      else if (armed){
        var CP = commitPx();
        acc = clamp(acc + dy, -1.3 * CP, 1.3 * CP);      // accumulate (only while this gesture can still commit)
        if (acc >=  CP && index < N-1){ index++; acc = 0; armed = false; }   // commit once, then this gesture is spent
        else if (acc <= -CP && index > 0){ index--; acc = 0; armed = false; }
        if (index === N-1 && acc > 0) acc = 0;           // can't over-drag past the last / first cover
        if (index === 0   && acc < 0) acc = 0;
      }
      startRaf();
    }

    function animate(){
      var t = nowMs(), active = (t - lastScrollT) < 90, CP = commitPx();
      if (!active){ acc += (0 - acc) * 0.20; if (Math.abs(acc) < 0.5) acc = 0; }  // settle: snap the preview back
      var dragFrac = clamp(acc / CP, -1, 1) * PREVIEW;    // covers slide a little while dragging
      var target = index + dragFrac;
      display += (target - display) * EASE;
      if (Math.abs(display - target) < 0.0006) display = target;
      var holeH = holeEl ? holeEl.offsetHeight : window.innerHeight * 0.66;
      strip.style.transform = 'translateY(' + (-display * holeH).toFixed(2) + 'px)';
      if (index !== idxShown){ renderText(index, idxShown !== -1); idxShown = index; }
      if (active || Math.abs(acc) > 0.5 || Math.abs(display - target) > 0.0006){ raf = requestAnimationFrame(animate); }
      else { raf = 0; }
    }
    function startRaf(){ if (!raf) raf = requestAnimationFrame(animate); }

    function settle(){ display = index; strip.style.transform = 'translateY(' + (-display*(holeEl?holeEl.offsetHeight:0)).toFixed(2) + 'px)'; }

    layout(); renderText(0, false); idxShown = 0; settle();
    window.addEventListener('scroll', onScroll, { passive:true });
    window.addEventListener('resize', function(){ layout(); settle(); });
    window.addEventListener('load', function(){ layout(); settle(); });
    if (mql.addEventListener) mql.addEventListener('change', function(){ layout(); settle(); });
    document.addEventListener('langchange', function(){ fillCaps(); renderText(index, false); });
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
    // State lives on <html> as data-* attributes and is persisted in localStorage,
    // so a setting chosen here carries to every page. The no-flash <head> script in
    // each HTML file applies the SAME attributes before first paint — keep the keys
    // below in sync with that script. The switches here only need wiring on this page
    // (it's the only one with the settings panel).
    var el = document.documentElement;
    function store(key, val) {
      try {
        if (val === null) localStorage.removeItem(key);
        else localStorage.setItem(key, val);
      } catch (e) { /* storage unavailable — the toggle still works for this visit */ }
    }

    var preCollege  = document.getElementById("toggle-pre-college");
    var readability = document.getElementById("toggle-readability");
    var colorblind  = document.getElementById("toggle-colorblind");
    var darkMode    = document.getElementById("toggle-dark-mode");

    // Reflect the already-applied state (from the <head> script) in each switch.
    if (preCollege)  preCollege.checked  = !el.hasAttribute("data-hide-precollege");
    if (readability) readability.checked = el.hasAttribute("data-readability");
    if (colorblind)  colorblind.checked  = el.hasAttribute("data-colorblind");
    if (darkMode)    darkMode.checked    = el.getAttribute("data-theme") === "dark";

    if (preCollege) preCollege.addEventListener("change", function () {
      if (preCollege.checked) { el.removeAttribute("data-hide-precollege"); store("viewShowPrecollege", "1"); }
      else                    { el.setAttribute("data-hide-precollege", "1"); store("viewShowPrecollege", "0"); }
    });

    if (readability) readability.addEventListener("change", function () {
      if (readability.checked) { el.setAttribute("data-readability", "1"); store("viewReadability", "1"); }
      else                     { el.removeAttribute("data-readability"); store("viewReadability", null); }
    });

    if (colorblind) colorblind.addEventListener("change", function () {
      if (colorblind.checked) { el.setAttribute("data-colorblind", "1"); store("viewColorblind", "1"); }
      else                    { el.removeAttribute("data-colorblind"); store("viewColorblind", null); }
    });

    if (darkMode) darkMode.addEventListener("change", function () {
      var theme = darkMode.checked ? "dark" : "light";
      el.setAttribute("data-theme", theme);
      store("viewTheme", theme);   // explicit choice overrides the OS default from here on
    });
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
