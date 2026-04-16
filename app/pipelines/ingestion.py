from __future__ import annotations

from app.core.config import settings
from app.db.supabase import supabase_service, supabase_user
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.services.chunking import chunk_text
from app.services.embedding_svc import embedding_service
from app.services.text_extract import extract_text_from_bytes


class IngestionPipeline:
    async def process_document(self, document_id: str, user_jwt: str) -> None:
        """
        End-to-end: fetch document -> extract -> chunk -> embed -> insert chunks -> mark ready/error.
        """
        sb = supabase_user(user_jwt)
        svc = supabase_service()
        doc_repo = DocumentRepository(sb)
        chunk_repo = ChunkRepository(svc)

        doc_res = sb.table("documents").select("*").eq("id", document_id).limit(1).execute()
        if not doc_res.data:
            return
        doc = doc_res.data[0]

        try:
            doc_repo.update_document_status(document_id, "processing")

            filename = doc["filename"]
            file_path = doc.get("file_path")
            content = doc.get("content")

            if content:
                text = content
            else:
                if not file_path:
                    raise RuntimeError("Missing file_path for document")
                blob = doc_repo.download_file(file_path)
                data = blob.encode("utf-8", errors="ignore") if isinstance(blob, str) else blob
                text = extract_text_from_bytes(filename, data)

            chunks = chunk_text(text)
            if not chunks:
                raise RuntimeError("No text extracted from document")

            # Insert chunks synchronously or sequentially over api
            for idx, ch in enumerate(chunks):
                emb = await embedding_service.embed_text(ch)
                chunk_repo.insert_chunk(
                    document_id=document_id,
                    bot_id=doc["bot_id"],
                    text=ch,
                    embedding=emb,
                    chunk_index=idx,
                    source_filename=filename
                )

            doc_repo.update_document_status(document_id, "ready")
        except Exception as e:
            doc_repo.update_document_status(document_id, "error", error=str(e))

ingestion_pipeline = IngestionPipeline()
