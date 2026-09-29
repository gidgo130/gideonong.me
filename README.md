# gideonong.me

Personal site of Gideon A. Ong, a Mechanical Engineering student at the University of
Tulsa: projects, experience, an About page, and an unlisted teaching section,
**Reading Your Fits** (`learning/`), on checking a line fit against lab data.

Plain HTML, CSS and vanilla JavaScript. No framework, no build step, no npm: the
repository is exactly what Vercel serves. English and Spanish throughout.

## Layout

| Path | What it is |
| --- | --- |
| `index.html`, `about.html`, `experience.html`, `projects.html`, `projects/` | The site's pages |
| `css/`, `js/` | Styles and scripts; the data files under `js/` feed every list on the site |
| `assets/` | Images, videos, and the resume / CV / transcript PDFs |
| `learning/` | The teaching section: modules, shared assets, and their editable notebooks |
| `learning/workshop/`, `scripts/` | Dev-side tooling: slide sources, exporters, the content editor. Never deployed |
| `CLAUDE.md` | The working manual for the site (structure, conventions, rules) |

Dev tools are Python and Node scripts run before committing; see `CLAUDE.md` and
`learning/README.md`.

An offline copy of the `/learning` pages (Windows installers and a zip) is on the
[Releases](https://github.com/gidgo130/gideonong.me/releases) page.

## Licensing

`LICENSE` and `LICENSE-CONTENT` hold only the standard license texts; this section says which
parts of the repository each one covers.

- **Code** (HTML, CSS, JavaScript, Python and other scripts): [MIT](LICENSE).
- **Teaching content** under `learning/` (module text, strings, slides, figures, the
  companion scripts and notebooks): [CC BY-SA 4.0](LICENSE-CONTENT). Share and adapt it
  with credit to "Gideon A. Ong, gideonong.me/learning", and keep adaptations under the
  same license.
- **Not licensed, all rights reserved:** Gideon A. Ong's name and likeness; the headshot
  and other personal photos; everything under `assets/pdfs/` (resume, CV, transcript,
  project reports); the project and experience photos and videos under `assets/images/`
  and `assets/videos/`, some of which belong to the employers or institutions where they
  were taken; and the personal text of the site (the strings in `js/translations.js` and
  `content.md`). Cited papers are linked by DOI and are not part of this repository.
