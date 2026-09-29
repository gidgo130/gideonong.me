"""Read-only preview server for the repo root (127.0.0.1:5501).

Behaves like the deployed site:
  * root-relative links work (the repo root is the site root);
  * everything .vercelignore excludes (scripts/, staging/, references/, *.md,
    .githooks/, ...) plus Vercel's own defaults (.git, .vercel, .env*, ...)
    answers 404, so the CV masters never appear here and a link to a
    non-deployed file fails as it would live;
  * no directory listings, GET and HEAD only;
  * while drafts exist, edited data files are served from memory in place of
    the disk version so drafts can be previewed before saving;
  * only requests whose Host (and Origin, when sent) is 127.0.0.1:<port> or
    localhost:<port> are answered — anything else gets 403, so a page on
    another site cannot read the preview through DNS rebinding;
  * every request is resolved on disk before the ignore rules run, so on a
    case-insensitive file system (Windows) `/STAGING/x` or an 8.3 short name
    cannot reach a file the rules hide, and nothing outside the root is served.
"""

from __future__ import annotations

import fnmatch
import http.server
import logging
import mimetypes
import posixpath
import socketserver
import threading
import urllib.parse
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger("editor.preview")

# Paths Vercel never uploads regardless of .vercelignore.
VERCEL_DEFAULT_IGNORES = [
    ".git",
    ".gitmodules",
    ".gitignore",
    ".vercel",
    ".vercelignore",
    ".env",
    ".env.*",
    "node_modules",
    "__pycache__",
    ".DS_Store",
    "*.swp",
]


class IgnoreRules:
    """Minimal gitignore-style matcher (enough for this repo's .vercelignore).

    Matching is case-insensitive on purpose: the preview runs on Windows, where
    the file system is too, so `STAGING/x` must hide exactly what `staging/x`
    hides. (Vercel builds on Linux; a path that differs only by case would be a
    404 there, so being stricter here never shows something the live site hides.)
    """

    def __init__(self, patterns):
        self.rules: list[tuple[bool, str, bool, bool]] = []  # (negate, pattern, dir_only, anchored)
        for raw in patterns:
            p = raw.strip()
            if not p or p.startswith("#"):
                continue
            neg = p.startswith("!")
            if neg:
                p = p[1:]
            dir_only = p.endswith("/")
            p = p.rstrip("/")
            anchored = p.startswith("/")
            p = p.lstrip("/")
            if "/" in p:
                anchored = True
            self.rules.append((neg, p.lower(), dir_only, anchored))

    @classmethod
    def from_repo(cls, repo_root: Path) -> "IgnoreRules":
        pats = list(VERCEL_DEFAULT_IGNORES)
        f = Path(repo_root) / ".vercelignore"
        if f.is_file():
            pats += f.read_text(encoding="utf-8", errors="replace").splitlines()
        return cls(pats)

    def ignored(self, rel_posix: str) -> bool:
        """True if the file at rel_posix (no leading slash) is excluded from the deploy."""
        parts = [p.lower() for p in rel_posix.split("/") if p]
        if not parts:
            return False
        result = False
        for neg, pat, dir_only, anchored in self.rules:
            hit = False
            # Every prefix is a directory; the full path is the file itself.
            for depth in range(1, len(parts) + 1):
                is_dir = depth < len(parts)
                if dir_only and not is_dir:
                    continue
                sub = "/".join(parts[:depth])
                if anchored:
                    if fnmatch.fnmatchcase(sub, pat):
                        hit = True
                        break
                else:
                    if fnmatch.fnmatchcase(parts[depth - 1], pat):
                        hit = True
                        break
            if hit:
                result = not neg
        return result


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "gideonong-preview/1"
    protocol_version = "HTTP/1.1"

    # set on the class by make_server()
    repo_root: Path = Path(".")  # already resolved (make_server does it once)
    rules: IgnoreRules = IgnoreRules([])
    overrides: Callable[[], dict] = staticmethod(lambda: {})

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(self.repo_root), **kw)

    def log_message(self, fmt, *args):  # quiet by default
        log.debug("%s " + fmt, self.address_string(), *args)

    def _rel(self) -> str:
        path = urllib.parse.urlsplit(self.path).path
        path = posixpath.normpath(urllib.parse.unquote(path))
        return path.lstrip("/")

    def _allowed_host(self) -> bool:
        """Host must be this server's own 127.0.0.1/localhost:<port>; Origin, if sent, the same."""
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = (self.headers.get("Host") or "").strip().lower()
        if host not in hosts:
            return False
        origin = (self.headers.get("Origin") or "").strip().lower()
        if origin and origin not in {"http://" + h for h in hosts}:
            return False
        return True

    def _resolve(self, rel: str) -> Optional[Path]:
        """The on-disk path for rel, or None if it would leave the root.

        Resolving canonicalises letter case and expands 8.3 short names on
        Windows and follows symlinks everywhere, so the ignore check and the
        file the OS actually opens always agree.
        """
        try:
            target = (self.repo_root / rel).resolve() if rel else self.repo_root
        except (OSError, RuntimeError, ValueError):
            return None
        if not target.is_relative_to(self.repo_root):
            return None
        return target

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404, "Not Found")
        return None

    def send_head(self):
        if not self._allowed_host():
            log.warning("preview: rejected Host %r / Origin %r", self.headers.get("Host"), self.headers.get("Origin"))
            self.send_error(403, "Forbidden")
            return None
        rel = self._rel()
        if rel.startswith("..") or "\\" in rel or "\0" in rel:
            self.send_error(404, "Not Found")
            return None
        target = self._resolve(rel)
        if target is None:
            self.send_error(404, "Not Found")
            return None
        # The ignore check runs on the path as it really is on disk, not as typed.
        real_rel = target.relative_to(self.repo_root).as_posix()
        if real_rel == ".":
            real_rel = ""
        # a directory URL maps to its index.html for the ignore check
        check = real_rel
        if not real_rel or target.is_dir():
            check = (real_rel + "/" if real_rel else "") + "index.html"
        if self.rules.ignored(check):
            self.send_error(404, "Not Found")
            return None
        data = self.overrides().get(check)
        if isinstance(data, Path):  # an alias: serve another file on disk under this path (a pending rename)
            try:
                data = data.read_bytes()
            except OSError:
                self.send_error(404, "Not Found")
                return None
        if data is not None:
            ctype = mimetypes.guess_type(check)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
                ctype += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Editor-Draft", "1")
            self.end_headers()
            import io

            return io.BytesIO(data)
        return super().send_head()


class PreviewServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = False


def make_server(repo_root: Path, port: int, overrides: Optional[Callable[[], dict]] = None) -> PreviewServer:
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("image/webp", ".webp")
    mimetypes.add_type("image/avif", ".avif")
    mimetypes.add_type("video/mp4", ".mp4")
    handler = type(
        "BoundPreviewHandler",
        (PreviewHandler,),
        {
            "repo_root": Path(repo_root).resolve(),
            "rules": IgnoreRules.from_repo(repo_root),
            "overrides": staticmethod(overrides or (lambda: {})),
        },
    )
    return PreviewServer(("127.0.0.1", port), handler)


def serve_in_thread(server: PreviewServer) -> threading.Thread:
    t = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.5}, name="preview", daemon=True)
    t.start()
    return t
