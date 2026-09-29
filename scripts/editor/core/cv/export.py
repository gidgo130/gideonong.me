"""Export a .docx to PDF with a PRIVATE Word instance.

docx2pdf.convert() attaches to whatever Word is already running and calls
Quit() when it is done, which would close Gideon's open documents (and close
the master itself, unsaved, if he had it open). So this uses the same COM
route (pywin32, which docx2pdf depends on) but with DispatchEx: a separate,
hidden Word process that opens the master read-only, exports, closes it and
quits itself. The user's Word session is never touched. Decision 2026-09-28.

A master that is open in Word (its "~$" owner file exists) is refused with
"close it in Word": what Word shows may not be on disk yet.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, Optional

from .masters import word_lock_file

WD_EXPORT_FORMAT_PDF = 17


class ExportError(RuntimeError):
    pass


def check_exportable(docx: Path) -> Optional[str]:
    """None if the file can be exported now, else the reason."""
    docx = Path(docx)
    if not docx.is_file():
        return f"{docx.name} is missing"
    if word_lock_file(docx) is not None:
        return f"{docx.name} is open in Word — close it in Word first (what you see there may not be saved)"
    return None


def export_pdf(docx: Path, pdf: Path, log: Callable[[str], None] = lambda s: None) -> Path:
    """Export docx → pdf. Writes a temp file first, then replaces pdf atomically."""
    docx, pdf = Path(docx).resolve(), Path(pdf).resolve()
    reason = check_exportable(docx)
    if reason:
        raise ExportError(reason)
    pdf.parent.mkdir(parents=True, exist_ok=True)
    tmp = pdf.with_name(f"{pdf.stem}.tmp-{os.getpid()}-{int(time.time() * 1000)}.pdf")
    try:
        import pythoncom
        import win32com.client
    except ImportError as e:  # pragma: no cover - pywin32 is a docx2pdf dependency
        raise ExportError(f"pywin32 is not installed ({e}); run the requirements install") from e

    pythoncom.CoInitialize()
    word = None
    try:
        try:
            word = win32com.client.DispatchEx("Word.Application")
        except Exception as e:
            raise ExportError(f"Word could not be started ({e}). Is Microsoft Word installed?") from e
        try:
            word.Visible = False
            word.DisplayAlerts = 0
            log(f"Word {getattr(word, 'Version', '?')} started (private instance)")
            doc = word.Documents.Open(str(docx), ReadOnly=True, AddToRecentFiles=False, Visible=False)
            try:
                log(f"opened {docx.name}")
                doc.ExportAsFixedFormat(str(tmp), WD_EXPORT_FORMAT_PDF)
                log(f"exported {pdf.name}")
            finally:
                doc.Close(0)  # wdDoNotSaveChanges
        except ExportError:
            raise
        except Exception as e:
            raise ExportError(f"Word did not export {docx.name}: {e}") from e
        finally:
            if word is not None:
                try:
                    word.Quit()
                except Exception:  # pragma: no cover
                    pass
    finally:
        pythoncom.CoUninitialize()
    if not tmp.is_file():
        raise ExportError(f"Word reported success but {tmp.name} was not written")
    os.replace(tmp, pdf)
    return pdf
