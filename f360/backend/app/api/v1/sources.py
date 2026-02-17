"""
F360 – Sources Multimodales API Endpoints
Upload documents from local files, connect to S3/Kafka/API/SharePoint,
and ingest IoT/log data.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.financial import Document
from app.schemas.schemas import IngestionResult, ConnectorTestResult, IoTIngestPayload

settings = get_settings()
router = APIRouter()


# ── File Upload (multimodal) ────────────────────────────────────

@router.post("/upload", response_model=IngestionResult)
async def upload_document(
    file: UploadFile = File(...),
    company_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file (PDF, Excel, CSV, DOCX, images, audio, video).
    The cognitive ingestion pipeline will extract text, entities
    and generate vector embeddings.
    """
    allowed_types = {
        ".pdf", ".xlsx", ".xls", ".csv", ".docx",
        ".png", ".jpg", ".jpeg", ".tiff",
        ".mp3", ".wav", ".m4a", ".ogg",
        ".mp4", ".mkv", ".avi",
    }
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed_types}",
        )

    contents = await file.read()
    if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")

    file_id = uuid.uuid4()
    file_path = settings.upload_path / f"{file_id}{ext}"
    file_path.write_bytes(contents)

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

    # Use new cognitive ingestion pipeline
    from app.services.cognitive_ingestion.indexer import ingest_document
    result = await ingest_document(doc, contents, db)
    return result


# ── Connector Test ──────────────────────────────────────────────

@router.post("/connector/test", response_model=ConnectorTestResult)
async def test_connector(
    connector_type: str,
    config: dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """
    Test connectivity to an external source (s3, kafka, api, sharepoint).
    """
    from app.services.sources.connectors import CONNECTOR_REGISTRY

    connector_cls = CONNECTOR_REGISTRY.get(connector_type.lower())
    if not connector_cls:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown connector: {connector_type}. "
                   f"Available: {list(CONNECTOR_REGISTRY.keys())}",
        )

    connector = connector_cls(config)
    try:
        await connector.connect()
        data = await connector.fetch()
        await connector.close()
        return ConnectorTestResult(
            connector_type=connector_type,
            status="success",
            message=f"Connected successfully. Fetched {len(data)} items.",
            sample_keys=list(data.keys())[:5] if isinstance(data, dict) else [],
        )
    except Exception as e:
        return ConnectorTestResult(
            connector_type=connector_type,
            status="error",
            message=str(e),
        )


# ── IoT / Logs ─────────────────────────────────────────────────

@router.post("/iot/ingest")
async def ingest_iot_data(
    payload: IoTIngestPayload,
    current_user: User = Depends(get_current_user),
):
    """
    Ingest IoT events or log entries for anomaly detection.
    """
    from app.services.sources.iot_logger import IoTLogCollector, IoTEvent

    collector = IoTLogCollector()
    for event in payload.events:
        collector.add_event(IoTEvent(
            source=event.get("source", "unknown"),
            metric=event.get("metric", "value"),
            value=event.get("value", 0),
        ))

    anomalies = collector.detect_anomalies()
    return {
        "events_ingested": len(payload.events),
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies,
    }
