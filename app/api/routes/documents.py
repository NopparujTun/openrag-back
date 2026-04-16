from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile

from app.db.supabase import supabase_user
from app.middleware.auth import AuthUser, get_current_user
from app.pipelines.ingestion import ingestion_pipeline
from app.repositories.document_repo import DocumentRepository
from app.schemas.documents import DocumentOut, TextKnowledgeIn

router = APIRouter(prefix="/bots/{bot_id}/documents", tags=["documents"])

ALLOWED_EXTS = {".pdf", ".docx", ".txt", ".csv"}

def get_doc_repo(req: Request, user: AuthUser = Depends(get_current_user)) -> DocumentRepository:
    """Depends on get_current_user to guarantee req.state.user_jwt is set first."""
    sb = supabase_user(req.state.user_jwt)
    return DocumentRepository(sb)


@router.get("", response_model=list[DocumentOut])
def list_documents(bot_id: str, user: AuthUser = Depends(get_current_user), repo: DocumentRepository = Depends(get_doc_repo)):
    return repo.list_documents(bot_id)


@router.post("/text", response_model=DocumentOut)
async def add_text_knowledge(
    req: Request,
    bot_id: str,
    payload: TextKnowledgeIn,
    background: BackgroundTasks,
    repo: DocumentRepository = Depends(get_doc_repo),
    user: AuthUser = Depends(get_current_user),
):
    doc = repo.create_pending_document(bot_id, filename=payload.filename, content=payload.content)
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create document")
    
    background.add_task(ingestion_pipeline.process_document, doc["id"], req.state.user_jwt)
    return doc


@router.post("", response_model=DocumentOut)
async def upload_document(
    req: Request,
    bot_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    repo: DocumentRepository = Depends(get_doc_repo),
    user: AuthUser = Depends(get_current_user),
):
    filename = file.filename or "upload"
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    
    try:
        storage_path = repo.upload_file(user.user_id, bot_id, filename, data, file.content_type or "application/octet-stream")
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))

    doc = repo.create_pending_document(bot_id, filename=filename, file_path=storage_path)
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create document")
    
    background.add_task(ingestion_pipeline.process_document, doc["id"], req.state.user_jwt)
    return doc


@router.delete("/{document_id}")
def delete_document(bot_id: str, document_id: str, user: AuthUser = Depends(get_current_user), repo: DocumentRepository = Depends(get_doc_repo)):
    deleted = repo.delete_document(bot_id, document_id)
    return {"ok": True, "deleted": deleted}
