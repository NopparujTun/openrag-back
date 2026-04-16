from __future__ import annotations

from typing import Any

from supabase import Client

from app.db.supabase import supabase_service


class ChunkRepository:
    def __init__(self, sb: Client):
        self.sb = sb

    def insert_chunk(self, document_id: str, bot_id: str, text: str, embedding: list[float], chunk_index: int, source_filename: str) -> None:
        """
        Inserts a single chunk. We use the service client since ingestion might happen in background
        where user RLS policies on chunks can be finicky.
        """
        svc = supabase_service()
        svc.table("chunks").insert(
            {
                "document_id": document_id,
                "bot_id": bot_id,
                "text": text,
                "embedding": embedding,
                "chunk_index": chunk_index,
                "source_filename": source_filename,
            }
        ).execute()

    def retrieve_top_k(self, bot_id: str, query_embedding: list[float], k: int = 4) -> list[dict[str, Any]]:
        """
        Retrieve chunks matching query embedding for the authenticated user (enforced via RLS or RPC logic).
        """
        res = self.sb.rpc(
            "match_chunks",
            {
                "p_bot_id": bot_id,
                "p_query_embedding": query_embedding,
                "p_match_count": k,
            },
        ).execute()
        return res.data or []

    def retrieve_top_k_public(self, bot_id: str, query_embedding: list[float], k: int = 4) -> list[dict[str, Any]]:
        """
        Retrieves matching chunks for public bots using a service account bypassing RLS.
        RPC enforces `is_public` checking implicitly.
        """
        svc = supabase_service()
        res = svc.rpc(
            "match_chunks_public",
            {
                "p_bot_id": bot_id,
                "p_query_embedding": query_embedding,
                "p_match_count": k,
            },
        ).execute()
        return res.data or []
