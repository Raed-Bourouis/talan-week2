"""
F360 – Data Ingestion Endpoints
Upload PDF/Excel, extract structured financial entities.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.financial import Document
from app.schemas.schemas import IngestionResult
from app.services.ingestion.pipeline import ingest_document

settings = get_settings()
router = APIRouter()


@router.post("/upload", response_model=IngestionResult)
async def upload_document(
    file: UploadFile = File(...),
    company_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a PDF or Excel file, extract financial entities,
    chunk content and store embeddings for RAG.
    """
    # Validate file type
    allowed_types = {".pdf", ".xlsx", ".xls", ".csv", ".docx"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed_types}",
        )

    # Validate file size
    contents = await file.read()
    if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")

    # Save file to disk
    file_id = uuid.uuid4()
    file_path = settings.upload_path / f"{file_id}{ext}"
    file_path.write_bytes(contents)

    # Create document record
    doc = Document(
        id=file_id,
        company_id=company_id,
        filename=file.filename,
        file_type=ext.lstrip("."),
        file_path=str(file_path),
        file_size_bytes=len(contents),
        entity_type=entity_type,
    )
    db.add(doc)
    await db.flush()

    # Run ingestion pipeline
    result = await ingest_document(doc, contents, db)
    return result


@router.post("/erp/sync")
async def sync_erp(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mock ERP sync endpoint.
    In production, connects to SAP/Oracle/Sage API.
    """
    # Mock data for MVP
    mock_data = {
        "source": "ERP-Mock",
        "company_id": str(company_id),
        "synced_records": {
            "invoices": 42,
            "accounting_entries": 156,
            "budget_lines": 18,
        },
        "status": "success",
        "message": "ERP data synced successfully (mock)",
    }
    return mock_data
