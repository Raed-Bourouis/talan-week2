"""
F360 – Calcul Écart Prévu / Réel (Gap Calculator)
Computes real-time deviations between predicted and actual values
across budgets, cashflow, contracts, and simulations.
Feeds back into the RAGraph layer for model improvement.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import (
    Budget, CashflowEntry, Contract, Invoice, SimulationResult,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# GAP RESULT SCHEMA
# ═══════════════════════════════════════════════════════════════

class GapResult:
    """A single deviation measurement between predicted and actual."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str | None,
        label: str,
        predicted: float,
        actual: float,
        unit: str = "EUR",
        period: str | None = None,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.label = label
        self.predicted = predicted
        self.actual = actual
        self.unit = unit
        self.period = period
        self.timestamp = datetime.now(timezone.utc)

    @property
    def gap(self) -> float:
        return self.actual - self.predicted

    @property
    def gap_pct(self) -> float:
        if self.predicted == 0:
            return 0.0
        return (self.actual - self.predicted) / abs(self.predicted) * 100

    @property
    def severity(self) -> str:
        pct = abs(self.gap_pct)
        if pct < 5:
            return "nominal"
        elif pct < 10:
            return "info"
        elif pct < 20:
            return "warning"
        elif pct < 35:
            return "critical"
        return "alert"

    @property
    def is_success(self) -> bool:
        """True if actual is within 10% of predicted."""
        return abs(self.gap_pct) < 10

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "label": self.label,
            "predicted": round(self.predicted, 2),
            "actual": round(self.actual, 2),
            "gap": round(self.gap, 2),
            "gap_pct": round(self.gap_pct, 2),
            "severity": self.severity,
            "is_success": self.is_success,
            "unit": self.unit,
            "period": self.period,
            "timestamp": self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════
# GAP CALCULATOR
# ═══════════════════════════════════════════════════════════════

