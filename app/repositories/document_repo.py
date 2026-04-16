from __future__ import annotations

from typing import Any

from supabase import Client

from app.core.config import settings
from app.db.supabase import supabase_service


class DocumentRepository:
    def __init__(self, sb: Client):
        self.sb = sb

    def list_documents(self, bot_id: str) -> list[dict[str, Any]]:
        res = self.sb.table("documents").select("*").eq("bot_id", bot_id).order("created_at", desc=True).execute()
        return res.data or []

    def create_pending_document(self, bot_id: str, filename: str, content: str | None = None, file_path: str | None = None) -> dict[str, Any] | None:
        payload = {
            "bot_id": bot_id,
            "filename": filename,
            "status": "pending",
        }
        if content is not None:
            payload["content"] = content
        if file_path is not None:
            payload["file_path"] = file_path

        res = self.sb.table("documents").insert(payload).execute()
        return res.data[0] if res.data else None

    def update_document_status(self, document_id: str, status: str, error: str | None = None) -> None:
        payload = {"status": status}
        if error is not None:
            payload["error"] = error
        self.sb.table("documents").update(payload).eq("id", document_id).execute()

    def delete_document(self, bot_id: str, document_id: str) -> int:
        res = self.sb.table("documents").delete().eq("id", document_id).eq("bot_id", bot_id).execute()
        return len(res.data or [])

    def upload_file(self, user_id: str, bot_id: str, filename: str, data: bytes, content_type: str) -> str:
            """
            Uploads a file to Supabase Storage and returns the storage path.
            """
            storage_path = f"{user_id}/{bot_id}/{filename}"
            try:
                storage = self.sb.storage.from_(settings.storage_bucket)
                # 🚨 จุดที่ 1: เพิ่ม "x-upsert": "true"
                storage.upload(
                    storage_path, 
                    data, 
                    {"content-type": content_type, "x-upsert": "true"}
                )
            except Exception as e:
                try:
                    # Fallback to service role
                    svc = supabase_service()
                    # 🚨 จุดที่ 2: เพิ่ม "x-upsert": "true" ตรงนี้ด้วยครับ
                    svc.storage.from_(settings.storage_bucket).upload(
                        storage_path, 
                        data, 
                        {"content-type": content_type, "x-upsert": "true"}
                    )
                except Exception as inner_e:
                    raise RuntimeError("Storage upload blocked by policies") from inner_e
                    
            return storage_path

    def download_file(self, file_path: str) -> bytes:
        """
        Downloads a file from Supabase Storage.
        Using service key if user context is lost, or just falling back.
        """
        try:
            return self.sb.storage.from_(settings.storage_bucket).download(file_path)
        except Exception:
            svc = supabase_service()
            return svc.storage.from_(settings.storage_bucket).download(file_path)
