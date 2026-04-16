import os
import httpx

class EmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
            
        # URL สำหรับเรียก API ของ Gemini ตรงๆ (ไม่ต้องง้อ SDK)
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"

    async def embed_text(self, text: str) -> list[float]:
        # จัดรูปแบบข้อมูลตามที่ Google ต้องการเป๊ะๆ พร้อมบังคับไซส์ 768
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            },
            "outputDimensionality": 768
        }
        
        try:
            # ใช้ httpx ยิง Request แบบ Asynchronous
            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, timeout=30.0)
                
                # ถ้า API ตอบกลับว่าพัง ให้โยน Error ออกมาดู
                response.raise_for_status()
                
                # แกะเอาเฉพาะตัวเลข Vector ออกมา
                data = response.json()
                return data["embedding"]["values"]
                
        except Exception as e:
            raise RuntimeError(f"Gemini API Direct Call failed: {str(e)}")

# สร้าง Instance ไว้เรียกใช้งาน
embedding_service = EmbeddingService()