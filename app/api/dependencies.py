from __future__ import annotations
from fastapi import Depends, Request
from app.db.supabase import supabase_user
from app.middleware.auth import AuthUser, get_current_user
from app.repositories.bot_repo import BotRepository
from app.repositories.document_repo import DocumentRepository
from app.services.bot_service import BotService
from app.services.document_service import DocumentService

def get_bot_repo(req: Request, user: AuthUser = Depends(get_current_user)) -> BotRepository:
    sb = supabase_user(req.state.user_jwt)
    return BotRepository(sb)

def get_doc_repo(req: Request, user: AuthUser = Depends(get_current_user)) -> DocumentRepository:
    sb = supabase_user(req.state.user_jwt)
    return DocumentRepository(sb)

def get_bot_service(repo: BotRepository = Depends(get_bot_repo)) -> BotService:
    return BotService(repo)

def get_document_service(repo: DocumentRepository = Depends(get_doc_repo)) -> DocumentService:
    return DocumentService(repo)
