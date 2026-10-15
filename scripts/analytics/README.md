# Analytics notebook

Reads the site's self-built analytics (the collector in `api/hit.js`, served by
`api/export.js`) and charts the questions from plan.md → Phase 3 → "Analytics, self-built":

- pageviews per day, with GoatCounter's count on top when you load its CSV
- unique visitors **per day**
- top pages
- sessions by source
- source → résumé download
- EN vs ES
- country
- time on page

Dev-only: `scripts/` is never deployed. It **is** public on GitHub, though, so read
"Keeping data out of the repo" below.

| File | What it is |
|---|---|
| `analytics.py` | The source. A plain Python script with `# %%` cell markers. Edit this one. |
| `analytics.ipynb` | Generated from `analytics.py`. It's what Colab opens. Never edit it by hand. |
| `make-notebook.py` | Writes `analytics.ipynb` from `analytics.py`, always with no outputs. |

## Run it in Colab

1. Open the notebook from GitHub:
   https://colab.research.google.com/github/gidgo130/gideonong.me/blob/main/scripts/analytics/analytics.ipynb
2. The first time only, set up the token: click the 🔑 **Secrets** icon in the left bar → **Add new
   secret**. Name it `ANALYTICS_EXPORT_TOKEN`, paste the value from your password manager, and turn
   **Notebook access** on. Colab keeps it for your account. It's never written into the notebook.
3. Edit the **Settings** cell:
   - `FROM` / `TO`: UTC days, `YYYY-MM-DD`. Any range works; the notebook splits it into requests
     of at most 31 days by itself.
   - `GOATCOUNTER_CSV`: optional, see below.
4. **Runtime → Run all.**

Without a token (or with `USE_SAMPLE = True`), it runs on built-in **fake** data and says so at
the top. That's handy for checking the charts.

### Adding GoatCounter's numbers (optional)

1. In GoatCounter, **Settings → "Individual pageviews"** must be on. The export only contains
   pageviews from after you turn it on.
2. **Settings → Export → Start export**, then download the file
   (`goatcounter-export-gideonong-….csv.gz`).
3. In Colab, drag the file into the 📁 **Files** panel and set
   `GOATCOUNTER_CSV = "/content/<file name>"`.

The file holds raw user agents and session ids. It lives only on Colab's machine, which is wiped
when the session ends. Never put it in the repo.

## Reading the charts

- **Unique visitors are per day only.** The visitor hash is salted with the UTC date, so it resets
  every day by design. A weekly or monthly unique count isn't possible, and adding up the daily
  bars counts returning visitors more than once.
- **Days are UTC.** That's the day the hash uses. 7 pm in Tulsa is already the next UTC day.
- **A session** is one browser tab. A recruiter who opens three tabs counts as three sessions.
- **Source** comes from the session's first pageview:
  - `utm_source` wins when the link had one ("utm: resume")
  - with no referrer from the LinkedIn / Instagram / Facebook in-app browser, it's
    "linkedin (app)" / "instagram (app)" / "facebook (app)"
  - with no referrer otherwise, it's "direct"
  - links from the site itself are "(internal)"
- **Time on page** counts visible time only, capped at 30 minutes (`TIME_CAP_MIN`).

## ⚠ Never use Colab's "Save a copy in GitHub"

**File → Save a copy in GitHub** commits straight through GitHub's website. The repo's pre-commit
hook never runs, so nothing checks for data or outputs. The notebook also has Colab's "omit code
cell output when saving" switched on, but don't rely on it.

To change the notebook:

1. Edit `analytics.py` on your computer.
2. Regenerate the notebook from the repo root:
   ```
   & "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" scripts/analytics/make-notebook.py
   ```
3. Commit `analytics.py` and `analytics.ipynb` together.

`make-notebook.py --check` tells you whether the notebook matches the `.py`.

## Running it on your computer

From the repo root, in PowerShell:

```
$env:ANALYTICS_EXPORT_TOKEN = "<ANALYTICS_EXPORT_TOKEN>"
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" scripts/analytics/analytics.py
```

That runs it as a plain script: charts open in windows and tables print. To use the notebook
instead, open `analytics.ipynb` in VS Code or Jupyter, but **don't commit it after running**. The
hook blocks that (rule d); regenerate it instead.

To try it against `vercel dev`, set `$env:ANALYTICS_BASE_URL = "http://localhost:3000"`, plus a
Development `ANALYTICS_EXPORT_TOKEN` in Vercel. It then reads only the `dev:` test data.
`SAVE_LOCAL_COPY = True` writes the export to `scripts/analytics/data/`, which is gitignored.

## The export endpoint

```
GET https://gideonong.me/api/export?from=YYYY-MM-DD&to=YYYY-MM-DD
Authorization: Bearer <ANALYTICS_EXPORT_TOKEN>
```

- **Response:** one stored record per line (NDJSON), oldest day first. Example line, with
  placeholders:
  `{"t":"<ISO time>","type":"pageview","path":"/projects","ref":"linkedin.com",…,"visitor":"<16 hex>"}`
- **Unauthorized:** anything without the right token, or any method but GET, gets an empty 404.
- **With a valid token, errors are:**
  - 400 for bad dates (more than 31 days, `from` after `to`, an impossible date)
  - 413 if the answer would pass 4 MB; the notebook then halves the range by itself
- Details: CLAUDE.md → Analytics.

## Keeping data out of the repo

The repo is public, so analytics data must never be committed.

- **`.gitignore`** ignores everything in this folder except the four files listed above, plus
  `*.ndjson`, `*.jsonl` and `goatcounter*.csv(.gz)` anywhere.
- **The pre-commit hook** (`scripts/check-staged-data.js`) blocks a commit that stages any of
  these, even with `git add -f`:

  | Rule | Blocks |
  |---|---|
  | a | data files by name |
  | b | a GoatCounter CSV, even renamed or gzipped |
  | c | a collector record anywhere |
  | d | this notebook with outputs |
  | e | a token or password-looking value |

  It needs `git config core.hooksPath .githooks` once per clone.
- **Placeholders:** in docs and comments, write `<16 hex>`, `<ANALYTICS_EXPORT_TOKEN>` and so on.
  A real-looking value trips rules c and e.
- **A genuine false positive:** `git commit --no-verify` skips the hook for that one commit.
