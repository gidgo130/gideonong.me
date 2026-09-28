"""Read-only preview server for the repo root (127.0.0.1:5501).

Behaves like the deployed site:
  * root-relative links work (the repo root is the site root);
  * everything .vercelignore excludes (scripts/, staging/, references/, *.md,
    .githooks/, ...) plus Vercel's own defaults (.git, .vercel, .env*, ...)
    answers 404, so the CV masters never appear here and a link to a
    non-deployed file fails as it would live;
  * no directory listings, GET and HEAD only;
  * while drafts exist, edited data files are served from memory in place of
    the disk version so drafts can be previewed before saving.
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
    """Minimal gitignore-style matcher (enough for this repo's .vercelignore)."""

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
            self.rules.append((neg, p, dir_only, anchored))

    @classmethod
    def from_repo(cls, repo_root: Path) -> "IgnoreRules":
        pats = list(VERCEL_DEFAULT_IGNORES)
        f = Path(repo_root) / ".vercelignore"
        if f.is_file():
            pats += f.read_text(encoding="utf-8", errors="replace").splitlines()
        return cls(pats)

    def ignored(self, rel_posix: str) -> bool:
        """True if the file at rel_posix (no leading slash) is excluded from the deploy."""
        parts = [p for p in rel_posix.split("/") if p]
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
    repo_root: Path = Path(".")
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

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404, "Not Found")
        return None

    def send_head(self):
        rel = self._rel()
        if rel.startswith("..") or "\\" in rel:
            self.send_error(404, "Not Found")
            return None
        # a directory URL maps to its index.html for the ignore check
        check = rel
        if not rel or (self.repo_root / rel).is_dir():
            check = (rel + "/" if rel else "") + "index.html"
        if self.rules.ignored(check):
            self.send_error(404, "Not Found")
            return None
        data = self.overrides().get(check)
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
            "repo_root": Path(repo_root),
            "rules": IgnoreRules.from_repo(repo_root),
            "overrides": staticmethod(overrides or (lambda: {})),
        },
    )
    return PreviewServer(("127.0.0.1", port), handler)


def serve_in_thread(server: PreviewServer) -> threading.Thread:
    t = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.5}, name="preview", daemon=True)
    t.start()
    return t
