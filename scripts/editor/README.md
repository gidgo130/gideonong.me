# Local content editor (dev-side tool, never deployed)

Edits the site's content files in place from a local web page shown in its own window. Phase 1
edits the EN/ES strings in `js/translations.js`; later phases add projects, experience, tags,
images and the CV/transcript tools (see `staging/editor-plan.md`). `scripts/` is in
`.vercelignore`, so nothing here is published. The tool never runs a git write command — you
commit.

## One-time setup (Windows, PowerShell, from the repo root)

```powershell
$py = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"   # not `python` (that's Inkscape's)
& $py -m pip install -r scripts\editor\requirements.txt
powershell -ExecutionPolicy Bypass -File scripts\editor\make-shortcut.ps1
```

This installs Flask (the server) and pywebview (the window; it uses the WebView2 runtime that
ships with Edge — no Edge profile, no Edge window, so Cold Turkey Blocker leaves it alone). The
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
drafts exist, or on Ctrl+C).

Covers: round-trip of every data file, one edit = one changed line, no-edit save = identical
file, changed-on-disk → refused (including a same-size rewrite), unsupported syntax or a
duplicate key → refused with line number, save gating, a write that fails because the file is
open elsewhere → 409 with file and drafts untouched, backups/restore (and that a backup path
cannot reach a sibling set), autosave, the token/Host/Origin checks (including `/api/focus`
and `/api/open-preview`), the preview's Vercel-style 404s, draft overlay, Host/Origin
allow-list, letter-case and 8.3 short-name variants of excluded paths (the short-name test
skips where the volume has no 8.3 names), hidden-key prefixes from both data files, and a scan
that fails if the editor's code contains a git write command.

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
| `static/` | The page (index.html, app.js, app.css) |
| `tests/` | unittest suite |
| `make-shortcut.ps1` | Desktop shortcut with the full pythonw.exe path |
