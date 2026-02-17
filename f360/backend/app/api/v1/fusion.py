"""
F360 – Decision Fusion & Tactical Dashboard API Endpoints (Layers 6-7)
Aggregation multi-sources, décisions tactiques, weak signals, dashboard.
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
    FusionRequest,
    FusionResponse,
    WeakSignalResponse,
)

router = APIRouter()


# ── Tactical Decision Generation ──────────────────────────────

@router.post("/decisions", response_model=FusionResponse)
async def generate_tactical_decisions(
    payload: FusionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate tactical decisions by fusing signals from
    simulation, feedback, RAG, and other sources.
    """
    from app.services.decision_fusion.tactical import TacticalDecisionEngine

    engine = TacticalDecisionEngine()
    result = await engine.generate_decisions(
        gaps=payload.gaps,
        simulation_results=payload.simulation_results,
    )
    return FusionResponse(
        decisions=result["decisions"],
        aggregation_summary=result["aggregation_summary"],
        generated_at=result["generated_at"],
    )


# ── Weak Signal Detection ────────────────────────────────────

@router.post("/weak-signals", response_model=WeakSignalResponse)
async def detect_weak_signals(
    company_id: uuid.UUID,
    fiscal_year: int = 2025,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Scan for weak signals across all data sources and detect
    correlations that indicate emerging risks or opportunities.
    """
    from app.services.recommendation.weak_signals import (
        WeakSignalCorrelator,
        signal_from_budget_drift,
        signal_from_contract_expiry,
        signal_from_cashflow_anomaly,
    )
    from app.services.realtime_feedback.gap_calculator import GapCalculator

    # Gather gaps as a source of weak signals
    calculator = GapCalculator()
    gaps = await calculator.compute_all_gaps(
        company_id=str(company_id),
        fiscal_year=fiscal_year,
        db=db,
    )

    correlator = WeakSignalCorrelator()
    for gap in gaps:
        category = gap.get("category", "")
        deviation = gap.get("gap_pct", 0)
        if "budget" in category.lower():
            correlator.add_signal(signal_from_budget_drift(category, deviation))
        elif "cashflow" in category.lower():
            correlator.add_signal(signal_from_cashflow_anomaly(
                f"Cashflow deviation: {deviation:.1f}%", deviation
            ))

    correlations = correlator.detect_correlations()
    return WeakSignalResponse(
        company_id=company_id,
        signal_count=correlator.signal_count,
        correlations=[c.to_dict() for c in correlations],
    )


# ── Tactical Dashboard ──────────────────────────────────────

@router.get("/dashboard")
async def tactical_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the full tactical dashboard payload:
    KPIs, alerts, budget usage, cashflow trend, contracts.
    """
    from app.services.recommendation.dashboard import TacticalDashboard

    dashboard = TacticalDashboard(db)
    return await dashboard.get_full_dashboard()


# ── Scenario Generation (AI) ───────────────────────────────

@router.post("/scenarios")
async def generate_scenarios(
    context: dict[str, Any],
    num_scenarios: int = 5,
    current_user: User = Depends(get_current_user),
):
    """
    Generate AI-powered what-if scenarios based on company context.
    """
    from app.services.simulation.scenario_generator import ScenarioGenerator

    generator = ScenarioGenerator()
    result = await generator.generate_scenarios(context, num_scenarios)
    return result
