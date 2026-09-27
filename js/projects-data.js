// projects-data.js
// Single source of truth for projects.html §2 (featured) and §3 (index), the
// featured block on index.html, and the project sub-pages. There is no second
// array and no duplicated copy: `featured: true` promotes an entry into the
// featured blocks, and that same entry still appears in the index.
//
// ARRAY ORDER DOES NOT MATTER. Display order is sortDate descending, with
// `pinned: true` lifting an entry to the top of the index and `featuredOrder`
// ordering the featured blocks. Reordering this file changes nothing.
//
// SCHEMA (see plan.md → Page Spec — projects.html → Maintainability, and
// CLAUDE.md → Data conventions):
//   slug          URL slug → /projects/<slug>.html. Also the index row's id, so
//                 projects.html#<slug> deep-links to the row. Must be unique.
//   titleKey      i18n key → EN + ES. Per-entry keys are named by slug:
//   descKey         proj<SlugCamel>Title / Desc / LongDesc / Alt / Search
//   longDescKey     (e.g. slug "g-view" → projGViewTitle). longDescKey is the
//                 featured-card paragraph — required on featured entries, ""
//                 on index-only ones.
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
//   thumbSrc      OPTIONAL — index-row thumbnail; falls back to imageSrc
//   thumbAltKey   OPTIONAL i18n key for thumbSrc; falls back to imageAlt
//   subpageUrl    "/projects/<slug>.html" once the page file exists, else ""
//                 → the "View project →" link is omitted AND the entry's images
//                 stay plain (an image links to the sub-page only when one exists).
//                 → the "View project →" link is omitted. The dev check HEADs
//                 each non-empty value (localhost only).
//   featured      true → ALSO rendered in the featured blocks (still in the
//                 index). Only honoured on listing: "index". Max 3.
//   featuredOrder OPTIONAL number — order among the featured blocks (home and
//                 projects.html §2), ascending. Entries without it follow, by
//                 sortDate.
//   pinned        true → lifted to the top of the index, independently of
//                 `featured` and of sortDate
//   searchTextKey i18n key — EN + ES blob folded into the search corpus. Never
//                 displayed. Tool and method names that are not tags.
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
//                 "Part of: <org short> →" link to experience.html#<slug>, and
//                 the band lists this project under "Projects from this role".
//                 The two-way link is derived from this one field.
//   homeLayout    OPTIONAL — how the entry renders in the index.html featured
//                 block only (projects.html §2 keeps its alternating layout):
//                   "stacked"    (default) full-width 16:9 image, text below
//                   "imageLeft"  image ~55% left, text right
//                   "imageRight" text left, image right
//                   "collage"    full-width 16:9 grid of the `gallery` images
//                 Fallbacks: collage with fewer than 2 usable gallery items →
//                 stacked; stacked / imageLeft / imageRight with no imageSrc →
//                 text only.
//   gallery       OPTIONAL, collage only — the collage cells, 2–4 images:
//                 [{ src: "", altKey: "" }]. imageSrc is NOT a cell. altKey is
//                 an i18n key (proj<SlugCamel>Gallery<N>Alt). Ignored on other
//                 presets.
//   page          OPTIONAL — sub-page content (js/project-page.js). Every
//                 part is optional; a missing part renders nothing:
//                   sections:  [{ headingKey, bodyKey }]   proj<SlugCamel>Section<N>Heading / Body
//                   facts:     [{ labelKey, valueKey }]    proj<SlugCamel>Fact<N>Label / Value
//                   photos:    [{ src, altKey }]           proj<SlugCamel>Photo<N>Alt
//                   reportPdf: "assets/pdfs/projects/….pdf"  "Read the report" link, new tab
//                   creditKey: ""                          proj<SlugCamel>Credit
//                 `gallery` stays collage-only; sub-page photos use page.photos.
//
// Content loaded 2026-09-27 from staging/copy-en.md, copy-es.md,
// content-intake.md and image-manifest.md. Sort months with no explicit value
// in the intake were derived from the season (Velora, AutoScan 2026-07;
// Dynamics PDF Unifier 2026-09).

