"""
F360 – Simulation Endpoints
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.financial import SimulationResult
from app.schemas.schemas import SimulationRequest, SimulationResponse
from app.services.simulation.parallel_engine import ParallelSimulationEngine

router = APIRouter()
engine = ParallelSimulationEngine()


@router.post("/", response_model=SimulationResponse)
async def run_simulation(
    payload: SimulationRequest,
    company_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run a financial simulation.
    Types: budget_variation, cashflow_projection, monte_carlo, renegotiation
    """
    results = engine.run(payload.simulation_type, payload.parameters)

    # Persist result
    sim = SimulationResult(
        company_id=company_id,
        user_id=current_user.id,
        simulation_type=payload.simulation_type,
        parameters=payload.parameters,
        results=results,
    )
    db.add(sim)
    await db.flush()
    await db.refresh(sim)
    return sim
