from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.core.config import settings

class EngineError(RuntimeError):
    pass

class LLMService:
    async def stream_response(self, prompt: str) -> AsyncIterator[str]:
        """
        Streams raw text tokens from DeepSeek API as they arrive.
        """
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat", # ใช้โมเดลพื้นฐานของ DeepSeek
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
                        raise EngineError(f"DeepSeek generate failed: {r.status_code} {error_msg.decode('utf-8')}")
                    
                    async for line in r.aiter_lines():
                        # ข้ามบรรทัดว่าง หรือบรรทัดที่ไม่ใช่ข้อมูล SSE
                        if not line or not line.startswith("data: "):
                            continue
                            
                        # ตัดคำว่า "data: " ออก (6 ตัวอักษร) เพื่อเอาแค่ก้อน JSON
                        data_str = line[6:].strip()
                        
                        # เช็คว่าสตรีมจบหรือยัง
                        if data_str == "[DONE]":
                            break
                            
                        try:
                            obj = json.loads(data_str)
                            # โครงสร้างแบบ OpenAI/DeepSeek จะอยู่ที่ choices[0].delta.content
                            choices = obj.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                token = delta.get("content")
                                
                                if isinstance(token, str) and token:
                                    yield token
                        except json.JSONDecodeError:
                            continue
                            
            except httpx.RequestError as e:
                raise EngineError("DeepSeek API is not reachable") from e

llm_service = LLMService()