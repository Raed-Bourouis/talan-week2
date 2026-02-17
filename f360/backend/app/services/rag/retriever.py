"""
F360 – RAG Retriever
Semantic search over financial documents + LLM-augmented answer generation.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.schemas.schemas import RAGResponse
from app.services.rag.embedder import get_embedding

settings = get_settings()


class RAGRetriever:
    """
    Retrieval-Augmented Generation engine.
    1. Embed the user query
    2. Vector search in pgvector (cosine similarity)
    3. Build context from top-k chunks
    4. Send to LLM for answer generation
    """

    async def query(
        self,
        question: str,
        company_id: uuid.UUID | None,
        top_k: int,
        db: AsyncSession,
    ) -> RAGResponse:
        # ── 1. Embed the question ──
        query_embedding = await get_embedding(question)

        # ── 2. Vector similarity search ──
        filter_clause = ""
        params: dict[str, Any] = {
            "embedding": str(query_embedding),
            "top_k": top_k,
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
                1 - (dc.embedding <=> :embedding::vector) AS similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.embedding IS NOT NULL
            {filter_clause}
            ORDER BY dc.embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        result = await db.execute(sql, params)
        rows = result.fetchall()

        # ── 3. Build context ──
        sources: list[dict[str, Any]] = []
        context_parts: list[str] = []

        for row in rows:
            chunk_id, content, metadata, filename, similarity = row
            sources.append({
                "chunk_id": str(chunk_id),
                "filename": filename,
                "similarity": round(float(similarity), 4),
                "excerpt": content[:300] + "..." if len(content) > 300 else content,
            })
            context_parts.append(f"[Source: {filename}]\n{content}")

        context = "\n\n---\n\n".join(context_parts)

        # ── 4. LLM-augmented answer ──
        answer = await self._generate_answer(question, context)

        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=float(rows[0][4]) if rows else None,
        )

    async def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using OpenAI with retrieved context."""
        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
            return self._fallback_answer(question, context)

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)

            system_prompt = """You are F360, an AI financial analyst assistant.
You answer questions about financial documents, contracts, invoices and budgets.
Base your answers ONLY on the provided context. If the context doesn't contain
enough information, say so clearly.
Always cite the source document when referencing specific data.
Respond in the same language as the question."""

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {question}",
                    },
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            return response.choices[0].message.content

        except Exception as e:
            return self._fallback_answer(question, context)

    def _fallback_answer(self, question: str, context: str) -> str:
        """Fallback when OpenAI is not available."""
        if not context:
            return "No relevant documents found for your query."
        return (
            f"Based on the retrieved documents, here is the relevant context:\n\n"
            f"{context[:1500]}\n\n"
            f"(Note: Full AI analysis requires a valid OpenAI API key)"
        )
