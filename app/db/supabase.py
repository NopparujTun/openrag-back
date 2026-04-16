from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings


_service: Client | None = None


def supabase_service() -> Client:
    global _service
    if _service is None:
        _service = create_client(settings.supabase_url, settings.supabase_service_key)
    return _service


def supabase_user(user_jwt: str) -> Client:
    """
    Supabase client scoped to the authenticated end-user (RLS-friendly).
    """
    c = create_client(settings.supabase_url, settings.supabase_anon_key)
    c.postgrest.auth(user_jwt)
    return c

