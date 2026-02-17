"""
F360 – Corrélation d'Indices Faibles (Weak Signal Correlation Engine)
Detects faint, early-warning signals from heterogeneous data sources
(cashflow anomalies, contract expirations, budget drift, RAG insights)
and correlates them to surface emerging risks or opportunities.
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


class WeakSignal:
    """A single faint indicator that may become significant when correlated."""

    __slots__ = (
        "source", "category", "description", "strength",
        "timestamp", "metadata",
    )

    def __init__(
        self,
        source: str,
        category: str,
        description: str,
        strength: float = 0.3,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.source = source            # e.g. "cashflow", "contract", "rag"
        self.category = category        # e.g. "liquidity", "vendor_risk"
        self.description = description
        self.strength = max(0.0, min(1.0, strength))  # 0 = barely noticeable
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "category": self.category,
            "description": self.description,
            "strength": round(self.strength, 3),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class Correlation:
    """A detected correlation between multiple weak signals."""

    def __init__(
        self,
        signals: list[WeakSignal],
        combined_strength: float,
        narrative: str,
        risk_type: str,
    ):
        self.signals = signals
        self.combined_strength = combined_strength
        self.narrative = narrative
        self.risk_type = risk_type  # "emerging_risk" | "emerging_opportunity" | "monitoring"
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_type": self.risk_type,
            "combined_strength": round(self.combined_strength, 3),
            "narrative": self.narrative,
            "signal_count": len(self.signals),
            "signals": [s.to_dict() for s in self.signals],
            "created_at": self.created_at.isoformat(),
        }


class WeakSignalCorrelator:
    """
    Collects weak signals over time, detects patterns and surfaces
    correlations that individually might go unnoticed.

    Detection strategies:
    1. Category clustering – many signals in the same category
    2. Temporal clustering – multiple signals within a narrow window
    3. Cross-source convergence – independent sources flagging the same area
    4. Trend detection – strength increasing over time
    """

    CATEGORY_THRESHOLD = 3   # min signals in same category to trigger
    TIME_WINDOW_HOURS = 72   # temporal clustering window
    STRENGTH_FLOOR = 0.15    # ignore extremely faint signals

    def __init__(self):
        self._signals: list[WeakSignal] = []

    # ── Ingest ──────────────────────────────────────────

    def add_signal(self, signal: WeakSignal) -> None:
        if signal.strength >= self.STRENGTH_FLOOR:
            self._signals.append(signal)

    def add_signals(self, signals: list[WeakSignal]) -> None:
        for s in signals:
            self.add_signal(s)

    def clear(self) -> None:
        self._signals.clear()

    @property
    def signal_count(self) -> int:
        return len(self._signals)

    # ── Detection ───────────────────────────────────────

    def detect_correlations(self) -> list[Correlation]:
        """Run all detection strategies and return discovered correlations."""
        results: list[Correlation] = []
        results.extend(self._cluster_by_category())
        results.extend(self._cluster_by_time())
        results.extend(self._cross_source_convergence())
        results.extend(self._trend_detection())

        # Deduplicate by narrative
        seen: set[str] = set()
        unique = []
        for c in results:
            key = c.narrative[:80]
            if key not in seen:
                seen.add(key)
                unique.append(c)

        unique.sort(key=lambda c: c.combined_strength, reverse=True)
        return unique

    # ── Strategy 1: Category Clustering ─────────────────

    def _cluster_by_category(self) -> list[Correlation]:
        by_cat: dict[str, list[WeakSignal]] = defaultdict(list)
        for s in self._signals:
            by_cat[s.category].append(s)

        correlations = []
        for cat, signals in by_cat.items():
            if len(signals) >= self.CATEGORY_THRESHOLD:
                combined = self._combine_strength(signals)
                correlations.append(Correlation(
                    signals=signals,
                    combined_strength=combined,
                    narrative=(
                        f"{len(signals)} weak signals detected in category '{cat}' "
                        f"from sources: {', '.join({s.source for s in signals})}. "
                        f"Combined strength {combined:.2f} suggests an emerging pattern."
                    ),
                    risk_type=self._classify_risk(combined),
                ))
        return correlations

    # ── Strategy 2: Temporal Clustering ─────────────────

    def _cluster_by_time(self) -> list[Correlation]:
        if len(self._signals) < 2:
            return []

        window = timedelta(hours=self.TIME_WINDOW_HOURS)
        sorted_sigs = sorted(self._signals, key=lambda s: s.timestamp)
        correlations = []

        i = 0
        while i < len(sorted_sigs):
            cluster = [sorted_sigs[i]]
            j = i + 1
            while j < len(sorted_sigs) and (sorted_sigs[j].timestamp - sorted_sigs[i].timestamp) <= window:
                cluster.append(sorted_sigs[j])
                j += 1

            if len(cluster) >= self.CATEGORY_THRESHOLD:
                combined = self._combine_strength(cluster)
                start = cluster[0].timestamp.strftime("%Y-%m-%d %H:%M")
                end = cluster[-1].timestamp.strftime("%Y-%m-%d %H:%M")
                correlations.append(Correlation(
                    signals=cluster,
                    combined_strength=combined,
                    narrative=(
                        f"Burst of {len(cluster)} weak signals between {start} and {end}. "
                        f"Categories: {', '.join({s.category for s in cluster})}."
                    ),
                    risk_type=self._classify_risk(combined),
                ))

            i = j if j > i + 1 else i + 1

        return correlations

    # ── Strategy 3: Cross-Source Convergence ────────────

    def _cross_source_convergence(self) -> list[Correlation]:
        # Group by category, then check for multiple distinct sources
        by_cat: dict[str, list[WeakSignal]] = defaultdict(list)
        for s in self._signals:
            by_cat[s.category].append(s)

        correlations = []
        for cat, signals in by_cat.items():
            sources = {s.source for s in signals}
            if len(sources) >= 2:
                combined = self._combine_strength(signals)
                correlations.append(Correlation(
                    signals=signals,
                    combined_strength=combined * 1.2,  # boost for cross-source
                    narrative=(
                        f"Cross-source convergence in '{cat}': "
                        f"{len(sources)} independent sources ({', '.join(sources)}) "
                        f"flagging the same area. High credibility."
                    ),
                    risk_type=self._classify_risk(combined * 1.2),
                ))
        return correlations

    # ── Strategy 4: Trend Detection ────────────────────

    def _trend_detection(self) -> list[Correlation]:
        by_cat: dict[str, list[WeakSignal]] = defaultdict(list)
        for s in self._signals:
            by_cat[s.category].append(s)

        correlations = []
        for cat, signals in by_cat.items():
            if len(signals) < 3:
                continue

            sorted_sigs = sorted(signals, key=lambda s: s.timestamp)
            strengths = [s.strength for s in sorted_sigs]

            # Check if strength is monotonically increasing (allowing 1 dip)
            increases = sum(1 for i in range(1, len(strengths)) if strengths[i] > strengths[i - 1])
            if increases >= len(strengths) * 0.6:
                trend_rate = (strengths[-1] - strengths[0]) / max(len(strengths) - 1, 1)
                combined = min(1.0, strengths[-1] + trend_rate * 3)
                correlations.append(Correlation(
                    signals=sorted_sigs,
                    combined_strength=combined,
                    narrative=(
                        f"Escalating trend detected in '{cat}': "
                        f"strength rising from {strengths[0]:.2f} to {strengths[-1]:.2f} "
                        f"over {len(signals)} observations. "
                        f"Projected to reach significant level soon."
                    ),
                    risk_type="emerging_risk" if strengths[-1] > 0.4 else "monitoring",
                ))
        return correlations

    # ── Helpers ─────────────────────────────────────────

    def _combine_strength(self, signals: list[WeakSignal]) -> float:
        """
        Combine independent signal strengths using probability union:
        P(A or B) = 1 - (1-P(A))(1-P(B))
        """
        prob_none = 1.0
        for s in signals:
            prob_none *= (1.0 - s.strength)
        return min(1.0, 1.0 - prob_none)

    def _classify_risk(self, strength: float) -> str:
        if strength >= 0.7:
            return "emerging_risk"
        elif strength >= 0.4:
            return "monitoring"
        else:
            return "emerging_opportunity"


# ── Convenience builders ───────────────────────────────────────

def signal_from_cashflow_anomaly(
    description: str,
    deviation_pct: float,
    **metadata: Any,
) -> WeakSignal:
    return WeakSignal(
        source="cashflow",
        category="liquidity",
        description=description,
        strength=min(1.0, abs(deviation_pct) / 50),
        metadata=metadata,
    )


def signal_from_contract_expiry(
    vendor: str, days_until_expiry: int, value: float
) -> WeakSignal:
    urgency = max(0.1, 1.0 - days_until_expiry / 365)
    return WeakSignal(
        source="contract",
        category="vendor_risk",
        description=f"Contract with {vendor} expires in {days_until_expiry} days (€{value:,.0f}/yr)",
        strength=urgency,
        metadata={"vendor": vendor, "days": days_until_expiry, "value": value},
    )


def signal_from_budget_drift(
    category: str, drift_pct: float
) -> WeakSignal:
    return WeakSignal(
        source="budget",
        category="budget_drift",
        description=f"{category} budget drifting by {drift_pct:+.1f}%",
        strength=min(1.0, abs(drift_pct) / 30),
        metadata={"budget_category": category, "drift_pct": drift_pct},
    )


def signal_from_rag_insight(
    insight: str, confidence: float = 0.5
) -> WeakSignal:
    return WeakSignal(
        source="rag",
        category="intelligence",
        description=insight,
        strength=confidence * 0.6,  # RAG insights start as weak
        metadata={"raw_confidence": confidence},
    )
