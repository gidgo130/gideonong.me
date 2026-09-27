// site-config.js
// Author-side switches. Loaded on index.html before js/home.js. No visitor UI.
//
//   homeFeaturedSideBySide  false (default) → every home featured entry uses
//                           its own `homeLayout` preset from js/projects-data.js
//                           (stacked / imageLeft / imageRight / collage).
//                           true → at 1200px and wider the entries alternate
//                           image-left / image-right (a collage entry keeps its
//                           grid in the image column); below 1200px they
//                           stack, image above text, whatever the preset says.
//                           Flip it here; nothing else changes.
const SITE_CONFIG = {
  homeFeaturedSideBySide: false
};
