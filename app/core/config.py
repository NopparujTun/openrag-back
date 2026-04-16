from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    supabase_jwt_secret: str

    ollama_base_url: str
    ollama_llm_model: str
    ollama_embed_model: str

    frontend_origin: str
    storage_bucket: str

    deepseek_api_key: str

def _required(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


settings = Settings(
    supabase_url=_required("SUPABASE_URL"),
    supabase_anon_key=_required("SUPABASE_ANON_KEY"),
    supabase_service_key=_required("SUPABASE_SERVICE_KEY"),
    supabase_jwt_secret=_required("SUPABASE_JWT_SECRET"),
    ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    ollama_llm_model=os.getenv("OLLAMA_LLM_MODEL", "llama3"),
    ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
    storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "documents"),
    deepseek_api_key=_required("DEEPSEEK_API_KEY"),
)
