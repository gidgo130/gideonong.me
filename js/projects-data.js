// projects-data.js
// Single source of truth for projects.html §2 (featured) and §3 (index), the
// featured block on index.html, and the project sub-pages. There is no second
// array and no duplicated copy: `featured: true` promotes an entry into the
// featured blocks, and that same entry still appears in the index.
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
//   dates         language-neutral, rendered per language (CLAUDE.md → Dates):
//                   { from: { season: "summer", year: 2026 } }
//                   { from: { month: 7, year: 2022 } }
//                   { from: { year: 2025 } }
//                   { from: {…}, to: "present" }  or  { from: {…}, to: {…} }
//   sortDate      "YYYY-MM" — the ONLY thing ordering reads. Newest first. The
//                 dev check flags a sortDate that disagrees with `dates`
//                 (against `to` when it is a point, else `from`).
//   context       "industry" | "coursework" | "personal" | "service" | "research"
//                 Rendered in the meta line as "<Context> · <dates>" via the
//                 ctxIndustry / ctxCoursework / … i18n keys.
//   tags          tag IDS from js/tags-data.js (never labels). Every pill is a
//                 link to projects.html?tag=<id>.
//   imageSrc      "" is valid → the row renders with no thumbnail and the text
//                 occupying the full width. Never a broken image, a grey box,
//                 or a placeholder icon.
//   imageAlt      i18n key — required whenever imageSrc is set
//   subpageUrl    "/projects/<slug>.html" once the page file exists, else ""
//                 → the "View project →" link is omitted. The dev check HEADs
//                 each non-empty value (localhost only).
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
//                              entry stays here so its sub-page renders, but it
//                              never appears in any listing.
//                 "hidden"   → excluded everywhere; its sub-page renders only
//                              on localhost.
//                 "nested"   → RESERVED, not implemented. An entry set to it
//                              does not render and the dev check warns.
//   experience    slug of the js/experience-data.js entry this project belongs
//                 to, or "". Set → the row/featured block/sub-page shows a
//                 "Part of: <role>, <org> →" link to experience.html#<slug>,
//                 and the band lists this project under "Projects from this
//                 role". The two-way link is derived from this one field.
//   homeLayout    OPTIONAL — how the entry renders in the index.html featured
//                 block only (projects.html §2 keeps its alternating layout):
//                   "stacked"    (default) full-width 16:9 image, text below
//                   "imageLeft"  image ~55% left, text right
//                   "imageRight" text left, image right
//                   "collage"    full-width 16:9 grid of imageSrc + gallery
//                 Fallbacks: collage with no usable gallery → stacked; any
//                 preset with no imageSrc → text only.
//   gallery       OPTIONAL, collage only — 1–3 EXTRA images after imageSrc:
//                 [{ src: "", altKey: "" }]. altKey is an i18n key
//                 (proj<SlugCamel>Gallery<N>Alt). Ignored on other presets.
//   page          OPTIONAL — sub-page content (js/project-page.js). Every
//                 part is optional; a missing part renders nothing:
//                   sections:  [{ headingKey, bodyKey }]   proj<SlugCamel>Section<N>Heading / Body
//                   facts:     [{ labelKey, valueKey }]    proj<SlugCamel>Fact<N>Label / Value
//                   photos:    [{ src, altKey }]           proj<SlugCamel>Photo<N>Alt
//                   reportPdf: "assets/pdfs/projects/….pdf"  "Read the report" link, new tab
//                   creditKey: ""                          proj<SlugCamel>Credit
//                 `gallery` stays collage-only; sub-page photos use page.photos.
//
// SCAFFOLD NOTE: every entry below is a PLACEHOLDER. No real project content is
// recorded here yet — titles, descriptions, dates, tags, and images all arrive
// from the projects content interview (plan.md open decisions #2 and #3). Every
// placeholder string is prefixed "TODO " in both languages so it stays greppable.
// The sortDate / dates / context / experience values below are stand-ins chosen
// to exercise each render path, not facts. Every subpageUrl except
// todo-project-2's is "" because no other page file exists.

