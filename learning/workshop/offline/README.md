# Offline Windows app (Phase D)

An Inno Setup installer that puts the /learning pages on a Windows PC, so they open from disk in
the default browser with no internet. Plan and status: `learning/learning-plan.md` → Phase D.

```
offline/
  build.ps1              Stage learning/ and compile. The repo path is $RepoRoot at the top.
  ReadingYourFits.iss    The installer. AppVersion lives in its #define at the top (the only place).
  stage/                 GENERATED, gitignored: the copy that ships + modules*.iss
  dist/                  GENERATED, gitignored: ReadingYourFits-Setup-<version>.exe
```

## Build

One-time: `winget install JRSoftware.InnoSetup`. Installed for all users it lands in
`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`; with `--scope user`, in
`%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`. build.ps1 finds either (or `$env:ISCC`).

From the repo root (the machine's execution policy is Restricted, hence the Bypass):

```
powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1              # stage + compile
powershell -ExecutionPolicy Bypass -File learning\workshop\offline\build.ps1 -StageOnly   # stage only
```

To release: bump `AppVersion` in ReadingYourFits.iss, build, then run the checks below.

## What ships

Git-tracked and new-but-not-ignored files under learning/ (`git ls-files --cached --others
--exclude-standard`), so the gitignored papers can't slip in, minus `$Exclude` in build.ps1:
workshop/, `*.md`, `*.pdf`, `assets/og/` (link-preview cards) and `fits/*/play/` (the marimo
notebooks need HTTP and a CDN; the pages already hide that link from disk). Plus the favicon
`assets/glogo.ico` from the repo root, because every page links `../assets/glogo.ico`. build.ps1
fails if a `.md`, `.pdf` or `.qmd` reaches stage/.

## Choosing what to install

The components page is a tree built from `learning/assets/modules.js` (ready modules only) and
the titles in `strings-common.js`, in the language the reader picked for setup:

```
Learning home page and shared files        always
Reading Your Fits                          the series
  Module 1: Why R² isn't enough            the interactive page
    Slides (English and Spanish)           slides.html + slides.es.html
    Python script and Jupyter notebook     <slug>.py + <slug>.ipynb
  ...
```

Setup types: Everything, Interactive pages only, or Custom. A new module needs no edit here:
add it to modules.js and rebuild. A second series would need its own group in build.ps1
section 3 (and the pages would need a registry for it first; learning.js assumes `fits/`).

After copying files, the installer appends `window.LEARN_OFFLINE = { version, missing: [...] }`
to the installed `assets/modules.js`: the paths the reader left out. learning.js reads it
(nothing else does, and it never exists on the site) to:
- show a left-out module as "Not installed" on the hub and in prev/next, with no link;
- hide a module's Slides or Python link when that part was left out;
- send the "gideonong.me" crumb, which points outside learning/, to https://gideonong.me/.

Every install, repair or upgrade first deletes `{app}\learning`, so modules deselected on a
re-run, and files dropped in a newer version, don't linger.

## Checks before a release

- Silent install into a scratch folder with a partial selection, e.g.
  `ReadingYourFits-Setup-<v>.exe /VERYSILENT /DIR="<tmp>" /COMPONENTS="hub,fits\rsquared,fits\rsquared\slides"`,
  then look at the file list and the last line of `learning\assets\modules.js`. Uninstall with
  `<tmp>\unins000.exe /VERYSILENT`.
- Open `learning\index.html` from disk in Chrome and Edge, online and offline: hub → each
  module → Slides → "Try it yourself" iframe → back → All modules; EN/ES toggle; OS dark mode;
  console clean apart from the Google Fonts request when offline.
- Run the installer once by hand, in Spanish, to see the wizard text.
