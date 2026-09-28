"""Launcher for the local content editor (double-click target; no console).

  * lock file: a second launch focuses the existing window (or reopens one)
    instead of starting a second copy;
  * starts the editor on 127.0.0.1:5510 and the read-only preview on
    127.0.0.1:5501 in this process;
  * opens Microsoft Edge in --app mode with its own profile under .local/edge;
  * primary shutdown signal: that Edge process exits (and no other msedge.exe
    is left using the profile). Crash fallback: no heartbeat from the page for
    10 minutes AND no drafts AND no Edge process on the profile;
  * logs in .local/logs/editor.log.

Run with `--no-edge` to start the servers without a browser (tests).
"""

from __future__ import annotations

import argparse
import ctypes
import json
import logging
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

LOCAL = HERE / ".local"
LOGS = LOCAL / "logs"
EDGE_PROFILE = LOCAL / "edge"
LOCK = LOCAL / "editor.lock"
TITLE_PART = "Site editor"  # part of the page <title>; used to find the window
APP_NAME = "gideonong-editor"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

log = logging.getLogger("editor.launch")


# ----------------------------------------------------------------- helpers


def msgbox(text: str, title: str = "Site editor", flags: int = 0x10) -> None:
    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(0, text, title, flags)
            return
        except Exception:  # pragma: no cover
            pass
    print(f"{title}: {text}", file=sys.stderr)


def setup_logging() -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOGS / "editor.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    if sys.stderr is not None and sys.stderr.isatty():
        root.addHandler(logging.StreamHandler())
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def ping(port: int, timeout: float = 1.5) -> Optional[dict]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=timeout) as r:
            j = json.loads(r.read().decode("utf-8"))
            return j if j.get("app") == APP_NAME else None
    except Exception:
        return None


def read_lock() -> Optional[dict]:
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_lock(data: dict) -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(data, indent=2), encoding="utf-8")


def remove_lock() -> None:
    try:
        LOCK.unlink()
    except OSError:
        pass


def find_edge() -> Optional[str]:
    cands = []
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            cands.append(Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe")
    for c in cands:
        if c.is_file():
            return str(c)
    if os.name == "nt":
        try:
            import winreg

            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe") as k:
                        v, _ = winreg.QueryValueEx(k, None)
                        if v and Path(v).is_file():
                            return v
                except OSError:
                    continue
        except ImportError:  # pragma: no cover
            pass
    return None


def edge_args(edge: str, url: str) -> list[str]:
    return [
        edge,
        f"--app={url}",
        f"--user-data-dir={EDGE_PROFILE}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-mode",
        "--disable-features=msEdgeStartupBoost,StartupBoost,msImplicitSignin,msSidebarV2,msHubApps",
        "--disable-sync",
        "--disable-extensions",
        "--disable-component-update",
        "--no-service-autorun",
        "--window-size=1440,920",
    ]


def edge_pids_using(profile_dir: Path) -> list[int]:
    """PIDs of msedge.exe processes whose command line names our profile folder."""
    if os.name != "nt":
        return []
    needle = str(profile_dir).replace("'", "''")
    cmd = (
        "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | "
        f"Where-Object {{ $_.CommandLine -and $_.CommandLine.Contains('{needle}') }} | "
        "ForEach-Object { $_.ProcessId }"
    )
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=CREATE_NO_WINDOW,
        )
        return [int(x) for x in r.stdout.split() if x.strip().isdigit()]
    except (OSError, subprocess.SubprocessError) as e:
        log.warning("process query failed: %s", e)
        return []


def kill_pids(pids: list[int]) -> None:
    for pid in pids:
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=15, creationflags=CREATE_NO_WINDOW)
        except (OSError, subprocess.SubprocessError) as e:
            log.warning("taskkill %s failed: %s", pid, e)


def find_windows(title_part: str) -> list[int]:
    if os.name != "nt":
        return []
    user32 = ctypes.windll.user32
    found: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if title_part in buf.value:
                    found.append(hwnd)
        return True

    user32.EnumWindows(cb, 0)
    return found


