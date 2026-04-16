from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    bot_id: str
    filename: str
    status: str
    created_at: str | None = None
    error_msg: str | None = None


class TextKnowledgeIn(BaseModel):
    filename: str = Field(default="notes.txt", min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=1_000_000)
