LinkedIn's [in] logo files for the Designed CV go in this folder, copied UNCHANGED from
staging/cv-design/icons/ (from brand.linkedin.com/downloads, plus the *-noR.png copies with
the registered mark trimmed):

    InBug-White.png  InBug-Black.png  LI-In-Bug.png  and their -noR.png copies

They are LinkedIn's files, so .gitignore keeps them out of the repository. The page uses
InBug-White-noR.png as a CSS mask (scaling and coloring happen in CSS only). When the file is
not here — a fresh clone — the LinkedIn row gets the generic link icon instead.

The other icons (cake, phone, mail, the website glyphs) are inline SVG in ../parts.html.
