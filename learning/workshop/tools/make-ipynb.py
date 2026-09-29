"""make-ipynb.py — turn a module's companion script into its Colab notebook.

    python learning/workshop/tools/make-ipynb.py <slug> [--check]
    python learning/workshop/tools/make-ipynb.py all [--check]

Reads   learning/fits/<slug>/<slug>.py      (the script, with "percent" cell markers)
Writes  learning/fits/<slug>/<slug>.ipynb   (tracked; the module page's "Open in Colab" link
                                             opens it from GitHub, so the repo must be public)

The script stays an ordinary Python file that runs top to bottom. The markers are comments:
    # %% [markdown]      a markdown cell: every following line is "# text" (or a bare "#")
    # %%                 a code cell (an optional title may follow the marker)
Text before the first marker must be the module docstring; it becomes the first markdown
cell. Standard library only: the notebook JSON (nbformat 4.5) is written directly, with
deterministic cell ids, so re-running the tool on an unchanged script produces no diff.

--check validates without Jupyter: the code cells are joined in order and run as a script,
the original script is run too (both with MPLBACKEND=Agg, each in its own temp folder so
no figures land in the repo, same interpreter), and their stdout must be identical. If the
nbformat package is importable the notebook is also validated against the schema.

Dev Python on this machine: %LOCALAPPDATA%\\Python\\pythoncore-3.14-64\\python.exe (not `python`).
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # tools -> workshop -> learning -> repo
FITS = ROOT / "learning" / "fits"
MARKER = re.compile(r"^# %%(?P<md> \[markdown\])?(?P<title>.*)$")


def slugs():
    text = (ROOT / "learning" / "assets" / "modules.js").read_text(encoding="utf-8")
    return re.findall(r'slug:\s*"([a-z0-9-]+)"', text)


def split_cells(source, name):
    """Return [(kind, title, lines)] for the script text; kind is 'markdown' or 'code'."""
    lines = source.replace("\r\n", "\n").split("\n")
    cells, current = [], None
    head = []
    for ln in lines:
        m = MARKER.match(ln)
        if m:
            current = ["markdown" if m.group("md") else "code", m.group("title").strip(), []]
            cells.append(current)
        elif current is None:
            head.append(ln)
        else:
            current[2].append(ln)
    if not cells:
        raise SystemExit(f"{name}: no '# %%' cell markers found")
    doc = "\n".join(head).strip()
    if not (doc.startswith('"""') and doc.endswith('"""')):
        raise SystemExit(f"{name}: text before the first marker must be only the module docstring")
    intro = doc[3:-3].strip("\n")
    cells.insert(0, ["markdown", "", intro.split("\n")])
    out = []
    for kind, title, body in cells:
        if kind == "markdown" and title == "" and body is cells[0][2]:
            text = body
        elif kind == "markdown":
            text = []
            for ln in body:
                if ln == "#":
                    text.append("")
                elif ln.startswith("# "):
                    text.append(ln[2:])
                elif ln.strip() == "":
                    text.append("")
                else:
                    raise SystemExit(f"{name}: a markdown cell holds a non-comment line: {ln!r}")
        else:
            text = body
            if any(l.lstrip().startswith("if __name__") for l in text):
                raise SystemExit(f"{name}: drop the __main__ guard; the notebook runs top to bottom")
        while text and text[0].strip() == "":
            text.pop(0)
        while text and text[-1].strip() == "":
            text.pop()
        if text:
            out.append((kind, title, text))
    return out


def notebook_json(slug, cells):
    nb_cells = []
    for i, (kind, title, text) in enumerate(cells):
        source = [ln + "\n" for ln in text[:-1]] + [text[-1]]
        cell = {"cell_type": kind, "id": f"{slug}-{i:02d}", "metadata": {}, "source": source}
        if title:
            cell["metadata"]["title"] = title
        if kind == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        nb_cells.append(cell)
    return {
        "cells": nb_cells,
        "metadata": {
            "colab": {"name": f"{slug}.ipynb", "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def run_in_temp(code, label):
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / f"{label}.py"
        script.write_text(code, encoding="utf-8")
        res = subprocess.run([sys.executable, str(script)], cwd=tmp, env=env,
                             capture_output=True, text=True, encoding="utf-8", timeout=900)
    if res.returncode != 0:
        raise SystemExit(f"{label} failed:\n{res.stderr[-2000:]}")
    # The scripts print where the figures went; that path differs per temp folder.
    return "\n".join(l for l in res.stdout.splitlines() if not l.startswith("Figures saved in"))


def check(slug, source, cells, path):
    try:
        import nbformat
        nbformat.validate(nbformat.reads(path.read_text(encoding="utf-8"), as_version=4))
        print(f"  nbformat: valid")
    except ImportError:
        print("  nbformat not installed; schema check skipped")
    code = "\n\n".join("\n".join(text) for kind, _, text in cells if kind == "code") + "\n"
    a = run_in_temp(source, f"{slug}-script")
    b = run_in_temp(code, f"{slug}-cells")
    if a != b:
        diff = "\n".join(difflib.unified_diff(a.splitlines(), b.splitlines(), "script", "cells", lineterm=""))
        raise SystemExit(f"{slug}: notebook cells and script print different output:\n{diff}")
    n_md = sum(1 for k, _, _ in cells if k == "markdown")
    print(f"  stdout identical ({len(a.splitlines())} lines); {n_md} markdown cells")


def build(slug, do_check):
    script = FITS / slug / f"{slug}.py"
    out = FITS / slug / f"{slug}.ipynb"
    if not script.is_file():
        raise SystemExit(f"no script at {script}")
    source = script.read_text(encoding="utf-8")
    cells = split_cells(source, script.name)
    text = json.dumps(notebook_json(slug, cells), indent=1, ensure_ascii=False) + "\n"
    changed = not out.is_file() or out.read_text(encoding="utf-8") != text
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"{out.relative_to(ROOT)}: {len(cells)} cells" + (" (updated)" if changed else " (unchanged)"))
    if do_check:
        check(slug, source, cells, out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_check = "--check" in sys.argv
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)
    for s in (slugs() if args[0] == "all" else [args[0]]):
        build(s, do_check)
