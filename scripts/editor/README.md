# Local content editor (dev-side tool, never deployed)

Edits the site's content files in place from a local web page shown in its own window. Phase 1
edits the EN/ES strings in `js/translations.js` (**Site text** tab); Phase 2 edits projects,
experience and tags as entries (**Content** tab); Phase 1b checks and publishes the CV /
résumé PDFs (**CV & résumé** tab); Phase 3 runs the transcript scripts and edits their inputs
(**Transcript** tab); images come later (see `staging/editor-plan.md`). `scripts/` is in
`.vercelignore`, so nothing here is published. The tool never runs a git write command — you
commit.

## One-time setup (Windows, PowerShell, from the repo root)

```powershell
$py = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"   # not `python` (that's Inkscape's)
& $py -m pip install -r scripts\editor\requirements.txt
powershell -ExecutionPolicy Bypass -File scripts\editor\make-shortcut.ps1
```

This installs Flask (the server), pywebview (the window; it uses the WebView2 runtime that
ships with Edge — no Edge profile, no Edge window, so Cold Turkey Blocker leaves it alone) and,
for the CV tab, python-docx, pdfplumber, Pillow and docx2pdf (which brings pywin32). The
second command puts a **Site editor** shortcut on the desktop that runs `launch.pyw` with the
real `pythonw.exe` (no console window). Re-run it any time; it just rewrites the shortcut.

## Using it

Double-click **Site editor**. A window opens with the editor. A second double-click brings that
window to the front. Closing the window stops the editor; with unsaved drafts it asks first
(the drafts are autosaved either way).

- Keys are grouped by the comment sections of `js/translations.js`; EN and ES sit side by
  side. Search matches keys and text in both languages, ignoring accents.
- Each key shows its parity: **EN + ES**, **ES = EN**, **TODO**, **EN only**, **ES only**.
  The pills in the top bar count them; click one to filter. **Needs attention** shows
  everything that is not plain EN + ES, has a warning, or has a draft.
- Typing makes a draft (orange edge). Nothing touches disk until **Review & save**
  (Ctrl+S), which lists every change in words plus the exact unified diff, then writes
  exactly that. Drafts are also autosaved to `.local/drafts/`; if the editor is closed
  with drafts, the next launch offers to restore them.
- Before writing, the previous file is copied to `.local/backups/<timestamp>/`. **Restore…**
  lists those sets, shows what restoring would change, and restores one (backing up the
  current file first).
- If `js/translations.js` changes on disk while the editor is open (VS Code, Claude Code,
  git), a banner appears and saving is refused until you click **Reload**; drafts are kept
  and re-applied.
- **Preview ↗** opens `http://127.0.0.1:5501/` in your normal browser: a read-only copy of
  the site that serves your drafts in place of the saved file, and answers 404 for
  everything `.vercelignore` excludes, as the live site would. Each request is resolved on
  disk before that check, so a different letter case or an 8.3 short name cannot reach an
  excluded file, and only requests addressed to `127.0.0.1:5501`/`localhost:5501` are
  answered (403 otherwise). Live Server on :5500 keeps showing saved files only.

### Validation
Errors block a save; warnings don't. Only errors the draft **introduces**, or errors on
keys the draft **touches**, block — anything pre-existing elsewhere is shown in a banner.

| Errors | Warnings |
|---|---|
| Key missing in EN or ES | ES identical to EN (allow-list: Python, CAD, MATLAB, emails, templates…) |
| `TODO` in visible text | `TODO` on hidden entries (`visible: false`, `listing: "hidden"`) |
| HTML in a string | Voice words (leveraged, spearheaded, passionate, showcasing, moreover…) |
| File outside the supported JS subset, or a key that appears twice in one object (the file becomes read-only; the message names the line) | |
| The file could not be written (open in another program): the save answers "close it and retry", nothing changes, drafts are kept | |

## Content tab (Phase 2: projects, experience, tags)
Entries, not keys. The left list shows projects in the order the site renders them (featured,
then the index with pinned first, then unlisted / hidden), roles by date, and the tag
vocabulary with how often each tag is used. The form on the right edits one entry:
- every text field is EN | ES side by side (title, description, long description, search
  text, alt texts, sub-page sections / facts / photos / credit; role, organization, bullets);
  the key (`proj<SlugCamel>Title`, `expBakerHughesBullet3`, …) is named by the CLAUDE.md
  conventions and never shown. Text of keys that already exist is a Site text draft (the two
  tabs share one translations.js review); new keys are inserted after the entry's block;
