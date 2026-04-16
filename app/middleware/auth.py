from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
import httpx


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    user_id: str
    email: str | None = None


def _unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=401, detail=detail)


def _fetch_user_from_supabase(token: str) -> dict:
    """
    Validate the access token by asking Supabase Auth directly.
    This avoids local JWT-secret mismatch issues and matches Supabase behavior.
    """
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_anon_key,
    }
    try:
        r = httpx.get(url, headers=headers, timeout=10)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Supabase auth is not reachable") from e
    if r.status_code != 200:
        raise _unauthorized("Invalid token")
    data = r.json()
    if not isinstance(data, dict) or not data.get("id"):
        raise _unauthorized("Invalid token")
    return data


def get_current_user(
    req: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthUser:
    token = None
    if creds and creds.scheme.lower() == "bearer":
        token = creds.credentials
    if not token:
        raise _unauthorized("Missing bearer token")

    u = _fetch_user_from_supabase(token)
    sub = u["id"]
    email = u.get("email")

    req.state.user_jwt = token
    return AuthUser(user_id=sub, email=email)

