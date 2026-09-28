"""Launcher for the local content editor (double-click target; no console).

  * lock file: a second launch brings the existing window to the front. If the
    lock points at a server whose window is gone, that server is ended and a
    fresh one starts;
  * starts the editor on 127.0.0.1:5510 and the read-only preview on
    127.0.0.1:5501 in background threads of this process;
  * opens a pywebview window (WebView2) on the editor URL with the per-launch
    token. webview.start() blocks; when it returns — window closed normally,
    destroyed by the watchdog, or killed — both servers stop, the lock is
    removed and the process exits with os._exit so nothing can linger;
  * closing with unsaved drafts asks first (they are autosaved anyway);
  * crash fallback: no heartbeat from the page for 10 minutes AND no drafts →
    the window is destroyed, which ends the process the same way;
  * logs in .local/logs/editor.log; WebView2 storage in .local/webview.

Run with `--no-window` to start the servers without a window (tests).
"""

from __future__ import annotations

import argparse
import ctypes
import json
import logging
import os
import secrets
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

LOCAL = HERE / ".local"
LOGS = LOCAL / "logs"
WEBVIEW_DIR = LOCAL / "webview"
LOCK = LOCAL / "editor.lock"
WINDOW_TITLE = "Site editor — gideonong.me"
TITLE_PART = "Site editor"
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


def api_post(port: int, path: str, token: str, timeout: float = 3.0) -> Optional[dict]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=b"{}",
        method="POST",
        headers={"X-Editor-Token": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log.info("POST %s failed: %s", path, e)
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


def process_cmdline(pid: int) -> Optional[str]:
    """Command line of a process, or None if it does not exist (Windows only)."""
    if os.name != "nt":
        return None
    cmd = f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=CREATE_NO_WINDOW,
        )
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def end_stale_server(lock: dict) -> bool:
    """End a launcher whose window is gone (pid from the lock). True if its ports came free."""
    pid = int(lock.get("pid") or 0)
    if pid and pid != os.getpid():
        cmdline = process_cmdline(pid)
        if cmdline and "launch.pyw" in cmdline:
            log.warning("ending stale editor process %d (window gone)", pid)
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError as e:
                log.warning("could not end pid %d: %s", pid, e)
        else:
            log.warning("pid %d from the lock is not the editor (%r); not touching it", pid, cmdline)
    remove_lock()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if port_free(int(lock.get("port", 5510))) and port_free(int(lock.get("previewPort", 5501))):
            return True
        time.sleep(0.5)
    return False


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


def bring_to_front(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    user32.ShowWindow(ctypes.c_void_p(hwnd), 9)  # SW_RESTORE
    user32.keybd_event(0x12, 0, 0, 0)  # a synthetic Alt press lets SetForegroundWindow succeed
    user32.keybd_event(0x12, 0, 2, 0)
    user32.SetForegroundWindow(ctypes.c_void_p(hwnd))


def token_from_url(url: str) -> str:
    from urllib.parse import parse_qs, urlsplit

    return (parse_qs(urlsplit(url).query).get("token") or [""])[0]


# -------------------------------------------------------------------- main


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-window", "--no-edge", dest="no_window", action="store_true", help="servers only (tests)")
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
        log.info("editor already running (pid %s)", lock.get("pid"))
        if args.no_window:
            print("already running: " + (lock.get("url") or ""), flush=True)
            return 0
        r = api_post(int(lock.get("port", editor_port)), "/api/focus", token_from_url(lock.get("url", "")))
        if r and r.get("focused"):
            for hwnd in find_windows(TITLE_PART):
                bring_to_front(hwnd)
            log.info("focused the existing window")
            return 0
        log.warning("server answers but has no window; replacing it")
        if not end_stale_server(lock):
            msgbox("An earlier editor process is still holding port 5510 or 5501 and could not be ended.\nClose it in Task Manager (pythonw.exe) and try again.")
            return 1
    elif lock:
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

    def shutdown(reason: str) -> None:
        log.info("shutting down: %s", reason)
        try:
            servers.stop()
        finally:
            remove_lock()
            log.info("editor stopped")
            logging.shutdown()

    # ---- servers only (tests) --------------------------------------------
    if args.no_window:
        print(url, flush=True)
        try:
            while not state.shutdown_requested.is_set():
                time.sleep(1.0)
                if state.heartbeat_silence() >= editor_app.HEARTBEAT_TIMEOUT and not state.drafts:
                    break
        except KeyboardInterrupt:
            pass
        shutdown("no-window mode ended")
        return 0

    # ---- window -----------------------------------------------------------
    import webview

    WEBVIEW_DIR.mkdir(parents=True, exist_ok=True)
    window = webview.create_window(WINDOW_TITLE, url, width=1440, height=920, min_size=(900, 600), text_select=True)

    def on_closing():
        n = len(state.drafts)
        if n and not state.shutdown_requested.is_set():
            return bool(
                window.create_confirmation_dialog(
                    "Site editor",
                    f"{n} unsaved draft{'s' if n > 1 else ''}. They are autosaved and will be offered again "
                    "next time you open the editor.\n\nClose anyway?",
                )
            )
        return True

    window.events.closing += on_closing

    def focus() -> bool:
        if window not in webview.windows:
            return False
        try:
            window.restore()
            window.show()
            return True
        except Exception as e:  # pragma: no cover
            log.warning("focus failed: %s", e)
            return False

    state.focus_callback = focus

    def watchdog():
        gone_since = None
        while True:
            time.sleep(5)
            if state.shutdown_requested.is_set():
                log.info("shutdown requested; destroying window")
                _destroy(window)
                return
            if window not in webview.windows:
                gone_since = gone_since or time.monotonic()
                if time.monotonic() - gone_since > 15:
                    # webview.start() should have returned by now; make sure we leave anyway
                    shutdown("window gone but start() did not return")
                    os._exit(0)
                continue
            gone_since = None
            if state.heartbeat_silence() >= editor_app.HEARTBEAT_TIMEOUT and not state.drafts:
                log.info("no heartbeat for %.0f s and no drafts — destroying window", state.heartbeat_silence())
                state.shutdown_requested.set()
                _destroy(window)
                return

    threading.Thread(target=watchdog, name="watchdog", daemon=True).start()

    try:
        webview.start(gui="edgechromium", private_mode=False, storage_path=str(WEBVIEW_DIR))
    except Exception as e:
        log.exception("webview failed")
        shutdown("webview error")
        msgbox(f"The editor window could not be opened:\n\n{e!r}\n\nIs the WebView2 runtime installed? (It ships with Edge.)")
        os._exit(1)
    shutdown("window closed")
    os._exit(0)


def _destroy(window) -> None:
    try:
        window.destroy()
    except Exception as e:  # pragma: no cover
        logging.getLogger("editor.launch").warning("destroy failed: %s", e)


if __name__ == "__main__":
    try:
        code = main()
    except Exception as e:  # last-resort report for a windowless process
        logging.getLogger("editor.launch").exception("launcher crashed")
        msgbox(f"The editor crashed:\n\n{e!r}\n\nSee scripts\\editor\\.local\\logs\\editor.log")
        code = 1
    remove_lock() if code else None
    os._exit(code)
