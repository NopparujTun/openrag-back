from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str) -> list[str]:
    """
    PRD specifies 400 tokens with 50 overlap. We approximate tokens using characters.
    In practice ~4 chars/token for English, so 1600 chars ~= 400 tokens.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1600,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if c.strip()]

