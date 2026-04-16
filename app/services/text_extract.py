from __future__ import annotations

import csv
import io
from pathlib import Path

import pdfplumber
from docx import Document as DocxDocument
from unidecode import unidecode


def _clean(s: str) -> str:
    s = s.replace("\u0000", " ")
    s = unidecode(s)
    s = "\n".join([line.rstrip() for line in s.splitlines()])
    return s.strip()


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = []
            for p in pdf.pages:
                pages.append(p.extract_text() or "")
        return _clean("\n\n".join(pages))
    if ext == ".docx":
        doc = DocxDocument(io.BytesIO(data))
        return _clean("\n".join([p.text for p in doc.paragraphs]))
    if ext in (".txt",):
        return _clean(data.decode("utf-8", errors="ignore"))
    if ext in (".csv",):
        # Flatten CSV rows to text for embedding
        text = data.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        rows = [" | ".join([c.strip() for c in row if c is not None]) for row in reader]
        return _clean("\n".join([r for r in rows if r.strip()]))
    raise ValueError(f"Unsupported file type: {ext}")

