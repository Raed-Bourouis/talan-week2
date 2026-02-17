"""
F360 – Cashflow Endpoints
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.financial import CashflowEntry, Invoice
from app.schemas.schemas import CashflowForecast

router = APIRouter()


@router.get("/forecast", response_model=list[CashflowForecast])
async def cashflow_forecast(
    company_id: uuid.UUID,
    days: int = Query(default=90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a J+N cashflow forecast combining:
    - Historical cashflow entries
    - Projected entries from pending invoices
    """
    today = date.today()
    horizon = today + timedelta(days=days)

    # ── Historical entries ──
    result = await db.execute(
        select(CashflowEntry).where(
            CashflowEntry.company_id == company_id,
            CashflowEntry.entry_date >= today - timedelta(days=30),
            CashflowEntry.entry_date <= horizon,
        ).order_by(CashflowEntry.entry_date)
    )
    entries = result.scalars().all()

    # ── Projected from pending invoices ──
    inv_result = await db.execute(
        select(Invoice).where(
            Invoice.company_id == company_id,
            Invoice.status == "pending",
            Invoice.due_date.isnot(None),
            Invoice.due_date >= today,
            Invoice.due_date <= horizon,
        )
    )
    pending_invoices = inv_result.scalars().all()

    # Build daily aggregation
    daily: dict[date, dict] = {}

    for entry in entries:
        d = entry.entry_date
        if d not in daily:
            daily[d] = {"inflows": Decimal("0"), "outflows": Decimal("0"), "projected": False}
        if entry.direction == "in":
            daily[d]["inflows"] += entry.amount
        else:
            daily[d]["outflows"] += entry.amount

    for inv in pending_invoices:
        d = inv.due_date
        if d not in daily:
            daily[d] = {"inflows": Decimal("0"), "outflows": Decimal("0"), "projected": True}
        if inv.direction == "inbound":
            daily[d]["inflows"] += inv.amount_ttc
        else:
            daily[d]["outflows"] += inv.amount_ttc
        daily[d]["projected"] = True

    # Build cumulative forecast
    forecast: list[CashflowForecast] = []
    cumulative = Decimal("0")
    for d in sorted(daily.keys()):
        data = daily[d]
        cumulative += data["inflows"] - data["outflows"]
        forecast.append(
            CashflowForecast(
                date=d,
                cumulative_balance=cumulative,
                inflows=data["inflows"],
                outflows=data["outflows"],
                is_projected=data["projected"],
            )
        )

    return forecast
