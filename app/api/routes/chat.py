from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.middleware.auth import AuthUser, get_current_user
from app.repositories.bot_repo import BotRepository
from app.services.chat_engine import chat_engine


router = APIRouter(prefix="/bots/{bot_id}", tags=["chat"])

class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

async def sse_wrapper(stream) -> AsyncGenerator[str, None]:
    async for item in stream:
        yield _sse(item)

@router.post("/chat")
async def chat(req: Request, bot_id: str, payload: ChatIn, user: AuthUser = Depends(get_current_user)):
    from app.api.routes.bots import get_bot_repo
    repo = get_bot_repo(req)
    
    bot = repo.get_bot(bot_id, user.user_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    gen = chat_engine.execute_rag_stream(
        bot_id=bot_id,
        user_jwt=req.state.user_jwt,
        message=payload.message,
        instructions=bot.get("instructions") or ""
    )
    
    return StreamingResponse(sse_wrapper(gen), media_type="text/event-stream")


@router.post("/chat/public")
async def chat_public(bot_id: str, payload: ChatIn):
    # Public route needs a service bot_repo explicitly
    from app.db.supabase import supabase_service
    repo = BotRepository(supabase_service())
    
    bot = repo.get_bot_public(bot_id)
    if not bot or not bot.get("is_public"):
        raise HTTPException(status_code=404, detail="Bot not found or not public")

    gen = chat_engine.execute_rag_stream_public(
        bot_id=bot_id,
        message=payload.message,
        instructions=bot.get("instructions") or ""
    )
    
    return StreamingResponse(sse_wrapper(gen), media_type="text/event-stream")
