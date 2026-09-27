// experience-data.js
// Data array driving §2 of experience.html. Set visible: false to hide an
// entry without deleting it. roleKey / orgKey / bulletKeys map to strings in
// js/translations.js.
//
// ARRAY ORDER DOES NOT MATTER. Bands render in sortDate descending order.
//
// SCHEMA (see plan.md → Page Spec — experience.html → §2, and CLAUDE.md →
// Data conventions):
//   slug     Unique id for the role. The band gets id="<slug>" so
//            experience.html#<slug> deep-links to it, and a project in
//            js/projects-data.js points here with `experience: "<slug>"`. Per-
//            entry i18n keys are exp<SlugCamel>Role / Org / OrgShort / Bullet1… /
//            ImageAlt.
//   roleKey  i18n key → EN + ES
//   orgKey   i18n key — the full organization string shown on the band and in
//            the hero status ("McElroy Prototyping Lab, University of Tulsa").
//   orgShortKey  OPTIONAL i18n key — the short form used by project "Part of"
//            links ("Part of: Baker Hughes →"). Falls back to orgKey.
//   dates    language-neutral, rendered per language (CLAUDE.md → Dates):
//              { from: { season: "summer", year: 2026 } }
//              { from: { season: "spring", year: 2026 }, to: "present" }
//              { from: { month: 7, year: 2022 }, to: { month: 8, year: 2022 } }
//   sortDate "YYYY-MM" — the ONLY thing ordering reads. Newest first. The dev
//            check flags a sortDate that disagrees with `dates`.
//   bulletKeys  i18n keys → EN + ES (any number; 2–5 in practice)
//   tags     tag IDS from js/tags-data.js (never labels); each pill links to
//            projects.html?tag=<id>
//   imageSrc path, or "" for no image
//   imageAltKey  i18n key for the band image's alt text — required whenever
//            imageSrc is set (falls back to "<role> — <org>" if missing)
//   imageLink  OPTIONAL — where the band image links (relative to the site
//            root, e.g. "projects.html?part=baker-hughes" or
//            "projects/pump-cylinder-failure.html"). Absent → the image is
//            plain, no hover.
//   layout   "imageLeft" | "imageRight" | "fullBleed" | "textOnly"
//            Maps 1:1 to a CSS class (.exp-band--image-left, etc.). Adding a
//            preset later means one new class — never bespoke markup.
//   status   "current" on at most ONE entry, else null. Author-side flag, not a
//            visitor toggle: the flagged entry supplies the hero status sentence
//            and gets the .exp-band--current treatment. With no current entry the
//            hero falls back to expHeroStatus and no band is marked.
//   subpageUrl "" = no case-study page yet → the link is omitted. Every value
//            is "" today because none of the /experience/<slug>.html pages
//            exist; a live 404 link is worse than no link.
//   color    Per-entry band colors, written to the band as inline custom
//            properties by js/experience.js. These CANNOT live in :root — they
//            are per-entry values, so the inline style is deliberate and is the
//            one sanctioned exception to CLAUDE.md's token convention.
//            Each mode needs bg / border / accent:
//              bg      12–20% tint of the employer color over var(--bg-section)
//                      for that mode — NEVER the raw brand color.
//              border  band hairline + rule under the role title.
//              accent  case-study link and tag pill borders (must clear 4.5:1
//                      on bg; body text must clear 4.5:1, role titles 3:1).
//            ink is optional and omitted here — bands inherit var(--ink).
//   visible  false → hidden. A hidden role is also an invalid `experience`
//            target for projects (the dev check warns, the link is omitted).
//
// Related projects: a band lists every listing: "index" project whose
// `experience` equals this entry's slug — nothing is stored on this side.
//
// COLOR NOTE: every color below is still a NEUTRAL GREY tint, not an employer
// color. Real employer colors are deferred until after the fair (plan.md open
// decision #9). Light mixes are over #EDE6D5 (light --bg-section), dark mixes
// over #211C14 (dark --bg-section) — a dark band is re-mixed, never the light
// value reused.