const projectsData = [
  {
    slug: "todo-project-1",
    titleKey: "projTodoProject1Title",
    descKey: "projTodoProject1Desc",
    longDescKey: "projTodoProject1LongDesc",
    dates: { from: { season: "summer", year: 2026 } },
    sortDate: "2026-06",
    context: "coursework",
    tags: ["todo-a", "todo-b"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject1Alt",
    subpageUrl: "",
    featured: true,
    pinned: true,
    searchTextKey: "projTodoProject1Search",
    listing: "index",
    experience: "",
    // Home featured preset: the default, spelled out so the scaffold shows one
    // stacked and one collage entry.
    homeLayout: "stacked"
  },
  {
    // The SUB-PAGE scaffold. listing: "hidden" so neither this entry nor any
    // link to projects/todo-project-2.html can appear on the live site; the
    // page itself renders on localhost only (js/project-page.js). Linked to
    // Baker Hughes so the sub-page "Part of" link is exercised. Carries a full
    // `page` object with fake sections, facts, photos, report and credit.
    slug: "todo-project-2",
    titleKey: "projTodoProject2Title",
    descKey: "projTodoProject2Desc",
    longDescKey: "projTodoProject2LongDesc",
    dates: { from: { season: "spring", year: 2026 } },
    sortDate: "2026-05",
    context: "industry",
    tags: ["todo-b", "todo-c"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject2Alt",
    subpageUrl: "/projects/todo-project-2.html",
    featured: false,
    pinned: false,
    searchTextKey: "projTodoProject2Search",
    listing: "hidden",
    experience: "baker-hughes",
    page: {
      sections: [
        { headingKey: "projTodoProject2Section1Heading", bodyKey: "projTodoProject2Section1Body" },
        { headingKey: "projTodoProject2Section2Heading", bodyKey: "projTodoProject2Section2Body" }
      ],
      facts: [
        { labelKey: "projTodoProject2Fact1Label", valueKey: "projTodoProject2Fact1Value" },
        { labelKey: "projTodoProject2Fact2Label", valueKey: "projTodoProject2Fact2Value" },
        { labelKey: "projTodoProject2Fact3Label", valueKey: "projTodoProject2Fact3Value" }
      ],
      photos: [
        { src: "assets/images/placeholder.jpg", altKey: "projTodoProject2Photo1Alt" },
        { src: "assets/images/book-placeholder-1.jpg", altKey: "projTodoProject2Photo2Alt" },
        { src: "assets/images/book-placeholder-2.jpg", altKey: "projTodoProject2Photo3Alt" }
      ],
      reportPdf: "assets/pdfs/projects/paint-sprayer-pump-failure-analysis.pdf",
      creditKey: "projTodoProject2Credit"
    }
  },
  {
    // Linked to the Baker Hughes role: this is the featured-block "Part of"
    // test case, and it appears under the Baker Hughes band on experience.html.
    // Home featured preset: collage of imageSrc + two extra placeholder images
    // (three cells → large left, two stacked right; large on top below 768px).
    slug: "todo-project-3",
    titleKey: "projTodoProject3Title",
    descKey: "projTodoProject3Desc",
    longDescKey: "projTodoProject3LongDesc",
    dates: { from: { month: 2, year: 2026 }, to: { month: 4, year: 2026 } },
    sortDate: "2026-04",
    context: "research",
    tags: ["todo-a", "todo-c", "todo-d"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject3Alt",
    subpageUrl: "",
    featured: true,
    pinned: false,
    searchTextKey: "projTodoProject3Search",
    listing: "index",
    experience: "baker-hughes",
    homeLayout: "collage",
    gallery: [
      { src: "assets/images/book-placeholder-1.jpg", altKey: "projTodoProject3Gallery1Alt" },
      { src: "assets/images/placeholder.jpg", altKey: "projTodoProject3Gallery2Alt" }
    ]
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
    dates: { from: { month: 3, year: 2026 } },
    sortDate: "2026-03",
    context: "industry",
    tags: ["todo-d"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projTodoProject4Search",
    listing: "index",
    experience: "baker-hughes"
  },
  {
    // No sub-page yet — subpageUrl is "" so the "View project →" link is
    // omitted rather than rendered as a dead link. Year-only date.
    slug: "todo-project-5",
    titleKey: "projTodoProject5Title",
    descKey: "projTodoProject5Desc",
    longDescKey: "projTodoProject5LongDesc",
    dates: { from: { year: 2026 } },
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
    dates: { from: { season: "fall", year: 2025 }, to: { season: "spring", year: 2026 } },
    sortDate: "2026-01",
    context: "service",
    tags: ["todo-e", "todo-f"],
    imageSrc: "assets/images/placeholder.jpg",
    imageAlt: "projTodoProject6Alt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projTodoProject6Search",
    listing: "unlisted",
    experience: "baker-hughes"
  }
];
