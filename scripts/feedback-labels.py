"""feedback-labels.py — create the /learning feedback labels once in the private feedback repo.

    $py scripts/feedback-labels.py                 repo from FEEDBACK_REPO, else gidgo130/gideonong-feedback
    $py scripts/feedback-labels.py --repo o/name   another repo

Labels (CLAUDE.md → /learning → Feedback; learning-plan.md decision F4): feedback, kind:<kind>,
series:<series>, source:visitor | source:gideon. api/feedback.js puts them on every issue it
files. Standard library plus the GitHub CLI (`gh`, logged in as the repo owner); each label is
created with --force, so rerunning only updates colors and descriptions. Dev-only, never deployed.

Dev Python on this machine: %LOCALAPPDATA%\\Python\\pythoncore-3.14-64\\python.exe (not `python`).
"""
import argparse
import os
import shutil
import subprocess
import sys

DEFAULT_REPO = "gidgo130/gideonong-feedback"
GH_FALLBACK = r"C:\Program Files\GitHub CLI\gh.exe"

# name, color (hex, no #), description
LABELS = [
    ("feedback", "0e8a16", "Filed by the /learning feedback widget (api/feedback.js)"),
    ("kind:mistake", "d73a4a", "Something on the page is wrong"),
    ("kind:confusing", "e4a11b", "Something on the page is unclear"),
    ("kind:suggestion", "0075ca", "An idea for the page or the series"),
    ("kind:other", "bfbfbf", "Anything else"),
    ("series:fits", "1d5ea6", "Reading Your Fits (learning/fits/)"),
    ("series:reflections", "7e5b17", "Reflections (learning/reflections/)"),
    ("series:marginalia", "a83a2e", "Marginalia (learning/marginalia/)"),
    ("series:hub", "5319e7", "The /learning hub page"),
    ("source:visitor", "ededed", "Sent by a visitor"),
    ("source:gideon", "6f42c1", "Sent by Gideon with the owner key (F5)"),
]


def gh_path():
    return shutil.which("gh") or (GH_FALLBACK if os.path.exists(GH_FALLBACK) else None)


def main():
    ap = argparse.ArgumentParser(description="Create the feedback labels once (idempotent).")
    ap.add_argument("--repo", default=os.environ.get("FEEDBACK_REPO", DEFAULT_REPO), help="owner/name")
    args = ap.parse_args()
    gh = gh_path()
    if not gh:
        sys.exit("gh not found: install the GitHub CLI (winget install GitHub.cli) and run `gh auth login`.")
    failures = 0
    for name, color, desc in LABELS:
        cmd = [gh, "label", "create", name, "--repo", args.repo, "--color", color, "--description", desc, "--force"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  ok   {name}")
        else:
            failures += 1
            print(f"  FAIL {name}: {(r.stderr or r.stdout).strip()}")
    print(f"{len(LABELS) - failures} of {len(LABELS)} labels in {args.repo}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
