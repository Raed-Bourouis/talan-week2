"""
F360 – Document Ingestion Pipeline
Extracts structured financial entities from PDF/Excel,
chunks content, and prepares for vector embedding.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import Document, DocumentChunk
from app.schemas.schemas import IngestionResult
from app.services.ingestion.parsers import parse_pdf, parse_excel
from app.services.ingestion.entity_extractor import extract_financial_entities
from app.services.rag.embedder import chunk_and_embed


async def ingest_document(
    doc: Document,
    raw_bytes: bytes,
    db: AsyncSession,
) -> IngestionResult:
    """
    Main ingestion pipeline:
    1. Parse document (PDF/Excel) → raw text
    2. Extract financial entities (amount, date, counterparty, etc.)
    3. Chunk content for RAG
    4. Store chunks + embeddings in pgvector
    5. Return structured result
    """
    try:
        # ── 1. Parse ──
        if doc.file_type in ("pdf",):
            raw_text = parse_pdf(raw_bytes)
        elif doc.file_type in ("xlsx", "xls", "csv"):
            raw_text = parse_excel(raw_bytes, doc.file_type)
        else:
            raw_text = raw_bytes.decode("utf-8", errors="ignore")

        doc.raw_text = raw_text if hasattr(doc, "raw_text") else None

        # ── 2. Extract entities ──
        entities = extract_financial_entities(raw_text)

        # ── 3. Chunk & embed ──
        chunks = await chunk_and_embed(
            text=raw_text,
            document_id=doc.id,
            metadata={
                "filename": doc.filename,
                "file_type": doc.file_type,
                "entity_type": doc.entity_type,
                "entities": entities,
            },
            db=db,
        )

        # ── 4. Mark processed ──
        doc.processed = True

        return IngestionResult(
            document_id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            entities_extracted=entities,
            chunks_created=len(chunks),
            status="success",
        )

    except Exception as e:
        return IngestionResult(
            document_id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type or "unknown",
            entities_extracted={},
            chunks_created=0,
            status="error",
            message=str(e),
        )
