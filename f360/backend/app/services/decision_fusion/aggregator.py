"""
F360 – Agrégation Multi-sources (Multi-Source Aggregator)
Collects, normalises and fuses signals from every upstream layer
(simulation, feedback, RAG, graph, real-time) into a single
weighted score per decision topic.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ── Signal dataclass ────────────────────────────────────────────

class Signal:
    """One piece of evidence produced by any upstream layer."""

    __slots__ = (
        "source", "topic", "value", "confidence",
        "direction", "timestamp", "metadata",
    )

    def __init__(
        self,
        source: str,
        topic: str,
        value: float,
        confidence: float = 1.0,
        direction: str = "neutral",
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.source = source          # e.g. "simulation", "feedback", "rag"
        self.topic = topic            # e.g. "budget_cut", "supplier_risk"
        self.value = value            # numeric intensity (-1 … +1 normalised)
        self.confidence = max(0.0, min(1.0, confidence))
        self.direction = direction    # "positive", "negative", "neutral"
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "topic": self.topic,
            "value": self.value,
            "confidence": self.confidence,
            "direction": self.direction,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


# ── Aggregator ──────────────────────────────────────────────────

class MultiSourceAggregator:
    """
    Fuses heterogeneous signals into aggregated decision scores.

    Supports:
    - Confidence-weighted averaging
    - Time-decay weighting (recent signals matter more)
    - Source-priority weighting (configurable per use-case)
    - Conflict detection between opposing signals
    """

    DEFAULT_SOURCE_WEIGHTS: dict[str, float] = {
        "simulation": 0.25,
        "feedback": 0.20,
        "rag": 0.20,
        "graph": 0.15,
        "realtime": 0.10,
        "manual": 0.10,
    }

    def __init__(
        self,
        source_weights: dict[str, float] | None = None,
        decay_half_life_hours: float = 48.0,
    ):
        self.source_weights = source_weights or self.DEFAULT_SOURCE_WEIGHTS
        self.decay_half_life = decay_half_life_hours
        self._buffer: list[Signal] = []

    # ── Ingest ──────────────────────────────────────────

    def add_signal(self, signal: Signal) -> None:
        self._buffer.append(signal)

    def add_signals(self, signals: list[Signal]) -> None:
        self._buffer.extend(signals)

    def clear(self) -> None:
        self._buffer.clear()

    # ── Aggregate ───────────────────────────────────────

    def aggregate(
        self,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate all buffered signals (optionally filtered by topic).
        Returns per-topic scores and an overall summary.
        """
        signals = self._buffer
        if topic:
            signals = [s for s in signals if s.topic == topic]

        if not signals:
            return {"topics": {}, "overall_score": 0, "signal_count": 0}

        # Group by topic
        by_topic: dict[str, list[Signal]] = {}
        for s in signals:
            by_topic.setdefault(s.topic, []).append(s)

        topic_scores: dict[str, dict[str, Any]] = {}
        for t, sigs in by_topic.items():
            topic_scores[t] = self._aggregate_topic(sigs)

        # Overall score = weighted mean of topic scores
        total_w = 0.0
        total_v = 0.0
        for t, info in topic_scores.items():
            w = info["total_weight"]
            total_w += w
            total_v += info["score"] * w

        overall = total_v / total_w if total_w else 0.0

        return {
            "topics": topic_scores,
            "overall_score": round(overall, 4),
            "signal_count": len(signals),
            "conflicts": self._detect_conflicts(by_topic),
        }

    def _aggregate_topic(self, signals: list[Signal]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        weighted_sum = 0.0
        weight_total = 0.0

        for s in signals:
            sw = self.source_weights.get(s.source, 0.05)
            tw = self._time_weight(s.timestamp, now)
            w = s.confidence * sw * tw
            weighted_sum += s.value * w
            weight_total += w

        score = weighted_sum / weight_total if weight_total else 0.0

        directions = [s.direction for s in signals]
        positive = directions.count("positive")
        negative = directions.count("negative")
        consensus = (
            "positive" if positive > negative * 2
            else "negative" if negative > positive * 2
            else "mixed"
        )

        return {
            "score": round(score, 4),
            "total_weight": round(weight_total, 4),
            "signal_count": len(signals),
            "consensus": consensus,
            "sources": list({s.source for s in signals}),
            "avg_confidence": round(
                sum(s.confidence for s in signals) / len(signals), 3
            ),
        }

    # ── Conflict Detection ──────────────────────────────

    def _detect_conflicts(
        self, by_topic: dict[str, list[Signal]]
    ) -> list[dict[str, Any]]:
        """Detect topics where sources disagree strongly."""
        conflicts = []
        for topic, sigs in by_topic.items():
            pos = [s for s in sigs if s.direction == "positive"]
            neg = [s for s in sigs if s.direction == "negative"]
            if pos and neg:
                avg_pos = sum(s.confidence for s in pos) / len(pos)
                avg_neg = sum(s.confidence for s in neg) / len(neg)
                if avg_pos > 0.5 and avg_neg > 0.5:
                    conflicts.append({
                        "topic": topic,
                        "positive_sources": [s.source for s in pos],
                        "negative_sources": [s.source for s in neg],
                        "severity": "HIGH" if min(avg_pos, avg_neg) > 0.7 else "MODERATE",
                    })
        return conflicts

    # ── Time Decay ──────────────────────────────────────

    def _time_weight(self, ts: datetime, now: datetime) -> float:
        age_hours = (now - ts).total_seconds() / 3600
        if age_hours < 0:
            age_hours = 0
        return math.exp(-0.693 * age_hours / self.decay_half_life)  # ln(2) ≈ 0.693


# ── Convenience builder ────────────────────────────────────────

def build_signal_from_gap(gap: dict[str, Any]) -> Signal:
    """Convert a GapResult dict (from gap_calculator) into an aggregator Signal."""
    severity = gap.get("severity", "low")
    sev_map = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
    value = -sev_map.get(severity, 0.3)  # gaps are negative signals
    return Signal(
        source="feedback",
        topic=gap.get("category", "unknown"),
        value=value,
        confidence=0.9,
        direction="negative" if value < 0 else "neutral",
        metadata=gap,
    )


def build_signal_from_simulation(result: dict[str, Any]) -> Signal:
    """Convert a simulation result dict into an aggregator Signal."""
    risk = result.get("risk_assessment", "MODERATE")
    risk_map = {"LOW": 0.6, "MODERATE": 0.2, "HIGH": -0.3, "CRITICAL": -0.8}
    value = risk_map.get(risk, 0.0)
    return Signal(
        source="simulation",
        topic=result.get("simulation_type", "unknown"),
        value=value,
        confidence=0.85,
        direction="positive" if value > 0 else "negative",
        metadata={"risk_assessment": risk},
    )
