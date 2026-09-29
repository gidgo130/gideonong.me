# Workshop — Reading Your Fits

Source material for the /learning decks. It lives in the repo so GitHub backs it up, but it is
**never deployed**: `.vercelignore` lists `learning/workshop/`. Visitors only load what's in
`learning/` outside this folder. The plan and status are in `learning/learning-plan.md`; how
the section works is in `learning/README.md`.

```
modules/<slug>/
  slides.qmd, custom.scss    Slide source (Quarto revealjs)
  figures/                   PNGs made by the module's Python script (tracked)
tools/
  check-es.js                Checks the ES strings against EN
.gitignore                   Keeps build output out of git (rendered slides.html, installer builds)
```

## Rebuild a module's slides

From `learning\workshop\modules\<slug>\` in PowerShell:

1. Make the figures (they land in `figures\` here):
   `python ..\..\..\fits\<slug>\<slug>.py`
2. `quarto render slides.qmd`
3. Quarto marks the embedded interactive as an image (`role="img"`), which hides its controls
   from screen readers. Remove it:
   `(Get-Content slides.html -Raw) -replace '<iframe role="img" ', '<iframe ' | Set-Content slides.html -Encoding utf8`
4. Copy it to the page folder (the tracked copy):
   `Copy-Item slides.html ..\..\..\fits\<slug>\slides.html`

The `slides.html` left here is ignored by git. Its "Try it yourself" slide is blank here,
because it loads the `index.html` next to it, which only exists in the page folder.

Quarto: install from https://quarto.org/docs/get-started/ and the Quarto extension for VS Code.

## Check the Spanish strings

From the repo root: `node learning/workshop/tools/check-es.js`. It checks every strings file:
same keys in `en` and `es`, same {placeholders}, same tag counts in *Html keys, and an `es`
phrase on every chip. It ends with "All files OK" or a problem count (exit code 1).
