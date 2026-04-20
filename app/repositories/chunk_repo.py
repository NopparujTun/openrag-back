"""
app/repositories/chunk_repo.py
-------------------------------
Data-access layer for the `chunks` table and vector similarity search.

Repository responsibilities:
  - Insert chunk rows (text + embedding) into Supabase
  - Retrieve top-K similar chunks via RPC (match_chunks / match_chunks_public)

The Supabase client is always injected via __init__ — this repository
never calls supabase_service() or supabase_user() internally. That keeps
the class fully testable and maintains clean dependency direction:
  pipeline → repository(client) → supabase
"""
from __future__ import annotations

from typing import Any

from supabase import Client


class ChunkRepository:
    def __init__(self, sb: Client) -> None:
        self.sb = sb

    def insert_chunk(
        self,
        document_id: str,
        bot_id: str,
        text: str,
        embedding: list[float],
        chunk_index: int,
        source_filename: str,
    ) -> None:
        """
        Inserts a single text chunk with its embedding vector.

        The caller is responsible for providing a client with sufficient
        privileges (typically the service-role client during background ingestion,
        since user-level RLS rules on the chunks table can reject background writes).
        """
        self.sb.table("chunks").insert(
            {
                "document_id": document_id,
                "bot_id": bot_id,
                "text": text,
                "embedding": embedding,
                "chunk_index": chunk_index,
                "source_filename": source_filename,
            }
        ).execute()

    def retrieve_top_k(
        self,
        bot_id: str,
        query_embedding: list[float],
        k: int = 4,
    ) -> list[dict[str, Any]]:
        """
        Returns the top-K most similar chunks for the given bot,
        using the authenticated user's client (RLS-enforced).
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

    def retrieve_top_k_public(
        self,
        bot_id: str,
        query_embedding: list[float],
        k: int = 4,
    ) -> list[dict[str, Any]]:
        """
        Returns the top-K most similar chunks for a public bot.
        Uses the service-role client (passed at construction time) to bypass
        user-level RLS. The RPC enforces is_public implicitly.
        """
        res = self.sb.rpc(
            "match_chunks_public",
            {
                "p_bot_id": bot_id,
                "p_query_embedding": query_embedding,
                "p_match_count": k,
            },
        ).execute()
        return res.data or []
