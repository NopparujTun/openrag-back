from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.db.supabase import supabase_user
from app.middleware.auth import AuthUser, get_current_user
from app.repositories.bot_repo import BotRepository
from app.schemas.bots import BotCreate, BotOut, BotUpdate

# นำเข้า settings เพื่อดึง URL อัตโนมัติ (ถ้าต้องการ)
from app.core.config import settings

router = APIRouter(prefix="/bots", tags=["bots"])

def get_bot_repo(req: Request, user: AuthUser = Depends(get_current_user)) -> BotRepository:
    """Depends on get_current_user to guarantee req.state.user_jwt is set first."""
    sb = supabase_user(req.state.user_jwt)
    return BotRepository(sb)

# =====================================================================
# 🌐 PUBLIC ENDPOINT: สำหรับให้ Widget ฝั่งลูกค้าดึง Config ไปใช้งาน
# ไม่ต้องใช้ Depends(get_current_user) เพราะเป็น Public API
# =====================================================================
@router.get("/{bot_id}.js")
def get_bot_widget_script(bot_id: str):
    # หมายเหตุ: ในอนาคตคุณสามารถใช้ Supabase (Admin/Service Key) 
    # เพื่อดึงข้อมูลชื่อและสีของบอทจากฐานข้อมูลมาใส่ตรงนี้ได้
    
    bot_settings = {
        "botId": bot_id,
        "name": "AI Support Assistant", # ดึงจาก DB ได้ในอนาคต
        "themeColor": "#3b82f6",       # ดึงจาก DB ได้ในอนาคต
        "apiUrl": "https://yourbot-api.onrender.com" # ใส่ URL ของ Backend จริงเวลาขึ้น Render
    }
    
    config_json = json.dumps(bot_settings)
    
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
# 🔒 PROTECTED ENDPOINTS: สำหรับ Dashboard ของเจ้าของระบบ (ต้อง Login)
# =====================================================================

@router.get("", response_model=list[dict])
def list_bots(user: AuthUser = Depends(get_current_user), repo: BotRepository = Depends(get_bot_repo)):
    bots = repo.list_bots_for_user(user.user_id)
    out = []
    for b in bots:
        doc_count = 0
        docs = b.get("documents")
        if isinstance(docs, list) and docs and isinstance(docs[0], dict):
            doc_count = docs[0].get("count") or 0
        out.append({**b, "document_count": doc_count})
    return out


@router.post("", response_model=BotOut)
def create_bot(payload: BotCreate, user: AuthUser = Depends(get_current_user), repo: BotRepository = Depends(get_bot_repo)):
    bot = repo.create_bot(user.user_id, payload.name, instructions="", is_public=False)
    if not bot:
        raise HTTPException(status_code=500, detail="Failed to create bot")
    return bot


@router.get("/{bot_id}", response_model=BotOut)
def get_bot(bot_id: str, user: AuthUser = Depends(get_current_user), repo: BotRepository = Depends(get_bot_repo)):
    bot = repo.get_bot(bot_id, user.user_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.patch("/{bot_id}", response_model=BotOut)
def update_bot(bot_id: str, payload: BotUpdate, user: AuthUser = Depends(get_current_user), repo: BotRepository = Depends(get_bot_repo)):
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    bot = repo.update_bot(bot_id, user.user_id, patch)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.delete("/{bot_id}")
def delete_bot(bot_id: str, user: AuthUser = Depends(get_current_user), repo: BotRepository = Depends(get_bot_repo)):
    deleted = repo.delete_bot(bot_id, user.user_id)
    return {"ok": True, "deleted": deleted}