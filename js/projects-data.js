// projects-data.js
// Single source of truth for BOTH §2 (featured) and §3 (index) of projects.html.
// There is no second array and no duplicated copy: `featured: true` promotes an
// entry into §2, and that same entry still appears in §3.
// Reorder entries to change display order; `visible: false` hides one without
// deleting it. titleKey / descKey / longDescKey / imageAlt / searchTextKey all
// map to strings in js/translations.js.
//
// SCHEMA (see plan.md → Page Spec — projects.html → Maintainability):
//   slug          URL slug → /projects/[slug].html
//   titleKey      i18n key → EN + ES
//   descKey       i18n key — one line, used in the §3 index row
//   longDescKey   i18n key — fuller paragraph, used in §2 featured + sub-page
//   dates         literal, never translated
//   tags          MUST come from PROJECT_TAGS below
//   imageSrc      "" is valid → the row renders with no thumbnail and the text
//                 occupying the full width. Never a broken image, a grey box,
//                 or a placeholder icon.
//   imageAlt      i18n key — required whenever imageSrc is set
//   subpageUrl    "" = no sub-page yet → the "View project →" link is omitted
//   featured      true → ALSO rendered in §2 (still rendered in §3)
//   pinned        true → lifted to the top of §3, independently of `featured`
//   searchTextKey i18n key — EN + ES blob indexed by the Phase 3 search. Unused
//                 today: the §1 search band ships hidden and inert.
//   visible       false → hidden from both §2 and §3 without deleting the entry
//   unlisted      true → reachable by direct URL only; excluded from §2, §3 and
//                 search. This is how the "unlinked pages" decision is
//                 implemented — the entry stays here so its sub-page can be
//                 generated, but it never appears in any listing.
//
// SCAFFOLD NOTE: every entry below is a PLACEHOLDER. No real project content is
// recorded here yet — titles, descriptions, dates, tags, and images all arrive
// from the projects content interview (plan.md open decisions #2 and #3). Every
// placeholder string is prefixed "TODO " in both languages so it stays greppable.

// Controlled tag vocabulary — defined ONCE, here, and nowhere else. Entries may
// only use tags from this list, and the §3 filter row is built from it (in this
// order). This is what keeps "CAD" / "cad" / "SolidWorks" from fragmenting the
// filter into three pills that each match a third of the work.
//
// Tags are literal strings, not i18n keys — same convention as
// js/experience-data.js. If the real vocabulary turns out to need translating,
// that is a deliberate change to both files, not something to do by halves.
//
// TODO: replace with the real vocabulary drafted in the content interview.
// plan.md open decision #2 also asks whether experience.html should draw from
// this same list instead of its current free-form tags.
const PROJECT_TAGS = [
  "TODO Tag A",
  "TODO Tag B",
  "TODO Tag C",
  "TODO Tag D",
  "TODO Tag E",
  "TODO Tag F"
];

const projectsData = [
  {
    slug: "todo-project-1",
    titleKey: "proj1Title",
    descKey: "proj1Desc",
    longDescKey: "proj1LongDesc",
    dates: "TODO dates",
    tags: ["TODO Tag A", "TODO Tag B"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "proj1Alt",
    subpageUrl: "/projects/todo-project-1.html",
    featured: true,
    pinned: true,
    searchTextKey: "proj1Search",
    visible: true,
    unlisted: false
  },
  {
    slug: "todo-project-2",
    titleKey: "proj2Title",
    descKey: "proj2Desc",
    longDescKey: "proj2LongDesc",
    dates: "TODO dates",
    tags: ["TODO Tag B", "TODO Tag C"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "proj2Alt",
    subpageUrl: "/projects/todo-project-2.html",
    featured: true,
    pinned: false,
    searchTextKey: "proj2Search",
    visible: true,
    unlisted: false
  },
  {
    slug: "todo-project-3",
    titleKey: "proj3Title",
    descKey: "proj3Desc",
    longDescKey: "proj3LongDesc",
    dates: "TODO dates",
    tags: ["TODO Tag A", "TODO Tag C", "TODO Tag D"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "proj3Alt",
    subpageUrl: "/projects/todo-project-3.html",
    featured: false,
    pinned: false,
    searchTextKey: "proj3Search",
    visible: true,
    unlisted: false
  },
  {
    // No photograph for this one — imageSrc is deliberately "". The row renders
    // text-only at full width (see .project-row--no-image in style.css). This
    // case is in the scaffold on purpose: the index must degrade cleanly for
    // entries that will never have a good photo.
    slug: "todo-project-4",
    titleKey: "proj4Title",
    descKey: "proj4Desc",
    longDescKey: "proj4LongDesc",
    dates: "TODO dates",
    tags: ["TODO Tag D"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "/projects/todo-project-4.html",
    featured: false,
    pinned: false,
    searchTextKey: "proj4Search",
    visible: true,
    unlisted: false
  },
  {
    // No sub-page yet — subpageUrl is "" so the "View project →" link is
    // omitted rather than rendered as a dead link.
    slug: "todo-project-5",
    titleKey: "proj5Title",
    descKey: "proj5Desc",
    longDescKey: "proj5LongDesc",
    dates: "TODO dates",
    tags: ["TODO Tag B", "TODO Tag E"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "proj5Alt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "proj5Search",
    visible: true,
    unlisted: false
  },
  {
    slug: "todo-project-6",
    titleKey: "proj6Title",
    descKey: "proj6Desc",
    longDescKey: "proj6LongDesc",
    dates: "TODO dates",
    tags: ["TODO Tag E", "TODO Tag F"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "proj6Alt",
    subpageUrl: "/projects/todo-project-6.html",
    featured: false,
    pinned: false,
    searchTextKey: "proj6Search",
    visible: true,
    unlisted: false
  }
];
