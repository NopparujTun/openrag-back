"""
app/services/embedding_svc.py
------------------------------
Embedding service — wraps the local Ollama embeddings API.

Responsibility: convert a text string into a float vector using the
configured embedding model. All HTTP concerns (retry, timeout, error
wrapping) are handled here so callers stay decoupled from transport details.
"""
from __future__ import annotations

import httpx

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embed_model

    async def embed(self, text: str) -> list[float]:
        """
        Embeds a text string via the local Ollama instance.

        Returns a list of floats representing the embedding vector.
        Raises RuntimeError on any transport or API error so callers
        can handle it uniformly without catching httpx internals.
        """
        payload = {"model": self.model, "prompt": text}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/api/embeddings",
                    json=payload,
                    timeout=60.0,
                )
                response.raise_for_status()

                data = response.json()
                if "embedding" not in data:
                    raise RuntimeError(
                        f"Ollama response missing 'embedding' field: {data}"
                    )

                return data["embedding"]

        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Ollama embedding failed: {exc}") from exc


embedding_service = EmbeddingService()
