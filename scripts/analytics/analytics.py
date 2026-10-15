"""# gideonong.me analytics

Reads the self-built collector's records from `/api/export` and, optionally, a GoatCounter CSV export.
It answers the questions in plan.md → Phase 3 → "Analytics, self-built" (A3):
- pageviews and unique visitors per day
- top pages and referrers
- the referrer → résumé-download funnel
- EN vs ES
- country
- time on page

**How to run it in Colab:**
1. Add the export token once under 🔑 **Secrets**, as `ANALYTICS_EXPORT_TOKEN`, with notebook access switched on.
2. Edit the **Settings** cell.
3. Choose **Runtime → Run all**.

Without a token, it runs on built-in sample data.

**Never use File → "Save a copy in GitHub".** That commits through GitHub's website, so the repo's pre-commit
hook (which blocks data and notebook outputs) never runs. To change the notebook, edit `scripts/analytics/analytics.py`
locally, run `make-notebook.py`, and commit both. See `scripts/analytics/README.md`.

This notebook is generated from `analytics.py` by `make-notebook.py`; edit the `.py`, not this file.
"""

# %% [markdown]
# ## Settings
#
# Dates are UTC days (`YYYY-MM-DD`), both inclusive. Any range works: the notebook splits it into
# requests of at most 31 days (the export's cap) by itself.

# %%
import os

BASE_URL = os.environ.get("ANALYTICS_BASE_URL", "https://gideonong.me")
FROM = None              # e.g. "2026-10-13"; None = 29 days before TO
TO = None                # e.g. "2026-11-30"; None = today (UTC)
GOATCOUNTER_CSV = None   # an uploaded GoatCounter export, e.g. "/content/goatcounter-export-gideonong-….csv.gz"
USE_SAMPLE = False       # True = built-in fake data (also used automatically when no token is found)
SAVE_LOCAL_COPY = False  # local runs only: also save the export to scripts/analytics/data/ (gitignored)
TOP_N = 10               # rows in the "top" charts
TIME_CAP_MIN = 30        # time on page above this counts as this (a tab left open isn't reading)

# %% [markdown]
# ## Setup
#
# The token comes from Colab Secrets (or, outside Colab, the `ANALYTICS_EXPORT_TOKEN` environment
# variable). It is never printed or saved.

# %%
import datetime as dt
import hashlib
import json
import random
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

try:
    from IPython.display import display
except ImportError:  # plain `python analytics.py`
    display = print

# Chart colors: series 1 (collector) and 2 (GoatCounter) of the dataviz reference palette,
# validated as an adjacent pair; text and grid stay neutral.
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "figure.dpi": 110, "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlelocation": "left", "axes.titlesize": 12, "axes.titlecolor": INK, "axes.titlepad": 10,
})


def get_token():
    try:
        from google.colab import userdata
        try:
            return userdata.get("ANALYTICS_EXPORT_TOKEN"), "Colab Secrets"
        except Exception:  # not set, or notebook access off
            pass
    except ImportError:
        pass
    token = os.environ.get("ANALYTICS_EXPORT_TOKEN")
    return (token, "environment variable") if token else (None, None)


TOKEN, token_source = (None, None) if USE_SAMPLE else get_token()
SAMPLE = USE_SAMPLE or not TOKEN
if SAMPLE:
    print("Using built-in SAMPLE data: no token found, or USE_SAMPLE = True. Every chart below is fake.")
else:
    print(f"Token found ({token_source}). Exporting from {BASE_URL}.")

today = dt.datetime.now(dt.timezone.utc).date()
END = dt.date.fromisoformat(TO) if TO else today
START = dt.date.fromisoformat(FROM) if FROM else END - dt.timedelta(days=29)
assert START <= END, "FROM must be on or before TO"
print(f"Range: {START} to {END} ({(END - START).days + 1} days, UTC)")

# %% [markdown]
# ## Load the collector's records
#
# Each request covers at most 31 days. If one still comes back too large (413), it is split in half
# and retried.

# %%
MAX_DAYS = 31


def chunks(start, end, size=MAX_DAYS):
    a = start
    while a <= end:
        b = min(end, a + dt.timedelta(days=size - 1))
        yield a, b
        a = b + dt.timedelta(days=1)


