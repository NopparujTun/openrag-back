import os
import httpx

class EmbeddingService:
    def __init__(self):
        # ดึง API Key จาก Environment (ต้องตั้งใน Vercel ด้วยนะครับ)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
            
        # ใช้ URL รูปแบบนี้ครับ (v1beta)
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"

    async def embed_text(self, text: str) -> list[float]:
        # สำหรับ v1beta ต้องใช้โครงสร้าง payload แบบนี้
        payload = {
            "content": {
                "parts": [{"text": text}]
            },
            # เพิ่มจุดนี้เข้าไปเพื่อให้มั่นใจว่าได้ 768 มิติ
            "outputDimensionality": 768
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # ส่งแบบ POST
                response = await client.post(self.url, json=payload, timeout=30.0)
                
                # ถ้าไม่สำเร็จ ให้ print ดูว่า Google บ่นว่าอะไร
                if response.status_code != 200:
                    print(f"Google API Error: {response.text}")
                
                response.raise_for_status()
                
                data = response.json()
                # โครงสร้าง JSON ของ Google คือ data['embedding']['values']
                return data["embedding"]["values"]
                
        except Exception as e:
            raise RuntimeError(f"Gemini API Direct Call failed: {str(e)}")

embedding_service = EmbeddingService()