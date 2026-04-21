"""
app/services/text_extract.py
-----------------------------
Text extraction service — converts raw file bytes into clean plain text.

Supports: PDF (.pdf), Word (.docx), plain text (.txt), CSV (.csv).
All extracted text is normalized via _normalize_text to remove null bytes,
strip trailing whitespace per line, and produce clean UTF-8 output.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import fitz  # PyMuPDF
from pythainlp.util import normalize as thai_normalize
from docx import Document as DocxDocument


def _normalize_text(raw: str) -> str:
    """
    Normalises raw extracted text:
      - Removes null bytes (common in PDF extraction artefacts)
      - Strips trailing whitespace from each line
      - Strips leading/trailing blank lines from the result
    """
    raw = raw.replace("\x00", " ")
    raw = "\n".join(line.rstrip() for line in raw.splitlines())
    return raw.strip()


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    """
    Extracts plain text from a file given as raw bytes.

    Args:
        filename: Original filename (used only to determine file type via extension).
        data:     Raw file bytes.

    Returns:
        Normalised plain-text string.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        doc = fitz.open(stream=data, filetype="pdf")
        pages = []
        for page in doc:
            # Using 'blocks' with sort=True helps maintain logical reading order
            blocks = page.get_text("blocks", sort=True)
            page_text = "\n".join(b[4] for b in blocks if len(b) > 4)
            # Normalize Thai characters to fix floating vowels and tone marks, and remove zero-width spaces
            normalized_page = thai_normalize(page_text).replace('\u200b', '')
            pages.append(normalized_page)
        return _normalize_text("\n\n".join(pages))

    if ext == ".docx":
        doc = DocxDocument(io.BytesIO(data))
        return _normalize_text("\n".join(p.text for p in doc.paragraphs))

    if ext == ".txt":
        return _normalize_text(data.decode("utf-8", errors="ignore"))

    if ext == ".csv":
        text = data.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        rows = [
            " | ".join(cell.strip() for cell in row if cell is not None)
            for row in reader
        ]
        return _normalize_text("\n".join(r for r in rows if r.strip()))

    raise ValueError(f"Unsupported file type: {ext}")
