"""
F360 – Recommendation Endpoints
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.financial import Recommendation, Budget
from app.schemas.schemas import RecommendationResponse
from app.services.recommendation.engine import RecommendationEngine

router = APIRouter()
reco_engine = RecommendationEngine()


@router.get("/", response_model=list[RecommendationResponse])
async def list_recommendations(
    company_id: uuid.UUID,
    category: str | None = None,
    include_resolved: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all recommendations for a company."""
    query = select(Recommendation).where(Recommendation.company_id == company_id)
    if category:
        query = query.where(Recommendation.category == category)
    if not include_resolved:
        query = query.where(Recommendation.is_resolved == False)  # noqa: E712
    query = query.order_by(Recommendation.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/generate", response_model=list[RecommendationResponse])
async def generate_recommendations(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze financial data and generate AI-powered recommendations.
    Combines rule-based checks with LLM reasoning.
    """
    # Fetch budgets for analysis
    result = await db.execute(
        select(Budget).where(Budget.company_id == company_id)
    )
    budgets = result.scalars().all()

    # Generate recommendations
    new_recos = await reco_engine.analyze_budgets(budgets, company_id)

    for reco in new_recos:
        db.add(reco)
    await db.flush()

    # Return fresh list
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.company_id == company_id,
            Recommendation.is_resolved == False,  # noqa: E712
        ).order_by(Recommendation.created_at.desc())
    )
    return result.scalars().all()
