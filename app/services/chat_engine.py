from __future__ import annotations

from typing import AsyncGenerator, AsyncIterator

from app.pipelines.retrieval import retrieval_pipeline
from app.services.llm_svc import EngineError, llm_service


class ChatEngine:
    async def execute_rag_stream(self, bot_id: str, user_jwt: str, message: str, instructions: str) -> AsyncIterator[dict]:
        """
        Executes internal retrieval via user permissions and returns a stream of tokens & complete schema.
        Returns `AsyncIterator[dict]` rather than formatted SSE strings directly to keep service decoupled
        from HTTP representation.
        """
        chunks = await retrieval_pipeline.retrieve_context(user_jwt, bot_id, message, k=4)
        prompt = retrieval_pipeline.build_prompt(instructions, message, chunks)
        
        try:
            async for token in llm_service.stream_response(prompt):
                yield {"token": token}
        except EngineError as e:
            yield {"error": str(e), "done": True}
            return
            
        yield {
            "done": True,
            "sources": [
                {"filename": c.filename, "text": (c.text[:280] + "…") if len(c.text) > 280 else c.text}
                for c in chunks
            ],
        }

    async def execute_rag_stream_public(self, bot_id: str, message: str, instructions: str) -> AsyncIterator[dict]:
        """
        Executes public retrieval bypassing standard RLS checks and enforcing via RPC.
        """
        chunks = await retrieval_pipeline.retrieve_context_public(bot_id, message, k=4)
        prompt = retrieval_pipeline.build_prompt(instructions, message, chunks)
        
        try:
            async for token in llm_service.stream_response(prompt):
                yield {"token": token}
        except EngineError as e:
            yield {"error": str(e), "done": True}
            return
            
        yield {
            "done": True,
            "sources": [
                {"filename": c.filename, "text": (c.text[:280] + "…") if len(c.text) > 280 else c.text}
                for c in chunks
            ],
        }

chat_engine = ChatEngine()
