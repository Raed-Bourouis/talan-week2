"""
F360 – Vectorizer
Text chunking + embedding generation via OpenAI.
Converts raw text into vector representations for semantic search.
"""
from __future__ import annotations

import uuid
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.financial import DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Chunking constants ──
CHUNK_SIZE = 1000       # characters per chunk
CHUNK_OVERLAP = 200     # overlap between chunks


def chunk_text(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks for embedding.
    Uses sentence-aware splitting when possible.
    """
    if not content or len(content) <= chunk_size:
        return [content] if content else []

    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = start + chunk_size

        # Try to end at a sentence boundary
        if end < len(content):
            for sep in [". ", ".\n", "\n\n", "\n", " "]:
                boundary = content.rfind(sep, start + chunk_size // 2, end + 50)
                if boundary != -1:
                    end = boundary + len(sep)
                    break

        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


async def get_embedding(text_input: str) -> list[float]:
    """
    Generate embedding vector using OpenAI API.
    Returns a list of floats (dimension = 1536 for text-embedding-3-small).
    """
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text_input,
        )
        return response.data[0].embedding
    except Exception:
        # Fallback: return zero vector for development without API key
        return [0.0] * settings.embedding_dimension


async def vectorize_and_store(
    text_content: str,
    document_id: uuid.UUID,
    metadata: dict[str, Any],
    db: AsyncSession,
) -> list[DocumentChunk]:
    """
    Full vectorization pipeline: chunk text → embed each chunk → store in DB with pgvector.
    """
    chunks_text = chunk_text(text_content)
    stored_chunks: list[DocumentChunk] = []

    for idx, chunk_content in enumerate(chunks_text):
        embedding = await get_embedding(chunk_content)

        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            content=chunk_content,
            chunk_metadata={
                **metadata,
                "chunk_index": idx,
                "total_chunks": len(chunks_text),
            },
        )
        db.add(chunk)
        await db.flush()
        await db.refresh(chunk)

        await db.execute(
            text(
                "UPDATE document_chunks SET embedding = :embedding WHERE id = :chunk_id"
            ),
            {"embedding": str(embedding), "chunk_id": str(chunk.id)},
        )

        stored_chunks.append(chunk)

    logger.info(f"Vectorized document {document_id}: {len(stored_chunks)} chunks stored")
    return stored_chunks
