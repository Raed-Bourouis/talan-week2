"""
F360 – Real-Time Feedback API Endpoints (Layer 4)
Gap analysis, feedback cycles, and re-indexation triggers.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import GapAnalysisRequest, GapAnalysisResponse

router = APIRouter()


@router.post("/gaps", response_model=GapAnalysisResponse)
async def compute_gaps(
    payload: GapAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute gaps between predicted and actual values across
    budget, cashflow, contracts, and simulations.
    """
    from app.services.realtime_feedback.gap_calculator import GapCalculator

    calculator = GapCalculator()
    results = await calculator.compute_all_gaps(
        company_id=str(payload.company_id),
        fiscal_year=payload.fiscal_year,
        db=db,
    )
    return GapAnalysisResponse(
        company_id=payload.company_id,
        gaps=results,
        total_gaps=len(results),
    )


@router.post("/cycle")
async def run_feedback_cycle(
    company_id: uuid.UUID,
    fiscal_year: int = 2025,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run a full feedback cycle: compute gaps → classify → reindex → store.
    """
    from app.services.realtime_feedback.reindexer import FeedbackReindexer

    reindexer = FeedbackReindexer()
    result = await reindexer.process_feedback_cycle(
        company_id=str(company_id),
        fiscal_year=fiscal_year,
        db=db,
    )
    return result


@router.get("/history")
async def feedback_history(
    company_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve recent feedback events for a company."""
    from app.services.realtime_feedback.reindexer import FeedbackReindexer

    reindexer = FeedbackReindexer()
    history = reindexer.get_feedback_history(limit=limit)
    return {"company_id": str(company_id), "events": history}