def focus_window(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    user32.ShowWindow(ctypes.c_void_p(hwnd), 9)  # SW_RESTORE
    # A synthetic Alt press lets a background process call SetForegroundWindow.
    user32.keybd_event(0x12, 0, 0, 0)
    user32.keybd_event(0x12, 0, 2, 0)
    user32.SetForegroundWindow(ctypes.c_void_p(hwnd))


# -------------------------------------------------------------------- main


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-edge", action="store_true", help="servers only, no browser (tests)")
    ap.add_argument("--editor-port", type=int, default=None)
    ap.add_argument("--preview-port", type=int, default=None)
    args = ap.parse_args(argv)

    LOCAL.mkdir(parents=True, exist_ok=True)
    setup_logging()
    import app as editor_app

    editor_port = args.editor_port or editor_app.EDITOR_PORT
    preview_port = args.preview_port or editor_app.PREVIEW_PORT
    repo_root, local_dir = editor_app.default_paths()
    if not (repo_root / "js" / "translations.js").is_file():
        msgbox(f"Cannot find js/translations.js under\n{repo_root}\n\nIs the editor still inside scripts/editor/?")
        return 1

    # ---- second launch? ---------------------------------------------------
    lock = read_lock()
    if lock and ping(int(lock.get("port", editor_port))):
        log.info("editor already running (pid %s); focusing", lock.get("pid"))
        if args.no_edge:
            print("already running: " + (lock.get("url") or ""), flush=True)
            return 0
        hw = find_windows(TITLE_PART)
        if hw:
            focus_window(hw[0])
        else:
            edge = find_edge()
            url = lock.get("url") or f"http://127.0.0.1:{editor_port}/"
            if edge:
                subprocess.Popen(edge_args(edge, url), close_fds=True)
            else:
                webbrowser.open(url)
        return 0
    if lock:
        log.info("stale lock file removed")
        remove_lock()

    for port in (editor_port, preview_port):
        if not port_free(port):
            msgbox(
                f"Port {port} is already in use, so the editor cannot start.\n\n"
                "Close whatever is listening there (another editor copy that did not exit, "
                "or a dev server) and try again."
            )
            return 1

    # ---- start servers ---------------------------------------------------
    token = secrets.token_urlsafe(32)
    state = editor_app.EditorState(repo_root, local_dir, token, editor_port, preview_port)
    servers = editor_app.Servers(state)
    servers.start()
    for _ in range(40):
        if ping(editor_port, 0.5):
            break
        time.sleep(0.25)
    else:
        servers.stop()
        msgbox("The editor server did not answer on 127.0.0.1:%d. See .local\\logs\\editor.log." % editor_port)
        return 1
    url = f"http://127.0.0.1:{editor_port}/?token={token}"
    write_lock(
        {
            "pid": os.getpid(),
            "port": editor_port,
            "previewPort": preview_port,
            "url": url,
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    log.info("editor on :%d, preview on :%d (pid %d)", editor_port, preview_port, os.getpid())

    # ---- open Edge --------------------------------------------------------
    proc: Optional[subprocess.Popen] = None
    launched_at = time.monotonic()
    if not args.no_edge:
        edge = find_edge()
        if edge:
            EDGE_PROFILE.mkdir(parents=True, exist_ok=True)
            proc = subprocess.Popen(edge_args(edge, url), close_fds=True)
            log.info("edge started (pid %d)", proc.pid)
        else:
            log.warning("msedge.exe not found; using the default browser")
            msgbox(
                "Microsoft Edge was not found, so the editor opens in your default browser.\n"
                "It will keep running until about 10 minutes after you close that tab.",
                flags=0x30,
            )
            webbrowser.open(url)
    else:
        print(url, flush=True)

    # ---- wait for shutdown ------------------------------------------------
    last_proc_check = 0.0
    drafts_notice_at = 0.0
    try:
        while not state.shutdown_requested.is_set():
            time.sleep(1.0)
            now = time.monotonic()
            if proc is not None and proc.poll() is not None:
                if now - launched_at < 5:
                    # Edge handed the URL to an instance already using this profile.
                    leftovers = edge_pids_using(EDGE_PROFILE)
                    if leftovers:
                        log.info("edge handed off to existing process(es) %s; using heartbeat mode", leftovers)
                        proc = None
                        continue
                log.info("edge process exited (rc %s)", proc.returncode)
                leftovers = edge_pids_using(EDGE_PROFILE)
                deadline = now + 15
                while leftovers and time.monotonic() < deadline:
                    time.sleep(2)
                    leftovers = edge_pids_using(EDGE_PROFILE)
                if leftovers:
                    log.warning("msedge.exe still using the profile after the window closed: %s — ending them", leftovers)
                    kill_pids(leftovers)
                break
            if proc is None and state.heartbeat_silence() >= editor_app.HEARTBEAT_TIMEOUT:
                if state.drafts:
                    if now - drafts_notice_at > 600:
                        log.info("no heartbeat for %.0f s but %d draft(s) exist; staying alive", state.heartbeat_silence(), len(state.drafts))
                        drafts_notice_at = now
                    continue
                if now - last_proc_check >= 60:
                    last_proc_check = now
                    if not edge_pids_using(EDGE_PROFILE):
                        log.info("no heartbeat for %.0f s, no drafts, no edge process — exiting", state.heartbeat_silence())
                        break
    except KeyboardInterrupt:
        pass
    finally:
        servers.stop()
        remove_lock()
        log.info("editor stopped")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as e:  # last-resort report for a windowless process
        logging.getLogger("editor.launch").exception("launcher crashed")
        msgbox(f"The editor crashed:\n\n{e!r}\n\nSee scripts\\editor\\.local\\logs\\editor.log")
        code = 1
    raise SystemExit(code)
