"""The Designed CV: a fourth CV output with no Word master — a one-page HTML/CSS page with a
photo and age, printed to PDF by headless Edge. Private: nothing here publishes anything.

schema.py   content.json version 2 (the `design` block), the one-time migration, what an
            "Import masters" carries over, and the seed
model.py    pure operations on the Designed part of the content set (checklist, per-output
            text, section placement, sort, the sidebar rows)
render.py   content set → the page's HTML (static/designed/page.html + designed.css)
export.py   headless Edge / Chrome: measure the columns, print the PDF
checks.py   what blocks an export or marks it failed (D8)
service.py  what the Designed CV page talks to
"""