- context, listing, "Part of" role, tags, dates (season / month / year, optional end, with the
  sortDate the dev check wants suggested), featured / order / pinned, image and thumbnail
  pickers (files under `assets/images/`), home layout and collage gallery, sub-page content
  (sections, quick facts, photos, report PDF, credit) and **Create sub-page** (copies the
  `projects/g-view.html` shell with the slug, title and description); layout, current-role
  flag, band colors and visibility for roles;
- **Add project / role** (slug + EN/ES title; new entries start hidden with today's season),
  **Hide** (listing → hidden / visible → false), **Delete…** (confirmed; the entry, the keys
  nothing else references, and the sub-page — moved to the backup set); **Add tag** and delete
  (only when no entry uses it). The slug never changes here (a rename wizard comes later).

**Images (Phase 5).** **Import…** beside every image field (main image, thumbnail, collage
cell, sub-page photo, band image) takes a JPG or PNG from anywhere (up to 25 MB), applies the
phone's orientation, converts the colour profile to sRGB, drops every camera tag, GPS position
and profile, resizes by preset (main: fit 1600; thumbnail: 4:3 at 800 × 600; wide: 16:9 at
1600 × 900; portrait: fit 1250; as is: metadata strip only, for plots) — never upscaling — and
names the file from the original (`IMG_2041.jpg` → `img-2041.jpg`, `-thumb` for thumbnails)
under `assets/images/<projects|experience>/<slug>/`. Alt text in both languages is required
before the import is accepted; the field and the alt keys are set at once. The file lives in
`.local/drafts/images/` until Review & save copies it into `assets/images/` (a replaced file
is backed up first); the preview shows it immediately. The **Images** sub-tab lists every file
with its size, what uses it (entries and HTML pages) and warnings (EXIF, GPS, profile, over
600 KB or 2000 px); files nothing uses can be removed (into the backup set on save). Existing
files are never re-encoded.

Saving writes the data files with span edits that touch only the changed lines (comments,
blank lines and every untouched entry stay byte for byte), translations.js with the new /
removed keys, and the shells; every file is backed up first and re-parsed by the tokenizer
before it is written. The :5501 preview serves all drafts (data files, keys, shells), so a
hidden test entry can be checked on `/projects/<slug>.html` before it is saved or listed.

The dev check (`siteData.checkData`, js/data-helpers.js) is ported to Python
(`core/site/datacheck.py`) and gates every save — errors block, warnings do not, only errors
the draft introduces or touches count (as on the Site text tab):

| Errors | Warnings |
|---|---|
| Missing or empty EN/ES text on a visible entry; TODO or HTML in it; a blocklist hit | Empty text on a hidden entry; ES = EN; voice words |
| Unknown tag id; duplicate slug; "Part of" role missing or hidden | Unused `proj…` / `exp…` / `tag…` keys |
| Image, thumbnail, gallery, photo, PDF or sub-page file that does not exist | Two visible roles marked current |
| Malformed `dates`; sortDate that disagrees; unknown listing / context / layout / homeLayout | ES tag label much longer than EN |
| More than 3 featured; featured on a non-index entry; gallery / sub-page shape problems | |

## CV & résumé tab (Phase 1b: check & publish, no editing)
You keep editing the six masters in Word (`staging/cv-masters/`, gitignored). The tab only
reads them.

- **Export** (all, or one row) turns each master into `staging/cv-out/<same name>.pdf` with a
  **private, hidden Word instance** that opens the master read-only and quits when done — your
  own Word session is never touched (docx2pdf's `convert()` would have attached to it and quit
  it). A master that is open in Word (its `~$…` owner file exists) is skipped with "close it in
  Word first", because what Word shows may not be on disk yet. Progress streams into the log
  panel; closing the window during an export asks first.
- **Run checks** (no Word; runs automatically after an export and on load):
  * *One-line fit* — for every "Role · Org ⇥ Date" line, the text, one space and the date are
    measured with Georgia itself (`C:\Windows\Fonts\georgia*.ttf`, bold / italic faces as used)
    against the room between the paragraph's indent and its right tab stop, taken from the
    document. **Details** shows a space-left meter per line; within 3% is "tight".
  * *PDF check* (the authority): every entry line must sit on one line of the PDF, every
    paragraph of the master must be in the PDF (otherwise it was edited after the export →
    "stale"), a PDF older than its master is stale, and the résumé must be exactly one page.
  * *Confidentiality* — every term in `staging/editor-private/blocklist.txt` (gitignored; one
    `term | reason` per line, `#` comments, case- and spacing-insensitive) must be absent from
    the PDF text. The +1 (918) number is allowed in these PDFs (decision 9) and stripped first.
  * *Voice words* (same list as the site text; "leveraged" is allowed in the Spinelli bullet)
    and *EN/ES parity* (paragraph and entry counts, bullets per entry, numbers per paired
    paragraph) are warnings.
- **Publish…** shows the dry run for a date (default today, `YYYYMMDD`): which PDFs are added or
  overwritten under `assets/pdfs/<cv|resume>/<en|es> Gideon Ong <CV|Resume> <date>.pdf`, and
  which older dated files of the same type + language move to the backup set. Errors (missing,
  stale or wrapped PDF, résumé > 1 page, blocklist hit) block it; warnings do not. Publishing
  backs up every file it overwrites or moves, copies the PDFs, then runs
  `node scripts/build-docs-manifest.js` exactly as the pre-commit hook would (no node → a
  warning; the hook regenerates it at commit). The Full CV is never published.
- **Restore…** (Site text tab) lists publish sets too. Restoring one writes the old PDFs back
  but does not remove the newer published files — delete those by hand if you really want the
  old ones to win (the manifest picks the newest date).

## Transcript tab (Phase 3: the scripts stay in charge)
`scripts/transcript/` keeps doing the work (see its README); the tab runs its two scripts as
subprocesses with the editor's own interpreter and shows their output live, and edits their
JSON inputs without reformatting them. One job (parse, build or a Word export) runs at a time.

1. **Source** — lists `references/transcripts/*.pdf` (gitignored; TU's PDFs hold the student
   ID). **Parse** backs up `transcript-data.json`, runs `parse_transcript.py`, and shows the
   unified diff of what changed. Only files in that folder can be parsed.
2. **Course titles** — every entry of `course-titles.json` joined with the transcript: code,
   TU's printed title and the terms it appears in, EN, ES, source, verified. Filters:
   *Needs attention*, *Missing* (on the transcript, no title yet — an error until both EN and
   ES are typed; new codes are inserted in sorted position), *Unverified*, *ES = EN*, *Drafts*.
   Special-topics codes (`ES 4863`, `ME 4863`) have one row per section title.
3. **Profile** and 4. **Adjustments** — forms over `profile.json` and `adjustments.json`
   (majors / minors one per line; an adjustment's block must exist on the transcript, credits
   0–6, a known grade, a code that TU does not already print).
5. **Build** — `make_transcript.py` with Word files into `scripts/transcript/output/` and, with
   *Also PDFs*, PDFs into `staging/transcript-out/` (private Word instance). *Strict* fails on
   unverified titles; *Date* overrides the print date in the file names. The summary pulls the
   script's own messages (STOPPED reasons, ADJUSTMENT lines, unverified titles) out of the log.
   Drafts must be saved or discarded first — the build reads the files on disk. "Rebuild
   needed" appears when an input changed after the last build; a GPA that differs from the
   `GPA:` line in the CV masters is flagged.
6. **Publish…** — copies the newest built EN + ES PDFs to `assets/pdfs/transcript/<en|es>
   Gideon Ong Transcript <date>.pdf` (the date they were built with), moves older dated
   transcript PDFs to the backup set, and regenerates `js/docs-data.js`. Blocked when a
   language is not built, the build is older than an input, EN and ES carry different dates, or
   the blocklist hits (fill the student-ID / birth-date placeholders in
   `staging/editor-private/blocklist.txt` so this gate means something).

**Review & save** (Ctrl+S) lists the changes per JSON file in words plus the exact diff; the
files are written back in their own layout (`indent=2`, LF, no trailing newline — checked on
every load; a file in another layout is read-only here). Backups, changed-on-disk refusal,
autosave and Restore work as on the Site text tab.

## How it stays lossless
`core/jsdata.py` tokenizes the file with exact character spans and re-emits it. On every
load it checks that re-emitting with no edits reproduces the file byte for byte
(encoding, BOM and line endings included). A string edit replaces only the characters
between that value's quotes. Anything outside the subset (template literals, spreads,
calls, identifiers as values) makes the tool refuse to write and name the line.

