from dataclasses import dataclass

@dataclass(frozen=False)
class RetrievedChunk:
    """A single chunk returned by the vector similarity search."""
    filename: str
    text: str
    score: float | None = None
