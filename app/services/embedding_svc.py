from __future__ import annotations

import os
from app.core.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class EmbeddingService:
    def __init__(self):
        # ดึง API Key จาก Environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
            
        # เรียกใช้ Gemini Embedding Model (เวอร์ชันล่าสุด)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001", 
            google_api_key=api_key
        )

    async def embed_text(self, text: str) -> list[float]:
        try:
            # ใช้ฟังก์ชัน embed_query ของ LangChain
            vector = self.embeddings.embed_query(text)
            return vector
        except Exception as e:
            raise RuntimeError(f"Gemini Embedding failed: {str(e)}")

# สร้าง Instance ไว้เรียกใช้งาน
embedding_service = EmbeddingService()
