"""
app/api/routes/documents.py
---------------------------
Document management endpoints — thin controller layer only.
File validation and upload orchestration happen here;
actual storage and DB writes are delegated to DocumentRepository.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile

from app.api.dependencies import get_document_service
from app.middleware.auth import AuthUser, get_current_user
from app.pipelines.ingestion import ingestion_pipeline
from app.services.document_service import DocumentService
from app.schemas.documents import DocumentOut, TextKnowledgeIn

router = APIRouter(prefix="/bots/{bot_id}/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}


@router.get("", response_model=list[DocumentOut])
def list_documents(
    bot_id: str,
    user: AuthUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> list:
    """Returns all documents associated with a bot, ordered by creation date."""
    return service.list_documents(bot_id)


@router.post("/text", response_model=DocumentOut)
async def add_text_knowledge(
    req: Request,
    bot_id: str,
    payload: TextKnowledgeIn,
    background: BackgroundTasks,
    service: DocumentService = Depends(get_document_service),
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """
    Creates a document from raw text content and queues it for ingestion.
    The document is created immediately with status='pending'; the chunking
    and embedding happens asynchronously in the background.
    """
    doc = service.create_pending_document(bot_id, filename=payload.filename, content=payload.content)
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
    service: DocumentService = Depends(get_document_service),
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """
    Uploads a file to storage and queues it for ingestion.
    Validates file type before uploading. Document is created with
    status='pending' and processed asynchronously in the background.
    """
    filename = file.filename or "upload"
    extension = "." + filename.split(".")[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()

    try:
        storage_path = service.upload_file(
            user.user_id, bot_id, filename, data, file.content_type or "application/octet-stream"
        )
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))

    doc = service.create_pending_document(bot_id, filename=filename, file_path=storage_path)
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create document")

    background.add_task(ingestion_pipeline.process_document, doc["id"], req.state.user_jwt)
    return doc


@router.delete("/{document_id}")
def delete_document(
    bot_id: str,
    document_id: str,
    user: AuthUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    """Permanently deletes a document and its associated chunks."""
    deleted = service.delete_document(bot_id, document_id)
    return {"ok": True, "deleted": deleted}
