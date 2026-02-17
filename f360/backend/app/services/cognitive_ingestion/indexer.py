"""
F360 – Indexer
Vector + Metadata indexation layer.
Manages the lifecycle of indexed documents: store, update, search, delete.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import Document, DocumentChunk
from app.services.sources.parsers import parse_file
from app.services.cognitive_ingestion.extractor import extract_financial_entities
from app.services.cognitive_ingestion.vectorizer import vectorize_and_store
from app.schemas.schemas import IngestionResult

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# MAIN INGESTION PIPELINE
# ═══════════════════════════════════════════════════════════════

async def ingest_document(
    doc: Document,
    raw_bytes: bytes,
    db: AsyncSession,
) -> IngestionResult:
    """
    Complete cognitive ingestion pipeline:
    1. Parse document (multimodal) → raw text
    2. Extract financial entities (regex + optional LLM)
    3. Vectorize content → chunk & embed
    4. Store vectors + metadata in pgvector
    5. Return structured result
    """
    try:
        # ── 1. Parse (multimodal) ──
        raw_text = await parse_file(raw_bytes, doc.file_type or "txt")

        # ── 2. Extract entities ──
        entities = extract_financial_entities(raw_text)

        # ── 3 & 4. Vectorize & index ──
        chunks = await vectorize_and_store(
            text_content=raw_text,
            document_id=doc.id,
            metadata={
                "filename": doc.filename,
                "file_type": doc.file_type,
                "entity_type": doc.entity_type,
                "entities": entities,
            },
            db=db,
        )

        # ── 5. Mark processed ──
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
        logger.error(f"Ingestion failed for {doc.filename}: {e}")
        return IngestionResult(
            document_id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type or "unknown",
            entities_extracted={},
            chunks_created=0,
            status="error",
            message=str(e),
        )


# ═══════════════════════════════════════════════════════════════
# INDEX MANAGEMENT
# ═══════════════════════════════════════════════════════════════

async def reindex_document(doc_id: uuid.UUID, db: AsyncSession) -> IngestionResult:
    """
    Re-index a previously processed document.
    Deletes old chunks and re-runs the pipeline.
    """
    # Delete existing chunks
    await db.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
    )

    # Fetch document
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    # Reload file bytes
    from pathlib import Path
    file_path = Path(doc.file_path) if doc.file_path else None
    if file_path and file_path.exists():
        raw_bytes = file_path.read_bytes()
    else:
        raise FileNotFoundError(f"File not found: {doc.file_path}")

    doc.processed = False
    return await ingest_document(doc, raw_bytes, db)


async def delete_document_index(doc_id: uuid.UUID, db: AsyncSession) -> int:
    """Delete all chunks/vectors for a document. Returns count of deleted chunks."""
    result = await db.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
    )
    count = result.rowcount
    logger.info(f"Deleted {count} chunks for document {doc_id}")
    return count


async def search_index(
    query_embedding: list[float],
    company_id: uuid.UUID | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
    db: AsyncSession = None,
) -> list[dict[str, Any]]:
    """
    Search the vector index for similar document chunks.
    Returns ranked results with similarity scores.
    """
    filter_clause = ""
    params: dict[str, Any] = {
        "embedding": str(query_embedding),
        "top_k": top_k,
        "threshold": similarity_threshold,
    }

    if company_id:
        filter_clause = "AND d.company_id = :company_id"
        params["company_id"] = str(company_id)

    sql = text(f"""
        SELECT
            dc.id,
            dc.content,
            dc.chunk_metadata,
            d.filename,
            d.id AS document_id,
            1 - (dc.embedding <=> :embedding::vector) AS similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE dc.embedding IS NOT NULL
        AND 1 - (dc.embedding <=> :embedding::vector) >= :threshold
        {filter_clause}
        ORDER BY dc.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    return [
        {
            "chunk_id": str(row[0]),
            "content": row[1],
            "metadata": row[2],
            "filename": row[3],
            "document_id": str(row[4]),
            "similarity": round(float(row[5]), 4),
        }
        for row in rows
    ]


async def get_index_stats(company_id: uuid.UUID | None, db: AsyncSession) -> dict[str, Any]:
    """Return statistics about the vector index."""
    filter_clause = ""
    params: dict[str, Any] = {}

    if company_id:
        filter_clause = "WHERE d.company_id = :company_id"
        params["company_id"] = str(company_id)

    sql = text(f"""
        SELECT
            COUNT(DISTINCT d.id) AS total_documents,
            COUNT(dc.id) AS total_chunks,
            COUNT(CASE WHEN dc.embedding IS NOT NULL THEN 1 END) AS indexed_chunks,
            SUM(d.file_size_bytes) AS total_size_bytes
        FROM documents d
        LEFT JOIN document_chunks dc ON dc.document_id = d.id
        {filter_clause}
    """)

    result = await db.execute(sql, params)
    row = result.fetchone()

    return {
        "total_documents": row[0] or 0,
        "total_chunks": row[1] or 0,
        "indexed_chunks": row[2] or 0,
        "total_size_bytes": row[3] or 0,
    }
