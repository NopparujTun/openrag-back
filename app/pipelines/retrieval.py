"""
app/pipelines/retrieval.py
--------------------------
Retrieval pipeline — embeds a user query and fetches the top-K
most relevant chunks from the vector store.

Pipeline flow:
  1. Embed the query string via EmbeddingService
  2. Query the ChunkRepository for similar vectors (via Supabase RPC)
  3. Map raw DB rows → typed RetrievedChunk dataclasses
  4. Build a prompt string by injecting chunks into the template

Two public methods are exposed:
  - retrieve_context       → for authenticated users (RLS-enforced)
  - retrieve_context_public → for public bots (service-role client)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.db.supabase import supabase_service, supabase_user
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding_svc import embedding_service


@dataclass(frozen=True)
class RetrievedChunk:
    """A single chunk returned by the vector similarity search."""
    filename: str
    text: str
    score: float | None = None


_PROMPT_TEMPLATE = """\
SYSTEM:
{instructions}

You have access to the following context to answer the user's question.
Answer ONLY using the provided context.
If the context does not contain enough information, say:
"I don't have enough information to answer that."
Do NOT make up information.

CONTEXT:
{context}

USER:
{query}
"""


class RetrievalPipeline:
    async def retrieve_context(
        self,
        user_jwt: str,
        bot_id: str,
        query: str,
        k: int = 4,
    ) -> list[RetrievedChunk]:
        """
        Embeds the query and retrieves the top-K chunks for an authenticated user.
        The user-scoped Supabase client ensures RLS policies are respected.
        """
        query_embedding = await embedding_service.embed(query)
        repo = ChunkRepository(supabase_user(user_jwt))
        rows = repo.retrieve_top_k(bot_id, query_embedding, k)
        return self._rows_to_chunks(rows)

    async def retrieve_context_public(
        self,
        bot_id: str,
        query: str,
        k: int = 4,
    ) -> list[RetrievedChunk]:
        """
        Embeds the query and retrieves the top-K chunks for a public bot.
        Uses the service-role client; the RPC enforces is_public implicitly.
        """
        query_embedding = await embedding_service.embed(query)
        repo = ChunkRepository(supabase_service())
        rows = repo.retrieve_top_k_public(bot_id, query_embedding, k)
        return self._rows_to_chunks(rows)

    def build_prompt(
        self,
        instructions: str,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> str:
        """
        Assembles the final LLM prompt by injecting the system instructions,
        retrieved context, and user query into the prompt template.
        """
        context = "\n\n---\n\n".join(c.text for c in chunks) if chunks else ""
        return _PROMPT_TEMPLATE.format(
            instructions=instructions or "",
            context=context,
            query=query,
        )

    def _rows_to_chunks(self, rows: list[dict[str, Any]]) -> list[RetrievedChunk]:
        """Maps raw Supabase RPC result rows to typed RetrievedChunk objects."""
        return [
            RetrievedChunk(
                filename=row.get("filename") or "unknown",
                text=row.get("text") or "",
                score=row.get("similarity"),
            )
            for row in rows
        ]


retrieval_pipeline = RetrievalPipeline()
