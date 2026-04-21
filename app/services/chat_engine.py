"""
app/services/chat_engine.py
-----------------------------
Chat engine — orchestrates RAG retrieval and LLM streaming.

This service sits between the HTTP layer (routes) and the AI pipeline
(retrieval + LLM). It:
  1. Retrieves relevant document chunks from the vector store
  2. Builds a prompt from the retrieved context
  3. Streams LLM tokens back to the caller as an async iterator of dicts

The dict format matches the SSE event schema consumed by the frontend:
  {"token": "..."} — a single streamed text token
  {"done": true, "sources": [...]} — final event with citation sources
  {"error": "...", "done": true} — error event if LLM fails
"""
from __future__ import annotations

from typing import AsyncIterator

from app.pipelines.retrieval import retrieval_pipeline
from app.services.llm_svc import EngineError, llm_service


class ChatEngine:
    async def _rewrite_query(self, message: str, history: list[dict[str, str]] | None) -> str:
        """
        Rewrites the query if there is conversation history to make it a standalone search query.
        """
        if not history:
            return message
            
        # Format recent history
        history_text = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-4:])
        
        prompt = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Given the conversation history and a new user query, rewrite the new query to be a standalone search query that includes all necessary context (e.g., replacing pronouns with entity names from the history). Do not answer the question, just output the rewritten query. If the query is already standalone, output it as is."
            },
            {
                "role": "user", 
                "content": f"History:\n{history_text}\n\nNew query: {message}\n\nRewritten query:"
            }
        ]
        
        try:
            rewritten = await llm_service.generate(prompt)
            return rewritten.strip()
        except EngineError:
            return message

    async def execute_rag_stream(
        self,
        bot_id: str,
        user_jwt: str,
        message: str,
        history: list[dict[str, str]] | None = None,
        instructions: str = "",
    ) -> AsyncIterator[dict]:
        """
        Authenticated RAG stream.

        Retrieves context using the user's JWT (respects RLS), builds a
        prompt, then streams LLM tokens. Yields dicts formatted for SSE.
        """
        search_query = await self._rewrite_query(message, history)
        chunks = await retrieval_pipeline.retrieve_context(user_jwt, bot_id, search_query, k=4)
        prompt = retrieval_pipeline.build_prompt(instructions, message, chunks, history)

        try:
            async for token in llm_service.stream(prompt):
                yield {"token": token}
        except EngineError as exc:
            yield {"error": str(exc), "done": True}
            return

        yield {
            "done": True,
            "sources": [
                {
                    "filename": chunk.filename,
                    "text": (chunk.text[:280] + "…") if len(chunk.text) > 280 else chunk.text,
                }
                for chunk in chunks
            ],
        }

    async def execute_rag_stream_public(
        self,
        bot_id: str,
        message: str,
        history: list[dict[str, str]] | None = None,
        instructions: str = "",
    ) -> AsyncIterator[dict]:
        """
        Public RAG stream (no user JWT required).

        Retrieves context using the service-role client via an RPC that
        enforces is_public=true. Yields the same SSE dict format as the
        authenticated variant.
        """
        search_query = await self._rewrite_query(message, history)
        chunks = await retrieval_pipeline.retrieve_context_public(bot_id, search_query, k=4)
        prompt = retrieval_pipeline.build_prompt(instructions, message, chunks, history)

        try:
            async for token in llm_service.stream(prompt):
                yield {"token": token}
        except EngineError as exc:
            yield {"error": str(exc), "done": True}
            return

        yield {
            "done": True,
            "sources": [
                {
                    "filename": chunk.filename,
                    "text": (chunk.text[:280] + "…") if len(chunk.text) > 280 else chunk.text,
                }
                for chunk in chunks
            ],
        }


chat_engine = ChatEngine()
