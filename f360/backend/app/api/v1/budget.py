"""
F360 – Budget Endpoints
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.financial import Budget, Department
from app.schemas.schemas import BudgetCreate, BudgetOverview, BudgetResponse

router = APIRouter()


@router.get("/overview", response_model=BudgetOverview)
async def budget_overview(
    company_id: uuid.UUID,
    fiscal_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return aggregated budget overview with deviation analysis.
    """
    result = await db.execute(
        select(Budget).where(
            Budget.company_id == company_id,
            Budget.fiscal_year == fiscal_year,
        )
    )
    budgets = result.scalars().all()

    total_planned = sum(b.planned_amount for b in budgets) or Decimal("0")
    total_actual = sum(b.actual_amount for b in budgets) or Decimal("0")
    deviation_pct = (
        float((total_actual - total_planned) / total_planned * 100)
        if total_planned
        else 0.0
    )

    # Group by category
    by_category = {}
    for b in budgets:
        cat = b.category or "Uncategorized"
        if cat not in by_category:
            by_category[cat] = {"category": cat, "planned": Decimal("0"), "actual": Decimal("0")}
        by_category[cat]["planned"] += b.planned_amount
        by_category[cat]["actual"] += b.actual_amount

    for v in by_category.values():
        v["deviation_pct"] = (
            float((v["actual"] - v["planned"]) / v["planned"] * 100)
            if v["planned"]
            else 0.0
        )
        v["planned"] = float(v["planned"])
        v["actual"] = float(v["actual"])

    # Group by department
    dept_ids = {b.department_id for b in budgets if b.department_id}
    dept_map = {}
    if dept_ids:
        dept_result = await db.execute(select(Department).where(Department.id.in_(dept_ids)))
        dept_map = {d.id: d.name for d in dept_result.scalars().all()}

    by_department = {}
    for b in budgets:
        dept_name = dept_map.get(b.department_id, "Unassigned")
        if dept_name not in by_department:
            by_department[dept_name] = {"department": dept_name, "planned": Decimal("0"), "actual": Decimal("0")}
        by_department[dept_name]["planned"] += b.planned_amount
        by_department[dept_name]["actual"] += b.actual_amount

    for v in by_department.values():
        v["deviation_pct"] = (
            float((v["actual"] - v["planned"]) / v["planned"] * 100)
            if v["planned"]
            else 0.0
        )
        v["planned"] = float(v["planned"])
        v["actual"] = float(v["actual"])

    return BudgetOverview(
        fiscal_year=fiscal_year,
        total_planned=total_planned,
        total_actual=total_actual,
        deviation_pct=deviation_pct,
        by_category=list(by_category.values()),
        by_department=list(by_department.values()),
    )


@router.post("/", response_model=BudgetResponse, status_code=201)
async def create_budget(
    payload: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = Budget(**payload.model_dump())
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget
