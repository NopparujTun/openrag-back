import os
import httpx

class EmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
            
        # ✅ ใช้โมเดล embedding-001 ซึ่งเป็นตัวที่เสถียรที่สุด (Stable)
        self.url = f"https://generativelanguage.googleapis.com/v1/models/embedding-001:embedContent?key={self.api_key}"

    async def embed_text(self, text: str) -> list[float]:
        # ✅ โครงสร้าง Payload สำหรับ embedding-001
        payload = {
            "model": "gemini-embedding-001",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, timeout=30.0)
                
                if response.status_code != 200:
                    # พ่น Error ออกมาดูถ้ายังพัง (แต่อันนี้ไม่น่าพังแล้วครับ)
                    print(f"DEBUG - Status: {response.status_code}, Body: {response.text}")
                
                response.raise_for_status()
                
                data = response.json()
                return data["embedding"]["values"]
                
        except Exception as e:
            raise RuntimeError(f"Gemini API Direct Call failed: {str(e)}")

embedding_service = EmbeddingService()