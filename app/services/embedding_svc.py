import os
import httpx

class EmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("VOYAGE_API_KEY")
        self.url = "https://api.voyageai.com/v1/embeddings"

    async def embed_text(self, text: str) -> list[float]:
        payload = {
            "model": "voyage-3", # ตัวใหม่ล่าสุด เสถียรและเก่งมาก
            "input": text
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                # Voyage คืนค่ากลับมาใน data['data'][0]['embedding']
                return data["data"][0]["embedding"]
                
        except Exception as e:
            raise RuntimeError(f"Voyage API failed: {str(e)}")

embedding_service = EmbeddingService()