"""Plan §5: the editor's code must never run a git write command.

Scans every code file under scripts/editor (not this test, not README) for a
`git` invocation followed by a verb that changes the repository. Read-only
`git status` / `git diff` are allowed.
"""

import re
import unittest
from pathlib import Path

from _helpers import EDITOR_DIR

WRITE_VERBS = (
    "add|commit|push|pull|fetch|merge|rebase|reset|checkout|switch|restore|stash|tag|rm|mv|"
    "cherry-pick|revert|am|apply|clean|branch|init|clone|gc|prune|filter-branch|submodule|worktree"
)
# `git` then, on the same line, one of the verbs (as a word or a quoted arg)
PATTERN = re.compile(r"\bgit\b[^\n]*?[\s\"',\[(](?:" + WRITE_VERBS + r")\b", re.IGNORECASE)
CODE_SUFFIXES = {".py", ".pyw", ".js", ".ps1", ".html", ".css", ".bat", ".cmd"}


class NoGitWrites(unittest.TestCase):
    def test_no_git_write_commands_in_editor_code(self):
        hits = []
        for p in EDITOR_DIR.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in CODE_SUFFIXES:
                continue
            if ".local" in p.parts or p.name == Path(__file__).name:
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if PATTERN.search(line):
                    hits.append(f"{p.relative_to(EDITOR_DIR)}:{n}: {line.strip()}")
        self.assertEqual(hits, [], "git write command(s) found:\n" + "\n".join(hits))

    def test_pattern_catches_the_obvious_forms(self):
        for bad in ('subprocess.run(["git", "add", "."])', "os.system('git commit -m x')", "git push origin main", '["git", "-C", root, "reset", "--hard"]'):
            self.assertTrue(PATTERN.search(bad), bad)
        for ok in ('["git", "status", "--porcelain"]', "git diff --stat", "# read-only git status only"):
            self.assertFalse(PATTERN.search(ok), ok)


if __name__ == "__main__":
    unittest.main()
