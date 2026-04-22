"""
app/services/text_extraction_service.py
---------------------------------------
Text extraction service — converts raw file bytes into clean plain text.

Supports: PDF (.pdf), Word (.docx), plain text (.txt), CSV (.csv).
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import fitz  # PyMuPDF
from pythainlp.util import normalize as thai_normalize
from docx import Document as DocxDocument


class TextExtractionService:
    def _normalize_text(self, raw: str) -> str:
        """
        Normalises raw extracted text:
          - Removes null bytes
          - Strips trailing whitespace from each line
          - Strips leading/trailing blank lines
        """
        raw = raw.replace("\x00", " ")
        raw = "\n".join(line.rstrip() for line in raw.splitlines())
        return raw.strip()

    def extract_text(self, filename: str, data: bytes) -> str:
        """
        Extracts plain text from a file given as raw bytes.
        """
        ext = Path(filename).suffix.lower()

        if ext == ".pdf":
            doc = fitz.open(stream=data, filetype="pdf")
            pages = []
            for page in doc:
                blocks = page.get_text("blocks", sort=True)
                page_text = "\n".join(b[4] for b in blocks if len(b) > 4)
                normalized_page = thai_normalize(page_text).replace('\u200b', '')
                pages.append(normalized_page)
            return self._normalize_text("\n\n".join(pages))

        if ext == ".docx":
            doc = DocxDocument(io.BytesIO(data))
            return self._normalize_text("\n".join(p.text for p in doc.paragraphs))

        if ext == ".txt":
            return self._normalize_text(data.decode("utf-8", errors="ignore"))

        if ext == ".csv":
            text = data.decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(text))
            rows = [
                " | ".join(cell.strip() for cell in row if cell is not None)
                for row in reader
            ]
            return self._normalize_text("\n".join(r for r in rows if r.strip()))

        raise ValueError(f"Unsupported file type: {ext}")


text_extraction_service = TextExtractionService()
