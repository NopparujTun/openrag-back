"""
app/api/routes/chat.py
----------------------
Chat endpoints — thin controller layer only.
Business logic (RAG pipeline, LLM streaming) lives in ChatEngine.

Note: previously this file imported get_bot_repo directly from bots.py,
creating a circular dependency. That is now resolved by importing from
app.api.dependencies instead.
"""
from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_bot_service
from app.db.supabase import supabase_service
from app.middleware.auth import AuthUser, get_current_user
from app.services.bot_service import BotService
from app.services.chat_engine import chat_engine


router = APIRouter(prefix="/bots/{bot_id}", tags=["chat"])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def _format_sse(data: dict) -> str:
    """Formats a dict as a Server-Sent Events data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_as_sse(stream: AsyncGenerator) -> AsyncGenerator[str, None]:
    """Wraps an async generator of dicts into SSE-formatted strings."""
    async for item in stream:
        yield _format_sse(item)


@router.post("/chat")
async def chat(
    req: Request,
    bot_id: str,
    payload: ChatIn,
    user: AuthUser = Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
) -> StreamingResponse:
    """
    Authenticated chat endpoint. Streams LLM tokens back as SSE.
    Validates bot ownership before processing.
    """
    bot = service.get_bot(bot_id, user.user_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    stream = chat_engine.execute_rag_stream(
        bot_id=bot_id,
        user_jwt=req.state.user_jwt,
        message=payload.message,
        instructions=bot.get("instructions") or "",
    )

    return StreamingResponse(_stream_as_sse(stream), media_type="text/event-stream")


@router.post("/chat/public")
async def chat_public(bot_id: str, payload: ChatIn) -> StreamingResponse:
    """
    Public chat endpoint (no authentication required).
    Only works for bots with is_public=True.
    Uses the service client to bypass user-level RLS.
    """
    service = BotService(BotRepository(supabase_service()))

    bot = service.get_bot_public(bot_id)
    if not bot or not bot.get("is_public"):
        raise HTTPException(status_code=404, detail="Bot not found or not public")

    stream = chat_engine.execute_rag_stream_public(
        bot_id=bot_id,
        message=payload.message,
        instructions=bot.get("instructions") or "",
    )

    return StreamingResponse(_stream_as_sse(stream), media_type="text/event-stream")
