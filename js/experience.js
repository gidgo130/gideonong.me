// experience.js
// Renders §2 experience cards from js/experience-data.js, re-rendering on
// language change, and fades each card in on scroll (IntersectionObserver,
// opacity 0→1, no movement — standard CLAUDE.md rule, no carve-out here).

(function () {
  var list = document.getElementById("experience-list");
  if (!list || typeof experienceData === "undefined") return;

  function currentLang() {
    return document.documentElement.getAttribute("lang") === "es" ? "es" : "en";
  }

  function text(key) {
    var dict = translations[currentLang()];
    return (dict && dict[key] !== undefined) ? dict[key] : key;
  }

  function buildCard(entry) {
    var card = document.createElement("article");
    card.className = "exp-card";

    var img = document.createElement("img");
    img.className = "exp-card-image";
    img.src = entry.imageSrc;
    img.alt = text(entry.roleKey) + " — " + text(entry.orgKey);
    card.appendChild(img);

    var body = document.createElement("div");
    body.className = "exp-card-body";

    var role = document.createElement("h2");
    role.className = "exp-card-role";
    role.setAttribute("data-i18n", entry.roleKey);
    role.textContent = text(entry.roleKey);
    body.appendChild(role);

    var meta = document.createElement("p");
    meta.className = "exp-card-meta";
    var org = document.createElement("span");
    org.setAttribute("data-i18n", entry.orgKey);
    org.textContent = text(entry.orgKey);
    meta.appendChild(org);
    meta.appendChild(document.createTextNode(" · " + entry.dates));
    body.appendChild(meta);

    var bullets = document.createElement("ul");
    bullets.className = "exp-card-bullets";
    entry.bulletKeys.forEach(function (key) {
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

    var link = document.createElement("a");
    link.className = "exp-card-link";
    link.href = entry.subpageUrl;
    link.setAttribute("data-i18n", "expCaseStudyLink");
    link.textContent = text("expCaseStudyLink");
    body.appendChild(link);

    card.appendChild(body);
    return card;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  function render() {
    list.innerHTML = "";
    experienceData
      .filter(function (entry) { return entry.visible; })
      .forEach(function (entry) {
        var card = buildCard(entry);
        list.appendChild(card);
        observer.observe(card);
      });
  }

  document.addEventListener("langchange", render);
  render();
}());
