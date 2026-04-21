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

import re
from dataclasses import dataclass
from typing import Any

from app.db.supabase import supabase_service, supabase_user
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding_svc import embedding_service


@dataclass(frozen=False)
class RetrievedChunk:
    """A single chunk returned by the vector similarity search."""
    filename: str
    text: str
    score: float | None = None


class RetrievalPipeline:
    def _rerank_chunks(self, chunks: list[RetrievedChunk], query: str) -> list[RetrievedChunk]:
        if not chunks:
            return []
        
        # Extract keywords (words > 2 chars)
        keywords = set(w.lower() for w in re.findall(r'\b\w{3,}\b', query))
        
        for c in chunks:
            c_text_lower = c.text.lower()
            keyword_matches = sum(1 for kw in keywords if kw in c_text_lower)
            # Boost score based on keyword matches (hybrid retrieval)
            c.score = (c.score or 0.0) + (keyword_matches * 0.1)
            
        chunks.sort(key=lambda x: x.score or 0.0, reverse=True)
        return chunks

    async def retrieve_context(
        self,
        user_jwt: str,
        bot_id: str,
        query: str,
        k: int = 4,
    ) -> list[RetrievedChunk]:
        """
        Embeds the query and retrieves candidates. Re-ranks using keyword matching.
        """
        query_embedding = await embedding_service.embed(query)
        repo = ChunkRepository(supabase_user(user_jwt))
        # Fetch more candidates for re-ranking
        rows = repo.retrieve_top_k(bot_id, query_embedding, k=15)
        chunks = self._rows_to_chunks(rows)
        return self._rerank_chunks(chunks, query)[:k]

    async def retrieve_context_public(
        self,
        bot_id: str,
        query: str,
        k: int = 4,
    ) -> list[RetrievedChunk]:
        """
        Embeds the query and retrieves candidates. Re-ranks using keyword matching.
        """
        query_embedding = await embedding_service.embed(query)
        repo = ChunkRepository(supabase_service())
        # Fetch more candidates for re-ranking
        rows = repo.retrieve_top_k_public(bot_id, query_embedding, k=15)
        chunks = self._rows_to_chunks(rows)
        return self._rerank_chunks(chunks, query)[:k]

    def build_prompt(
        self,
        instructions: str,
        query: str,
        chunks: list[RetrievedChunk],
        history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """
        Assembles the final LLM prompt using proper ChatML roles.
        Includes optional chat history for multi-turn context carryover.
        """
        context = "\n\n---\n\n".join(c.text for c in chunks) if chunks else ""
        
        system_content = (
            f"{instructions or ''}\n\n"
            "You are an expert analytical assistant. You have been provided with specific CONTEXT to answer the user's question.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Read the context exhaustively and systematically. Locate exact keywords from the user's query.\n"
            "2. If you find a keyword match, explicitly extract the sentence or line containing it.\n"
            "3. Identify any entities associated with the extracted line (even if they are in lists, prefixes, or parentheses).\n"
            "4. Construct your final answer strictly based on that evidence.\n"
            "5. NEVER state that a term is 'not found' or 'not listed' if it appears anywhere in the context.\n"
            "6. Provide your step-by-step reasoning in an <analysis> block before outputting your final answer.\n\n"
            f"<context>\n{context}\n</context>"
        )

        prompt = [{"role": "system", "content": system_content}]
        if history:
            # Include recent history for context carryover
            for h in history[-6:]: # Last 6 messages
                # Filter out <analysis> tags from history to save tokens
                content = re.sub(r'<analysis>.*?</analysis>', '', h['content'], flags=re.DOTALL).strip()
                prompt.append({"role": h['role'], "content": content})
                
        prompt.append({"role": "user", "content": query})
        return prompt

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
