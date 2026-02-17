"""
F360 – Recommendation Engine
Combines rule-based checks with LLM reasoning to generate
actionable financial recommendations.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.core.config import get_settings
from app.models.financial import Budget, Recommendation

settings = get_settings()


class RecommendationEngine:
    """
    Hybrid recommendation engine:
    - Rule-based: deterministic checks (budget deviation, overdue invoices, etc.)
    - LLM-based: contextual analysis and explanation generation
    """

    # ─────────────────────────────────────────────────
    # Rule-based Analysis
    # ─────────────────────────────────────────────────

    async def analyze_budgets(
        self, budgets: list[Budget], company_id: uuid.UUID
    ) -> list[Recommendation]:
        """Analyze budget lines and generate recommendations."""
        recommendations: list[Recommendation] = []

        for budget in budgets:
            if not budget.planned_amount or budget.planned_amount == 0:
                continue

            deviation = float(
                (budget.actual_amount - budget.planned_amount) / budget.planned_amount * 100
            )

            # ── Rule: Budget deviation > 10% ──
            if deviation > 10:
                severity = "critical" if deviation > 25 else "warning"
                explanation = await self._llm_explain_deviation(
                    budget.category, deviation, budget.planned_amount, budget.actual_amount
                )
                recommendations.append(
                    Recommendation(
                        company_id=company_id,
                        category="budget",
                        severity=severity,
                        title=f"Budget overrun: {budget.category or 'N/A'} ({deviation:+.1f}%)",
                        description=explanation,
                        suggested_action=self._suggest_budget_action(budget.category, deviation),
                        entity_type="budget",
                        entity_id=budget.id,
                    )
                )

            # ── Rule: Budget under-execution < -20% ──
            elif deviation < -20:
                recommendations.append(
                    Recommendation(
                        company_id=company_id,
                        category="budget",
                        severity="info",
                        title=f"Under-execution: {budget.category or 'N/A'} ({deviation:+.1f}%)",
                        description=(
                            f"Budget category '{budget.category}' is significantly under-executed. "
                            f"Planned: €{budget.planned_amount:,.2f}, "
                            f"Actual: €{budget.actual_amount:,.2f}. "
                            f"Consider reallocating unused funds."
                        ),
                        suggested_action=(
                            "Review spending roadmap. Consider reallocating unused budget "
                            "to over-performing categories or carrying forward to next fiscal year."
                        ),
                        entity_type="budget",
                        entity_id=budget.id,
                    )
                )

        return recommendations

    def _suggest_budget_action(self, category: str | None, deviation: float) -> str:
        """Generate actionable suggestion based on category and deviation level."""
        actions = {
            "OPEX": (
                "Review operational expenditures for non-essential spending. "
                "Negotiate supplier contracts. Consider process automation."
            ),
            "CAPEX": (
                "Defer non-critical capital projects. Reassess ROI of planned investments. "
                "Consider leasing vs. purchasing."
            ),
            "HR": (
                "Review hiring plan. Analyze overtime costs. "
                "Consider contractors vs. permanent hires for temporary needs."
            ),
            "IT": (
                "Audit software licenses for unused subscriptions. "
                "Review cloud infrastructure sizing. Consolidate tools."
            ),
            "Marketing": (
                "Analyze campaign ROI. Shift budget to highest-performing channels. "
                "Pause underperforming campaigns."
            ),
        }

        base_action = actions.get(category, "Review spending and identify optimization opportunities.")

        if deviation > 25:
            return f"URGENT: {base_action} Escalate to CFO for immediate review."
        return base_action

    async def _llm_explain_deviation(
        self, category: str | None, deviation: float,
        planned: Decimal, actual: Decimal,
    ) -> str:
        """Use LLM to generate a contextual explanation."""
        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
            return (
                f"Budget category '{category}' shows a {deviation:+.1f}% deviation. "
                f"Planned: €{planned:,.2f}, Actual: €{actual:,.2f}. "
                f"Delta: €{float(actual - planned):,.2f}."
            )

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a CFO advisor. Provide a concise 2-3 sentence analysis "
                            "of a budget deviation. Be specific and actionable."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Category: {category}\n"
                            f"Planned: €{planned:,.2f}\n"
                            f"Actual: €{actual:,.2f}\n"
                            f"Deviation: {deviation:+.1f}%\n"
                            f"Explain this deviation and its potential impact."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=200,
            )
            return response.choices[0].message.content

        except Exception:
            return (
                f"Budget category '{category}' shows a {deviation:+.1f}% deviation. "
                f"Planned: €{planned:,.2f}, Actual: €{actual:,.2f}."
            )
