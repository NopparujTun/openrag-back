from __future__ import annotations

from typing import Any

from supabase import Client


class BotRepository:
    def __init__(self, sb: Client):
        self.sb = sb

    def list_bots_for_user(self, user_id: str) -> list[dict[str, Any]]:
        res = (
            self.sb.table("bots")
            .select("id,user_id,name,instructions,is_public,created_at,updated_at,documents(count)")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return res.data or []

    def create_bot(self, user_id: str, name: str, instructions: str = "", is_public: bool = False) -> dict[str, Any] | None:
        res = self.sb.table("bots").insert({
            "user_id": user_id,
            "name": name,
            "instructions": instructions,
            "is_public": is_public
        }).execute()
        return res.data[0] if res.data else None

    def get_bot(self, bot_id: str, user_id: str) -> dict[str, Any] | None:
        res = self.sb.table("bots").select("*").eq("id", bot_id).eq("user_id", user_id).limit(1).execute()
        return res.data[0] if res.data else None

    def get_bot_public(self, bot_id: str) -> dict[str, Any] | None:
        res = self.sb.table("bots").select("id,instructions,is_public").eq("id", bot_id).limit(1).execute()
        return res.data[0] if res.data else None

    def update_bot(self, bot_id: str, user_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        if not patch:
            return None
        res = self.sb.table("bots").update(patch).eq("id", bot_id).eq("user_id", user_id).execute()
        return res.data[0] if res.data else None

    def delete_bot(self, bot_id: str, user_id: str) -> int:
        res = self.sb.table("bots").delete().eq("id", bot_id).eq("user_id", user_id).execute()
        return len(res.data or [])
