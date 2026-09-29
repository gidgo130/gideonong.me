"""Spanish figures for a module's slides, without touching the public script.

Runs learning/fits/<slug>/<slug>.py unchanged (same seeds, same data) with two hooks:
  - every piece of text matplotlib draws (titles, labels, ticks, legends, notes) is translated
    through modules/<slug>/figures-es.json and its decimal points become commas;
  - figures are saved to modules/<slug>/figures-es/ instead of figures/.

Table keys are the English text with every number replaced by "#", e.g.
  "without it: #"  ->  "sin él: #"
Numbers come back in order, with a decimal comma. Text that is only numbers, symbols or a
single letter needs no entry. Any other text missing from the table is listed and the run
fails (exit 1), so no English slips into a Spanish deck.

Usage (from the repo root or anywhere):
  python learning/workshop/tools/figures-es.py <slug>            make figures-es/
  python learning/workshop/tools/figures-es.py <slug> --list     print the table keys the
                                                                 script needs (writes nothing)
"""
import json
import os
import re
import runpy
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.text import Text  # noqa: E402

WORKSHOP = Path(__file__).resolve().parent.parent
LEARNING = WORKSHOP.parent
NUM = re.compile(r"(?<![A-Za-z_])[-−]?\d+(?:\.\d+)?")
TRIVIAL = re.compile(r"^[\s#%×±·−\-+=<>()/,.:;$^{}\\]*[A-Za-z]?[\s#%×±·−\-+=<>()/,.:;$^{}\\]*$")


def template(text):
    """English text -> (key with numbers as '#', list of the numbers as strings)."""
    nums = NUM.findall(text)
    return NUM.sub("#", text), nums


def comma(num):
    return num.replace(".", ",")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug, listing = sys.argv[1], "--list" in sys.argv[2:]
    script = LEARNING / "fits" / slug / f"{slug}.py"
    module = WORKSHOP / "modules" / slug
    table_path = module / "figures-es.json"
    table = {} if listing else json.loads(table_path.read_text(encoding="utf-8"))
    out = module / "figures-es"
    missing, used = {}, set()

    def translate(text):
        if not text or not text.strip():
            return text
        key, nums = template(text)
        if key in table:
            used.add(key)
            es = table[key]
        elif TRIVIAL.match(key):
            es = key
        else:
            missing.setdefault(key, text)
            return text
        if es.count("#") != len(nums):
            missing.setdefault(key, f"{text}   <-- the table entry has {es.count('#')} '#', the text has {len(nums)} numbers")
            return text
        for n in nums:
            es = es.replace("#", comma(n), 1)
        return es

    # Every text element gets its Spanish for real before tight_layout and before saving, so
    # matplotlib sizes legends, spacing and the saved crop around the Spanish, not the English.
    # Tick labels are rebuilt from the numbers on every draw, so draw_es translates those
    # (numbers only: just the decimal comma). `_es` marks text that is already Spanish.
    def translate_all(fig):
        for t in fig.findobj(Text):
            text = t.get_text()
            if getattr(t, "_es", None) != text:
                t._es = translate(text)
                t.set_text(t._es)

    draw = Text.draw

    def draw_es(self, renderer):
        original = self.get_text()
        if getattr(self, "_es", None) == original:
            return draw(self, renderer)
        self.set_text(translate(original))
        try:
            return draw(self, renderer)
        finally:
            self.set_text(original)

    tight_layout = Figure.tight_layout

    def tight_layout_es(self, *args, **kwargs):
        translate_all(self)
        return tight_layout(self, *args, **kwargs)

    savefig = Figure.savefig

    def savefig_es(self, fname, *args, **kwargs):
        name = Path(fname).name
        translate_all(self)
        if listing:
            self.canvas.draw()  # collects the tick-label keys too
            print(f"  (would save {name})")
            return None
        out.mkdir(exist_ok=True)
        return savefig(self, out / name, *args, **kwargs)

    Text.draw, Figure.tight_layout, Figure.savefig = draw_es, tight_layout_es, savefig_es
    plt.show = lambda *a, **k: None
    os.chdir(module)
    runpy.run_path(str(script), run_name="__main__")

    if listing:
        print(json.dumps({k: "" for k in missing}, ensure_ascii=False, indent=2))
        return
    unused = sorted(set(table) - used)
    if unused:
        print("Table entries the script never drew (check for typos):")
        for k in unused:
            print("  ", json.dumps(k, ensure_ascii=False))
    if missing:
        print(f"{len(missing)} text(s) with no Spanish in {table_path.name}:")
        for k, v in missing.items():
            print("  ", json.dumps(k, ensure_ascii=False), "  from", json.dumps(v, ensure_ascii=False))
        sys.exit(1)
    print(f"Spanish figures saved in {out}")


if __name__ == "__main__":
    main()
