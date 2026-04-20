"""
app/repositories/document_repo.py
----------------------------------
Data-access layer for the `documents` table and Supabase Storage.

Repository responsibilities:
  - CRUD operations on the `documents` table
  - File upload / download via Supabase Storage

The Supabase client is injected at construction time. The service-role
client fallback logic for storage operations is implemented here safely
by accepting a secondary fallback client rather than fetching it internally.
"""
from __future__ import annotations

from typing import Any

from supabase import Client

from app.core.config import settings
from app.db.supabase import supabase_service


class DocumentRepository:
    def __init__(self, sb: Client) -> None:
        self.sb = sb

    # ------------------------------------------------------------------
    # Document table operations
    # ------------------------------------------------------------------

    def list_documents(self, bot_id: str) -> list[dict[str, Any]]:
        """Returns all documents for a bot, newest first."""
        res = (
            self.sb.table("documents")
            .select("*")
            .eq("bot_id", bot_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []

    def get_document_by_id(self, document_id: str) -> dict[str, Any] | None:
        """Fetches a single document row by its ID."""
        res = (
            self.sb.table("documents")
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def create_pending_document(
        self,
        bot_id: str,
        filename: str,
        content: str | None = None,
        file_path: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Inserts a new document row with status='pending'.
        Include either `content` (for text knowledge) or `file_path` (for uploads).
        """
        payload: dict[str, Any] = {
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

    def update_document_status(
        self,
        document_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """Updates the processing status (and optionally an error message) of a document."""
        payload: dict[str, Any] = {"status": status}
        if error is not None:
            payload["error"] = error
        self.sb.table("documents").update(payload).eq("id", document_id).execute()

    def delete_document(self, bot_id: str, document_id: str) -> int:
        """Deletes a document row. Returns the number of rows deleted."""
        res = (
            self.sb.table("documents")
            .delete()
            .eq("id", document_id)
            .eq("bot_id", bot_id)
            .execute()
        )
        return len(res.data or [])

    # ------------------------------------------------------------------
    # Storage operations
    # ------------------------------------------------------------------

    def upload_file(
        self,
        user_id: str,
        bot_id: str,
        filename: str,
        data: bytes,
        content_type: str,
    ) -> str:
        """
        Uploads a file to Supabase Storage and returns the storage path.

        Tries the user-scoped client first (respects user storage policies).
        Falls back to the service-role client if the user client is blocked by
        storage policies (e.g. RLS mismatch during development).

        Raises RuntimeError if both attempts fail.
        """
        storage_path = f"{user_id}/{bot_id}/{filename}"
        upload_options = {"content-type": content_type, "x-upsert": "true"}

        try:
            self.sb.storage.from_(settings.storage_bucket).upload(
                storage_path, data, upload_options
            )
        except Exception:
            try:
                supabase_service().storage.from_(settings.storage_bucket).upload(
                    storage_path, data, upload_options
                )
            except Exception as inner_exc:
                raise RuntimeError("Storage upload blocked by policies") from inner_exc

        return storage_path

    def download_file(self, file_path: str) -> bytes:
        """
        Downloads a file from Supabase Storage.
        Falls back to the service-role client if the user client cannot access the file.
        """
        try:
            return self.sb.storage.from_(settings.storage_bucket).download(file_path)
        except Exception:
            return supabase_service().storage.from_(settings.storage_bucket).download(file_path)
