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

**About (the About page's lists).** The **About** sub-tab edits `js/about-data.js` — the
books strip, the interview FAQ and the interesting-sites list, each with inline EN | ES text
(no translations keys), a `visible` flag per entry, ↑ ↓, add (id + the two texts; new
entries start hidden) and delete — and, per list, a **Shown on the site** checkbox that sets
or removes the `hidden` attribute of that block in `about.html` (the whole block; one
attribute in the review's diff). Sites carry a URL (`https://…` or a site-relative path) and
an "opens in the same tab" flag; books take a cover through the image import (preset
portrait, into `assets/images/about/books/`, no alt text — the strip is decorative). Rules:
empty EN or ES, TODO, HTML, a missing cover or a bad URL are errors on a visible entry
(warnings on a hidden one); voice words and ES = EN are warnings. A reordered list is
re-emitted whole, one entry per line, in the file's own style.

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

## CV text tab (Phase 4: import + proof, editor, apply to the masters by two routes, export & check)
The full CV editor comes in four steps. **Import masters…** (4a) reads the six Word masters
into one private content set, `staging/cv-content/content.json` (gitignored, like the
masters): header (name, title words per variant, contact), sections, and items — entry lines
as role · organization · date, bullets and plain lines under them — each with EN + ES text
and include flags per variant (Full / Professional / Résumé), with the item order kept per
variant. Items are shared across variants only when both languages match word for word; the
report lists near-duplicates (same English, different Spanish), paragraphs with no twin in
the other language (imported with empty text there), and formatting notes (a role that is not
bold, a separator that is not " · "). Slot maps in `staging/cv-content/slots/` record, per
master, which paragraph each item lives in and the exact run formatting. The import is
refused while the tab holds unsaved edits.

**The proof.** Before anything is written, every master is re-rendered from the imported text
into a temporary copy and compared with the original: paragraph count, paragraph properties,
run formatting and text (after dropping spell-check markers, cached page breaks and revision
ids), and every other package part. One difference blocks the import and names the
paragraph. On 2026-09-29 all six masters passed. The masters are never modified by this step;
your own check is Word › Review › Compare against a backup.

Masters are read with python-docx and must be paragraphs only (no tables, fields, hyperlinks,
content controls or tracked changes) — anything else refuses the import naming the paragraph.

**The editor (4b).** The variant switch (Full | Professional | Résumé) picks which document
you are looking at; the left list shows the header, then every section with its items in that
document's order, and after them, greyed, the section's items that are only in other
documents. The `F P R` marks on each row say where it appears. The form on the right edits
one thing:
- an **entry**: role, organization and date, EN | ES side by side (the role is written bold,
  the organization after " · ", the date at the right tab); "In these documents" checkboxes
  per variant; the **one-line fit** table — one row per document the entry is in, an EN and
  an ES meter each — measured exactly as the CV & résumé tab measures the file (Georgia via
  Pillow, the master's own tab stop and indents, the text as it would be written), live while
  you type: green fits, amber within 3 %, red overflows (that is an error for that document);
  its bullets and lines in this document's order as cards (EN | ES, their own checkboxes,
  ↑ ↓ within this document, Delete), then the ones not in this document greyed, and
  **Add bullet / Add line** (into this document; tick the others in the card);
- a **line** (a skills line, an honour): its text EN | ES and its checkboxes;
- a **section**: its heading EN | ES (a section is in a document when one of its items is);
- the **header**: the name, the title line per variant (the résumé masters have none), and
  the contact line — the +1 (918) phone lives there and nowhere else (decision 9).
Items and bullets are shared: an edit changes every document the item is in. When one
document should say something different, **Duplicate into <Document>** (on the item form or
a bullet card, shown while the item is in two or more documents including the current one)
puts a copy with the same text in its place in the current document only and takes the
original out of it; edit the copy afterwards. An entry's copy takes the bullets it showed in
that document. ↑ ↓ on an item moves it within its section in the current document only; ticking a document puts the
item after its nearest neighbour from the current view (taking an entry out of a document
takes its bullets out too). **+ Add item…** under a section asks for the kind (entry or line)
and the English text, which names the item; the item starts in the current document only. A
new bullet or line needs both languages before saving. **+ Add section…** (bottom of the
list) takes a heading in both languages; an empty section can be deleted from its form.
**Delete…** is confirmed and lists the documents the item leaves. Nothing touches disk until
**Review & save** (Ctrl+S): the change list in words, a table of what Apply would do to each
master (paragraphs rewritten / added / removed), the last apply (route, time, backup) with a
**Cross-check** button, the Word edits found since the last apply (below), the gate, and the
exact content.json diff. Three ways out: **Save** writes `staging/cv-content/content.json`
only (backed up first, atomic); **Apply with python** and **Apply with Word** also rewrite
the Word masters (below). Drafts autosave to `.local/drafts/cvtext.json`; changed-on-disk
refusal, Reload, Discard and the restore banner work as on the other tabs.

**Apply.** Every master is rendered in memory first: the slot map's paragraphs are
re-read from the file as it is now (so a formatting tweak made in Word is what gets reused),
only paragraphs whose text differs from the content are rewritten (their run formatting kept,
the whole part written into its first run), a new item clones the nearest paragraph of its
kind — the closest entry in the same section, the closest bullet under the same entry, the
previous section's heading — with the new text, removed or unticked items lose their
paragraphs, and the body is put in the content's order. Each rendered file must then pass a
self-check: read back, its paragraphs are exactly the content's items with the content's text
and every other package part (styles, numbering, settings) is untouched — one failure and
nothing is written (the Word route comes with 4d). Then content.json, the six masters and the
six slot maps go to a backup set, the changed masters are written atomically, the slot maps
and the text hashes are rebuilt from the files as written, and content.json is saved. Apply
needs the whole content set error-free (a pre-existing empty or overflowing paragraph must
never reach a master — the résumé's IEL line blocks it until it has Spanish), and refuses
while a master to be written is open in Word (`~$` owner file: "close it in Word first"). Your
own check afterwards: Word › Review › Compare the master against its copy in the backup set.

**Two routes, both always there.** *Apply with python* edits the files directly
(python-docx; fully testable, byte-exact on untouched paragraphs). *Apply with Word* plans
the very same operations (which paragraphs to rewrite part by part, which to copy, move or
delete) and carries them out in a **private, hidden Word instance** on a temp copy of each
master — the role, organization and date are replaced inside their own ranges so each keeps
its formatting, a new paragraph is a copy of its template, nothing is ever inserted after
the final paragraph mark, bookmarks are removed — then the copy is checked exactly like the
python result on its paragraphs (the wanted items, their text and kinds); the package parts
Word re-saves on its own (docProps, settings, footnotes / endnotes, list definitions; more
on a file Word had never saved) are listed as notes, not failures. Word must be installed;
masters you have open in Word block both routes. Use python by default; use
Word when a python result looks wrong in Word, or to see whether the two agree:
**Cross-check with Word / python** reruns the last apply through the other route from that
apply's backup set (its masters and slot maps) against the content as applied, and compares
each written master with the file on disk — paragraph count and kinds, every paragraph's text
and its resolved bold / italic / underline / size runs (raw XML is not compared: the two
write it differently). Nothing is written by a cross-check; it needs the backup set to still
exist and no unsaved drafts. The review names the route of the last apply.

**Export & check.** After an apply (banner button) or any time (top bar), the masters last
written — all six when none are recorded — are exported to PDF and the CV & résumé tab's
checks run on them (one-line fit, every entry line on one line in the PDF, the résumé one
page, blocklist, stale PDFs), shown per master with the job log. Publishing stays on the CV &
résumé tab (Publish…), where the same checks gate it.

**Word edits since the last apply.** Each paragraph's text is hashed when the tool writes
or imports it. A paragraph whose text now reads differently was edited in Word; the review
lists it per master with Word's text beside the tool's: **Pull into content** makes it a
normal draft edit (the content takes Word's words — for an entry its role, organization and
date), **Discard** lets Apply overwrite it; *Pull all* / *Discard all* per master. Apply is
refused while any is unresolved. A change beyond text (a paragraph added or removed, a
bullet turned into plain text) is structure drift: the review says so and asks for **Import
masters** again, which rebuilds the content set from the files (backing up the old one).
Formatting-only edits are never drift.

One structural rule for the content: a plain line that follows an entry is read as that
entry's sub-line on the next import, so section-level lines belong in sections without
entries (Skills, Honors) or before the first entry.

Validation (errors block a save, warnings do not; only errors the draft introduces or on
items it touches block — the résumé's IEL line, imported with no Spanish, stays a
pre-existing error until you type it or untick Résumé on it):

| Errors | Warnings |
|---|---|
| Empty EN or ES on an item that is in any document (entries: role and date; the organization may be empty) | Voice words (same list as the site text; "leveraged" is allowed in the Spinelli item) |
| `TODO` or HTML in a text | A GPA line that disagrees with the transcript's cumulative GPA (Transcript tab) |
| A blocklist term (`staging/editor-private/blocklist.txt`; the (918) phone is allowed — this text only becomes the CV / résumé PDFs) | An entry line within 3 % of its width in a document it is in |
| A degree line (under the Education entry) naming a degree or minor that `scripts/transcript/profile.json` does not list in that language (decision 4) | Degree lines unchecked because profile.json is not readable |
| An entry line that overflows its width in a document it is in (that document only) | |

The Word-route tests run only with `EDITOR_WORD_TESTS=1` (a private Word for about a
minute); the plan of operations and the pure simulation are tested without Word.

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
delete, blocked saves, changed-on-disk refusal, autosave; the About lists: the data file
round-trips, one edit = one line, add / delete / a reorder that comes back byte-identical, the
`hidden` toggle changes one attribute, every rule, and the service flow (drafts, gate, review
with both files, save, and the reverse edits restoring both files byte for byte). Phase 5 (`test_images.py`): a
synthetic phone JPEG (EXIF camera fields, GPS IFD, orientation 6, ICC profile) comes out with
no metadata at all, upright and at the preset size; every preset; PNG stays PNG without text
chunks; refusals (GIF, non-image, 25 MB, unknown preset) and names; the repo's own images
carry no warnings; the service flow (field + alt keys set, preview override, review, save
writes clean files, replace backs up, delete refused while used, HTML references protect the
headshot, discard drops staged bytes) and the multipart endpoint with its token check.
Phase 4a (`test_cvtext.py`): synthetic masters with the real shapes (split runs with revision
ids and spell-check markers, right-tab entry lines, numbered bullets) read into merged spans
and classified; unsupported constructs refused; merge shares items only when EN and ES both
match and keeps per-variant order; a pairing gap imports with empty text; the proof passes on
the synthetic set and, when present, on all six real masters; an edited render changes only
its paragraph and re-imports to the new text; the service writes the content set only when
every master is lossless, backs up a previous set, and refuses unsupported or missing masters.
Phase 4b (same file): every operation (text edit, include on / off with its order placement,
move in one variant only, add item / child, delete) and every refused one; each validation
rule on a hand-built content set, the Spinelli exemption, the phone allowance, the degree rule
against a profile, the GPA cross-check, fit results per variant, and the gate (pre-existing
errors block only once touched); the fit meter equals `fit.check_doc` on the synthetic masters
and, when present, on every entry of all six real masters, goes red when a role is lengthened
and amber within 3 %, and borrows a sibling's geometry for a new entry; review (change list,
which masters would change, the diff), save (backup, reload, lossless), no-edit save, blocked
save, changed-on-disk refusal with the draft re-applied, import refused with a draft, autosave
offered and restored, and the `/api/cvtext/op` endpoint with its token check. Phase 4c: a
no-edit render of every master is lossless; one bullet edit changes exactly that paragraph's
text; a new bullet, entry, section-level line and section clone the right neighbour (same
paragraph properties, right place); removed and unticked items lose exactly their paragraphs;
a move keeps the element; an empty text is refused; drift found from a python-docx edit of a
master (bullet and entry), pull and discard both work, a formatting-only edit is no drift and
its formatting is reused, a paragraph added in Word is structure drift; apply refused for an
open master, for a pre-existing error, and before any write when the self-check fails; a
full apply backs up thirteen files, writes only the changed masters, re-imports to the
content, rebuilds slots and hashes, and is a noop afterwards; the apply / drift / section
endpoints. On the real masters (when present): the no-edit render is lossless, and an apply
on a temp copy reads back through a fresh import. Phase 4d: the Word route's plan equals the
python route's report for the same edit set (part-wise entry rewrites with descending
offsets, the appended paragraph at the end, a move as a move) and its simulation reproduces
the python render's paragraphs; an empty text is refused before Word; the last apply is
recorded and shown; the cross-check refuses with drafts, without an apply or without its
backup set; the relaxed self-check lets Word's re-saved parts differ but not styles.xml;
`compare_layout`; Apply with Word refuses cleanly when Word is absent and writes nothing;
export & check through the app with the fake export. With `EDITOR_WORD_TESTS=1`: the Word
route renders the edit set, passes the relaxed self-check, matches the python route's layout
(kinds, texts, run formatting, the appended bullet's paragraph properties), a full Word apply
cross-checks against python and a python apply cross-checks against Word. Duplicate: a shared
bullet and a shared entry (with its shown bullets) split into a copy for one document, the
original keeps the others, the order position is kept, refusals, the render of that document
adds one paragraph and removes one with the same text, and the change line names it.

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
| `core/cv/importer.py` | Masters → spans, structure, EN/ES pairing, merge into the content set, the losslessness comparison |
| `core/cv/renderer.py` | Paragraph writer (one run per formatting span), the forced re-render the proof uses, `plan_master` (preview), and the edit-aware render: live slots, clone templates, `render_master`, `self_check`, `rebuild_slots` |
| `core/cv/content.py` | Pure operations on the content set: text edits, include per variant, move, add item / child / section, delete, the per-variant listing |
| `core/cv/cvcheck.py` | Validation of the content set (empty / TODO / HTML / blocklist / voice / degree / GPA / fit) and the fit meter on synthetic paragraphs |
| `core/cv/wordroute.py` | The Word route: the plan of paragraph operations (no Word), its plain-list simulation, and the private-Word execution on a temp copy |
| `core/cv/textservice.py` | Import with the proof gate; the draft, autosave, review, save; drift (pull / discard), apply by either route, the last-apply record and the cross-check — what the CV text page talks to |
| `core/spans.py` | Span edits on the token tree: replace any value, insert / delete properties and array items, re-parse check |
| `core/emit.py` | JS values in the data files' own style (inline vs one-per-line by property name) |
| `core/site/datafiles.py` | The three data files as entry dicts; minimal span edits on save |
| `core/site/keys.py` | Key naming by the conventions; which fields hold keys; slug rules |
| `core/site/order.py` | Rendered order (featured / index / roles), date rendering, suggested sortDate |
| `core/site/datacheck.py` | Python port of `siteData.checkData` as errors / warnings |
| `core/site/service.py` | Content drafts, text-field resolution, add / delete / shells / tags / images, review, save, preview overlay |
| `core/site/images.py` | Image import: orientation, sRGB, metadata strip, presets; inspect / scan for the Images panel |
| `core/site/about.py` | The About page's three lists as one data file (js/about-data.js), the `hidden` attribute of their blocks in about.html, and their checks |
| `core/jsonfile.py` | JSON file that re-emits byte-for-byte (layout detected and proven on load), path edits, change lists |
| `core/jobs.py` | One background job at a time with a live log; subprocess runner that streams output |
| `core/transcript/titles.py` | course-titles.json rows joined with transcript-data.json; edits; validation |
| `core/transcript/profile.py` | Validation for profile.json and adjustments.json |
| `core/transcript/service.py` | Drafts / review / save of the inputs, parse and build jobs, publish — what the Transcript page talks to |
| `static/` | The pages: index.html + app.js (site text), content.html + content.js, cv.html + cv.js, cvtext.html + cvtext.js, transcript.html + transcript.js, common.js, app.css |
| `tests/` | unittest suite |
| `make-shortcut.ps1` | Desktop shortcut with the full pythonw.exe path |
