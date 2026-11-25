"""Print the Designed CV page with headless Microsoft Edge (Chrome as the fallback). Word is
never involved.

Two short runs of the browser on the same file, each with a private profile folder so the
user's own Edge (windows, profile, extensions) is never touched:

    1. --dump-dom      the page measures its columns once its fonts are in and writes the
                       result onto <html data-meter>; a column over its height stops here
    2. --print-to-pdf  no header or footer; the page's own CSS sets Letter with no margins
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
BROWSERS = [
    ("Microsoft Edge", "ProgramFiles(x86)", r"Microsoft\Edge\Application\msedge.exe"),
    ("Microsoft Edge", "ProgramFiles", r"Microsoft\Edge\Application\msedge.exe"),
    ("Microsoft Edge", "LocalAppData", r"Microsoft\Edge\Application\msedge.exe"),
    ("Google Chrome", "ProgramFiles", r"Google\Chrome\Application\chrome.exe"),
    ("Google Chrome", "ProgramFiles(x86)", r"Google\Chrome\Application\chrome.exe"),
    ("Google Chrome", "LocalAppData", r"Google\Chrome\Application\chrome.exe"),
]
COMMON_FLAGS = ["--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--disable-background-networking", "--virtual-time-budget=10000"]
TIMEOUT_S = 90


class ExportError(RuntimeError):
    pass


def find_browser(env: Optional[dict] = None) -> Optional[tuple[str, Path]]:
    """(name, path) of Edge in its standard install paths, else Chrome, else None."""
    env = os.environ if env is None else env
    for name, var, rel in BROWSERS:
        base = env.get(var)
        if base and (Path(base) / rel).is_file():
            return name, Path(base) / rel
    return None


def _quote(s: str) -> str:
    return f'"{s}"' if " " in s else s


def _run(exe: Path, args: list[str], log: Callable[[str], None], capture: bool) -> str:
    cmd = [str(exe)] + args
    log("$ " + " ".join(_quote(c) for c in cmd))
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE if capture else subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=TIMEOUT_S, creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise ExportError(f"{exe.name} did not finish within {TIMEOUT_S} s") from None
    except OSError as e:
        raise ExportError(f"{exe.name} could not be started: {e}") from e
    if p.returncode != 0:
        raise ExportError(f"{exe.name} exited with code {p.returncode}")
    return p.stdout.decode("utf-8", "replace") if capture else ""


def _headless(exe: Path, work_dir: Path, args: list[str], log: Callable[[str], None], capture: bool) -> str:
    """One headless run with a profile folder of its own under work_dir (a browser that is still
    shutting down keeps its profile locked for a moment, and a second run on the same folder
    then exits at once). One retry, in a new folder, covers a slow start."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    last: Optional[ExportError] = None
    for attempt in (1, 2):
        profile = Path(tempfile.mkdtemp(prefix="profile-", dir=str(work_dir)))
        try:
            return _run(exe, COMMON_FLAGS + [f"--user-data-dir={profile}"] + args, log, capture)
        except ExportError as e:
            last = e
            log(f"attempt {attempt} failed: {e}")
            time.sleep(1.5)
        finally:
            shutil.rmtree(profile, ignore_errors=True)
    raise last  # type: ignore[misc]


def measure(exe: Path, page: Path, work_dir: Path, log: Callable[[str], None] = lambda s: None) -> dict:
    """{"main": px left, "side": px left, "fonts": "ok" | "missing: …"} as the page measured itself."""
    dom = _headless(exe, work_dir, ["--dump-dom", Path(page).resolve().as_uri()], log, capture=True)
    m = re.search(r'data-meter="([^"]*)"', dom)
    if not m:
        raise ExportError("the page did not report its column measure (its script did not run to the end)")
    try:
        out = json.loads(html.unescape(m.group(1)))
    except ValueError:
        raise ExportError("the page's column measure could not be read") from None
    f = re.search(r'data-fonts="([^"]*)"', dom)
    out["fonts"] = html.unescape(f.group(1)) if f else "unknown"
    return out


def print_pdf(exe: Path, page: Path, pdf: Path, work_dir: Path, log: Callable[[str], None] = lambda s: None) -> Path:
    pdf = Path(pdf).resolve()
    pdf.parent.mkdir(parents=True, exist_ok=True)
    if pdf.exists():
        pdf.unlink()
    _headless(exe, work_dir, ["--no-pdf-header-footer", f"--print-to-pdf={pdf}", Path(page).resolve().as_uri()], log, capture=False)
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise ExportError(f"{exe.name} reported success but wrote no PDF")
    return pdf