## Safety, launch and shutdown
- Every `/api/*` request except `ping` needs a per-launch random token (in the URL the
  window opens), a `Host` of `127.0.0.1:5510`/`localhost:5510` and no foreign `Origin`, so
  a web page in your normal browser cannot drive the editor.
- `launch.pyw` starts both servers in background threads and then opens the window with
  `webview.start()`, which blocks. When it returns — the window was closed, destroyed by the
  watchdog, or killed — the servers stop, the lock file goes, and the process ends with
  `os._exit`, so no `pythonw.exe` can stay behind. Killing the process itself takes the
  servers with it (they are threads of it).
- Crash fallback: no heartbeat from the page for 10 minutes **and** no drafts → the watchdog
  destroys the window, which ends the process the same way. It never exits while drafts exist.
- Second launch: if the lock file's server answers, the launcher asks it to focus its window
  (`POST /api/focus`) and brings it to the front. If the server answers but reports no
  window, that process is ended and a fresh editor starts.
- Logs: `.local/logs/editor.log`. Lock: `.local/editor.lock`. WebView2 storage:
  `.local/webview/`. Everything under `.local/` is gitignored.

## Tests (stdlib unittest, on a temp copy of the real files)

```powershell
cd scripts\editor
& $py -m unittest discover -s tests
```

