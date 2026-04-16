import os
from google import genai
from google.genai import types

class EmbeddingService:
    def __init__(self):
        # 1. ดึง API Key
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
            
        # 2. สร้าง Client ของ Google GenAI
        self.client = genai.Client(api_key=self.api_key)

    async def embed_text(self, text: str) -> list[float]:
        try:
            # 3. ใช้ aio (Async IO) เพื่อไม่ให้เซิร์ฟเวอร์บล็อกการทำงาน
            # และใช้โมเดล text-embedding-004 พร้อมบังคับไซส์ 768 ตามที่คุณนพเขียนเลยครับ
            result = await self.client.aio.models.embed_content(
                model="text-embedding-004",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            # SDK นี้จะคืนค่ากลับมาเป็นลิสต์ของค่า embeddings
            # เราดึง .values ออกมาส่งให้ Supabase ได้เลย
            return result.embeddings[0].values
            
        except Exception as e:
            raise RuntimeError(f"Gemini Embedding failed: {str(e)}")

# สร้าง Instance ไว้เรียกใช้งาน
embedding_service = EmbeddingService()