const experienceData = [
  {
    slug: "baker-hughes",
    roleKey: "expBakerHughesRole",
    orgKey: "expBakerHughesOrg",
    orgShortKey: "expBakerHughesOrgShort",
    dates: { from: { season: "summer", year: 2026 } },
    sortDate: "2026-07",
    bulletKeys: [
      "expBakerHughesBullet1",
      "expBakerHughesBullet2",
      "expBakerHughesBullet3",
      "expBakerHughesBullet4",
      "expBakerHughesBullet5"
    ],
    tags: ["python", "automation", "cad", "fabrication"],
    imageSrc: "assets/images/projects/autoscan/scanner-station.jpg",
    imageAltKey: "expBakerHughesImageAlt",
    imageLink: "projects.html?part=baker-hughes",
    subpageUrl: "",
    layout: "imageLeft",
    status: null,
    color: {
      light: { bg: "#D6D0C1", border: "#8B8375", accent: "#5B5349" }, // grey #5A5A5A @ 16%
      dark:  { bg: "#39342E", border: "#6F6659", accent: "#C9BFAE" }
    },
    visible: true
  },
  {
    slug: "machine-shop",
    roleKey: "expMachineShopRole",
    orgKey: "expMachineShopOrg",
    orgShortKey: "expMachineShopOrgShort",
    dates: { from: { season: "spring", year: 2026 }, to: "present" },
    sortDate: "2026-02",
    bulletKeys: [
      "expMachineShopBullet1",
      "expMachineShopBullet2",
      "expMachineShopBullet3"
    ],
    tags: ["fabrication", "cad"],
    // Pump lathe photo until Gideon supplies a shop photo (content-intake.md).
    imageSrc: "assets/images/projects/pump-cylinder-failure/pin-on-lathe.jpg",
    imageAltKey: "expMachineShopImageAlt",
    imageLink: "projects/pump-cylinder-failure.html",
    subpageUrl: "",
    layout: "imageRight",
    status: "current",
    color: {
      light: { bg: "#DED8C9", border: "#948C7E", accent: "#615951" }, // grey #6E6E6E @ 12%
      dark:  { bg: "#302C25", border: "#665E52", accent: "#C4BAA9" }
    },
    visible: true
  },
  {
    slug: "schultz-grader",
    roleKey: "expSchultzRole",
    orgKey: "expSchultzOrg",
    orgShortKey: "expSchultzOrgShort",
    dates: { from: { season: "spring", year: 2026 }, to: "present" },
    sortDate: "2026-01",
    bulletKeys: [
      "expSchultzBullet1",
      "expSchultzBullet2"
    ],
    tags: ["python", "data-analysis", "automation"],
    imageSrc: "",
    imageAltKey: "",
    subpageUrl: "",
    layout: "textOnly",
    status: null,
    color: {
      light: { bg: "#CCC7B9", border: "#837B6E", accent: "#554E45" }, // grey #4A4A4A @ 20%
      dark:  { bg: "#423E38", border: "#786F62", accent: "#D0C6B5" }
    },
    visible: true
  },
  {
    slug: "turc",
    roleKey: "expTurcRole",
    orgKey: "expTurcOrg",
    orgShortKey: "expTurcOrgShort",
    dates: { from: { season: "summer", year: 2025 } },
    sortDate: "2025-08",
    bulletKeys: [
      "expTurcBullet1",
      "expTurcBullet2",
      "expTurcBullet3"
    ],
    tags: ["leadership"],
    imageSrc: "assets/images/experience/turc/map-projections-session.jpg",
    imageAltKey: "expTurcImageAlt",
    subpageUrl: "",
    layout: "imageLeft",
    status: null,
    color: {
      light: { bg: "#DBD5C8", border: "#8F8779", accent: "#5E564D" }, // grey #8A8A8A @ 18%
      dark:  { bg: "#3B3730", border: "#6B6255", accent: "#C7BDAC" }
    },
    visible: true
  },

  // ---- Pre-college roles: in the data, never rendered (visible: false).
  // Only the EN role title was collected (content-intake.md, Round 0). Org,
  // dates and ES title are "TODO" until Gideon supplies them — see content.md
  // → experience.html → Pending. Nothing here can reach a visible page.
  {
    slug: "esl-tutor",
    roleKey: "expEslTutorRole",
    orgKey: "expEslTutorOrg",
    dates: { from: { year: 2022 } }, // TODO — placeholder year
    sortDate: "2022-01",
    bulletKeys: [],
    tags: [],
    imageSrc: "",
    imageAltKey: "",
    subpageUrl: "",
    layout: "textOnly",
    status: null,
    color: null,
    visible: false
  },
  {
    slug: "church-media",
    roleKey: "expChurchMediaRole",
    orgKey: "expChurchMediaOrg",
    dates: { from: { year: 2022 } }, // TODO — placeholder year
    sortDate: "2022-01",
    bulletKeys: [],
    tags: [],
    imageSrc: "",
    imageAltKey: "",
    subpageUrl: "",
    layout: "textOnly",
    status: null,
    color: null,
    visible: false
  },
  {
    slug: "senior-patrol-leader",
    roleKey: "expSeniorPatrolLeaderRole",
    orgKey: "expSeniorPatrolLeaderOrg",
    dates: { from: { year: 2022 } }, // TODO — placeholder year
    sortDate: "2022-01",
    bulletKeys: [],
    tags: [],
    imageSrc: "",
    imageAltKey: "",
    subpageUrl: "",
    layout: "textOnly",
    status: null,
    color: null,
    visible: false
  }
];
