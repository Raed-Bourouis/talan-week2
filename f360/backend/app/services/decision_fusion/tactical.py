"""
F360 – Décisions Tactiques (Tactical Decision Engine)
Combines aggregated signals with business rules to produce
actionable tactical decisions and priority-ranked action items.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.decision_fusion.aggregator import (
    MultiSourceAggregator,
    Signal,
    build_signal_from_gap,
    build_signal_from_simulation,
)

logger = logging.getLogger(__name__)


# ── Decision dataclass ──────────────────────────────────────────

class TacticalDecision:
    """A concrete, scored action recommendation."""

    __slots__ = (
        "id", "title", "category", "priority",
        "score", "rationale", "actions", "created_at",
    )

    def __init__(
        self,
        id: str,
        title: str,
        category: str,
        priority: str,
        score: float,
        rationale: str,
        actions: list[str],
    ):
        self.id = id
        self.title = title
        self.category = category        # budget, cashflow, contract, risk
        self.priority = priority        # P1 (critical) … P4 (informational)
        self.score = score
        self.rationale = rationale
        self.actions = actions
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "score": round(self.score, 3),
            "rationale": self.rationale,
            "actions": self.actions,
            "created_at": self.created_at.isoformat(),
        }


# ── Engine ──────────────────────────────────────────────────────

class TacticalDecisionEngine:
    """
    Ingests results from simulation, feedback, RAG, etc.,
    delegates aggregation to MultiSourceAggregator, then applies
    business rules / LLM reasoning to emit tactical decisions.
    """

    PRIORITY_THRESHOLDS = {
        "P1": -0.6,   # critical – score ≤ -0.6
        "P2": -0.3,   # high
        "P3":  0.0,   # medium
        "P4":  0.3,   # low – score > 0.3 → informational
    }

    def __init__(self):
        self.aggregator = MultiSourceAggregator()
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.llm_available = True
        except Exception:
            self.client = None
            self.llm_available = False

    # ── Public API ──────────────────────────────────────

    async def generate_decisions(
        self,
        gaps: list[dict[str, Any]] | None = None,
        simulation_results: list[dict[str, Any]] | None = None,
        rag_signals: list[Signal] | None = None,
        extra_signals: list[Signal] | None = None,
    ) -> dict[str, Any]:
        """
        End-to-end decision pipeline:
        1. Convert inputs → signals
        2. Aggregate
        3. Map aggregated topics to decisions via rules / LLM
        """
        # 1. Build signals
        self.aggregator.clear()

        if gaps:
            for g in gaps:
                self.aggregator.add_signal(build_signal_from_gap(g))

        if simulation_results:
            for r in simulation_results:
                self.aggregator.add_signal(build_signal_from_simulation(r))

        if rag_signals:
            self.aggregator.add_signals(rag_signals)

        if extra_signals:
            self.aggregator.add_signals(extra_signals)

        # 2. Aggregate
        aggregation = self.aggregator.aggregate()

        # 3. Decisions
        decisions = self._apply_rules(aggregation)

        if self.llm_available and decisions:
            decisions = await self._enrich_with_llm(decisions, aggregation)

        decisions.sort(key=lambda d: d.score)  # most negative first

        return {
            "decisions": [d.to_dict() for d in decisions],
            "aggregation_summary": {
                "overall_score": aggregation["overall_score"],
                "signal_count": aggregation["signal_count"],
                "conflicts": aggregation["conflicts"],
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Rule-Based Decision Mapping ─────────────────────

    def _apply_rules(
        self, aggregation: dict[str, Any]
    ) -> list[TacticalDecision]:
        decisions: list[TacticalDecision] = []
        topics = aggregation.get("topics", {})

        for idx, (topic, info) in enumerate(topics.items(), start=1):
            score = info["score"]
            priority = self._score_to_priority(score)
            decision = TacticalDecision(
                id=f"TD-{idx:04d}",
                title=self._topic_to_title(topic, score),
                category=self._infer_category(topic),
                priority=priority,
                score=score,
                rationale=self._build_rationale(topic, info),
                actions=self._suggest_actions(topic, score, priority),
            )
            decisions.append(decision)

        return decisions

    def _score_to_priority(self, score: float) -> str:
        for priority, threshold in self.PRIORITY_THRESHOLDS.items():
            if score <= threshold:
                return priority
        return "P4"

    def _topic_to_title(self, topic: str, score: float) -> str:
        direction = "Risque" if score < 0 else "Opportunité"
        pretty = topic.replace("_", " ").title()
        return f"{direction}: {pretty}"

    def _infer_category(self, topic: str) -> str:
        mapping = {
            "budget": "budget", "opex": "budget", "capex": "budget",
            "cashflow": "cashflow", "cash": "cashflow", "liquidity": "cashflow",
            "contract": "contract", "supplier": "contract", "renegotiation": "contract",
            "monte_carlo": "risk", "risk": "risk", "simulation": "risk",
        }
        t_lower = topic.lower()
        for key, cat in mapping.items():
            if key in t_lower:
                return cat
        return "general"

    def _build_rationale(self, topic: str, info: dict[str, Any]) -> str:
        return (
            f"{info['signal_count']} signals from {', '.join(info['sources'])} "
            f"with {info['consensus']} consensus "
            f"(avg confidence {info['avg_confidence']:.0%}). "
            f"Aggregated score: {info['score']:.3f}."
        )

    def _suggest_actions(
        self, topic: str, score: float, priority: str
    ) -> list[str]:
        """Rule-based action suggestions."""
        actions: list[str] = []

        if priority in ("P1", "P2"):
            actions.append("Schedule emergency review meeting with CFO")

        if "budget" in topic.lower():
            if score < -0.3:
                actions.append("Freeze non-essential budget allocations")
                actions.append("Request detailed OPEX breakdown by department")
            else:
                actions.append("Review budget utilization trends")

        if "cashflow" in topic.lower():
            if score < -0.3:
                actions.append("Accelerate accounts receivable collection")
                actions.append("Negotiate supplier payment term extensions")
            else:
                actions.append("Monitor daily cash position")

        if "contract" in topic.lower():
            actions.append("Audit top-5 contracts by value")
            if score < -0.3:
                actions.append("Initiate renegotiation process")

        if "risk" in topic.lower() or "monte_carlo" in topic.lower():
            actions.append("Update risk register with latest simulation data")
            if score < -0.5:
                actions.append("Activate contingency plan")

        if not actions:
            actions.append("Continue monitoring and report in next cycle")

        return actions

    # ── LLM Enrichment ──────────────────────────────────

    async def _enrich_with_llm(
        self,
        decisions: list[TacticalDecision],
        aggregation: dict[str, Any],
    ) -> list[TacticalDecision]:
        """Add LLM-generated rationale / actions to the top 3 decisions."""
        top_decisions = sorted(decisions, key=lambda d: d.score)[:3]

        for dec in top_decisions:
            try:
                resp = await self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a CFO advisor. Provide a concise "
                                "2-sentence rationale and up to 3 actionable steps."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Decision: {dec.title}\n"
                                f"Category: {dec.category}\n"
                                f"Priority: {dec.priority}\n"
                                f"Score: {dec.score:.3f}\n"
                                f"Current rationale: {dec.rationale}\n"
                                f"Current actions: {'; '.join(dec.actions)}\n"
                                "Improve the rationale and suggest better actions."
                            ),
                        },
                    ],
                    temperature=0.3,
                    max_tokens=300,
                )
                content = resp.choices[0].message.content.strip()
                dec.rationale = f"{dec.rationale}\n\nAI Insight: {content}"
            except Exception as e:
                logger.debug("LLM enrichment skipped for %s: %s", dec.id, e)

        return decisions