For browser checks, `& $py scripts\editor\launch.pyw --no-window` starts both servers without
a window and prints the tokenized URL (it exits ~10 min after the last page heartbeat if no
drafts exist, or on Ctrl+C). The real Word export test runs only with `EDITOR_WORD_TESTS=1`
(it starts a private Word for a few seconds); tests that read the private masters skip when
`staging/cv-masters/` is absent.

Covers: round-trip of every data file, one edit = one changed line, no-edit save = identical
file, changed-on-disk → refused (including a same-size rewrite), unsupported syntax or a
duplicate key → refused with line number, save gating, a write that fails because the file is
open elsewhere → 409 with file and drafts untouched, backups/restore (and that a backup path
cannot reach a sibling set), autosave, the token/Host/Origin checks (including `/api/focus`
and `/api/open-preview`), the preview's Vercel-style 404s, draft overlay, Host/Origin
allow-list, letter-case and 8.3 short-name variants of excluded paths (the short-name test
skips where the volume has no 8.3 names), hidden-key prefixes from both data files, and a scan
that fails if the editor's code contains a git write command. Phase 1b (`test_cv.py`, on
synthetic .docx/.pdf files with made-up text): the master table matches the manifest's
filename rule, Word owner-file detection, paragraph kinds and resolved fonts, the fit rule
(fits / tight / overflow; measurement agrees with Word's PDF within 1 pt), PDF line grouping
with hyphen-join tolerance, blocklist parsing and the phone exception, voice words with the
Spinelli exemption, EN/ES parity, the publish plan and apply (add / overwrite / move to backup,
manifest regenerated), every gate (2 pages, wrapped line, stale PDF, edited text, blocklist)
blocking, the background export job refusing an open master, and the `/api/cv/*` token checks.
Phase 3 (`test_transcript.py`, `test_jobs.py`, on temp copies of `scripts/transcript/`): the
four real JSON inputs round-trip byte for byte (other layouts detected or refused), one edit =
one diff line, title rows joined with the transcript, missing codes and sorted insertion, all
validation rules, drafts → review → save → changed-on-disk refusal and autosave, the parse job
restricted to `references/transcripts/` and backing up first (stand-in parser), the real
builder run docx-only (plus `--strict` stopping), publish plan / apply / gates (not built,
stale, mixed dates, blocklist), the job runner and subprocess streaming, and the
`/api/transcript/*` token checks. Phase 2 (`test_spans.py`, `test_content.py`, on temp copies
of the data files with stand-in assets): every span edit changes only its lines and re-parses,
comments between entries survive a delete, the emitter reproduces the files' own blocks,
key add / delete lands in the right translations blocks, key naming and referenced-key
rules, rendered order, the dev-check port (no errors on today's files, every seeded problem
caught), and the service: add → sub-page → index → save → delete → save leaves both data files
and translations.js byte-identical, bullets reorder, current-role flag, tag add / refuse /
delete, blocked saves, changed-on-disk refusal, autosave. Phase 5 (`test_images.py`): a
synthetic phone JPEG (EXIF camera fields, GPS IFD, orientation 6, ICC profile) comes out with
no metadata at all, upright and at the preset size; every preset; PNG stays PNG without text
chunks; refusals (GIF, non-image, 25 MB, unknown preset) and names; the repo's own images
carry no warnings; the service flow (field + alt keys set, preview override, review, save
writes clean files, replace backs up, delete refused while used, HTML references protect the
headshot, discard drops staged bytes) and the multipart endpoint with its token check.

## Files
| File | What it is |
|---|---|
| `launch.pyw` | Lock, servers, pywebview window, watchdog, shutdown (double-click target) |
| `app.py` | Flask app and the `EditorState` (drafts, save, backups, heartbeat, focus) |
| `core/jsdata.py` | Tokenizer / span tree / lossless re-emit |
| `core/site_text.py` | translations.js → keys, sections, parity, edits |
| `core/validate.py` | Rules, allow-list, save gate |
| `core/backups.py` | Backup sets, atomic write, restore, pruning (60 days / 100 sets) |
| `core/review.py` | Change list + unified diff |
| `core/preview.py` | Read-only preview server with `.vercelignore` rules and draft overlay |
| `core/cv/masters.py` | The six masters (file, variant, language, publish type), PDF paths, Word owner-file check |
| `core/cv/docxread.py` | Read a master into paragraphs with resolved bold / italic / size, tab stop, indents (read-only) |
| `core/cv/fit.py` | One-line fit rule measured with Georgia (Pillow) |
| `core/cv/export.py` | .docx → PDF through a private Word instance (pywin32) |
| `core/cv/pdfcheck.py` | Page count, line grouping, entry-line and coverage checks (pdfplumber) |
| `core/cv/scans.py` | Blocklist, voice words, EN/ES parity |
| `core/cv/publish.py` | Publish plan + apply into assets/pdfs/, manifest regeneration |
| `core/cv/service.py` | Cached checks, the background export job, publish — what the CV page talks to |
| `core/spans.py` | Span edits on the token tree: replace any value, insert / delete properties and array items, re-parse check |
| `core/emit.py` | JS values in the data files' own style (inline vs one-per-line by property name) |
| `core/site/datafiles.py` | The three data files as entry dicts; minimal span edits on save |
| `core/site/keys.py` | Key naming by the conventions; which fields hold keys; slug rules |
| `core/site/order.py` | Rendered order (featured / index / roles), date rendering, suggested sortDate |
| `core/site/datacheck.py` | Python port of `siteData.checkData` as errors / warnings |
| `core/site/service.py` | Content drafts, text-field resolution, add / delete / shells / tags / images, review, save, preview overlay |
| `core/site/images.py` | Image import: orientation, sRGB, metadata strip, presets; inspect / scan for the Images panel |
| `core/jsonfile.py` | JSON file that re-emits byte-for-byte (layout detected and proven on load), path edits, change lists |
| `core/jobs.py` | One background job at a time with a live log; subprocess runner that streams output |
| `core/transcript/titles.py` | course-titles.json rows joined with transcript-data.json; edits; validation |
| `core/transcript/profile.py` | Validation for profile.json and adjustments.json |
| `core/transcript/service.py` | Drafts / review / save of the inputs, parse and build jobs, publish — what the Transcript page talks to |
| `static/` | The pages: index.html + app.js (site text), content.html + content.js, cv.html + cv.js, transcript.html + transcript.js, common.js, app.css |
| `tests/` | unittest suite |
| `make-shortcut.ps1` | Desktop shortcut with the full pythonw.exe path |
