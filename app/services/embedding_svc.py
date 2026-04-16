from __future__ import annotations

import httpx

from app.core.config import settings


class OllamaEmbeddingError(RuntimeError):
    pass


class EmbeddingService:
    async def embed_text(self, text: str) -> list[float]:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                r = await client.post(url, json={"model": settings.ollama_embed_model, "prompt": text})
            except httpx.RequestError as e:
                raise OllamaEmbeddingError("Ollama is not reachable") from e
        if r.status_code != 200:
            raise OllamaEmbeddingError(f"Ollama embeddings failed: {r.status_code} {r.text}")
        data = r.json()
        emb = data.get("embedding")
        if not isinstance(emb, list):
            raise OllamaEmbeddingError("Ollama embeddings response missing embedding")
        return emb

embedding_service = EmbeddingService()
