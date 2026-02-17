"""
F360 – RAGraph API Endpoints (Layer 3)
Semantic search with episodic memory, knowledge graph traversal,
and chain-of-thought reasoning.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import (
    RAGQuery,
    RAGResponse,
    ChainOfThoughtRequest,
    ChainOfThoughtResponse,
)

router = APIRouter()


@router.post("/query", response_model=RAGResponse)
async def ragraph_query(
    payload: RAGQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full RAGraph pipeline: vector search + episodic memory recall +
    knowledge graph traversal + LLM reasoning.
    """
    from app.services.ragraph.orchestrator import RAGOrchestrator

    orchestrator = RAGOrchestrator()
    result = await orchestrator.query(
        question=payload.question,
        company_id=payload.company_id,
        top_k=payload.top_k,
        db=db,
    )
    return result


@router.post("/reason", response_model=ChainOfThoughtResponse)
async def chain_of_thought(
    payload: ChainOfThoughtRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Run multi-step chain-of-thought reasoning on a financial question.
    Returns structured reasoning steps with a final conclusion.
    """
    from app.services.ragraph.reasoning import ReasoningEngine

    engine = ReasoningEngine()
    # Convert context dict to string for the reasoning engine
    import json
    context_str = json.dumps(payload.context) if payload.context else ""
    result = await engine.chain_of_thought(
        question=payload.question,
        context=context_str,
    )
    return ChainOfThoughtResponse(
        question=payload.question,
        steps=result.get("steps", []),
        conclusion=result.get("conclusion", ""),
        model=result.get("model", "unknown"),
    )


@router.get("/memory/recall")
async def recall_episodes(
    query: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recall relevant past episodes from episodic memory."""
    from app.services.ragraph.episodic_memory import EpisodicMemory

    memory = EpisodicMemory()
    episodes = await memory.recall(query=query, top_k=limit, db=db)
    return {"query": query, "episodes": [e.to_dict() for e in episodes]}