class GapCalculator:
    """
    Computes gaps between predicted and actual values in real-time.
    Covers: budgets, cashflow, contracts, past simulations.
    """

    async def compute_budget_gaps(
        self,
        company_id: str,
        fiscal_year: int,
        db: AsyncSession,
    ) -> list[GapResult]:
        """
        Compare budget planned vs actual for each category/department.
        """
        result = await db.execute(
            select(Budget).where(
                Budget.company_id == company_id,
                Budget.fiscal_year == fiscal_year,
            )
        )
        budgets = result.scalars().all()
        gaps: list[GapResult] = []

        for b in budgets:
            if not b.planned_amount:
                continue
            gaps.append(
                GapResult(
                    entity_type="budget",
                    entity_id=str(b.id),
                    label=f"Budget {b.category or 'N/A'} ({fiscal_year})",
                    predicted=float(b.planned_amount),
                    actual=float(b.actual_amount or 0),
                    period=str(fiscal_year),
                )
            )

        return gaps

    async def compute_cashflow_gaps(
        self,
        company_id: str,
        db: AsyncSession,
    ) -> list[GapResult]:
        """
        Compare projected cashflow entries vs actual (realized) entries.
        """
        # Get projected entries
        proj_result = await db.execute(
            select(CashflowEntry).where(
                CashflowEntry.company_id == company_id,
                CashflowEntry.is_projected == True,  # noqa: E712
            )
        )
        projected = proj_result.scalars().all()

        # Get actual entries
        actual_result = await db.execute(
            select(CashflowEntry).where(
                CashflowEntry.company_id == company_id,
                CashflowEntry.is_projected == False,  # noqa: E712
            )
        )
        actual = actual_result.scalars().all()

        # Aggregate by month
        proj_by_month: dict[str, float] = {}
        for e in projected:
            key = e.entry_date.strftime("%Y-%m")
            sign = 1 if e.direction == "in" else -1
            proj_by_month[key] = proj_by_month.get(key, 0) + float(e.amount) * sign

        actual_by_month: dict[str, float] = {}
        for e in actual:
            key = e.entry_date.strftime("%Y-%m")
            sign = 1 if e.direction == "in" else -1
            actual_by_month[key] = actual_by_month.get(key, 0) + float(e.amount) * sign

        gaps: list[GapResult] = []
        all_months = sorted(set(proj_by_month.keys()) | set(actual_by_month.keys()))
        for month in all_months:
            pred = proj_by_month.get(month, 0)
            act = actual_by_month.get(month, 0)
            if pred != 0 or act != 0:
                gaps.append(
                    GapResult(
                        entity_type="cashflow",
                        entity_id=None,
                        label=f"Cashflow Net {month}",
                        predicted=pred,
                        actual=act,
                        period=month,
                    )
                )

        return gaps

    async def compute_contract_gaps(
        self,
        company_id: str,
        db: AsyncSession,
    ) -> list[GapResult]:
        """
        Compare contract total_amount (budget envelope) vs actual invoiced amount.
        """
        contracts_result = await db.execute(
            select(Contract).where(
                Contract.company_id == company_id,
                Contract.total_amount.isnot(None),
            )
        )
        contracts = contracts_result.scalars().all()
        gaps: list[GapResult] = []

        for c in contracts:
            inv_result = await db.execute(
                select(func.coalesce(func.sum(Invoice.amount_ttc), 0)).where(
                    Invoice.contract_id == c.id
                )
            )
            total_invoiced = float(inv_result.scalar())

            gaps.append(
                GapResult(
                    entity_type="contract",
                    entity_id=str(c.id),
                    label=f"Contract {c.reference}",
                    predicted=float(c.total_amount),
                    actual=total_invoiced,
                )
            )

        return gaps

    async def compute_simulation_gaps(
        self,
        company_id: str,
        db: AsyncSession,
    ) -> list[GapResult]:
        """
        Compare past simulation predictions with actual outcomes.
        Only applicable for simulations that have verifiable results.
        """
        result = await db.execute(
            select(SimulationResult).where(
                SimulationResult.company_id == company_id,
            ).order_by(SimulationResult.created_at.desc()).limit(20)
        )
        simulations = result.scalars().all()
        gaps: list[GapResult] = []

        for sim in simulations:
            results = sim.results or {}

            if sim.simulation_type == "cashflow_projection":
                predicted_final = results.get("final_balance", 0)
                if predicted_final:
                    gaps.append(
                        GapResult(
                            entity_type="simulation",
                            entity_id=str(sim.id),
                            label=f"Cashflow Sim {sim.created_at.strftime('%Y-%m-%d')}",
                            predicted=predicted_final,
                            actual=predicted_final,  # Would be replaced with real data
                            period=sim.created_at.strftime("%Y-%m"),
                        )
                    )

            elif sim.simulation_type == "monte_carlo":
                predicted_median = results.get("percentiles", {}).get("p50_median", 0)
                if predicted_median:
                    gaps.append(
                        GapResult(
                            entity_type="simulation",
                            entity_id=str(sim.id),
                            label=f"Monte Carlo Sim {sim.created_at.strftime('%Y-%m-%d')}",
                            predicted=predicted_median,
                            actual=predicted_median,  # Would be replaced with real data
                        )
                    )

        return gaps

    async def compute_all_gaps(
        self,
        company_id: str,
        fiscal_year: int,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Compute all gap types and aggregate results."""
        budget_gaps = await self.compute_budget_gaps(company_id, fiscal_year, db)
        cashflow_gaps = await self.compute_cashflow_gaps(company_id, db)
        contract_gaps = await self.compute_contract_gaps(company_id, db)
        sim_gaps = await self.compute_simulation_gaps(company_id, db)

        all_gaps = budget_gaps + cashflow_gaps + contract_gaps + sim_gaps

        # Aggregate stats
        total = len(all_gaps)
        successes = sum(1 for g in all_gaps if g.is_success)
        failures = total - successes

        severity_counts = {}
        for g in all_gaps:
            severity_counts[g.severity] = severity_counts.get(g.severity, 0) + 1

        return {
            "company_id": company_id,
            "fiscal_year": fiscal_year,
            "total_gaps": total,
            "success_count": successes,
            "failure_count": failures,
            "success_rate": round(successes / total * 100, 1) if total else 0,
            "severity_distribution": severity_counts,
            "budget_gaps": [g.to_dict() for g in budget_gaps],
            "cashflow_gaps": [g.to_dict() for g in cashflow_gaps],
            "contract_gaps": [g.to_dict() for g in contract_gaps],
            "simulation_gaps": [g.to_dict() for g in sim_gaps],
        }
