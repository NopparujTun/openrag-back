"""
app/api/routes/bots.py
----------------------
Bot CRUD endpoints — thin controller layer only.
Business logic lives in BotRepository; HTTP concerns live here.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.dependencies import get_bot_service, get_bot_service_public
from app.core.config import settings
from app.middleware.auth import AuthUser, get_current_user
from app.services.bot_service import BotService
from app.schemas.bots import BotCreate, BotOut, BotUpdate, BotOutPublic

router = APIRouter(prefix="/bots", tags=["bots"])


# =====================================================================
# PUBLIC ENDPOINTS: Widget clients fetch bot config from these routes.
# No authentication required — intentionally public.
# =====================================================================

@router.get("/{bot_id}/public", response_model=BotOutPublic)
def get_bot_public(
    bot_id: str,
    service: BotService = Depends(get_bot_service_public),
) -> dict:
    """Returns public metadata for a bot. No auth required."""
    bot = service.get_bot_public(bot_id)
    if not bot or not bot.get("is_public"):
        raise HTTPException(status_code=404, detail="Bot not found or not public")
    return bot


@router.get("/{bot_id}.js")
def get_bot_widget_script(bot_id: str) -> Response:
    """
    Returns a self-initialising JavaScript snippet that bootstraps the
    YourBot chat widget on any third-party page.
    """
    frontend_url = settings.frontend_url.rstrip("/")
    
    js_content = f"""
    (function() {{
        const botId = "{bot_id}";
        const frontendUrl = "{frontend_url}";
        
        const createWidget = () => {{
            // Create bubble
            const bubble = document.createElement('div');
            bubble.id = 'yourbot-bubble';
            bubble.style.cssText = 'position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; border-radius: 30px; background-color: #3b82f6; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 999999; transition: transform 0.2s ease;';
            bubble.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            `;
            document.body.appendChild(bubble);

            // Create iframe container
            const container = document.createElement('div');
            container.id = 'yourbot-container';
            container.style.display = 'none';
            container.style.position = 'fixed';
            container.style.bottom = '90px';
            container.style.right = '20px';
            container.style.width = '400px';
            container.style.height = '600px';
            container.style.maxHeight = 'calc(100vh - 110px)';
            container.style.maxWidth = 'calc(100vw - 40px)';
            container.style.borderRadius = '12px';
            container.style.boxShadow = '0 8px 32px rgba(0,0,0,0.15)';
            container.style.zIndex = '999999';
            container.style.overflow = 'hidden';
            container.style.backgroundColor = 'white';
            
            const iframe = document.createElement('iframe');
            iframe.src = `${{frontendUrl}}/bots/${{botId}}/chat/public`;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            
            container.appendChild(iframe);
            document.body.appendChild(container);

            // Toggle logic
            let isOpen = false;
            bubble.addEventListener('click', () => {{
                isOpen = !isOpen;
                container.style.display = isOpen ? 'block' : 'none';
                bubble.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
            }});
        }};

        if (document.readyState === 'complete') {{
            createWidget();
        }} else {{
            window.addEventListener('load', createWidget);
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