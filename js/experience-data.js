// experience-data.js
// Data array driving §2 of experience.html. Reorder entries to change display
// order; set visible: false to hide an entry without deleting it.
// roleKey / orgKey / bulletKeys map to strings in js/translations.js.

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
    visible: false
  }
];
