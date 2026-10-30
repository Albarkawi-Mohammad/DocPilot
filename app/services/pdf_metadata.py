"""Read-only PDF metadata helper.

This is the only operation DocPilot performs on a selected PDF in the interface
preview: reading its page count for display. It never edits, moves, renames, or
copies the file and performs no OCR or content analysis.
"""

from __future__ import annotations

from pathlib import Path


def read_pdf_page_count(path: str) -> int | None:
    """Return a PDF's page count using Qt's local PDF reader, if available."""
    try:
        from PySide6.QtPdf import QPdfDocument

        document = QPdfDocument()
        document.load(str(Path(path)))
        if document.status() == QPdfDocument.Status.Ready:
            count = int(document.pageCount())
            document.close()
            return count if count > 0 else None
        document.close()
    except Exception:
        return None
    return None
