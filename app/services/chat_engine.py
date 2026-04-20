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
    async def execute_rag_stream(
        self,
        bot_id: str,
        user_jwt: str,
        message: str,
        instructions: str,
    ) -> AsyncIterator[dict]:
        """
        Authenticated RAG stream.

        Retrieves context using the user's JWT (respects RLS), builds a
        prompt, then streams LLM tokens. Yields dicts formatted for SSE.
        """
        chunks = await retrieval_pipeline.retrieve_context(user_jwt, bot_id, message, k=4)
        prompt = retrieval_pipeline.build_prompt(instructions, message, chunks)

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
        instructions: str,
    ) -> AsyncIterator[dict]:
        """
        Public RAG stream (no user JWT required).

        Retrieves context using the service-role client via an RPC that
        enforces is_public=true. Yields the same SSE dict format as the
        authenticated variant.
        """
        chunks = await retrieval_pipeline.retrieve_context_public(bot_id, message, k=4)
        prompt = retrieval_pipeline.build_prompt(instructions, message, chunks)

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
