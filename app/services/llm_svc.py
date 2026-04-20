"""
app/services/llm_svc.py
------------------------
LLM service — wraps the DeepSeek chat completions API.

Responsibility: stream raw text tokens from the language model.
All HTTP and JSON-parsing concerns are handled here; callers receive
a clean async iterator of string tokens.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.core.config import settings


class EngineError(RuntimeError):
    """Raised when the LLM backend is unreachable or returns a non-200 response."""


class LLMService:
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """
        Streams raw text tokens from the DeepSeek API.

        Yields individual token strings as they arrive from the model.
        Raises EngineError if the API is unreachable or returns an error status,
        so callers can handle LLM failures separately from other RuntimeErrors.
        """
        url = "https://api.deepseek.com/chat/completions"
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        raise EngineError(
                            f"DeepSeek generate failed: {response.status_code} "
                            f"{error_body.decode('utf-8')}"
                        )

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        line = line.strip()
                        if line.startswith("data: "):
                            line = line[6:]
                            
                        if line == "[DONE]":
                            break
                            
                        try:
                            obj = json.loads(line)
                            choices = obj.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                token = delta.get("content")
                                if token:
                                    yield token
                        except json.JSONDecodeError:
                            continue

            except httpx.RequestError as exc:
                raise EngineError(
                    f"DeepSeek API is not reachable at {url}"
                ) from exc


llm_service = LLMService()
