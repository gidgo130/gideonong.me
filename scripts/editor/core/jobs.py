"""One background job at a time, with a timestamped log the page polls, plus a
subprocess runner that streams a child's output line by line into that log.

Used by the CV export (Word) and the transcript parse / build (the
scripts/transcript/*.py scripts run with the editor's own interpreter).
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger("editor.jobs")
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class JobRunner:
    def __init__(self):
        self.lock = threading.RLock()
        self.job: Optional[dict] = None

    def busy(self) -> bool:
        with self.lock:
            return bool(self.job and self.job.get("running"))

    def json(self) -> Optional[dict]:
        with self.lock:
            return dict(self.job) if self.job else None

    def log_line(self, line: str) -> None:
        with self.lock:
            if self.job is not None:
                self.job["log"].append(f"{time.strftime('%H:%M:%S')}  {line}")
        log.info("job: %s", line)

    def update(self, **fields) -> None:
        with self.lock:
            if self.job is not None:
                self.job.update(fields)

    def start(self, kind: str, fn: Callable[["JobRunner"], object], **fields) -> dict:
        """Run fn(runner) on a thread. Its return value lands in job["result"]; an exception in job["error"]."""
        with self.lock:
            if self.busy():
                raise RuntimeError(f"a {self.job['kind']} job is already running")
            self.job = {
                "kind": kind,
                "running": True,
                "started": time.time(),
                "finished": None,
                "log": [],
                "result": None,
                "error": None,
                **fields,
            }
            snapshot = dict(self.job)

        def run():
            try:
                result = fn(self)
                self.update(result=result)
            except Exception as e:  # the page shows this; the server keeps going
                log.exception("job %s crashed", kind)
                self.update(error=f"{type(e).__name__}: {e}")
                self.log_line(f"FAILED — {e}")
            finally:
                self.update(running=False, finished=time.time())

        threading.Thread(target=run, name=f"job-{kind}", daemon=True).start()
        return snapshot


def python_exe() -> str:
    """The console python next to the running interpreter (pythonw.exe → python.exe)."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        cand = exe.with_name("python.exe")
        if cand.is_file():
            return str(cand)
    return str(exe)


def run_subprocess(cmd: list[str], cwd: Path, log_line: Callable[[str], None], timeout: float = 600) -> int:
    """Run cmd, streaming each output line to log_line; returns the exit code (-1 on timeout)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    log_line("$ " + " ".join(_quote(c) for c in cmd))
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        creationflags=CREATE_NO_WINDOW,
    )
    assert proc.stdout is not None
    deadline = time.monotonic() + timeout
    timer = threading.Timer(timeout, proc.kill)
    timer.start()
    try:
        for line in proc.stdout:
            log_line(line.rstrip("\r\n"))
        proc.wait()
    finally:
        timer.cancel()
    if time.monotonic() >= deadline:
        log_line(f"killed after {timeout:.0f} s")
        return -1
    log_line(f"exit code {proc.returncode}")
    return proc.returncode


def _quote(s: str) -> str:
    return f'"{s}"' if " " in s else s
