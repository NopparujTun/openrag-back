from __future__ import annotations
from typing import Any
from app.repositories.bot_repo import BotRepository

class BotService:
    def __init__(self, repo: BotRepository):
        self.repo = repo

    def list_bots_for_user(self, user_id: str) -> list[dict[str, Any]]:
        bots = self.repo.list_bots_for_user(user_id)
        result = []
        for bot in bots:
            doc_count = 0
            docs = bot.get("documents")
            if isinstance(docs, list) and docs and isinstance(docs[0], dict):
                doc_count = docs[0].get("count") or 0
            # Remove the 'documents' key to keep the output clean and add document_count
            bot_data = {k: v for k, v in bot.items() if k != "documents"}
            bot_data["document_count"] = doc_count
            result.append(bot_data)
        return result

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
