// experience-data.js
// Data array driving §2 of experience.html. Reorder entries to change display
// order; set visible: false to hide an entry without deleting it.
// roleKey / orgKey / bulletKeys map to strings in js/translations.js.
//
// SCHEMA (see plan.md → Page Spec — experience.html → §2):
//   layout   "imageLeft" | "imageRight" | "fullBleed" | "textOnly"
//            Maps 1:1 to a CSS class (.exp-band--image-left, etc.). Adding a
//            preset later means one new class — never bespoke markup.
//   status   "current" on at most ONE entry, else null. Author-side flag, not a
//            visitor toggle: the flagged entry supplies the hero status sentence
//            and gets the .exp-band--current treatment. With no current entry the
//            hero falls back to expHeroStatus and no band is marked.
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
//
// SCAFFOLD NOTE: every color below is a NEUTRAL GREY tint, not an employer
// color. Real employer colors are TBD (plan.md open decision #9). Light mixes
// are over #EDE6D5 (light --bg-section), dark mixes over #211C14 (dark
// --bg-section) — a dark band is re-mixed, never the light value reused.

const experienceData = [
  {
    roleKey: "expBakerHughesRole",
    orgKey: "expBakerHughesOrg",
    dates: "Summer 2026",
    bulletKeys: [
      "expBakerHughesBullet1",
      "expBakerHughesBullet2",
      "expBakerHughesBullet3"
    ],
    tags: ["Engineering", "R&D", "ALS"],
    imageSrc: "assets/images/placeholder.jpg",
    subpageUrl: "/experience/baker-hughes-summer-2026.html",
    layout: "imageLeft",
    status: null,
    color: {
      light: { bg: "#D6D0C1", border: "#8B8375", accent: "#5B5349" }, // grey #5A5A5A @ 16%
      dark:  { bg: "#39342E", border: "#6F6659", accent: "#C9BFAE" }
    },
    visible: true
  },
  {
    roleKey: "expMachineShopRole",
    orgKey: "expMachineShopOrg",
    dates: "Spring 2026 – present",
    bulletKeys: [
      "expMachineShopBullet1",
      "expMachineShopBullet2",
      "expMachineShopBullet3"
    ],
    tags: ["Machining", "Prototyping", "Fabrication"],
    imageSrc: "assets/images/placeholder.jpg",
    subpageUrl: "/experience/tu-machine-shop.html",
    layout: "imageLeft",
    status: "current",
    color: {
      light: { bg: "#DED8C9", border: "#948C7E", accent: "#615951" }, // grey #6E6E6E @ 12%
      dark:  { bg: "#302C25", border: "#665E52", accent: "#C4BAA9" }
    },
    visible: true
  },
  {
    roleKey: "expSchultzRole",
    orgKey: "expSchultzOrg",
    dates: "Spring 2026",
    bulletKeys: [
      "expSchultzBullet1",
      "expSchultzBullet2",
      "expSchultzBullet3"
    ],
    tags: ["Data Analysis", "Grading", "Dynamics"],
    imageSrc: "assets/images/placeholder.jpg",
    subpageUrl: "/experience/dynamics-grading-schultz.html",
    layout: "imageLeft",
    status: null,
    color: {
      light: { bg: "#CCC7B9", border: "#837B6E", accent: "#554E45" }, // grey #4A4A4A @ 20%
      dark:  { bg: "#423E38", border: "#786F62", accent: "#D0C6B5" }
    },
    visible: true
  },
  {
    roleKey: "expTurcRole",
    orgKey: "expTurcOrg",
    dates: "TBD",
    bulletKeys: [
      "expTurcBullet1",
      "expTurcBullet2",
      "expTurcBullet3"
    ],
    tags: ["Research"],
    imageSrc: "assets/images/placeholder.jpg",
    subpageUrl: "/experience/turc-tmtc-edmonds.html",
    layout: "imageLeft",
    status: null,
    color: {
      light: { bg: "#DBD5C8", border: "#8F8779", accent: "#5E564D" }, // grey #8A8A8A @ 18%
      dark:  { bg: "#3B3730", border: "#6B6255", accent: "#C7BDAC" }
    },
    visible: false
  }
];
