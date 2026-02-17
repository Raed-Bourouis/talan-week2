"""
F360 – Document Chunker & Embedder
Chunks financial documents and stores embeddings in pgvector.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.financial import DocumentChunk

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
            # Look for sentence-ending punctuation near the boundary
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


async def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector using OpenAI API.
    Returns a list of floats (dimension = 1536 for text-embedding-3-small).
    """
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding
    except Exception:
        # Fallback: return zero vector for development without API key
        return [0.0] * settings.embedding_dimension


async def chunk_and_embed(
    text: str,
    document_id: uuid.UUID,
    metadata: dict[str, Any],
    db: AsyncSession,
) -> list[DocumentChunk]:
    """
    Full pipeline: chunk text → embed each chunk → store in DB with pgvector.
    """
    chunks_text = chunk_text(text)
    stored_chunks: list[DocumentChunk] = []

    for idx, chunk_content in enumerate(chunks_text):
        # Generate embedding
        embedding = await get_embedding(chunk_content)

        # Create chunk record
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            content=chunk_content,
            metadata={
                **metadata,
                "chunk_index": idx,
                "total_chunks": len(chunks_text),
            },
        )
        db.add(chunk)
        await db.flush()
        await db.refresh(chunk)

        # Store embedding via raw SQL (pgvector)
        await db.execute(
            text(
                "UPDATE document_chunks SET embedding = :embedding WHERE id = :chunk_id"
            ),
            {"embedding": str(embedding), "chunk_id": str(chunk.id)},
        )

        stored_chunks.append(chunk)

    return stored_chunks
