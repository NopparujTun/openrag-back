"""
app/pipelines/ingestion.py
--------------------------
End-to-end document ingestion pipeline.

Pipeline flow:
  1. Fetch document metadata via DocumentRepository
  2. Mark document as 'processing'
  3. Extract raw text (from inline content or from Storage)
  4. Chunk text into fixed-size overlapping segments
  5. Embed each chunk via the embedding service
  6. Insert chunks into the database via ChunkRepository
  7. Mark document as 'ready' (or 'error' on failure)

This pipeline is always run asynchronously in a background task
triggered by the upload or text-knowledge endpoints.
"""
from __future__ import annotations

from app.db.supabase import supabase_service, supabase_user
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.text_extraction_service import text_extraction_service


class IngestionPipeline:
    async def process_document(self, document_id: str, user_jwt: str) -> None:
        """
        Processes a single document through the full ingestion pipeline.

        Uses the user-scoped client for document reads/status updates
        (to respect RLS on documents table) and the service-role client
        for chunk inserts (background writes bypass user-level RLS on chunks).
        """
        user_client = supabase_user(user_jwt)
        service_client = supabase_service()

        doc_repo = DocumentRepository(user_client)
        chunk_repo = ChunkRepository(service_client)

        doc = doc_repo.get_document_by_id(document_id)
        if not doc:
            return

        try:
            doc_repo.update_document_status(document_id, "processing")

            filename = doc["filename"]
            file_path = doc.get("file_path")
            inline_content = doc.get("content")

            if inline_content:
                text = inline_content
            else:
                if not file_path:
                    raise RuntimeError("Missing file_path for document")
                blob = doc_repo.download_file(file_path)
                # Supabase storage may return str or bytes depending on the SDK version
                data = blob.encode("utf-8", errors="ignore") if isinstance(blob, str) else blob
                text = text_extraction_service.extract_text(filename, data)

            chunks = chunking_service.chunk_text(text)
            if not chunks:
                raise RuntimeError("No text extracted from document")

            for chunk_index, chunk_text_content in enumerate(chunks):
                embedding = await embedding_service.embed(chunk_text_content)
                chunk_repo.insert_chunk(
                    document_id=document_id,
                    bot_id=doc["bot_id"],
                    text=chunk_text_content,
                    embedding=embedding,
                    chunk_index=chunk_index,
                    source_filename=filename,
                )

            doc_repo.update_document_status(document_id, "ready")

        except Exception as exc:
            doc_repo.update_document_status(document_id, "error", error=str(exc))


ingestion_pipeline = IngestionPipeline()
