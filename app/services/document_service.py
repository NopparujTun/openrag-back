from __future__ import annotations
from typing import Any
from app.repositories.document_repo import DocumentRepository

class DocumentService:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo

    def validate_filename(self, filename: str) -> bool:
        """Validates if the filename has an allowed extension."""
        from app.utils.file_helpers import is_allowed_file
        return is_allowed_file(filename)

    def list_documents(self, bot_id: str) -> list[dict[str, Any]]:
        return self.repo.list_documents(bot_id)

    def get_document_by_id(self, document_id: str) -> dict[str, Any] | None:
        return self.repo.get_document_by_id(document_id)

    def create_pending_document(self, bot_id: str, filename: str, content: str | None = None, file_path: str | None = None) -> dict[str, Any] | None:
        return self.repo.create_pending_document(bot_id, filename, content, file_path)

    def update_document_status(self, document_id: str, status: str, error: str | None = None) -> None:
        return self.repo.update_document_status(document_id, status, error)

    def delete_document(self, bot_id: str, document_id: str) -> int:
        return self.repo.delete_document(bot_id, document_id)

    def upload_file(self, user_id: str, bot_id: str, filename: str, data: bytes, content_type: str) -> str:
        return self.repo.upload_file(user_id, bot_id, filename, data, content_type)

    def download_file(self, file_path: str) -> bytes:
        return self.repo.download_file(file_path)
