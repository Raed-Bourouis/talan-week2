"""
F360 – RAG (Retrieval-Augmented Generation) Endpoints
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import RAGQuery, RAGResponse
from app.services.rag.retriever import RAGRetriever

router = APIRouter()
retriever = RAGRetriever()


@router.post("/query", response_model=RAGResponse)
async def rag_query(
    payload: RAGQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Semantic search over financial documents with LLM-augmented answer.
    Example: "Which contracts include penalty clauses indexed on inflation?"
    """
    response = await retriever.query(
        question=payload.question,
        company_id=payload.company_id,
        top_k=payload.top_k,
        db=db,
    )
    return response
