// home.js
// index.html "Featured work": renders every js/projects-data.js entry with
// featured: true AND listing: "index", using the same builders and markup as
// projects.html §2 (js/data-helpers.js → siteData.buildFeatured), including the
// "Part of: <org> →" link. A project's copy exists in exactly one place.
//
// Layout is per project: entry.homeLayout ("stacked" | "imageLeft" |
// "imageRight" | "collage"), default "stacked" — full-width 16:9 image, text
// below. projects.html §2 ignores homeLayout and keeps its alternation.
//
// Wide-screen option (js/site-config.js → SITE_CONFIG.homeFeaturedSideBySide):
// when true the list gets .featured-list--side-by-side and the entries
// alternate imageLeft / imageRight; style.css applies the two columns at
// 1200px and wider only and stacks them below that. Default off.
//
// Scroll-triggered fade only (IntersectionObserver, opacity 0→1, no movement).

(function () {
  var list = document.getElementById("home-featured");
  if (!list || typeof siteData === "undefined") return;

  var sideBySide = (typeof SITE_CONFIG !== "undefined") && !!SITE_CONFIG.homeFeaturedSideBySide;
  list.classList.toggle("featured-list--side-by-side", sideBySide);

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
      var layout = entry.homeLayout || "stacked";
      if (sideBySide) {
        // Collage keeps its grid (it is the image column); everything else
        // alternates. Text-only entries fall out of the preset naturally.
        layout = layout === "collage" ? "collage" : (i % 2 === 0 ? "imageLeft" : "imageRight");
      }
      var article = siteData.buildFeatured(entry, i, { layout: layout });
      if (sideBySide && layout === "collage") {
        article.classList.add(i % 2 === 0 ? "featured-entry--side-left" : "featured-entry--side-right");
      }
      list.appendChild(article);
      observer.observe(article);
    });
  }

  document.addEventListener("langchange", render);
  render();
}());
