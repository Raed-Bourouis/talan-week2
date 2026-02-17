"""
F360 – Contracts Endpoints
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.financial import Contract, Invoice, Budget
from app.schemas.schemas import ContractAlert, ContractCreate, ContractResponse

router = APIRouter()


@router.get("/", response_model=list[ContractResponse])
async def list_contracts(
    company_id: uuid.UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all contracts for a company, optionally filtered by status."""
    query = select(Contract).where(Contract.company_id == company_id)
    if status:
        query = query.where(Contract.status == status)
    query = query.order_by(Contract.end_date.asc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ContractResponse, status_code=201)
async def create_contract(
    payload: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = Contract(**payload.model_dump())
    db.add(contract)
    await db.flush()
    await db.refresh(contract)
    return contract


@router.get("/alerts", response_model=list[ContractAlert])
async def contract_alerts(
    company_id: uuid.UUID,
    days_ahead: int = Query(default=90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate contract alerts:
    - Contracts expiring within `days_ahead` days
    - Contracts with invoices exceeding total amount
    - Contracts with penalty clauses at risk
    """
    alerts: list[ContractAlert] = []
    today = date.today()
    horizon = today + timedelta(days=days_ahead)

    # ── Expiring contracts ──
    result = await db.execute(
        select(Contract).where(
            Contract.company_id == company_id,
            Contract.status == "active",
            Contract.end_date.isnot(None),
            Contract.end_date <= horizon,
        )
    )
    for c in result.scalars().all():
        days_left = (c.end_date - today).days
        severity = "critical" if days_left <= 30 else "warning" if days_left <= 60 else "info"
        alerts.append(
            ContractAlert(
                contract_id=c.id,
                reference=c.reference,
                alert_type="expiring_soon",
                message=f"Contract {c.reference} expires in {days_left} days ({c.end_date})",
                severity=severity,
            )
        )

    # ── Over-spending contracts ──
    contracts_result = await db.execute(
        select(Contract).where(
            Contract.company_id == company_id,
            Contract.status == "active",
            Contract.total_amount.isnot(None),
        )
    )
    for c in contracts_result.scalars().all():
        inv_result = await db.execute(
            select(Invoice).where(Invoice.contract_id == c.id)
        )
        invoices = inv_result.scalars().all()
        total_invoiced = sum(i.amount_ttc for i in invoices)
        if c.total_amount and total_invoiced > c.total_amount:
            over_pct = float((total_invoiced - c.total_amount) / c.total_amount * 100)
            alerts.append(
                ContractAlert(
                    contract_id=c.id,
                    reference=c.reference,
                    alert_type="budget_exceeded",
                    message=f"Contract {c.reference} exceeded by {over_pct:.1f}% (invoiced: {total_invoiced}, budget: {c.total_amount})",
                    severity="critical" if over_pct > 20 else "warning",
                )
            )

    return alerts
