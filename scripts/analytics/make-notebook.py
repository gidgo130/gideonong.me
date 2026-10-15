"""make-notebook.py — write analytics.ipynb from analytics.py (same folder).

    python scripts/analytics/make-notebook.py           write the notebook
    python scripts/analytics/make-notebook.py --check   exit 1 if it's out of date

analytics.py is the source and stays a plain script that runs top to bottom. Cell markers are
comments, as in learning/workshop/tools/make-ipynb.py:
    # %% [markdown]    a markdown cell: every following line is "# text" (or a bare "#")
    # %%               a code cell
The module docstring becomes the first markdown cell.

The notebook is written with NO outputs and no execution counts, and with Colab's "omit code
cell output when saving" switched on (metadata.colab.private_outputs), so neither this file nor
a Colab save can carry data. The pre-commit hook checks the outputs again (rule d). Standard
library only; deterministic, so an unchanged analytics.py gives no diff.

Dev Python on this machine: %LOCALAPPDATA%\\Python\\pythoncore-3.14-64\\python.exe (not `python`).
"""
import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "analytics.py"
OUT = HERE / "analytics.ipynb"


def lines(text):
    """Notebook 'source' form: a list of lines, each but the last ending in a newline."""
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]] if text else []


def cells_from(source):
    tree = ast.parse(source)
    doc = ast.get_docstring(tree, clean=True) or ""
    body = source.split('"""', 2)[2] if doc else source  # everything after the docstring
    cells = [("markdown", doc)] if doc else []
    kind, buf = None, []

    def flush():
        if kind is None:
            return
        text = "\n".join(buf).strip("\n")
        if kind == "markdown":
            text = "\n".join(l[2:] if l.startswith("# ") else "" if l.strip() == "#" else l for l in text.split("\n"))
        if text.strip():
            cells.append((kind, text))

    for line in body.split("\n"):
        if line.startswith("# %% [markdown]"):
            flush(); kind, buf = "markdown", []
        elif line.startswith("# %%"):
            flush(); kind, buf = "code", []
        elif kind is not None:
            buf.append(line)
    flush()
    return cells


def notebook(cells):
    out = []
    for i, (kind, text) in enumerate(cells):
        cell = {"cell_type": kind, "id": f"cell-{i:02d}", "metadata": {}, "source": lines(text)}
        if kind == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        out.append(cell)
    return {
        "cells": out,
        "metadata": {
            "colab": {"private_outputs": True, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main():
    text = json.dumps(notebook(cells_from(SRC.read_text(encoding="utf-8"))), indent=1, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("analytics.ipynb is out of date: run scripts/analytics/make-notebook.py", file=sys.stderr)
            sys.exit(1)
        print("analytics.ipynb is up to date")
        return
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
