# Transcript generator (dev-side tool, not deployed)

Turns TU's unofficial transcript PDF into the public **Unofficial Academic Record**
in English and Spanish:
`assets/pdfs/transcript/<en|es> Gideon Ong Transcript YYYYMMDD.pdf`.
`scripts/` is in `.vercelignore`, so nothing here is published.

## Files
| File | What it is | Who edits it |
|---|---|---|
| `parse_transcript.py` | Reads the TU PDF → `transcript-data.json`. Skips everything above the course table (name, birth date, IDs). | nobody |
| `transcript-data.json` | Terms, courses, grades, TU's printed totals. | generated |
| `course-titles.json` | Full EN/ES title per course code (special-topics codes keyed by section title). `verified: false` = not yet checked against bulletin.utulsa.edu. | you, once per new course |
| `profile.json` | Majors, minors, program, expected graduation (EN/ES). | you, when they change |
| `make_transcript.py` | Checks the data, then writes the two .docx files and (with `--pdf`) the PDFs. | nobody |
| `output/` | The .docx files, for checking (gitignored). | generated |

## One-time setup (Windows, PowerShell)
```powershell
$py = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"   # not `python` (that's Inkscape's)
& $py -m pip install -r scripts\transcript\requirements.txt
```

## Each semester
1. Download the unofficial transcript PDF from TU and save it in `references\transcripts\` (gitignored; it has your student ID).
2. Parse it:
   ```powershell
   cd scripts\transcript
   & $py parse_transcript.py "..\..\references\transcripts\Ong_Gideon_Transcript_YYYYMMDD.pdf"
   ```
3. Build and check (stops if a course has no title, or if its GPA/credit math disagrees with TU's totals):
   ```powershell
   & $py make_transcript.py          # .docx only → output\, open them to look
   & $py make_transcript.py --pdf    # + PDFs into assets\pdfs\transcript\ (uses Word)
   ```
   New course codes → add them to `course-titles.json` (EN + ES) and rerun.
4. Delete the previous transcript PDFs from `assets\pdfs\transcript\` and commit. The pre-commit hook updates `js/docs-data.js`.

File dates come from the transcript's print date; override with `--date YYYYMMDD`.
`--strict` refuses to build while any title is still `verified: false`.
