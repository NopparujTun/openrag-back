"""
app/services/chunking_service.py
--------------------------------
Text chunking service — splits large documents into smaller overlapping segments.
"""
from __future__ import annotations

import re


class ChunkingService:
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Splits text into chunks of roughly chunk_size characters with overlap.
        Attempts to split on paragraph or sentence boundaries where possible.
        """
        if not text:
            return []

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            
            # If we're not at the end of the string, try to find a better breakpoint
            if end < len(text):
                # Look for last period, question mark, or exclamation point in the last 20% of the chunk
                search_start = max(start, end - 200)
                match = list(re.finditer(r'[.!?]\s', text[search_start:end+1]))
                if match:
                    end = search_start + match[-1].end()
            
            chunks.append(text[start:end].strip())
            start = end - overlap
            
            # Prevent infinite loop if overlap is too large or progress is zero
            if start >= len(text) or (end - start) <= 0:
                break
                
        return [c for c in chunks if len(c) > 10]


chunking_service = ChunkingService()
