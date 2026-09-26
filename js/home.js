// home.js
// index.html "Featured work": renders every js/projects-data.js entry with
// featured: true AND listing: "index", using the same builders and markup as
// projects.html §2 (js/data-helpers.js → siteData.buildFeatured), including the
// "Part of: <role>, <org> →" link. A project's copy exists in exactly one place.
//
// Scroll-triggered fade only (IntersectionObserver, opacity 0→1, no movement).

(function () {
  var list = document.getElementById("home-featured");
  if (!list || typeof siteData === "undefined") return;

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  function render() {
    observer.disconnect();
    list.innerHTML = "";
    siteData.featuredProjects().forEach(function (entry, i) {
      var article = siteData.buildFeatured(entry, i);
      list.appendChild(article);
      observer.observe(article);
    });
  }

  document.addEventListener("langchange", render);
  render();
}());
