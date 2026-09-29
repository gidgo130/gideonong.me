# Offline Windows app (Phase D)

Inno Setup installers (and a zip) that put the /learning pages on a computer, so they open
from disk in the default browser with no internet. Plan and status: `learning/learning-plan.md`
→ Phase D and D2.

```
offline/
  build.ps1              Stage learning/, compile, zip. The repo path is $RepoRoot at the top.
  ReadingYourFits.iss    The installer. AppVersion lives in its #define at the top (the only place).
  release-notes.md       Text of every GitHub release (EN + ES), passed to gh --notes-file.
  stage/                 GENERATED, gitignored: the copy that ships + modules*.iss
  dist/                  GENERATED, gitignored: the latest build only
```

## Build

One-time: `winget install JRSoftware.InnoSetup`. Installed for all users it lands in
`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`; with `--scope user`, in
`%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`. build.ps1 finds either (or `$env:ISCC`).

From the repo root (the machine's execution policy is Restricted, hence the Bypass):

```
powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1              # dev build
powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1 -Release     # release build
powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1 -StageOnly   # stage only
```

A build (about a minute) writes to dist\:

| File | What |
| --- | --- |
| `ReadingYourFits-Setup-<v>.exe` | everything, with the component choice (8.4 MB at 1.0.0) |
| `ReadingYourFits-<slug>-Setup-<v>.exe` | one per ready module: hub + that module (3.8–4.9 MB) |
| `ReadingYourFits-<v>.zip` | the whole series for any system (29 MB: zip can't share the decks' common code the way the installer's solid compression does) |

The commit (`git rev-parse --short HEAD`, plus `-dirty` if learning/, the favicon or the licenses
have uncommitted changes) goes into the installed pages' footer and NOTICE.txt. `-Release`
refuses a dirty tree, then adds `dist\release\`: the same files under version-free names
(`ReadingYourFits-Setup.exe`, `ReadingYourFits-<slug>-Setup.exe`, `ReadingYourFits.zip`) plus
`SHA256SUMS.txt`. Those names are what the site links as
`https://github.com/gidgo130/gideonong.me/releases/latest/download/<name>`, so they must not change.

## What ships

Git-tracked and new-but-not-ignored files under learning/ (`git ls-files --cached --others
--exclude-standard`), so the gitignored papers can't slip in, minus `$Exclude` in build.ps1:
workshop/, `*.md`, `*.pdf`, `assets/og/` (link-preview cards) and `fits/*/play/` (the marimo
notebooks need HTTP and a CDN; the pages already hide that link from disk). Plus, from the repo
root: the favicon `assets/glogo.ico` (every page links `../assets/glogo.ico`), `LICENSE` and
`LICENSE-CONTENT` (as .txt), and a NOTICE.txt written by build.ps1 that says what each license
covers (keep it in step with README.md → Licensing). The zip also gets `Reading Your Fits.html`
at its top, which opens learning/index.html. build.ps1 fails if a `.md`, `.pdf` or `.qmd`
reaches stage/.

## Full and per-module installers

Both come from the one .iss (`/DOnlyModule=<slug>` for a module) and share its AppId: one
folder, one entry in Settings → Apps, one uninstaller for everything any of them installed.

- The full installer clears `learning\` first and installs what's chosen. It always offers its
  own defaults (`UsePreviousSetupType=no`), not the last module installer's choice.
- A module installer clears only its own module folder, rewrites the hub files and adds its
  module (Slides and Python still optional). Run several to collect modules.

The component tree is built from `learning/assets/modules.js` (ready modules only) and the
titles in `strings-common.js`, in the language picked for setup. A new module needs no edit
here: add it to modules.js and rebuild, and it gets a component and its own installer. A second
series would need its own group in build.ps1 section 2 (and the pages would need a registry
for it first; learning.js assumes `fits/`).

After every install, the installer appends `window.LEARN_OFFLINE = { version, commit, missing }`
to the installed `assets/modules.js`, where `missing` lists the module folders and files that
are NOT on disk (read from disk, so modules from earlier runs count). The zip carries the same
line with `missing: []`. learning.js reads it (it never exists on the site) to:
- show a missing module as "Not installed" on the hub and in prev/next, with no link;
- hide a module's Slides or Python link when those files are missing;
- send the "gideonong.me" crumb, which points outside learning/, to https://gideonong.me/;
- show "Offline copy · v<version> (<commit>) · Check for updates" in the hub footer, linking
  the releases page.

## Checks before a release

- Installs into a scratch folder (`/VERYSILENT /DIR="<tmp>"`, `/COMPONENTS="hub,fits\rsquared"`
  to pick parts): module A, then module B (no Python), then the full installer, then a module
  installer again with the page only. After each: the files on disk and the last line of
  `learning\assets\modules.js` agree. One uninstall entry throughout. `<tmp>\unins000.exe
  /VERYSILENT` removes everything.
- Open `learning\index.html` from disk in Chrome and Edge, online and offline: hub → each
  module → Slides → "Try it yourself" iframe → back → All modules; EN/ES toggle; OS dark mode;
  the footer line in both languages; console clean apart from the Google Fonts request when
  offline.
- Unzip the zip (entries use `/`), open `Reading Your Fits.html`: it lands on the hub.
- Run the installer once by hand, in Spanish, to see the wizard text.

## Release (see learning-plan.md → Phase D2)

1. Bump `AppVersion` in ReadingYourFits.iss; commit everything.
2. `build.ps1 -Release`; run the checks above.
3. `git tag -a offline-v<v> -m "Reading Your Fits offline <v>"` and push the tag. Tags
   `offline-v*` are protected by a ruleset (no deleting, no moving): tag the right commit.
4. `gh release create offline-v<v> --draft --title "Reading Your Fits <v> (offline)"
   --notes-file learning\workshop\offline\release-notes.md learning\workshop\offline\dist\release\*`
5. Read the draft on github.com, then `gh release edit offline-v<v> --draft=false --latest`.
6. `gh release download offline-v<v> -D <tmp>`: checksums match SHA256SUMS.txt.
7. Never replace an asset of a published release; a fix is a new version.
