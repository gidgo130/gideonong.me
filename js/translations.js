// translations.js
// All EN/ES display strings. THIS FILE is the single source of display
// strings — content.md records status and field references, not copies of
// the strings. Unfilled slots are prefixed "TODO " in both languages (today:
// only the three hidden pre-college roles, which never render).
//
// Per-entry keys are named by slug: proj<SlugCamel><Field> for projects
// (Title / Desc / LongDesc / Alt / Search / Gallery<N>Alt, and for sub-pages
// Section<N>Heading / Section<N>Body / Fact<N>Label / Fact<N>Value /
// Photo<N>Alt / Credit) and exp<SlugCamel><Field> for experience (Role / Org
// / OrgShort / Bullet1… / ImageAlt). Tag labels are tag<IdCamel>, context
// labels ctx<Context>, date words date<Season> / dateMonth<N>. See CLAUDE.md
// → Data conventions.
//
// PLAIN TEXT ONLY — no HTML in any string. Inline links (IEL, Zohaib Sheikh,
// …) are added at render time by the phrase table in js/chips.js.
//
// Content loaded 2026-09-27 from staging/copy-en.md and staging/copy-es.md
// (approved copy, used verbatim) and staging/image-manifest.md (alt text).

const translations = {
  en: {
    // Navbar — nav link labels
    navProjects: "Projects",
    navExperience: "Experience",
    navAbout: "About",

    // "Under development" banner
    banner: "This site is under development.",

    // index.html — top section
    heroDesc: "Bilingual mechanical engineering IEL student with experience in automation, fabrication, and research; currently looking for summer internships for 2027. Interested in statistics, manufacturing, data analysis for applied engineering, and automating the boring stuff.",

    // Social chips
    sayHello: "say hello",

    // Resume button
    resumeBtn: "Download Resume",

    // index.html — Featured work section. The entries themselves render from
    // js/projects-data.js (featured: true, listing: "index") with the same
    // per-entry keys projects.html uses — nothing project-specific lives here.
    featuredWork: "Featured work",

    // Shared tag labels (js/tags-data.js). Pills show these; the data files
    // store the tag ID, never the label. Compact elements — keep EN and ES
    // close in length.
    tagPython: "Python",
    tagMatlab: "MATLAB",
    tagMachineLearning: "Machine Learning",
    tagDataAnalysis: "Data Analysis",
    tagAutomation: "Automation",
    tagCad: "CAD",
    tagFabrication: "Fabrication",
    tagSolidMechanics: "Solid Mechanics",
    tagThermoFluids: "Thermo/Fluids",
    tagTransportation: "Transportation",
    tagLeadership: "Leadership",

    // Project context labels — the `context` field in js/projects-data.js,
    // rendered as "<Context> · <dates>" in every project meta line. Short.
    ctxIndustry: "Industry",
    ctxCoursework: "Coursework",
    ctxPersonal: "Personal",
    ctxService: "Service",
    ctxResearch: "Research",

    // Dates — the language-neutral `dates` field on projects and experience
    // entries renders through these (js/data-helpers.js → formatDates).
    // Seasons are capitalized in both languages; ES month names are lowercase.
    dateSpring: "Spring",
    dateSummer: "Summer",
    dateFall: "Fall",
    dateWinter: "Winter",
    dateMonth1: "January",
    dateMonth2: "February",
    dateMonth3: "March",
    dateMonth4: "April",
    dateMonth5: "May",
    dateMonth6: "June",
    dateMonth7: "July",
    dateMonth8: "August",
    dateMonth9: "September",
    dateMonth10: "October",
    dateMonth11: "November",
    dateMonth12: "December",
    datePresent: "present",
    dateSeasonYear: "{season} {year}",   // "Summer 2026"
    dateMonthYear: "{month} {year}",     // "July 2022"
    dateRange: "{from} – {to}",          // "Spring 2026 – present"

    // about.html — §1 hero
    aboutIdentifiersEN: "Engineer · Geographer · Federalist · Philomath",
    aboutIdentifiersES: "Ingeniero · Geógrafo · Federalista · Aprendiz eterno",
    headshotAlt: "Portrait of Gideon A. Ong",

    // about.html — §2 "Who am I?"
    whoamiHeading: "Who am I?",
    whoamiBio1: "I'm an IEL student at the University of Tulsa, studying mechanical engineering and Spanish, and minoring in math and economics. I'm very interested in how better engineering can improve people's quality of life, and how public policy can help support that. My current plan is an engineering career right out of school, and to work on the policy side later on.",
    whoamiBio2: "I grew up in College Station, Texas, learning Spanish in a dual-language program and, most Sundays, having lunch with the international students my family hosted. Between those conversations and competing in geography in high school, I spent a lot of time learning about other countries, the world, and what problems other people and places face, and that's a big part of why I care about peace and good governance.",
    whoamiBio3: "Next, I'm looking for internships, hopefully in the Spanish-speaking world, and planning my year abroad (2027-28). Right now I'm deciding between the Universidad de Cantabria in Spain, the Universidad del Norte in Colombia, and UASLP in Mexico. I'm also learning more about modern statistics and data analytics.",
    cvBtn: "Download Full CV",
    transcriptBtn: "Download Transcript",

    // about.html — §3 "What have I been reading?" (section hidden for the fair)
    readingHeading: "What have I been reading?",

    // about.html — §4 Interview FAQ (section hidden for the fair)
    faqHeading: "Interview FAQ",

    // about.html — §5 Statement on AI
    aiHeading: "Statement on AI",
    // Plain text — "Zohaib Sheikh" becomes a chip via js/chips.js, never HTML here.
    aiPara1: "This website was inspired by Zohaib Sheikh, who I had the great pleasure of working together with at Baker Hughes in Claremore the summer of 2026. I have used Claude heavily to help develop and flesh out this website. Nearly all of the code, HTML and otherwise, has been written by AI. Claude has also assisted in grammar-checking and reorganizing content as I have populated this site with my projects and experiences.",

    // about.html — §6 Viewing settings + Interesting sites (sites hidden for the fair)
    settingsHeading: "Viewing settings",
    togglePreCollege: "Show pre-college achievements",
    toggleReadability: "Readability mode",
    toggleColorblind: "Colorblind mode",
    toggleDarkMode: "Dark mode",
    interestingSitesHeading: "Interesting sites",

    // experience.html — §1 hero
    // Key pair for the status sentence. expHeroStatus is the FALLBACK, shown
    // when no entry in js/experience-data.js carries status: "current".
    // expHeroStatusCurrent is the template used when one does — {role} and
    // {org} are substituted from that entry by js/experience.js.
    expHeroStatus: "Currently a Mechanical Engineering and Spanish IEL student at the University of Tulsa — seeking summer 2027 internships in engineering and Spanish.",
    expHeroStatusCurrent: "Currently {role} at {org}.",
    expHeroPara: "This past summer I worked at Baker Hughes, doing some mechanical engineering and some process automation. Now I'm looking for a summer 2027 internship where I can get more hands-on experience.",
    // Hero collage images (experience.html, slots 1–5 in manifest order)
    expHeroCollage1Alt: "Industrial 3D printer in the Baker Hughes R&D lab",
    expHeroCollage2Alt: "G-View plotting speed, torque, oil temperature, and vibration from a demo test file",
    expHeroCollage3Alt: "The old ultrasonic cleaning basket next to the smaller 3D-printed replacement",
    expHeroCollage4Alt: "Machining the pin on a lathe in the TU machine shop",
    expHeroCollage5Alt: "Gideon in his Scout uniform directing a volunteer on build day",

    // experience.html — §2 entries
    expCaseStudyLink: "View full case study →",
    expCurrentLabel: "Current",
    // Heading of the "Projects from this role" list a band shows when at least
    // one listing: "index" project points at it via `experience`.
    expRelatedHeading: "Projects from this role",

    expBakerHughesRole: "Engineering Intern, ALS R&D",
    expBakerHughesOrg: "Baker Hughes, Claremore OK",
    expBakerHughesOrgShort: "Baker Hughes",
    expBakerHughesBullet1: "Co-built Velora, a Python app that turns dyno test data into finished reports, cutting 8–40 hour reports by 80%+ (an estimated $200k a year).",
    expBakerHughesBullet2: "Automated a KEYENCE 3D optical scanner with AutoScan, a Python app that runs scan batches unattended, saving about 10 hours of operator time per batch.",
    expBakerHughesBullet3: "Spun off G-View, a standalone data-review app, and a no-code automation builder, G-RPA, from those two projects.",
    expBakerHughesBullet4: "Wrote user and technical guides for each app with AI assistance, cutting documentation time from weeks to days; presented my GitHub Copilot workflow to the R&D team and was asked to write a white paper on it.",
    expBakerHughesBullet5: "Reviewed and revised drawings for a precision stage tester fix, using 3D-printed parts to check fit before machining.",
    expBakerHughesImageAlt: "3D-printed fixtures for holding parts in the optical scanner",

    expMachineShopRole: "Machine Shop Technician",
    expMachineShopOrg: "McElroy Prototyping Lab, University of Tulsa",
    expMachineShopOrgShort: "McElroy Prototyping Lab",
    expMachineShopBullet1: "Machine parts on CNC and manual mills and lathes, mostly aluminum for student projects, plus some plastics and other materials for student clubs and research groups.",
    expMachineShopBullet2: "Help students use the shop safely and effectively.",
    expMachineShopBullet3: "Machined the valve-actuating pin for my team's prize-winning pump cylinder failure analysis.",
    expMachineShopImageAlt: "Machining the pin on a lathe in the TU machine shop",

    expSchultzRole: "Grader & Data Analyst",
    expSchultzOrg: "Dr. Joshua Schultz, University of Tulsa",
    expSchultzOrgShort: "Dr. Joshua Schultz",
    expSchultzBullet1: "Grade homework for Intro to Dynamics and give Dr. Schultz quick charts and summary statistics for each assignment.",
    expSchultzBullet2: "Built a Python app that merges each student's scans, PDFs, Word files, and code into one PDF per student for grading on an iPad.",

    expTurcRole: "Undergraduate Research Assistant, TURC",
    expTurcOrg: "Dr. Janica Edmonds, University of Tulsa",
    expTurcOrgShort: "Dr. Janica Edmonds",
    expTurcBullet1: "Designed a Math Teachers' Circle session on map projections, a topic new to the circle, and led it with Tulsa-area teachers in October 2025.",
    expTurcBullet2: "Reviewed research on math circles and teacher development to suggest ways the Tulsa Math Teachers' Circle could improve its communication and session structure; drafted further session ideas on circle inversion and linguistics puzzles.",
    expTurcBullet3: "Presented the project on a poster at a TU research event.",
    expTurcImageAlt: "Gideon presenting a map projections session to Tulsa-area teachers",

    // Pre-college roles — visible: false, never rendered. Only the EN role
    // title was collected; org / dates / ES are pending (content.md).
    expEslTutorRole: "ESL Tutor",
    expEslTutorOrg: "TODO organization",
    expChurchMediaRole: "Church Media Technician",
    expChurchMediaOrg: "TODO organization",
    expSeniorPatrolLeaderRole: "Senior Patrol Leader",
    expSeniorPatrolLeaderOrg: "TODO organization",

    // projects.html — §1 search band (live keyword search over the index)
    projSearchPlaceholder: "Search my projects",
    projSearchBtn: "Search",
    projSearchClear: "Clear search",       // aria-label on the × control

    // projects.html — §2 featured + §3 index chrome
    projFeaturedHeading: "Featured projects",
    projIndexHeading: "All projects",
    projViewLink: "View project →",
    // {org} is filled from the linked experience entry's orgShortKey (or
    // orgKey). Shown below the tags on any entry whose `experience` field is set.
    projPartOf: "Part of: {org} →",
    projTagClear: "Clear tag filter",      // aria-label on the ✕ of the "<Tag> ✕" chip
    projCount: "{n} projects",             // {n} filled by js/projects.js
    projCountOne: "{n} project",
    projEmpty: "No projects carry that tag.",
    projEmptySearch: "No projects match “{q}”.",   // {q} = the search query

    // projects/<slug>.html — sub-page chrome (js/project-page.js)
    projReportLink: "Read the report →",
    projAllProjects: "← All projects",

    /* ---- Projects: featured -------------------------------------------- */
    projPumpCylinderFailureTitle: "Paint Sprayer Pump Cylinder Failure Analysis",
    projPumpCylinderFailureDesc: "Traced cracked paint-sprayer pump cylinders to freezing rinse water, then built a $135 fix that drains it in 20 seconds.",
    projPumpCylinderFailureLongDesc: "Ultimate Painting & Drywall had ten paint sprayers down with cracked pump cylinders, at $10–15k per failure. Our team traced it to water freezing inside, and we designed and prototyped a valve-actuating pin to drain the water. Draining takes a painter about 20 seconds, and if it prevents even one failure, the $135 pin has paid for itself 80 times over. The project won the 2026 HackworthWillson Prize for Excellence in Failure Analysis.",
    projPumpCylinderFailureAlt: "The valve-actuating pin assembly, taken apart next to a ruler",
    projPumpCylinderFailureSearch: "Titan PowrTwin 8900 airless sprayer 440C stainless steel Rockwell hardness HRC microstructure hoop stress freezing ME 3033 Properties of Materials Henshaw HackworthWillson Prize Ultimate Painting & Drywall Impact 440 3D printing",
    projPumpCylinderFailureSection1Heading: "The problem",
    projPumpCylinderFailureSection1Body: "Ultimate Painting & Drywall runs Titan PowrTwin 8900 airless sprayers on jobs across the country. Ten of them were out of service with the same failure: a cracked or burst pump cylinder, often within the first year of a part meant to last five. On a job with only one sprayer, that meant at least two weeks of downtime, and $10–15k in repairs and lost labor.",
    projPumpCylinderFailureSection2Heading: "What we found",
    projPumpCylinderFailureSection2Body: "Hardness testing (58.7 HRC) and an etched microstructure pointed to 440C stainless steel, which Titan confirmed. There was no sign of wear, corrosion, or a manufacturing flaw. The one thing all the failures had in common was cold weather: every one happened on a night below freezing. At the end of each day the painters flush the sprayer with water, and the ball valve at the bottom of the cylinder holds that water in. Water expands about 9% when it freezes. Even at −10 °C, that puts more hoop stress on the cylinder (about 112 MPa) than it sees at full operating pressure (96 MPa).",
    projPumpCylinderFailureSection3Heading: "The fix",
    projPumpCylinderFailureSection3Body: "The painters were already wrapping the machines in insulation or hauling heaters around, and neither happened reliably after a long day. So we looked for something that took no extra effort. Titan's smaller Impact 440 has a small pin for knocking dried paint off its ball valve. We adapted that idea into a spring-loaded pin in the inlet elbow that lifts the valve so the water drains out through the inlet hose. The design was a team effort, and a lot of my input came from knowing what could actually be made in the shop. I machined the pin; Rachel and Dulce designed the 3D-printed cap.",
    projPumpCylinderFailureSection4Heading: "The result",
    projPumpCylinderFailureSection4Body: "One of the company's painters tried it at the end of a workday. It didn't change how the sprayer ran, it emptied the cylinder, and it took him about 20 seconds. If it prevents even one failure, the $135 retrofit has paid for itself 80 times over.",
    projPumpCylinderFailureFact1Label: "Team",
    projPumpCylinderFailureFact1Value: "Rachel Lewis (lead), Dulce Rios, Gideon Ong",
    projPumpCylinderFailureFact2Label: "My role",
    projPumpCylinderFailureFact2Value: "co-designed the pin; machined it; coordinated some of the technical work",
    projPumpCylinderFailureFact3Label: "Course",
    projPumpCylinderFailureFact3Value: "ME 3033 Properties of Materials, Dr. John Henshaw, Spring 2026",
    projPumpCylinderFailureFact4Label: "Methods",
    projPumpCylinderFailureFact4Value: "Rockwell hardness, microstructure analysis, thick-wall stress analysis, cost analysis",
    projPumpCylinderFailureFact5Label: "Award",
    projPumpCylinderFailureFact5Value: "2026 HackworthWillson Prize for Excellence in Failure Analysis",
    projPumpCylinderFailurePhoto1Alt: "A burst pump cylinder and a cracked one, with the failures marked",
    projPumpCylinderFailurePhoto2Alt: "Machining the pin on a lathe in the TU machine shop",
    projPumpCylinderFailurePhoto3Alt: "The pin installed on the sprayer's inlet elbow",
    projPumpCylinderFailurePhoto4Alt: "Paint sprayers stored in the company's work van",
    projPumpCylinderFailurePhoto5Alt: "A pump cylinder with a crack running along its length",

    projEaglePathwayTitle: "Wheelchair-Accessible Pathway (Eagle Scout Project)",
    projEaglePathwayDesc: "Planned and led 27 volunteers to build a 273.5 sq ft ADA-compliant pathway for a business that employs adults with special needs.",
    projEaglePathwayLongDesc: "The Bee Community in Bryan, Texas, employs adults with special needs. Their artisans who use wheelchairs couldn't reach the picnic tables out back, especially once rain turned the yard to mud. For my Eagle Scout project, I designed a 3-foot-wide, ADA-compliant decomposed granite pathway and led 27 volunteers to build it in one day.",
    projEaglePathwayAlt: "Gideon in his Scout uniform directing a volunteer on build day",
    projEaglePathwayGallery1Alt: "Volunteers spreading decomposed granite next to a plate compactor",
    projEaglePathwayGallery2Alt: "The finished decomposed granite pathway",
    projEaglePathwaySearch: "Eagle Scout BSA Boy Scouts ADA accessibility decomposed granite landscape fabric lumber edging plate compactor The Bee Community Bryan Texas volunteers",
    projEaglePathwaySection1Heading: "How it started",
    projEaglePathwaySection1Body: "My first Eagle project plan was rainwater tanks for a community garden, and it fell through when COVID hit. About a year later, through a connection in my troop, I found The Bee Community, a Bryan business that employs adults with special needs. Their artisans make goods like dog treats and soap. Their backyard was spacious, but artisans who use wheelchairs couldn't get to the picnic tables, especially when it was muddy.",
    projEaglePathwaySection2Heading: "Planning",
    projEaglePathwaySection2Body: "I laid out the path, worked out materials with suppliers, and split the work into three phases: digging, edging, and filling. The week before, I watered and edged the site every day so we could dig it in July.",
    projEaglePathwaySection3Heading: "Build day",
    projEaglePathwaySection3Body: "July 30, 2022, starting at 6 a.m. We dug out three inches of dirt, laid and pinned landscape fabric, staked lumber edging, then filled and tamped the decomposed granite. The whole thing took nine hours.",
    projEaglePathwaySection4Heading: "What I learned",
    projEaglePathwaySection4Body: "Most of what I learned was about communication. Before planning anything, I met with The Bee Community several times to find out what they needed most, and the pathway idea came out of those meetings. I'd never built anything like it, so I asked local experts, who pointed me to the ADA guidelines and critiqued my design as it developed. With my volunteers, I sent weekly emails in the month before the build with timetables and tool lists, and gave a briefing that morning. I learned to keep instructions short and clear, and that once people know the job, they don't need much more direction.",
    projEaglePathwayFact1Label: "My role",
    projEaglePathwayFact1Value: "Project lead",
    projEaglePathwayFact2Label: "Volunteers",
    projEaglePathwayFact2Value: "27 volunteers, about 285 total hours",
    projEaglePathwayFact3Label: "Size",
    projEaglePathwayFact3Value: "3 ft wide · 273.5 sq ft",
    projEaglePathwayFact4Label: "Materials",
    projEaglePathwayFact4Value: "decomposed granite, landscape fabric, lumber edging",
    projEaglePathwayFact5Label: "Beneficiary",
    projEaglePathwayFact5Value: "The Bee Community, Bryan TX",
    projEaglePathwayFact6Label: "Rank",
    projEaglePathwayFact6Value: "Eagle Scout rank, 2023",
    projEaglePathwayPhoto1Alt: "Volunteers spreading decomposed granite next to a plate compactor",
    projEaglePathwayPhoto2Alt: "The finished decomposed granite pathway",
    projEaglePathwayPhoto3Alt: "The volunteer crew at the end of build day",
    projEaglePathwayCredit: "Photos: Matthew Rowan",

    projGViewTitle: "G-View: Test Data Review App",
    projGViewDesc: "Built a desktop app for reviewing large test-data spreadsheets: plot the data, crop out bad sections, and export clean copies.",
    projGViewLongDesc: "Engineers at Baker Hughes often review hundreds of thousands of rows of test data by hand in Excel. G-View handles the repetitive part: open a workbook or CSV, confirm where the real data starts, plot any column against several others, crop out bad sections without touching the source file, and export a clean spreadsheet or chart. I spun it off in a day from the dyno report app I co-built that summer, then kept developing it into a standalone tool.",
    projGViewAlt: "G-View plotting speed, torque, oil temperature, and vibration from a demo test file",
    projGViewSearch: "Excel CSV TSV Parquet JSONL pandas pyarrow python-calamine matplotlib Tkinter scikit-learn k-means DBSCAN HDBSCAN clustering Gaussian mixture pytest Inno Setup installer Velora dyno GitHub Copilot spreadsheet plotting",
    projGViewSection1Heading: "Why",
    projGViewSection1Body: "A lot of data review is the same few Excel moves on very large sheets: find where the data actually starts, plot a few columns, cut out a bad stretch, send someone a clean copy. At that size, Excel gets slow, and it's easy to edit the original by accident.",
    projGViewSection2Heading: "What it does",
    projGViewSection2Body: "Opens Excel, CSV, TSV, Parquet and JSONL files. Confirms the sheet and header range before anything is plotted. Plots one x-axis against several y-series with pan, zoom, and undo. Crops regions out of the output while leaving the source file untouched. Groups points with clustering when outliers matter. Saves review state in a project folder. Exports a cleaned Excel file or the current chart as a PNG.",
    projGViewSection3Heading: "How it started",
    projGViewSection3Body: "Zohaib Sheikh and I built Velora, an app that automates dyno test reports. Its data-review screens were useful well beyond dyno testing, so I spun them off into a standalone app in one day using GitHub Copilot. Over the rest of the summer I added clustering, chart styling, project folders, an installer, and user and technical guides.",
    projGViewSection4Heading: "Where it stands",
    projGViewSection4Body: "I handed it off at the end of the internship. There's no usage data yet, but engineers in other groups were interested. If it catches on, my recommendation was to port it to a faster language and pair software interns with test engineers to add no-code column operations.",
    projGViewFact1Label: "Role",
    projGViewFact1Value: "sole developer",
    projGViewFact2Label: "Stack",
    projGViewFact2Value: "Python, pandas, pyarrow, matplotlib, Tkinter, scikit-learn (k-means, DBSCAN, HDBSCAN, hierarchical, Gaussian mixture), pytest, Inno Setup",
    projGViewFact3Label: "Where",
    projGViewFact3Value: "Baker Hughes ALS R&D, Claremore OK",

    /* ---- Projects: index ----------------------------------------------- */
    projVeloraTitle: "Velora: Dyno Report Automation",
    projVeloraDesc: "Co-built a Python app with Zohaib Sheikh that turns dyno test data into finished reports, saving up to 30 hours per report.",
    projVeloraSearch: "dynamometer dyno test report automation Velora Baker Hughes GitHub Copilot Excel",

    projAutoscanTitle: "AutoScan: 3D Scanner Automation",
    projAutoscanDesc: "Automated a KEYENCE 3D optical scanner so scan batches run unattended, saving around 10 hours of operator time per batch.",
    projAutoscanAlt: "3D-printed fixtures for holding parts in the optical scanner",
    projAutoscanSearch: "KEYENCE 3D optical scanner scan fixtures 3D printing AutoScan Baker Hughes",

    projDynamicsPdfUnifierTitle: "Dynamics PDF Unifier",
    projDynamicsPdfUnifierDesc: "Built a Python desktop app that merges each student's scans, PDFs, Word files, and code into one PDF per student for grading.",
    projDynamicsPdfUnifierSearch: "PDF Word iPad grading Intro to Dynamics Schultz merge",

    projKeplingerHeatingTitle: "Keplinger Hall Heating Analysis",
    projKeplingerHeatingDesc: "Estimated winter heat loss for TU's engineering building and sized a hot-water radiator system for it, using Python and Excel.",
    projKeplingerHeatingSearch: "heat transfer heat loss hot-water radiators Excel Keplinger Hall University of Tulsa",

    projMusicNotesMatlabTitle: "Finding Notes in Music with MATLAB",
    projMusicNotesMatlabDesc: "Wrote a MATLAB script that finds the main notes and overtones in a song using windowed Fourier transforms.",
    projMusicNotesMatlabAlt: "Plot of the principal notes and overtones detected in a trumpet recording",
    projMusicNotesMatlabSearch: "Fourier transform FFT windowed Hamming window spectrogram overtones notes trumpet",

    projGenderEmploymentCsTitle: "Gender and Employment in Computer Science",
    projGenderEmploymentCsDesc: "Used linear probability and logistic models in Stata to test whether gender affects the odds of being employed in computer science jobs.",
    projGenderEmploymentCsSearch: "Stata linear probability model logistic regression robust standard errors econometrics ECON 4273 Huang",

    projChilledWaterPipelineTitle: "Chilled Water Pipeline Design",
    projChilledWaterPipelineDesc: "Routed and sized a replacement chilled-water pipeline for TU's campus in Python; it scored 100% with the lowest-cost bid in the class.",
    projChilledWaterPipelineAlt: "The chosen pipeline route drawn over the TU campus map",
    projChilledWaterPipelineSearch: "fluids fluid mechanics chilled water pipeline routing convex hull cost estimate Amiri University of Tulsa campus",

    projNotchedBeamStressReliefTitle: "Stress Relief for a Notched Beam",
    projNotchedBeamStressReliefDesc: "Used SolidWorks simulation to design a spline cutout that reduced a notched beam's stress concentration by 42% in bending tests.",
    projNotchedBeamStressReliefAlt: "SolidWorks simulation of the notched beam with spline stress relief",
    projNotchedBeamStressReliefSearch: "SolidWorks Simulation FEA finite element stress concentration factor Kt spline bending ES 3023 Kinniburgh",

    projDieselDualCycleTitle: "Diesel vs. Dual Cycle Comparison",
    projDieselDualCycleDesc: "Modeled Diesel and dual combustion cycles in Python with NASA property data to compare efficiency, cost, and peak temperature.",
    projDieselDualCycleAlt: "Pressure–volume diagram of the Diesel cycle",
    projDieselDualCycleSearch: "thermodynamics Diesel cycle dual cycle NASA polynomials combustion efficiency peak temperature P-v diagram",

    projMechanicalFuseTitle: "Axial Mechanical Fuse",
    projMechanicalFuseDesc: "Designed a notch for an acrylic link to break in the middle at the highest possible load, using a Java search; two of three test links broke at the notch.",
    projMechanicalFuseAlt: "Three notched acrylic links after break testing",
    projMechanicalFuseSearch: "Java exhaustive search V-notch acrylic link stress concentration Kt ES 3023 Kinniburgh break test",

    projBicycleCrashSeverityTitle: "Predicting Bicycle Crash Severity",
    projBicycleCrashSeverityDesc: "Tested FAMD and undersampling to predict UK bicycle crash severity, using SHAP to trace results back to the original variables.",
    projBicycleCrashSeverityAlt: "SHAP summary plot of feature effects on crash severity",
    projBicycleCrashSeveritySearch: "FAMD undersampling SHAP bicycle accidents UK ES 4863 AI for Engineers Chowdhury",

    projUkCrashHotspotsTitle: "Recurring Crash Hotspots in the UK",
    projUkCrashHotspotsDesc: "Found UK intersections that stayed crash hotspots year after year using DBSCAN and QGIS, then confirmed them against local news reports.",
    projUkCrashHotspotsAlt: "QGIS map of England with crash hotspot clusters",
    projUkCrashHotspotsSearch: "DBSCAN QGIS clustering Kaggle UK accidents intersections hotspots GIS ES 4863 AI for Engineers Chowdhury",

    projLandmineClassificationTitle: "Classifying Landmines from Passive Sensor Data",
    projLandmineClassificationDesc: "Compared decision trees and neural networks, tuned with grid search, to classify five landmine types from passive sensor data.",
    projLandmineClassificationSearch: "decision tree neural network MLP grid search UCI passive sensor landmines ES 4863 AI for Engineers",

    // Footer
    footerContact: "gao9819@utulsa.edu",
    footerCopyright: "© 2026 Gideon A. Ong",
  },

  es: {
    // Navbar
    navProjects: "Proyectos",
    navExperience: "Experiencia",
    navAbout: "Sobre mí",

    // "Under development" banner
    banner: "Este sitio está en desarrollo.",

    // index.html — top section
    heroDesc: "Estudiante bilingüe de ingeniería mecánica IEL con experiencia en automatización, fabricación e investigación; actualmente buscando pasantías para el verano de 2027. Interesado en estadística, manufactura, análisis de datos para aplicaciones de ingeniería, y automatizar lo aburrido.",

    // Social chips
    sayHello: "escríbeme",

    // Resume button
    resumeBtn: "Descargar Currículum",

    // index.html — Featured work section
    featuredWork: "Proyectos destacados",

    // Shared tag labels — see the note in the en block.
    tagPython: "Python",
    tagMatlab: "MATLAB",
    tagMachineLearning: "Machine Learning",
    tagDataAnalysis: "Análisis de datos",
    tagAutomation: "Automatización",
    tagCad: "CAD",
    tagFabrication: "Fabricación",
    tagSolidMechanics: "Mecánica de sólidos",
    tagThermoFluids: "Termo/Fluidos",
    tagTransportation: "Transporte",
    tagLeadership: "Liderazgo",

    // Project context labels — kept short (meta line).
    ctxIndustry: "Industria",
    ctxCoursework: "Curso",
    ctxPersonal: "Personal",
    ctxService: "Servicio",
    ctxResearch: "Investigación",

    // Fechas — estaciones con mayúscula, meses en minúscula ("julio de 2022").
    dateSpring: "Primavera",
    dateSummer: "Verano",
    dateFall: "Otoño",
    dateWinter: "Invierno",
    dateMonth1: "enero",
    dateMonth2: "febrero",
    dateMonth3: "marzo",
    dateMonth4: "abril",
    dateMonth5: "mayo",
    dateMonth6: "junio",
    dateMonth7: "julio",
    dateMonth8: "agosto",
    dateMonth9: "septiembre",
    dateMonth10: "octubre",
    dateMonth11: "noviembre",
    dateMonth12: "diciembre",
    datePresent: "presente",
    dateSeasonYear: "{season} {year}",   // "Verano 2026"
    dateMonthYear: "{month} de {year}",  // "julio de 2022"
    dateRange: "{from} – {to}",          // "Primavera 2026 – presente"

    // about.html — §1 hero
    aboutIdentifiersEN: "Engineer · Geographer · Federalist · Philomath",
    aboutIdentifiersES: "Ingeniero · Geógrafo · Federalista · Aprendiz eterno",
    headshotAlt: "Retrato de Gideon A. Ong",

    // about.html — §2 "¿Quién soy?"
    whoamiHeading: "¿Quién soy?",
    whoamiBio1: "Soy estudiante del programa IEL en la Universidad de Tulsa: estudio ingeniería mecánica y español, con especializaciones menores en matemáticas y economía. Me interesa mucho cómo una mejor ingeniería puede mejorar la calidad de vida de las personas, y cómo las políticas públicas pueden ayudar a lograrlo. Por ahora, mi plan es trabajar en ingeniería al terminar la carrera y, más adelante, involucrarme en políticas públicas.",
    whoamiBio2: "Crecí en College Station, Texas, aprendiendo español en un programa de lenguaje dual y, casi todos los domingos, almorzando con los estudiantes internacionales que recibía mi familia. Entre esas conversaciones y los concursos de geografía en la secundaria, pasé mucho tiempo aprendiendo sobre otros países, el mundo y los problemas que enfrentan otras personas y lugares, y en buena parte por eso me importan la paz y el buen gobierno.",
    whoamiBio3: "Ahora estoy buscando pasantías, ojalá en el mundo hispanohablante, y planeando mi año en el extranjero (2027-28). Todavía estoy decidiendo entre la Universidad de Cantabria en España, la Universidad del Norte en Colombia y la UASLP en México. También estoy aprendiendo más sobre estadística moderna y análisis de datos.",
    cvBtn: "Descargar CV Completo",
    transcriptBtn: "Descargar Historial Académico",

    // about.html — §3 "¿Qué he estado leyendo?" (sección oculta para la feria)
    readingHeading: "¿Qué he estado leyendo?",

    // about.html — §4 Preguntas de entrevista (sección oculta para la feria)
    faqHeading: "Preguntas frecuentes de entrevista",

    // about.html — §5 Declaración sobre la IA
    aiHeading: "Declaración sobre la IA",
    aiPara1: "Este sitio web fue inspirado por Zohaib Sheikh, con quien tuve el gran placer de trabajar juntos en Baker Hughes en Claremore el verano de 2026. He usado Claude ampliamente para desarrollar y dar cuerpo a este sitio web; casi todo el código fue escrito por IA. Claude también me asistió en corregir mi gramática y mis traducciones, y en reorganizar mis experiencias y proyectos mientras los iba añadiendo a este sitio.",

    // about.html — §6 Preferencias de visualización + Sitios interesantes
    settingsHeading: "Preferencias de visualización",
    togglePreCollege: "Mostrar logros preuniversitarios",
    toggleReadability: "Modo de lectura fácil",
    toggleColorblind: "Modo daltónico",
    toggleDarkMode: "Modo oscuro",
    interestingSitesHeading: "Sitios interesantes",

    // experience.html — §1 hero
    // Same key pair as EN — see the comment in the en block above.
    expHeroStatus: "Actualmente estudiante de Ingeniería Mecánica y Español del programa IEL en la Universidad de Tulsa, en busca de pasantías de ingeniería y español para el verano de 2027.",
    expHeroStatusCurrent: "Actualmente trabajo como {role} en {org}.",
    expHeroPara: "El verano pasado trabajé en Baker Hughes, haciendo algo de ingeniería mecánica y algo de automatización de procesos. Ahora busco una pasantía para el verano de 2027 donde pueda ganar más experiencia práctica.",
    expHeroCollage1Alt: "Impresora 3D industrial en el laboratorio de I+D de Baker Hughes",
    expHeroCollage2Alt: "G-View graficando velocidad, par, temperatura del aceite y vibración de un archivo de prueba de demostración",
    expHeroCollage3Alt: "La canasta ultrasónica original junto al reemplazo más pequeño impreso en 3D",
    expHeroCollage4Alt: "Maquinando el pasador en un torno del taller de TU",
    expHeroCollage5Alt: "Gideon con su uniforme scout dirigiendo a un voluntario el día de la obra",

    // experience.html — §2 entries
    expCaseStudyLink: "Ver caso completo →",
    expCurrentLabel: "Actual",
    expRelatedHeading: "Proyectos de este puesto",

    expBakerHughesRole: "Pasante de Ingeniería, I+D de ALS",
    expBakerHughesOrg: "Baker Hughes, Claremore OK",
    expBakerHughesOrgShort: "Baker Hughes",
    expBakerHughesBullet1: "Desarrollé, junto con un compañero, Velora: una aplicación en Python que convierte datos de pruebas de dinamómetro en reportes terminados y reduce en más del 80% el tiempo de reportes que antes tomaban de 8 a 40 horas (un ahorro estimado de $200 mil al año).",
    expBakerHughesBullet2: "Automaticé un escáner óptico 3D KEYENCE con AutoScan, una aplicación en Python que ejecuta lotes de escaneo sin supervisión y ahorra unas 10 horas de trabajo de operador por lote.",
    expBakerHughesBullet3: "A partir de esos dos proyectos, desarrollé G-View, una aplicación independiente para revisar datos, y G-RPA, una herramienta para crear automatizaciones sin programar.",
    expBakerHughesBullet4: "Redacté guías técnicas y de usuario para cada aplicación con ayuda de IA, lo que redujo el tiempo de documentación de semanas a días; presenté mi flujo de trabajo con GitHub Copilot al equipo de I+D y me pidieron escribir un documento técnico al respecto.",
    expBakerHughesBullet5: "Revisé y corregí los planos para reparar un banco de precisión que prueba etapas de bomba, y usé piezas impresas en 3D para comprobar el ajuste antes del maquinado.",
    expBakerHughesImageAlt: "Soportes impresos en 3D para sujetar piezas en el escáner óptico",

    expMachineShopRole: "Técnico del Taller de Maquinado",
    expMachineShopOrg: "McElroy Prototyping Lab, Universidad de Tulsa",
    expMachineShopOrgShort: "McElroy Prototyping Lab",
    expMachineShopBullet1: "Maquino piezas en fresadoras y tornos CNC y manuales, principalmente de aluminio para proyectos estudiantiles, y a veces de plásticos y otros materiales para clubes estudiantiles y grupos de investigación.",
    expMachineShopBullet2: "Ayudo a los estudiantes a usar el taller de forma segura y eficaz.",
    expMachineShopBullet3: "Maquiné el pasador que acciona la válvula para un proyecto premiado de mi equipo: el análisis de falla de un cilindro de bomba.",
    expMachineShopImageAlt: "Maquinando el pasador en un torno del taller de TU",

    expSchultzRole: "Calificador y Analista de Datos",
    expSchultzOrg: "Dr. Joshua Schultz, Universidad de Tulsa",
    expSchultzOrgShort: "Dr. Joshua Schultz",
    expSchultzBullet1: "Califico las tareas de Introducción a la Dinámica y le entrego al Dr. Schultz gráficas rápidas y estadísticas resumidas de cada tarea.",
    expSchultzBullet2: "Desarrollé una aplicación en Python que une los escaneos, PDF, archivos de Word y código de cada estudiante en un solo PDF por estudiante, para calificar en iPad.",

    expTurcRole: "Asistente de Investigación de Licenciatura, TURC",
    expTurcOrg: "Dra. Janica Edmonds, Universidad de Tulsa",
    expTurcOrgShort: "Dra. Janica Edmonds",
    expTurcBullet1: "Diseñé una sesión del Math Teachers' Circle sobre proyecciones cartográficas, un tema nuevo para el círculo, y la dirigí con maestros del área de Tulsa en octubre de 2025.",
    expTurcBullet2: "Revisé investigaciones sobre círculos matemáticos y formación de maestros para proponer mejoras en la comunicación y la estructura de las sesiones del Tulsa Math Teachers' Circle; también esbocé ideas para sesiones sobre inversión respecto a una circunferencia y acertijos lingüísticos.",
    expTurcBullet3: "Presenté el proyecto con un póster en un evento de investigación de TU.",
    expTurcImageAlt: "Gideon presentando una sesión sobre proyecciones cartográficas a docentes de Tulsa",

    // Puestos preuniversitarios — visible: false, nunca se muestran. Pendientes.
    expEslTutorRole: "TODO ESL Tutor",
    expEslTutorOrg: "TODO organización",
    expChurchMediaRole: "TODO Church Media Technician",
    expChurchMediaOrg: "TODO organización",
    expSeniorPatrolLeaderRole: "TODO Senior Patrol Leader",
    expSeniorPatrolLeaderOrg: "TODO organización",

    // projects.html — §1 search band
    projSearchPlaceholder: "Buscar proyectos",
    projSearchBtn: "Buscar",
    projSearchClear: "Borrar búsqueda",

    // projects.html — §2 featured + §3 index chrome.
    // projSearchBtn sits inside a fixed-shape control, so the ES string is
    // kept the same length as the EN one (CLAUDE.md compact element rule).
    projFeaturedHeading: "Proyectos destacados",
    projIndexHeading: "Todos los proyectos",
    projViewLink: "Ver proyecto →",
    projPartOf: "Parte de: {org} →",
    projTagClear: "Quitar el filtro de etiqueta",
    projCount: "{n} proyectos",
    projCountOne: "{n} proyecto",
    projEmpty: "Ningún proyecto tiene esa etiqueta.",
    projEmptySearch: "Ningún proyecto coincide con «{q}».",

    // projects/<slug>.html — subpágina
    projReportLink: "Leer el reporte →",
    projAllProjects: "← Todos los proyectos",

    /* ---- Proyectos destacados ------------------------------------------ */
    projPumpCylinderFailureTitle: "Análisis de falla del cilindro de bomba de un equipo de pintura",
    projPumpCylinderFailureDesc: "Identificamos que los cilindros agrietados de unos equipos de pintura airless se debían al agua de enjuague congelada, y construimos una solución de $135 que la drena en 20 segundos.",
    projPumpCylinderFailureLongDesc: "Ultimate Painting & Drywall tenía diez equipos de pintura airless fuera de servicio por cilindros de bomba agrietados, con un costo de $10,000 a $15,000 por falla. Nuestro equipo encontró que la causa era agua que se congelaba adentro, y diseñamos e hicimos un prototipo de un pasador que acciona la válvula para drenar el agua. Drenarla le toma a un pintor unos 20 segundos, y si evita aunque sea una falla, el pasador de $135 recupera 80 veces lo que cuesta. El proyecto ganó el HackworthWillson Prize for Excellence in Failure Analysis de 2026.",
    projPumpCylinderFailureAlt: "El conjunto del pasador con resorte que acciona la válvula, desarmado junto a una regla",
    projPumpCylinderFailureSearch: "Titan PowrTwin 8900 equipo de pintura airless acero inoxidable 440C dureza Rockwell HRC microestructura esfuerzo circunferencial congelación ME 3033 Properties of Materials Henshaw HackworthWillson Prize Ultimate Painting & Drywall Impact 440 impresión 3D",
    projPumpCylinderFailureSection1Heading: "El problema",
    projPumpCylinderFailureSection1Body: "Ultimate Painting & Drywall usa equipos de pintura airless Titan PowrTwin 8900 en obras por todo el país. Diez de ellos estaban fuera de servicio por la misma falla: un cilindro de bomba agrietado o reventado, muchas veces dentro del primer año de una pieza diseñada para durar cinco. En una obra con un solo equipo, eso significaba al menos dos semanas de inactividad y de $10,000 a $15,000 en reparaciones y mano de obra perdida.",
    projPumpCylinderFailureSection2Heading: "Lo que encontramos",
    projPumpCylinderFailureSection2Body: "Las pruebas de dureza (58.7 HRC) y una microestructura atacada químicamente indicaban acero inoxidable 440C, lo cual Titan confirmó. No había señales de desgaste, corrosión ni defectos de fabricación. Lo único que todas las fallas tenían en común era el frío: todas ocurrieron en noches bajo cero. Al final de cada día, los pintores enjuagan el equipo con agua, y la válvula de bola en el fondo del cilindro retiene esa agua. El agua se expande alrededor de 9% al congelarse. Incluso a −10 °C, eso genera en el cilindro más esfuerzo circunferencial (unos 112 MPa) que el que soporta a plena presión de operación (96 MPa).",
    projPumpCylinderFailureSection3Heading: "La solución",
    projPumpCylinderFailureSection3Body: "Los pintores ya envolvían los equipos con aislante o cargaban calentadores, pero después de un día largo ninguna de las dos cosas se hacía con constancia. Así que buscamos algo que no requiriera esfuerzo extra. El Impact 440, un modelo más pequeño de Titan, tiene un pasador pequeño para desprender la pintura seca de su válvula de bola. Adaptamos esa idea en un pasador con resorte, dentro del codo de entrada, que levanta la válvula para que el agua salga por la manguera de entrada. El diseño fue un trabajo en equipo, y buena parte de mi aporte vino de saber qué se podía fabricar de verdad en el taller. Yo maquiné el pasador; Rachel y Dulce diseñaron la tapa impresa en 3D.",
    projPumpCylinderFailureSection4Heading: "El resultado",
    projPumpCylinderFailureSection4Body: "Uno de los pintores de la empresa lo probó al final de una jornada. No cambió el funcionamiento del equipo, vació el cilindro y le tomó unos 20 segundos. Si evita aunque sea una falla, la modificación de $135 recupera 80 veces lo que cuesta.",
    projPumpCylinderFailureFact1Label: "Equipo",
    projPumpCylinderFailureFact1Value: "Rachel Lewis (líder), Dulce Rios, Gideon Ong",
    projPumpCylinderFailureFact2Label: "Mi rol",
    projPumpCylinderFailureFact2Value: "codiseñé el pasador; lo maquiné; coordiné parte del trabajo técnico",
    projPumpCylinderFailureFact3Label: "Curso",
    projPumpCylinderFailureFact3Value: "ME 3033 Properties of Materials, Dr. John Henshaw, primavera 2026",
    projPumpCylinderFailureFact4Label: "Métodos",
    projPumpCylinderFailureFact4Value: "dureza Rockwell, análisis de microestructura, análisis de esfuerzos en cilindros de pared gruesa, análisis de costos",
    projPumpCylinderFailureFact5Label: "Premio",
    projPumpCylinderFailureFact5Value: "HackworthWillson Prize for Excellence in Failure Analysis 2026",
    projPumpCylinderFailurePhoto1Alt: "Un cilindro de bomba reventado y otro agrietado, con las fallas marcadas",
    projPumpCylinderFailurePhoto2Alt: "Maquinando el pasador en un torno del taller de TU",
    projPumpCylinderFailurePhoto3Alt: "El pasador instalado en el codo de entrada del equipo",
    projPumpCylinderFailurePhoto4Alt: "Equipos de pintura guardados en la camioneta de trabajo de la empresa",
    projPumpCylinderFailurePhoto5Alt: "Un cilindro de bomba con una grieta a lo largo",

    projEaglePathwayTitle: "Sendero accesible para sillas de ruedas (proyecto Eagle Scout)",
    projEaglePathwayDesc: "Planeé la obra y dirigí a 27 voluntarios para construir un sendero de 273.5 pies² que cumple con la ADA para una empresa que emplea a adultos con necesidades especiales.",
    projEaglePathwayLongDesc: "The Bee Community, en Bryan, Texas, emplea a adultos con necesidades especiales. Sus artesanos que usan silla de ruedas no podían llegar a las mesas de picnic, sobre todo cuando la lluvia convertía el patio en lodo. Para mi proyecto Eagle Scout, diseñé un sendero de granito descompuesto de 3 pies de ancho que cumple con la ADA y dirigí a 27 voluntarios para construirlo en un día.",
    projEaglePathwayAlt: "Gideon con su uniforme scout dirigiendo a un voluntario el día de la obra",
    projEaglePathwayGallery1Alt: "Voluntarios esparciendo granito descompuesto junto a una compactadora",
    projEaglePathwayGallery2Alt: "El sendero de granito descompuesto terminado",
    projEaglePathwaySearch: "Eagle Scout BSA scouts ADA accesibilidad granito descompuesto malla geotextil bordes de madera compactadora The Bee Community Bryan Texas voluntarios",
    projEaglePathwaySection1Heading: "Cómo empezó",
    projEaglePathwaySection1Body: "Mi primer plan para el proyecto Eagle eran tanques de agua de lluvia para un huerto comunitario, y se cayó cuando llegó el COVID. Como un año después, gracias a un contacto en mi tropa, conocí The Bee Community, una empresa de Bryan que emplea a adultos con necesidades especiales. Sus artesanos hacen productos como premios para perros y jabón. Su patio era amplio, pero los artesanos que usan silla de ruedas no podían llegar a las mesas de picnic, sobre todo cuando había lodo.",
    projEaglePathwaySection2Heading: "La planeación",
    projEaglePathwaySection2Body: "Tracé el sendero, definí los materiales con los proveedores y dividí el trabajo en tres fases: excavar, poner los bordes y rellenar. La semana anterior, regué y delimité el terreno todos los días para que pudiéramos excavarlo en pleno julio.",
    projEaglePathwaySection3Heading: "El día de la obra",
    projEaglePathwaySection3Body: "30 de julio de 2022, desde las 6 a. m. Excavamos tres pulgadas de tierra, pusimos y fijamos la malla geotextil, estacamos los bordes de madera, y luego rellenamos y compactamos el granito descompuesto. Todo tomó nueve horas.",
    projEaglePathwaySection4Heading: "Lo que aprendí",
    projEaglePathwaySection4Body: "La mayor parte de lo que aprendí fue sobre comunicación. Antes de planear nada, me reuní varias veces con The Bee Community para entender qué era lo que más necesitaban, y la idea del sendero salió de esas reuniones. Nunca había construido algo así, así que consulté a expertos locales, que me indicaron las normas de la ADA y revisaron mi diseño mientras lo desarrollaba. A mis voluntarios les mandé correos semanales durante el mes anterior con horarios y listas de herramientas, y les expliqué el plan esa misma mañana. Aprendí a dar instrucciones cortas y claras, y que, una vez que la gente sabe qué hacer, no necesita mucha más dirección.",
    projEaglePathwayFact1Label: "Mi rol",
    projEaglePathwayFact1Value: "Líder del proyecto",
    projEaglePathwayFact2Label: "Voluntarios",
    projEaglePathwayFact2Value: "27 voluntarios, unas 285 horas en total",
    projEaglePathwayFact3Label: "Tamaño",
    projEaglePathwayFact3Value: "3 pies de ancho · 273.5 pies²",
    projEaglePathwayFact4Label: "Materiales",
    projEaglePathwayFact4Value: "granito descompuesto, malla geotextil, bordes de madera",
    projEaglePathwayFact5Label: "Beneficiario",
    projEaglePathwayFact5Value: "The Bee Community, Bryan TX",
    projEaglePathwayFact6Label: "Rango",
    projEaglePathwayFact6Value: "Rango Eagle Scout, 2023",
    projEaglePathwayPhoto1Alt: "Voluntarios esparciendo granito descompuesto junto a una compactadora",
    projEaglePathwayPhoto2Alt: "El sendero de granito descompuesto terminado",
    projEaglePathwayPhoto3Alt: "El equipo de voluntarios al final del día de la obra",
    projEaglePathwayCredit: "Fotos: Matthew Rowan",

    projGViewTitle: "G-View: aplicación para revisar datos de pruebas",
    projGViewDesc: "Desarrollé una aplicación de escritorio para revisar hojas de cálculo grandes con datos de pruebas: graficar los datos, quitar tramos con errores y exportar copias limpias.",
    projGViewLongDesc: "En Baker Hughes, los ingenieros suelen revisar a mano en Excel cientos de miles de filas de datos de pruebas. G-View se encarga de la parte repetitiva: abrir un libro de Excel o un CSV, confirmar dónde empiezan los datos reales, graficar cualquier columna contra varias otras, quitar tramos con errores sin tocar el archivo original y exportar una hoja de cálculo o una gráfica limpia. En un solo día la separé de la aplicación de reportes de dinamómetro que hice con un compañero ese verano, y luego la seguí desarrollando como herramienta independiente.",
    projGViewAlt: "G-View graficando velocidad, par, temperatura del aceite y vibración de un archivo de prueba de demostración",
    projGViewSearch: "Excel CSV TSV Parquet JSONL pandas pyarrow python-calamine matplotlib Tkinter scikit-learn k-means DBSCAN HDBSCAN clustering mezcla gaussiana pytest Inno Setup instalador Velora dinamómetro GitHub Copilot hoja de cálculo gráficas",
    projGViewSection1Heading: "Por qué",
    projGViewSection1Body: "Buena parte de la revisión de datos consiste en repetir unos cuantos pasos en Excel sobre hojas muy grandes: encontrar dónde empiezan los datos, graficar unas columnas, quitar un tramo malo y mandarle a alguien una copia limpia. Con ese tamaño, Excel se vuelve lento y es fácil modificar el original por accidente.",
    projGViewSection2Heading: "Qué hace",
    projGViewSection2Body: "Abre archivos de Excel, CSV, TSV, Parquet y JSONL. Confirma la hoja y el rango de encabezados antes de graficar. Grafica un eje x contra varias series en el eje y, con zoom, desplazamiento y deshacer. Recorta regiones de la salida sin modificar el archivo original. Agrupa puntos con clustering cuando importan los valores atípicos. Guarda el estado de la revisión en una carpeta de proyecto. Exporta un Excel limpio o la gráfica actual como PNG.",
    projGViewSection3Heading: "Cómo empezó",
    projGViewSection3Body: "Zohaib Sheikh y yo desarrollamos Velora, una aplicación que automatiza los reportes de pruebas de dinamómetro. Sus pantallas de revisión de datos podían servir para mucho más que esas pruebas, así que, con GitHub Copilot, las separé en una aplicación independiente en un solo día. Durante el resto del verano agregué clustering, estilos de gráficas, carpetas de proyecto, un instalador y guías técnicas y de usuario.",
    projGViewSection4Heading: "En qué quedó",
    projGViewSection4Body: "La entregué al final de la pasantía. Todavía no hay datos de uso, pero hubo interés de ingenieros de otros grupos. Recomendé que, si tiene buena acogida, la pasen a un lenguaje más rápido y junten a pasantes de software con ingenieros de pruebas para agregar operaciones con columnas sin programar.",
    projGViewFact1Label: "Rol",
    projGViewFact1Value: "único desarrollador",
    projGViewFact2Label: "Tecnologías",
    projGViewFact2Value: "Python, pandas, pyarrow, matplotlib, Tkinter, scikit-learn (k-means, DBSCAN, HDBSCAN, jerárquico, mezcla gaussiana), pytest, Inno Setup",
    projGViewFact3Label: "Dónde",
    projGViewFact3Value: "I+D de ALS de Baker Hughes, Claremore OK",

    /* ---- Proyectos: índice --------------------------------------------- */
    projVeloraTitle: "Velora: automatización de reportes de dinamómetro",
    projVeloraDesc: "Desarrollé con Zohaib Sheikh una aplicación en Python que convierte datos de pruebas de dinamómetro en reportes terminados y ahorra hasta 30 horas por reporte.",
    projVeloraSearch: "dinamómetro reportes de pruebas automatización Velora Baker Hughes GitHub Copilot Excel",

    projAutoscanTitle: "AutoScan: automatización de un escáner 3D",
    projAutoscanDesc: "Automaticé un escáner óptico 3D KEYENCE para que los lotes de escaneo corran sin supervisión, lo que ahorra unas 10 horas de trabajo de operador por lote.",
    projAutoscanAlt: "Soportes impresos en 3D para sujetar piezas en el escáner óptico",
    projAutoscanSearch: "KEYENCE escáner óptico 3D soportes impresión 3D AutoScan Baker Hughes",

    projDynamicsPdfUnifierTitle: "Dynamics PDF Unifier",
    projDynamicsPdfUnifierDesc: "Desarrollé una aplicación de escritorio en Python que une los escaneos, PDF, archivos de Word y código de cada estudiante en un solo PDF por estudiante para calificar.",
    projDynamicsPdfUnifierSearch: "PDF Word iPad calificar Introducción a la Dinámica Schultz unir",

    projKeplingerHeatingTitle: "Análisis de calefacción de Keplinger Hall",
    projKeplingerHeatingDesc: "Estimé la pérdida de calor en invierno del edificio de ingeniería de TU y dimensioné un sistema de radiadores de agua caliente, con Python y Excel.",
    projKeplingerHeatingSearch: "transferencia de calor pérdida de calor radiadores de agua caliente Excel Keplinger Hall Universidad de Tulsa",

    projMusicNotesMatlabTitle: "Detección de notas musicales con MATLAB",
    projMusicNotesMatlabDesc: "Escribí un script de MATLAB que encuentra las notas principales y los armónicos de una canción usando transformadas de Fourier por ventanas.",
    projMusicNotesMatlabAlt: "Gráfica de las notas principales y armónicos detectados en una grabación de trompeta",
    projMusicNotesMatlabSearch: "transformada de Fourier FFT ventanas Hamming espectrograma armónicos notas trompeta",

    projGenderEmploymentCsTitle: "Género y empleo en ciencias de la computación",
    projGenderEmploymentCsDesc: "Usé modelos de regresión lineal y logística en Stata para evaluar si el género afecta la probabilidad de estar empleado en trabajos de computación.",
    projGenderEmploymentCsSearch: "Stata modelo de probabilidad lineal regresión logística errores estándar robustos econometría ECON 4273 Huang",

    projChilledWaterPipelineTitle: "Diseño de una tubería de agua helada",
    projChilledWaterPipelineDesc: "Tracé y dimensioné en Python una nueva tubería de agua helada para el campus de TU; obtuvo 100% con la oferta de menor costo de la clase.",
    projChilledWaterPipelineAlt: "La ruta elegida para la tubería trazada sobre el mapa del campus de TU",
    projChilledWaterPipelineSearch: "fluidos mecánica de fluidos tubería de agua helada trazado envolvente convexa estimación de costos Amiri campus Universidad de Tulsa",

    projNotchedBeamStressReliefTitle: "Alivio de esfuerzos en una viga con muesca",
    projNotchedBeamStressReliefDesc: "Usé simulación en SolidWorks para diseñar un corte en spline que redujo en 42% el factor de concentración de esfuerzos de una viga con muesca en pruebas de flexión.",
    projNotchedBeamStressReliefAlt: "Simulación en SolidWorks de la viga con muesca y alivio de esfuerzos en spline",
    projNotchedBeamStressReliefSearch: "SolidWorks Simulation FEA elementos finitos factor de concentración de esfuerzos Kt spline flexión ES 3023 Kinniburgh",

    projDieselDualCycleTitle: "Comparación de ciclos Diesel y dual",
    projDieselDualCycleDesc: "Modelé ciclos de combustión Diesel y dual en Python con datos de propiedades de la NASA para comparar eficiencia, costo y temperatura máxima.",
    projDieselDualCycleAlt: "Diagrama presión–volumen del ciclo Diesel",
    projDieselDualCycleSearch: "termodinámica ciclo Diesel ciclo dual polinomios de la NASA combustión eficiencia temperatura máxima diagrama P-v",

    projMechanicalFuseTitle: "Fusible mecánico axial",
    projMechanicalFuseDesc: "Diseñé una muesca para que un eslabón de acrílico se rompiera en el centro con la mayor carga posible, usando una búsqueda en Java; dos de tres eslabones de prueba se rompieron en la muesca.",
    projMechanicalFuseAlt: "Tres eslabones de acrílico con muesca después de las pruebas de ruptura",
    projMechanicalFuseSearch: "Java búsqueda exhaustiva muesca en V eslabón de acrílico concentración de esfuerzos Kt ES 3023 Kinniburgh prueba de ruptura",

    projBicycleCrashSeverityTitle: "Predicción de la gravedad de accidentes en bicicleta",
    projBicycleCrashSeverityDesc: "Probé FAMD y submuestreo para predecir la gravedad de accidentes de bicicleta en el Reino Unido, usando SHAP para relacionar los resultados con las variables originales.",
    projBicycleCrashSeverityAlt: "Gráfica resumen de SHAP con el efecto de cada variable en la gravedad del accidente",
    projBicycleCrashSeveritySearch: "FAMD submuestreo SHAP accidentes de bicicleta Reino Unido ES 4863 AI for Engineers Chowdhury",

    projUkCrashHotspotsTitle: "Puntos críticos recurrentes de accidentes en el Reino Unido",
    projUkCrashHotspotsDesc: "Encontré intersecciones del Reino Unido que seguían siendo puntos críticos de accidentes año tras año usando DBSCAN y QGIS, y las confirmé con noticias locales.",
    projUkCrashHotspotsAlt: "Mapa de Inglaterra en QGIS con los grupos de puntos críticos de accidentes",
    projUkCrashHotspotsSearch: "DBSCAN QGIS clustering Kaggle accidentes Reino Unido intersecciones puntos críticos SIG ES 4863 AI for Engineers Chowdhury",

    projLandmineClassificationTitle: "Clasificación de minas terrestres con sensores pasivos",
    projLandmineClassificationDesc: "Comparé árboles de decisión y redes neuronales, ajustados con búsqueda en malla, para clasificar cinco tipos de minas terrestres con datos de sensores pasivos.",
    projLandmineClassificationSearch: "árbol de decisión red neuronal MLP búsqueda en malla UCI sensores pasivos minas terrestres ES 4863 AI for Engineers",

    // Footer
    footerContact: "gao9819@utulsa.edu",
    footerCopyright: "© 2026 Gideon A. Ong",
  },
};
