from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.db.supabase import supabase_service, supabase_user
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding_svc import embedding_service


@dataclass(frozen=True)
class RetrievedChunk:
    filename: str
    text: str
    score: float | None = None


class RetrievalPipeline:
    async def retrieve_context(self, user_jwt: str, bot_id: str, query: str, k: int = 4) -> list[RetrievedChunk]:
        """
        Embeds the query and fetches top K chunks for the authenticated user.
        """
        q_emb = await embedding_service.embed_text(query)
        sb = supabase_user(user_jwt)
        repo = ChunkRepository(sb)
        
        rows = repo.retrieve_top_k(bot_id, q_emb, k)
        return self._map_to_chunks(rows)

    async def retrieve_context_public(self, bot_id: str, query: str, k: int = 4) -> list[RetrievedChunk]:
        """
        Embeds the query and fetches top K chunks for a public bot.
        """
        q_emb = await embedding_service.embed_text(query)
        svc = supabase_service()
        repo = ChunkRepository(svc)
        
        rows = repo.retrieve_top_k_public(bot_id, q_emb, k)
        return self._map_to_chunks(rows)

    def build_prompt(self, instructions: str, query: str, chunks: list[RetrievedChunk]) -> str:
        PROMPT_TEMPLATE = """SYSTEM:
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
        context_str = "\n\n---\n\n".join([c.text for c in chunks]) if chunks else ""
        return PROMPT_TEMPLATE.format(instructions=instructions or "", context=context_str, query=query)

    def _map_to_chunks(self, rows: list[dict[str, Any]]) -> list[RetrievedChunk]:
        out = []
        for r in rows:
            out.append(
                RetrievedChunk(
                    filename=r.get("filename") or "unknown",
                    text=r.get("text") or "",
                    score=r.get("similarity"),
                )
            )
        return out

retrieval_pipeline = RetrievalPipeline()
