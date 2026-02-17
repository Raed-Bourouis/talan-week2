"""
F360 – IoT & Logs Ingestion
Collects and normalizes data from IoT sensors and application logs
for financial monitoring (energy costs, equipment utilization, audit trails).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# IoT EVENT SCHEMA
# ═══════════════════════════════════════════════════════════════

class IoTEvent:
    """Normalized IoT event structure."""

    def __init__(
        self,
        device_id: str,
        event_type: str,
        value: float | str,
        unit: str = "",
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.device_id = device_id
        self.event_type = event_type
        self.value = value
        self.unit = unit
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "event_type": self.event_type,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Convert to text for vectorization."""
        return (
            f"IoT Event [{self.event_type}] from device {self.device_id}: "
            f"{self.value} {self.unit} at {self.timestamp.isoformat()}. "
            f"Context: {json.dumps(self.metadata)}"
        )


# ═══════════════════════════════════════════════════════════════
# LOG EVENT SCHEMA
# ═══════════════════════════════════════════════════════════════

class LogEvent:
    """Normalized log event for audit trail and anomaly detection."""

    def __init__(
        self,
        source: str,
        level: str,
        message: str,
        user_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        timestamp: datetime | None = None,
        extra: dict[str, Any] | None = None,
    ):
        self.source = source
        self.level = level  # INFO, WARNING, ERROR, CRITICAL
        self.message = message
        self.user_id = user_id
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "level": self.level,
            "message": self.message,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "extra": self.extra,
        }

    def to_text(self) -> str:
        return (
            f"[{self.level}] {self.source}: {self.message}. "
            f"Action: {self.action or 'N/A'}, Entity: {self.entity_type}:{self.entity_id}. "
            f"User: {self.user_id or 'system'}. {self.timestamp.isoformat()}"
        )


# ═══════════════════════════════════════════════════════════════
# IoT / LOG COLLECTOR
# ═══════════════════════════════════════════════════════════════

class IoTLogCollector:
    """
    Collects, normalizes and buffers IoT events and logs.
    Financial use cases:
    - Energy consumption → OPEX cost estimation
    - Equipment uptime → maintenance budget impact
    - Audit logs → compliance and anomaly detection
    """

    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self._iot_buffer: list[IoTEvent] = []
        self._log_buffer: list[LogEvent] = []

    def ingest_iot(self, raw: dict[str, Any]) -> IoTEvent:
        """Parse raw IoT payload and buffer the event."""
        event = IoTEvent(
            device_id=raw.get("device_id", "unknown"),
            event_type=raw.get("type", raw.get("event_type", "measurement")),
            value=raw.get("value", 0),
            unit=raw.get("unit", ""),
            metadata=raw.get("metadata", {}),
        )
        self._iot_buffer.append(event)

        if len(self._iot_buffer) >= self.buffer_size:
            logger.info(f"IoT buffer full ({self.buffer_size}), ready to flush")

        return event

    def ingest_log(self, raw: dict[str, Any]) -> LogEvent:
        """Parse raw log payload and buffer the event."""
        event = LogEvent(
            source=raw.get("source", "unknown"),
            level=raw.get("level", "INFO"),
            message=raw.get("message", ""),
            user_id=raw.get("user_id"),
            action=raw.get("action"),
            entity_type=raw.get("entity_type"),
            entity_id=raw.get("entity_id"),
            extra=raw.get("extra", {}),
        )
        self._log_buffer.append(event)
        return event

    def flush_iot(self) -> list[IoTEvent]:
        """Return and clear the IoT event buffer."""
        events = self._iot_buffer.copy()
        self._iot_buffer.clear()
        return events

    def flush_logs(self) -> list[LogEvent]:
        """Return and clear the log event buffer."""
        events = self._log_buffer.copy()
        self._log_buffer.clear()
        return events

    def get_iot_text_batch(self) -> str:
        """Convert buffered IoT events to text for vectorization."""
        return "\n".join(e.to_text() for e in self._iot_buffer)

    def get_log_text_batch(self) -> str:
        """Convert buffered log events to text for vectorization."""
        return "\n".join(e.to_text() for e in self._log_buffer)

    def detect_anomalies(self) -> list[dict[str, Any]]:
        """
        Simple anomaly detection on buffered IoT events.
        Flags events with values > 2 standard deviations from mean.
        """
        import statistics

        if len(self._iot_buffer) < 10:
            return []

        numeric_events = [e for e in self._iot_buffer if isinstance(e.value, (int, float))]
        if len(numeric_events) < 10:
            return []

        values = [e.value for e in numeric_events]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)

        anomalies = []
        for event in numeric_events:
            if abs(event.value - mean) > 2 * stdev:
                anomalies.append({
                    "event": event.to_dict(),
                    "mean": round(mean, 2),
                    "stdev": round(stdev, 2),
                    "deviation": round(abs(event.value - mean) / stdev, 2),
                    "type": "anomaly",
                })

        return anomalies
