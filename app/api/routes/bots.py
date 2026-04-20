"""
app/api/routes/bots.py
----------------------
Bot CRUD endpoints — thin controller layer only.
Business logic lives in BotRepository; HTTP concerns live here.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.dependencies import get_bot_service
from app.core.config import settings
from app.middleware.auth import AuthUser, get_current_user
from app.services.bot_service import BotService
from app.schemas.bots import BotCreate, BotOut, BotUpdate

router = APIRouter(prefix="/bots", tags=["bots"])


# =====================================================================
# PUBLIC ENDPOINT: Widget clients fetch bot config from this route.
# No authentication required — intentionally public.
# =====================================================================

@router.get("/{bot_id}.js")
def get_bot_widget_script(bot_id: str) -> Response:
    """
    Returns a self-initialising JavaScript snippet that bootstraps the
    YourBot chat widget on any third-party page.
    """
    bot_config = {
        "botId": bot_id,
        "name": "AI Support Assistant",
        "themeColor": "#3b82f6",
        "apiUrl": settings.frontend_url,
    }

    config_json = json.dumps(bot_config)

    js_content = f"""
    (function() {{
        const initBot = () => {{
            if (window.YourBot && typeof window.YourBot.init === 'function') {{
                window.YourBot.init({config_json});
            }} else {{
                setTimeout(initBot, 100);
            }}
        }};
        if (document.readyState === 'complete') {{
            initBot();
        }} else {{
            window.addEventListener('load', initBot);
        }}
    }})();
    """

    return Response(content=js_content, media_type="application/javascript")


# =====================================================================
# PROTECTED ENDPOINTS: Dashboard-facing routes (require authentication).
# =====================================================================

@router.get("", response_model=list[dict])
def list_bots(
    user: AuthUser = Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
) -> list[dict]:
    """Returns all bots owned by the authenticated user, with document counts."""
    bots = service.list_bots_for_user(user.user_id)
    result = []
    for bot in bots:
        doc_count = 0
        docs = bot.get("documents")
        if isinstance(docs, list) and docs and isinstance(docs[0], dict):
            doc_count = docs[0].get("count") or 0
        result.append({**bot, "document_count": doc_count})
    return result


@router.post("", response_model=BotOut)
def create_bot(
    payload: BotCreate,
    user: AuthUser = Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
) -> dict:
    """Creates a new bot for the authenticated user."""
    bot = service.create_bot(user.user_id, payload.name, instructions="", is_public=False)
    if not bot:
        raise HTTPException(status_code=500, detail="Failed to create bot")
    return bot


@router.get("/{bot_id}", response_model=BotOut)
def get_bot(
    bot_id: str,
    user: AuthUser = Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
) -> dict:
    """Returns a single bot by ID, scoped to the authenticated user."""
    bot = service.get_bot(bot_id, user.user_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.patch("/{bot_id}", response_model=BotOut)
def update_bot(
    bot_id: str,
    payload: BotUpdate,
    user: AuthUser = Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
) -> dict:
    """Partially updates a bot's fields (name, instructions, is_public)."""
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")

    bot = service.update_bot(bot_id, user.user_id, patch)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.delete("/{bot_id}")
def delete_bot(
    bot_id: str,
    user: AuthUser = Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
) -> dict:
    """Permanently deletes a bot and all associated data."""
    deleted = service.delete_bot(bot_id, user.user_id)
    return {"ok": True, "deleted": deleted}