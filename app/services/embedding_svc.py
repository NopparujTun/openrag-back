# ใน app/services/embedding_svc.py
import os
import httpx

class EmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("MXBAI_API_KEY")
        self.url = "https://api.mixedbread.ai/v1/embeddings"

    async def embed_text(self, text: str) -> list[float]:
        payload = {
            "model": "mixedbread-ai/mxbai-embed-large-v1",
            "input": text,
            "normalized": True,
            "encoding_format": "float"
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

embedding_service = EmbeddingService()