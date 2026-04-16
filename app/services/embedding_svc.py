import os
import httpx

class EmbeddingService:
    def __init__(self):
        # ดึง API Key จาก Environment (แนะนำให้ตั้งใน Vercel/Dotenv)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
            
        # URL ที่ถูกต้องสำหรับ v1beta (ไม่ต้องใส่ชื่อโมเดลใน URL)
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"

    async def embed_text(self, text: str) -> list[float]:
        # Payload ที่ถูกต้อง (โมเดลต้องระบุแบบนี้)
        payload = {
            "model": "models/text-embedding-004", # ต้องมีคำว่า models/ นำหน้าตรงนี้
            "content": {
                "parts": [{"text": text}]
            },
            "outputDimensionality": 768
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # ลองยิงแบบ POST
                response = await client.post(self.url, json=payload, timeout=30.0)
                
                if response.status_code != 200:
                    print(f"Error Detail: {response.text}") # ดู Error จริงจาก Google
                
                response.raise_for_status()
                
                data = response.json()
                return data["embedding"]["values"]
                
        except Exception as e:
            raise RuntimeError(f"Gemini API Direct Call failed: {str(e)}")

embedding_service = EmbeddingService()