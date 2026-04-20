from __future__ import annotations
from typing import Any
from app.repositories.bot_repo import BotRepository

class BotService:
    def __init__(self, repo: BotRepository):
        self.repo = repo

    def list_bots_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.repo.list_bots_for_user(user_id)

    def create_bot(self, user_id: str, name: str, instructions: str = "", is_public: bool = False) -> dict[str, Any] | None:
        return self.repo.create_bot(user_id, name, instructions, is_public)

    def get_bot(self, bot_id: str, user_id: str) -> dict[str, Any] | None:
        return self.repo.get_bot(bot_id, user_id)

    def get_bot_public(self, bot_id: str) -> dict[str, Any] | None:
        return self.repo.get_bot_public(bot_id)

    def update_bot(self, bot_id: str, user_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        return self.repo.update_bot(bot_id, user_id, patch)

    def delete_bot(self, bot_id: str, user_id: str) -> int:
        return self.repo.delete_bot(bot_id, user_id)