def fetch(a, b):
    query = urllib.parse.urlencode({"from": a.isoformat(), "to": b.isoformat()})
    req = urllib.request.Request(f"{BASE_URL.rstrip('/')}/api/export?{query}",
                                 headers={"Authorization": "Bearer " + TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            text = res.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 413 and a < b:
            mid = a + (b - a) // 2
            return fetch(a, mid) + fetch(mid + dt.timedelta(days=1), b)
        if e.code == 404:
            raise RuntimeError("404 from /api/export: the token is wrong, "
                               "or the export isn't deployed at BASE_URL.") from None
        raise RuntimeError(f"{e.code} from /api/export: "
                           f"{e.read().decode('utf-8', 'replace').strip()}") from None
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def make_sample(start, end, seed=7):
    """Fake records in the collector's exact shape, plus fake GoatCounter daily counts."""
    rng = random.Random(seed)
    pages = ["/", "/projects", "/experience", "/about", "/projects/g-view",
             "/projects/eagle-pathway", "/projects/pump-cylinder-failure"]
    # (referrer host, in-app browser, weight)
    sources = [("linkedin.com", "", 16), ("", "LinkedIn", 10), ("", "", 24), ("google.com", "", 12),
               ("github.com", "", 6), ("", "Instagram", 3), ("", "Facebook", 2), ("joinhandshake.com", "", 4)]
    countries = [("US", 70), ("MX", 6), ("ES", 5), ("IN", 5), ("CO", 3), ("DE", 3), ("GB", 3), ("CA", 3)]
    regions = ["OK", "OK", "OK", "TX", "TX", "CA", "NY", "IL", "CO", "KS"]
    records, rows = [], []
    day = start
    while day <= end:
        for s in range(rng.randint(8, 30)):
            ref, app, _ = rng.choices(sources, weights=[w for *_, w in sources])[0]
            country = rng.choices([c for c, _ in countries], weights=[w for _, w in countries])[0]
            es = rng.random() < (0.7 if country in ("MX", "ES", "CO") else 0.05)
            lang = "es" if es else "en"
            mobile = bool(app) or rng.random() < 0.4
            browser = app or rng.choice(["Chrome", "Chrome", "Safari", "Edge", "Firefox"])
            base = {
                "ref": ref, "lang": lang, "nav": "es-MX" if es else "en-US",
                "vw": "<480" if mobile else rng.choice(["1024-1439", "1440+", "768-1023"]),
                "tz": "America/Chicago", "sid": hashlib.sha1(f"{day}{s}".encode()).hexdigest()[:16],
                "utm": "resume" if rng.random() < 0.04 else "", "country": country,
                "region": rng.choice(regions) if country == "US" else "", "city": "",
                "browser": browser, "os": "iOS" if mobile else "Windows", "device": "mobile" if mobile else "desktop",
                "visitor": hashlib.sha256(f"v{day}{s}".encode()).hexdigest()[:16],
            }
            t = dt.datetime.combine(day, dt.time(rng.randint(0, 23), rng.randint(0, 59)), dt.timezone.utc)
            path = rng.choice(["/", "/", "/", rng.choice(pages)])
            for _ in range(rng.choices([1, 2, 3, 4, 5], weights=[40, 25, 15, 12, 8])[0]):
                stamp = lambda: t.isoformat().replace("+00:00", "Z")
                records.append(dict(base, t=stamp(), type="pageview", path=path))
                rows.append(day)
                if path in ("/", "/about") and rng.random() < (0.30 if "linkedin" in ref.lower() or app == "LinkedIn" else 0.10):
                    t += dt.timedelta(seconds=rng.randint(5, 60))
                    records.append(dict(base, t=stamp(), type="click", path=path, event=f"doc-resume-{lang}"))
                if rng.random() < 0.05:
                    t += dt.timedelta(seconds=3)
                    lang = "en" if lang == "es" else "es"
                    base["lang"] = lang
                    records.append(dict(base, t=stamp(), type="click", path=path, event=f"lang-{lang}"))
                seconds = min(int(rng.lognormvariate(3.3, 1.0)), 3000)
                t += dt.timedelta(seconds=seconds)
                records.append(dict(base, t=stamp(), type="leave", path=path, ms=seconds * 1000,
                                    scroll=rng.randint(15, 100)))
                path = rng.choice(pages)
        day += dt.timedelta(days=1)
    pv = pd.Series(rows).value_counts()
    gc = (pv * [rng.uniform(0.8, 0.95) for _ in pv]).round().astype(int).sort_index()
    return records, gc


gc_daily = None
if SAMPLE:
    records, gc_daily = make_sample(START, END)
    gc_label = "GoatCounter (sample)"
else:
    records = []
    for a, b in chunks(START, END):
        part = fetch(a, b)
        records += part
        print(f"  {a} to {b}: {len(part):,} records")
print(f"{len(records):,} records loaded")

if SAVE_LOCAL_COPY and not SAMPLE:
    here = Path("scripts/analytics") if Path("scripts/analytics").is_dir() else Path(".")
    if here.resolve().name != "analytics":
        print("Not saved: run from the repo root or scripts/analytics/, so the copy lands in the gitignored data/ folder.")
    else:
        out = here / "data" / f"export-{START}-{END}.ndjson"
        out.parent.mkdir(exist_ok=True)
        out.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        print(f"Saved a local copy: {out} (gitignored; never commit it)")

# %% [markdown]
# ## Optional: GoatCounter
#
# Upload the export (GoatCounter → Settings → Export; it needs "Individual pageviews" switched on)
# into Colab's file panel and set `GOATCOUNTER_CSV`. Only its daily pageview count is used; bots and
# events are left out.

# %%
def load_goatcounter(path):
    gc = pd.read_csv(path, dtype=str, keep_default_na=False)  # .csv or .csv.gz
    first = gc.columns[0]
    m = re.fullmatch(r"(\d+)Path", first)
    if not m or m.group(1) != "2":
        raise ValueError(f"Unexpected GoatCounter header {first!r}: this notebook reads export version 2.")
    gc = gc.rename(columns={first: "Path"})
    gc = gc[(gc["Event"].str.lower() != "true") & (gc["Bot"].isin(["0", ""]))]
    when = pd.to_datetime(gc["Date"], utc=True, errors="coerce").dt.date
    when = when[(when >= START) & (when <= END)]
    return when.value_counts().sort_index()


if GOATCOUNTER_CSV:
    gc_daily, gc_label = load_goatcounter(GOATCOUNTER_CSV), "GoatCounter"
    print(f"GoatCounter: {gc_daily.sum():,} pageviews in range")
elif not SAMPLE:
    print("No GoatCounter CSV set; the daily chart shows the collector only.")

# %% [markdown]
# ## Prepare
#
# - A **session** is one browser tab (`sid`).
# - Each `leave` belongs to the latest pageview in its tab. Time on page is that pageview's last
#   `leave`, capped at `TIME_CAP_MIN`.
# - A session's **source** is its first pageview's referrer:
#   - `utm_source` wins when present
#   - no referrer from the LinkedIn / Instagram / Facebook in-app browser is "linkedin (app)" etc.
#   - otherwise no referrer is "direct"
#   - links from the site itself are "(internal)"

# %%
COLUMNS = {"t": "", "type": "", "path": "/", "event": "", "ms": None, "scroll": None, "ref": "", "lang": "",
           "nav": "", "vw": "", "tz": "", "sid": "", "utm": "", "country": "", "region": "", "city": "",
           "browser": "", "os": "", "device": "", "visitor": ""}
df = pd.DataFrame(records, columns=list(COLUMNS))
for col, default in COLUMNS.items():
    if default is not None:
        df[col] = df[col].fillna(default)
df["t"] = pd.to_datetime(df["t"], utc=True)
df["day"] = df["t"].dt.date
# A tab without sessionStorage sends sid "": treat each such pageview as its own session.
nosid = df["sid"] == ""
df.loc[nosid, "sid"] = "nosid-" + df.index[nosid].astype(str)
df = df.sort_values(["sid", "t"], kind="stable").reset_index(drop=True)
df["pv_n"] = (df["type"] == "pageview").groupby(df["sid"]).cumsum()

pageviews = df[df["type"] == "pageview"].drop(columns=["ms", "scroll"])
clicks = df[df["type"] == "click"]
last_leave = (df[(df["type"] == "leave") & (df["pv_n"] > 0)]
              .groupby(["sid", "pv_n"]).agg(ms=("ms", "max"), scroll=("scroll", "max")).reset_index())
pageviews = pageviews.merge(last_leave, on=["sid", "pv_n"], how="left")
pageviews["sec"] = (pageviews["ms"] / 1000).clip(upper=TIME_CAP_MIN * 60)

IN_APP = {"LinkedIn": "linkedin (app)", "Instagram": "instagram (app)", "Facebook": "facebook (app)"}
ALIASES = [("linkedin.", "linkedin.com"), ("lnkd.in", "linkedin.com"), ("google.", "google"),
           ("facebook.", "facebook.com"), ("instagram.", "instagram.com"), ("bing.", "bing"),
           ("duckduckgo.", "duckduckgo")]


def source_label(ref, utm, browser):
    if utm:
        return "utm: " + utm.lower()
    host = (ref or "").lower().split(":")[0]
    if not host:
        return IN_APP.get(browser, "direct")
    if host in ("gideonong.me", "www.gideonong.me", "localhost", "127.0.0.1") or host.endswith(".vercel.app"):
        return "(internal)"
    for key, label in ALIASES:
        if key in host:
            return label
    return host.removeprefix("www.")


sessions = pageviews.groupby("sid").first()
sessions["source"] = [source_label(r, u, b) for r, u, b in zip(sessions["ref"], sessions["utm"], sessions["browser"])]
doc_sids = clicks.loc[clicks["event"].str.startswith("doc-"), "sid"]
resume_sids = clicks.loc[clicks["event"].str.startswith("doc-resume-"), "sid"]
sessions["resume"] = sessions.index.isin(resume_sids)
sessions["any_doc"] = sessions.index.isin(doc_sids)
sessions["switched_lang"] = sessions.index.isin(clicks.loc[clicks["event"].str.startswith("lang-"), "sid"])

summary = pd.Series({
    "records": len(df), "pageviews": len(pageviews), "sessions (tabs)": len(sessions),
    "unique visitors, summed over days": pageviews.groupby("day")["visitor"].nunique().sum(),
    "sessions with a résumé download": int(sessions["resume"].sum()),
    "sessions with any document download": int(sessions["any_doc"].sum()),
}, name="value")
display(summary.to_frame())

# %% [markdown]
# ## Chart helpers

# %%
def hbar(series, title, xlabel, labels=None, color=BLUE):
    """Horizontal bars, largest on top, each with its value at the end."""
    if series.empty:
        print(f"{title}: no data in range")
        return
    s = series.iloc[::-1]
    text = (labels.reindex(s.index) if labels is not None else s.map("{:,.0f}".format))
    fig, ax = plt.subplots(figsize=(8, 0.38 * len(s) + 1.3))
    ax.barh([str(i) for i in s.index], s.values, color=color, height=0.62)
    for y, (v, t) in enumerate(zip(s.values, text)):
        ax.text(v, y, "  " + t, va="center", color=INK2, fontsize=9)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.margins(x=0.18)
    plt.tight_layout()
    plt.show()


def top(series, n=TOP_N, other="Other"):
    """The n largest values; the rest summed into one 'Other' row (never a generated extra series)."""
    s = series.sort_values(ascending=False)
    if len(s) <= n:
        return s
    return pd.concat([s.iloc[:n], pd.Series({other: s.iloc[n:].sum()})])


days = pd.date_range(START, END, freq="D").date

# %% [markdown]
# ## 1. Pageviews per day
#
# The collector's daily count, with GoatCounter's on top when a CSV is loaded (or in sample mode).
# The collector should be at or above GoatCounter; it's same-origin, so blockers catch it less.

# %%
pv_daily = pageviews.groupby("day").size().reindex(days, fill_value=0)
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(days, pv_daily.values, color=BLUE, linewidth=2, label="Collector")
if gc_daily is not None:
    ax.plot(days, gc_daily.reindex(days, fill_value=0).values, color=ORANGE, linewidth=2, label=gc_label)
    ax.legend(frameon=False, loc="upper left")
ax.set_title("Pageviews per day (UTC days)")
ax.set_ylabel("pageviews")
ax.set_ylim(bottom=0)
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
fig.autofmt_xdate()
plt.tight_layout()
plt.show()
table = pd.DataFrame({"collector": pv_daily})
if gc_daily is not None:
    table[gc_label] = gc_daily.reindex(days, fill_value=0)
display(table.tail(14))

# %% [markdown]
# ## 2. Unique visitors per day
#
# The visitor hash is salted with the UTC date, so it resets every day **by design**. A weekly or
# monthly unique count isn't possible, and summing the daily bars overcounts returning visitors.

# %%
uv_daily = pageviews.groupby("day")["visitor"].nunique().reindex(days, fill_value=0)
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.bar(days, uv_daily.values, color=BLUE, width=0.7)
ax.set_title("Unique visitors per day (UTC days; the hash resets daily)")
ax.set_ylabel("visitors per day")
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
fig.autofmt_xdate()
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 3. Top pages

# %%
hbar(top(pageviews["path"].value_counts()), f"Top pages (top {TOP_N})", "pageviews")

# %% [markdown]
# ## 4. Where sessions come from
#
# By landing source. Sessions with no referrer from an in-app browser count as that app.

# %%
hbar(top(sessions["source"].value_counts()), f"Sessions by source (top {TOP_N})", "sessions")
utm = sessions.loc[sessions["utm"] != "", "utm"].str.lower().value_counts()
if len(utm):
    display(utm.rename("sessions").to_frame("sessions").rename_axis("utm_source"))

# %% [markdown]
# ## 5. Source → résumé download
#
# For each source, how many sessions downloaded the résumé (the CV and transcript are counted under
# "any document").

# %%
funnel = sessions.groupby("source").agg(sessions=("resume", "size"), resume=("resume", "sum"),
                                        any_doc=("any_doc", "sum")).sort_values("sessions", ascending=False)
funnel["resume %"] = (100 * funnel["resume"] / funnel["sessions"]).round(1)
funnel["any document %"] = (100 * funnel["any_doc"] / funnel["sessions"]).round(1)
shown = funnel.head(TOP_N)
labels = pd.Series([f"{n:,} sessions · {r:,} résumé ({p:.0f}%)" for n, r, p in
                    zip(shown["sessions"], shown["resume"], shown["resume %"])], index=shown.index)
hbar(shown["sessions"], f"Sessions and résumé downloads by source (top {TOP_N})", "sessions", labels=labels)
display(funnel)

# %% [markdown]
# ## 6. English vs Spanish

# %%
hbar(pageviews["lang"].replace("", "(unknown)").value_counts(), "Pageviews by site language", "pageviews")
print(f"Sessions that switched language: {int(sessions['switched_lang'].sum()):,} of {len(sessions):,}")
nav = pageviews["nav"].str.split("-").str[0].str.lower().replace("", "(unknown)")
display(nav.value_counts().head(8).rename("pageviews").to_frame().rename_axis("browser language"))

# %% [markdown]
# ## 7. Country

# %%
hbar(top(sessions["country"].replace("", "(unknown)").value_counts()), f"Sessions by country (top {TOP_N})", "sessions")
us = sessions.loc[sessions["country"] == "US", "region"].replace("", "(unknown)").value_counts()
if len(us):
    display(us.head(15).rename("sessions").to_frame().rename_axis("US state"))

# %% [markdown]
# ## 8. Time on page
#
# Visible time only (a hidden tab doesn't count), capped at `TIME_CAP_MIN` minutes. Pages with fewer
# than 3 timed views are left out of the per-page chart.

# %%
timed = pageviews.dropna(subset=["sec"])
per_page = timed.groupby("path").agg(views=("sec", "size"), median_sec=("sec", "median"),
                                     median_scroll=("scroll", "median"))
per_page = per_page[per_page["views"] >= 3].sort_values("views", ascending=False).head(TOP_N)
labels = pd.Series([f"{s:.0f} s · scroll {c:.0f}%" for s, c in zip(per_page["median_sec"], per_page["median_scroll"])],
                   index=per_page.index)
hbar(per_page["median_sec"], "Median time on page (top pages by views)", "seconds", labels=labels)

edges = [0, 5, 15, 30, 60, 120, 300, float("inf")]
names = ["<5 s", "5–15 s", "15–30 s", "30–60 s", "1–2 min", "2–5 min", "5+ min"]
hist = pd.cut(timed["sec"], bins=edges, labels=names, right=False).value_counts().reindex(names, fill_value=0)
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.bar(names, hist.values, color=BLUE, width=0.65)
ax.set_title("Time on page, all timed pageviews")
ax.set_ylabel("pageviews")
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout()
plt.show()
display(per_page.round(1))
