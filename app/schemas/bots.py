from __future__ import annotations

from pydantic import BaseModel, Field


class BotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class BotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    instructions: str | None = Field(default=None, max_length=20000)
    is_public: bool | None = Field(default=None)


class BotOut(BaseModel):
    id: str
    user_id: str
    name: str
    instructions: str
    is_public: bool
    created_at: str | None = None
    updated_at: str | None = None


class BotOutPublic(BaseModel):
    id: str
    name: str
    is_public: bool

