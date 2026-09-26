// projects-data.js
// Single source of truth for projects.html §2 (featured) and §3 (index), AND
// for the featured block on index.html. There is no second array and no
// duplicated copy: `featured: true` promotes an entry into the featured blocks,
// and that same entry still appears in the index.
//
// ARRAY ORDER DOES NOT MATTER. Display order is sortDate descending, with
// `pinned: true` lifting an entry to the top of the index. Reordering this
// file changes nothing.
//
// SCHEMA (see plan.md → Page Spec — projects.html → Maintainability, and
// CLAUDE.md → Data conventions):
//   slug          URL slug → /projects/<slug>.html. Also the index row's id, so
//                 projects.html#<slug> deep-links to the row. Must be unique.
//   titleKey      i18n key → EN + ES. Per-entry keys are named by slug:
//   descKey         proj<SlugCamel>Title / Desc / LongDesc / Alt / Search
//   longDescKey     (e.g. slug "todo-project-1" → projTodoProject1Title).
//   dates         literal display string, never translated
//   sortDate      "YYYY-MM" — the ONLY thing ordering reads. Newest first.
//   context       "industry" | "coursework" | "personal" | "service" | "research"
//                 Rendered in the meta line as "<Context> · <dates>" via the
//                 ctxIndustry / ctxCoursework / … i18n keys.
//   tags          tag IDS from js/tags-data.js (never labels)
//   imageSrc      "" is valid → the row renders with no thumbnail and the text
//                 occupying the full width. Never a broken image, a grey box,
//                 or a placeholder icon.
//   imageAlt      i18n key — required whenever imageSrc is set
//   subpageUrl    "" = no sub-page yet → the "View project →" link is omitted
//   featured      true → ALSO rendered in the featured blocks (still in the
//                 index). Only honoured on listing: "index". Max 3.
//   pinned        true → lifted to the top of the index, independently of
//                 `featured` and of sortDate
//   searchTextKey i18n key — EN + ES blob folded into the search corpus. Never
//                 displayed.
//   listing       "index"    → in the index, the tag filter, search, its role's
//                              "Projects from this role" list; may be featured
//                 "unlisted" → direct URL only. Excluded from the index, bands,
//                              filter, featured and search. This is how the
//                              "unlinked pages" decision is implemented — the
//                              entry stays here so its sub-page can be
//                              generated, but it never appears in any listing.
//                 "hidden"   → excluded everywhere
//                 "nested"   → RESERVED, not implemented. An entry set to it
//                              does not render and the dev check warns.
//   experience    slug of the js/experience-data.js entry this project belongs
//                 to, or "". Set → the row/featured block shows a
//                 "Part of: <role>, <org> →" link to experience.html#<slug>,
//                 and the band lists this project under "Projects from this
//                 role". The two-way link is derived from this one field.
//
// SCAFFOLD NOTE: every entry below is a PLACEHOLDER. No real project content is
// recorded here yet — titles, descriptions, dates, tags, and images all arrive
// from the projects content interview (plan.md open decisions #2 and #3). Every
// placeholder string is prefixed "TODO " in both languages so it stays greppable.
// The sortDate / context / experience values below are stand-ins chosen to
// exercise each render path, not facts.

const projectsData = [
  {
    slug: "todo-project-1",
    titleKey: "projTodoProject1Title",
    descKey: "projTodoProject1Desc",
    longDescKey: "projTodoProject1LongDesc",
    dates: "TODO dates",
    sortDate: "2026-06",
    context: "coursework",
    tags: ["todo-a", "todo-b"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject1Alt",
    subpageUrl: "/projects/todo-project-1.html",
    featured: true,
    pinned: true,
    searchTextKey: "projTodoProject1Search",
    listing: "index",
    experience: ""
  },
  {
    // Linked to the Baker Hughes role: this is the featured-block "Part of"
    // test case, and it appears under the Baker Hughes band on experience.html.
    slug: "todo-project-2",
    titleKey: "projTodoProject2Title",
    descKey: "projTodoProject2Desc",
    longDescKey: "projTodoProject2LongDesc",
    dates: "TODO dates",
    sortDate: "2026-05",
    context: "industry",
    tags: ["todo-b", "todo-c"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject2Alt",
    subpageUrl: "/projects/todo-project-2.html",
    featured: true,
    pinned: false,
    searchTextKey: "projTodoProject2Search",
    listing: "index",
    experience: "baker-hughes"
  },
  {
    slug: "todo-project-3",
    titleKey: "projTodoProject3Title",
    descKey: "projTodoProject3Desc",
    longDescKey: "projTodoProject3LongDesc",
    dates: "TODO dates",
    sortDate: "2026-04",
    context: "research",
    tags: ["todo-a", "todo-c", "todo-d"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject3Alt",
    subpageUrl: "/projects/todo-project-3.html",
    featured: false,
    pinned: false,
    searchTextKey: "projTodoProject3Search",
    listing: "index",
    experience: ""
  },
  {
    // No photograph for this one — imageSrc is deliberately "". The row renders
    // text-only at full width (see .project-row--no-image in style.css). This
    // case is in the scaffold on purpose: the index must degrade cleanly for
    // entries that will never have a good photo. Also the second Baker Hughes
    // link — an index-only (not featured) row with the "Part of" link.
    slug: "todo-project-4",
    titleKey: "projTodoProject4Title",
    descKey: "projTodoProject4Desc",
    longDescKey: "projTodoProject4LongDesc",
    dates: "TODO dates",
    sortDate: "2026-03",
    context: "industry",
    tags: ["todo-d"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "/projects/todo-project-4.html",
    featured: false,
    pinned: false,
    searchTextKey: "projTodoProject4Search",
    listing: "index",
    experience: "baker-hughes"
  },
  {
    // No sub-page yet — subpageUrl is "" so the "View project →" link is
    // omitted rather than rendered as a dead link.
    slug: "todo-project-5",
    titleKey: "projTodoProject5Title",
    descKey: "projTodoProject5Desc",
    longDescKey: "projTodoProject5LongDesc",
    dates: "TODO dates",
    sortDate: "2026-02",
    context: "personal",
    tags: ["todo-b", "todo-e"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject5Alt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projTodoProject5Search",
    listing: "index",
    experience: ""
  },
  {
    // Unlisted — the "unlinked pages" case. It lives here so its sub-page can
    // exist, but it must never show up in the index, the filter, search, the
    // featured blocks, or (despite the experience link) the Baker Hughes band.
    slug: "todo-project-6",
    titleKey: "projTodoProject6Title",
    descKey: "projTodoProject6Desc",
    longDescKey: "projTodoProject6LongDesc",
    dates: "TODO dates",
    sortDate: "2026-01",
    context: "service",
    tags: ["todo-e", "todo-f"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject6Alt",
    subpageUrl: "/projects/todo-project-6.html",
    featured: false,
    pinned: false,
    searchTextKey: "projTodoProject6Search",
    listing: "unlisted",
    experience: "baker-hughes"
  }
];