const projectsData = [
  /* ---- Featured ---------------------------------------------------------- */
  {
    slug: "pump-cylinder-failure",
    titleKey: "projPumpCylinderFailureTitle",
    descKey: "projPumpCylinderFailureDesc",
    longDescKey: "projPumpCylinderFailureLongDesc",
    dates: { from: { season: "spring", year: 2026 } },
    sortDate: "2026-05",
    context: "coursework",
    tags: ["solid-mechanics", "fabrication", "cad", "leadership"],
    imageSrc: "assets/images/projects/pump-cylinder-failure/pin-installed-wide.jpg",
    imageAlt: "projPumpCylinderFailureAlt",
    thumbSrc: "assets/images/projects/pump-cylinder-failure/pin-installed-thumb.jpg",
    thumbAltKey: "projPumpCylinderFailureAlt",
    subpageUrl: "/projects/pump-cylinder-failure.html",
    featured: true,
    featuredOrder: 1,
    pinned: false,
    searchTextKey: "projPumpCylinderFailureSearch",
    listing: "index",
    experience: "",
    homeLayout: "stacked",
    page: {
      sections: [
        { headingKey: "projPumpCylinderFailureSection1Heading", bodyKey: "projPumpCylinderFailureSection1Body" },
        { headingKey: "projPumpCylinderFailureSection2Heading", bodyKey: "projPumpCylinderFailureSection2Body" },
        { headingKey: "projPumpCylinderFailureSection3Heading", bodyKey: "projPumpCylinderFailureSection3Body" },
        { headingKey: "projPumpCylinderFailureSection4Heading", bodyKey: "projPumpCylinderFailureSection4Body" }
      ],
      facts: [
        { labelKey: "projPumpCylinderFailureFact1Label", valueKey: "projPumpCylinderFailureFact1Value" },
        { labelKey: "projPumpCylinderFailureFact2Label", valueKey: "projPumpCylinderFailureFact2Value" },
        { labelKey: "projPumpCylinderFailureFact3Label", valueKey: "projPumpCylinderFailureFact3Value" },
        { labelKey: "projPumpCylinderFailureFact4Label", valueKey: "projPumpCylinderFailureFact4Value" },
        { labelKey: "projPumpCylinderFailureFact5Label", valueKey: "projPumpCylinderFailureFact5Value" }
      ],
      photos: [
        { src: "assets/images/projects/pump-cylinder-failure/burst-and-cracked.jpg", altKey: "projPumpCylinderFailurePhoto1Alt" },
        { src: "assets/images/projects/pump-cylinder-failure/pin-on-lathe.jpg", altKey: "projPumpCylinderFailurePhoto2Alt" },
        { src: "assets/images/projects/pump-cylinder-failure/pin-installed.jpg", altKey: "projPumpCylinderFailurePhoto3Alt" },
        { src: "assets/images/projects/pump-cylinder-failure/work-van.jpg", altKey: "projPumpCylinderFailurePhoto4Alt" },
        { src: "assets/images/projects/pump-cylinder-failure/cracked-cylinder.jpg", altKey: "projPumpCylinderFailurePhoto5Alt" }
      ],
      reportPdf: "assets/pdfs/projects/paint-sprayer-pump-failure-analysis.pdf",
      creditKey: ""
    }
  },
  {
    slug: "eagle-pathway",
    titleKey: "projEaglePathwayTitle",
    descKey: "projEaglePathwayDesc",
    longDescKey: "projEaglePathwayLongDesc",
    dates: { from: { month: 7, year: 2022 } },
    sortDate: "2022-07",
    context: "service",
    tags: ["leadership", "fabrication"],
    imageSrc: "assets/images/projects/eagle-pathway/compacting-path.jpg",
    imageAlt: "projEaglePathwayAlt",
    thumbSrc: "assets/images/projects/eagle-pathway/finished-path.jpg",
    thumbAltKey: "projEaglePathwayGallery3Alt",
    subpageUrl: "/projects/eagle-pathway.html",
    featured: true,
    featuredOrder: 2,
    pinned: false,
    searchTextKey: "projEaglePathwaySearch",
    listing: "index",
    experience: "",
    // Home collage = exactly these three cells (imageSrc is not a cell).
    homeLayout: "collage",
    gallery: [
      { src: "assets/images/projects/eagle-pathway/directing-volunteers.jpg", altKey: "projEaglePathwayGallery1Alt" },
      { src: "assets/images/projects/eagle-pathway/granite-and-compactor.jpg", altKey: "projEaglePathwayGallery2Alt" },
      { src: "assets/images/projects/eagle-pathway/finished-path.jpg", altKey: "projEaglePathwayGallery3Alt" }
    ],
    page: {
      sections: [
        { headingKey: "projEaglePathwaySection1Heading", bodyKey: "projEaglePathwaySection1Body" },
        { headingKey: "projEaglePathwaySection2Heading", bodyKey: "projEaglePathwaySection2Body" },
        { headingKey: "projEaglePathwaySection3Heading", bodyKey: "projEaglePathwaySection3Body" },
        { headingKey: "projEaglePathwaySection4Heading", bodyKey: "projEaglePathwaySection4Body" }
      ],
      facts: [
        { labelKey: "projEaglePathwayFact1Label", valueKey: "projEaglePathwayFact1Value" },
        { labelKey: "projEaglePathwayFact2Label", valueKey: "projEaglePathwayFact2Value" },
        { labelKey: "projEaglePathwayFact3Label", valueKey: "projEaglePathwayFact3Value" },
        { labelKey: "projEaglePathwayFact4Label", valueKey: "projEaglePathwayFact4Value" },
        { labelKey: "projEaglePathwayFact5Label", valueKey: "projEaglePathwayFact5Value" },
        { labelKey: "projEaglePathwayFact6Label", valueKey: "projEaglePathwayFact6Value" }
      ],
      photos: [
        { src: "assets/images/projects/eagle-pathway/granite-and-compactor.jpg", altKey: "projEaglePathwayPhoto1Alt" },
        { src: "assets/images/projects/eagle-pathway/finished-path.jpg", altKey: "projEaglePathwayPhoto2Alt" },
        { src: "assets/images/projects/eagle-pathway/group.jpg", altKey: "projEaglePathwayPhoto3Alt" }
      ],
      reportPdf: "",
      creditKey: "projEaglePathwayCredit"
    }
  },
  {
    slug: "g-view",
    titleKey: "projGViewTitle",
    descKey: "projGViewDesc",
    longDescKey: "projGViewLongDesc",
    dates: { from: { season: "summer", year: 2026 } },
    sortDate: "2026-07",
    context: "industry",
    tags: ["python", "data-analysis", "automation", "machine-learning"],
    imageSrc: "assets/images/projects/g-view/g-view-demo.png",
    imageAlt: "projGViewAlt",
    thumbSrc: "assets/images/projects/g-view/g-view-thumb.png",
    thumbAltKey: "projGViewAlt",
    subpageUrl: "/projects/g-view.html",
    featured: true,
    featuredOrder: 3,
    pinned: false,
    searchTextKey: "projGViewSearch",
    listing: "index",
    experience: "baker-hughes",
    homeLayout: "imageRight",
    page: {
      sections: [
        { headingKey: "projGViewSection1Heading", bodyKey: "projGViewSection1Body" },
        { headingKey: "projGViewSection2Heading", bodyKey: "projGViewSection2Body" },
        { headingKey: "projGViewSection3Heading", bodyKey: "projGViewSection3Body" },
        { headingKey: "projGViewSection4Heading", bodyKey: "projGViewSection4Body" }
      ],
      facts: [
        { labelKey: "projGViewFact1Label", valueKey: "projGViewFact1Value" },
        { labelKey: "projGViewFact2Label", valueKey: "projGViewFact2Value" },
        { labelKey: "projGViewFact3Label", valueKey: "projGViewFact3Value" }
      ],
      photos: [],
      reportPdf: "",
      creditKey: ""
    }
  },

  /* ---- Index ------------------------------------------------------------- */
  {
    slug: "velora",
    titleKey: "projVeloraTitle",
    descKey: "projVeloraDesc",
    longDescKey: "",
    dates: { from: { season: "summer", year: 2026 } },
    sortDate: "2026-07",
    context: "industry",
    tags: ["python", "automation", "data-analysis"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projVeloraSearch",
    listing: "index",
    experience: "baker-hughes"
  },
  {
    slug: "autoscan",
    titleKey: "projAutoscanTitle",
    descKey: "projAutoscanDesc",
    longDescKey: "",
    dates: { from: { season: "summer", year: 2026 } },
    sortDate: "2026-07",
    context: "industry",
    tags: ["python", "automation", "fabrication"],
    imageSrc: "assets/images/projects/autoscan/scanner-station.jpg",
    imageAlt: "projAutoscanAlt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projAutoscanSearch",
    listing: "index",
    experience: "baker-hughes"
  },
  {
    slug: "dynamics-pdf-unifier",
    titleKey: "projDynamicsPdfUnifierTitle",
    descKey: "projDynamicsPdfUnifierDesc",
    longDescKey: "",
    dates: { from: { season: "fall", year: 2026 } },
    sortDate: "2026-09",
    context: "personal",
    tags: ["python", "automation"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projDynamicsPdfUnifierSearch",
    listing: "index",
    experience: "schultz-grader"
  },
  {
    slug: "keplinger-heating",
    titleKey: "projKeplingerHeatingTitle",
    descKey: "projKeplingerHeatingDesc",
    longDescKey: "",
    dates: { from: { season: "spring", year: 2026 } },
    sortDate: "2026-05",
    context: "coursework",
    tags: ["python", "thermo-fluids"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projKeplingerHeatingSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "music-notes-matlab",
    titleKey: "projMusicNotesMatlabTitle",
    descKey: "projMusicNotesMatlabDesc",
    longDescKey: "",
    dates: { from: { season: "spring", year: 2026 } },
    sortDate: "2026-05",
    context: "coursework",
    tags: ["matlab", "data-analysis"],
    imageSrc: "assets/images/projects/music-notes-matlab/trumpet-notes.png",
    imageAlt: "projMusicNotesMatlabAlt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projMusicNotesMatlabSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "gender-employment-cs",
    titleKey: "projGenderEmploymentCsTitle",
    descKey: "projGenderEmploymentCsDesc",
    longDescKey: "",
    dates: { from: { season: "spring", year: 2026 } },
    sortDate: "2026-05",
    context: "coursework",
    tags: ["data-analysis"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projGenderEmploymentCsSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "chilled-water-pipeline",
    titleKey: "projChilledWaterPipelineTitle",
    descKey: "projChilledWaterPipelineDesc",
    longDescKey: "",
    dates: { from: { season: "fall", year: 2025 } },
    sortDate: "2025-12",
    context: "coursework",
    tags: ["python", "thermo-fluids"],
    imageSrc: "assets/images/projects/chilled-water-pipeline/route-a.jpg",
    imageAlt: "projChilledWaterPipelineAlt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projChilledWaterPipelineSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "notched-beam-stress-relief",
    titleKey: "projNotchedBeamStressReliefTitle",
    descKey: "projNotchedBeamStressReliefDesc",
    longDescKey: "",
    dates: { from: { season: "fall", year: 2025 } },
    sortDate: "2025-12",
    context: "coursework",
    tags: ["cad", "solid-mechanics"],
    imageSrc: "assets/images/projects/notched-beam-stress-relief/fea-spline.png",
    imageAlt: "projNotchedBeamStressReliefAlt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projNotchedBeamStressReliefSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "diesel-dual-cycle",
    titleKey: "projDieselDualCycleTitle",
    descKey: "projDieselDualCycleDesc",
    longDescKey: "",
    dates: { from: { season: "fall", year: 2025 } },
    sortDate: "2025-11",
    context: "coursework",
    tags: ["python", "thermo-fluids"],
    imageSrc: "assets/images/projects/diesel-dual-cycle/pv-diagram.png",
    imageAlt: "projDieselDualCycleAlt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projDieselDualCycleSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "mechanical-fuse",
    titleKey: "projMechanicalFuseTitle",
    descKey: "projMechanicalFuseDesc",
    longDescKey: "",
    dates: { from: { season: "fall", year: 2025 } },
    sortDate: "2025-10",
    context: "coursework",
    tags: ["solid-mechanics", "cad"],
    imageSrc: "assets/images/projects/mechanical-fuse/broken-links.jpg",
    imageAlt: "projMechanicalFuseAlt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projMechanicalFuseSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "bicycle-crash-severity",
    titleKey: "projBicycleCrashSeverityTitle",
    descKey: "projBicycleCrashSeverityDesc",
    longDescKey: "",
    dates: { from: { season: "spring", year: 2025 } },
    sortDate: "2025-05",
    context: "coursework",
    tags: ["python", "machine-learning", "transportation"],
    imageSrc: "assets/images/projects/bicycle-crash-severity/shap.png",
    imageAlt: "projBicycleCrashSeverityAlt",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projBicycleCrashSeveritySearch",
    listing: "index",
    experience: ""
  },
  {
    // Gideon's favorite ML project — pinned to the top of the index.
    slug: "uk-crash-hotspots",
    titleKey: "projUkCrashHotspotsTitle",
    descKey: "projUkCrashHotspotsDesc",
    longDescKey: "",
    dates: { from: { season: "spring", year: 2025 } },
    sortDate: "2025-04",
    context: "coursework",
    tags: ["python", "machine-learning", "transportation", "data-analysis"],
    imageSrc: "assets/images/projects/uk-crash-hotspots/qgis-england.jpg",
    imageAlt: "projUkCrashHotspotsAlt",
    subpageUrl: "",
    featured: false,
    pinned: true,
    searchTextKey: "projUkCrashHotspotsSearch",
    listing: "index",
    experience: ""
  },
  {
    slug: "landmine-classification",
    titleKey: "projLandmineClassificationTitle",
    descKey: "projLandmineClassificationDesc",
    longDescKey: "",
    dates: { from: { season: "spring", year: 2025 } },
    sortDate: "2025-03",
    context: "coursework",
    tags: ["python", "machine-learning"],
    imageSrc: "",
    imageAlt: "",
    subpageUrl: "",
    featured: false,
    pinned: false,
    searchTextKey: "projLandmineClassificationSearch",
    listing: "index",
    experience: ""
  }
];
