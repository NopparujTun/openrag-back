import json
from typing import AsyncGenerator

def format_sse(data: dict) -> str:
    """Formats a dict as a Server-Sent Events data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

async def stream_as_sse(stream: AsyncGenerator) -> AsyncGenerator[str, None]:
    """Wraps an async generator of dicts into SSE-formatted strings."""
    async for item in stream:
        yield format_sse(item)
