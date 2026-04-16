from __future__ import annotations

import json
import os
from typing import AsyncIterator
import httpx

class EngineError(RuntimeError):
    pass

class LLMService:
    async def stream_response(self, prompt: str) -> AsyncIterator[str]:
        """
        Streams raw text tokens from Groq API (Llama-3) as they arrive.
        """
        # 1. เปลี่ยน URL ไปที่ Groq
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        # 2. ดึงคีย์จาก Env (อย่าลืมตั้งค่า GROQ_API_KEY ใน Vercel นะครับ)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EngineError("GROQ_API_KEY is not set")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 3. ปรับโมเดลเป็น Llama-3 (แรงและฟรี)
        payload = {
            "model": "llama3-70b-8192", 
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as r:
                    if r.status_code != 200:
                        error_msg = await r.aread()
                        raise EngineError(f"Groq generate failed: {r.status_code} {error_msg.decode('utf-8')}")
                    
                    async for line in r.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                            
                        data_str = line[6:].strip()
                        
                        if data_str == "[DONE]":
                            break
                            
                        try:
                            obj = json.loads(data_str)
                            choices = obj.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                token = delta.get("content")
                                
                                if isinstance(token, str) and token:
                                    yield token
                        except json.JSONDecodeError:
                            continue
                            
            except httpx.RequestError as e:
                raise EngineError("Groq API is not reachable") from e

llm_service = LLMService()