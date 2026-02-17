"""
F360 – Dashboard Tactique (Tactical Dashboard Data Provider)
Aggregates data from all upstream layers into structured payloads
ready for the frontend tactical dashboard.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TacticalDashboard:
    """
    Provides pre-aggregated data required by the frontend dashboard:
    - KPI cards (revenue, expenses, cash position, risk score)
    - Trend charts (30/60/90-day)
    - Alert feed
    - Decision queue
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_full_dashboard(self) -> dict[str, Any]:
        """Return complete dashboard payload in one call."""
        kpis = await self.get_kpis()
        alerts = await self.get_alerts()
        budget_usage = await self.get_budget_usage()
        cashflow_trend = await self.get_cashflow_trend()
        contract_summary = await self.get_contract_summary()

        return {
            "kpis": kpis,
            "alerts": alerts,
            "budget_usage": budget_usage,
            "cashflow_trend": cashflow_trend,
            "contract_summary": contract_summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── KPIs ────────────────────────────────────────────

    async def get_kpis(self) -> dict[str, Any]:
        try:
            # Budget KPIs
            budget_q = await self.db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(amount), 0) AS total_budget,
                        COALESCE(SUM(CASE WHEN category = 'OPEX' THEN amount END), 0) AS opex,
                        COALESCE(SUM(CASE WHEN category = 'CAPEX' THEN amount END), 0) AS capex,
                        COUNT(*) AS line_count
                    FROM budget_lines
                    WHERE fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)
                """)
            )
            budget = budget_q.mappings().first() or {}

            # Cashflow KPIs
            cf_q = await self.db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(CASE WHEN direction = 'IN' THEN amount END), 0) AS total_in,
                        COALESCE(SUM(CASE WHEN direction = 'OUT' THEN amount END), 0) AS total_out,
                        COUNT(*) AS tx_count
                    FROM cashflow_entries
                    WHERE entry_date >= CURRENT_DATE - INTERVAL '30 days'
                """)
            )
            cf = cf_q.mappings().first() or {}

            # Contract KPIs
            ct_q = await self.db.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_contracts,
                        COALESCE(SUM(annual_value), 0) AS total_value,
                        COUNT(CASE WHEN end_date < CURRENT_DATE + INTERVAL '90 days' THEN 1 END) AS expiring_soon
                    FROM contracts
                """)
            )
            ct = ct_q.mappings().first() or {}

            return {
                "budget": {
                    "total": float(budget.get("total_budget", 0)),
                    "opex": float(budget.get("opex", 0)),
                    "capex": float(budget.get("capex", 0)),
                    "lines": int(budget.get("line_count", 0)),
                },
                "cashflow_30d": {
                    "inflow": float(cf.get("total_in", 0)),
                    "outflow": float(cf.get("total_out", 0)),
                    "net": float(cf.get("total_in", 0)) - float(cf.get("total_out", 0)),
                    "transactions": int(cf.get("tx_count", 0)),
                },
                "contracts": {
                    "total": int(ct.get("total_contracts", 0)),
                    "annual_value": float(ct.get("total_value", 0)),
                    "expiring_90d": int(ct.get("expiring_soon", 0)),
                },
            }
        except Exception as e:
            logger.warning("KPI query failed (tables may not exist yet): %s", e)
            return self._empty_kpis()

    def _empty_kpis(self) -> dict[str, Any]:
        return {
            "budget": {"total": 0, "opex": 0, "capex": 0, "lines": 0},
            "cashflow_30d": {"inflow": 0, "outflow": 0, "net": 0, "transactions": 0},
            "contracts": {"total": 0, "annual_value": 0, "expiring_90d": 0},
        }

    # ── Alerts ──────────────────────────────────────────

    async def get_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        try:
            q = await self.db.execute(
                text("""
                    SELECT id, alert_type, severity, message, created_at, resolved
                    FROM alerts
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            rows = q.mappings().all()
            return [
                {
                    "id": str(r["id"]),
                    "type": r["alert_type"],
                    "severity": r["severity"],
                    "message": r["message"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "resolved": bool(r["resolved"]),
                }
                for r in rows
            ]
        except Exception:
            return []

    # ── Budget Usage ────────────────────────────────────

    async def get_budget_usage(self) -> list[dict[str, Any]]:
        try:
            q = await self.db.execute(
                text("""
                    SELECT category,
                           COALESCE(SUM(amount), 0) AS allocated,
                           COALESCE(SUM(spent), 0) AS spent
                    FROM budget_lines
                    WHERE fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)
                    GROUP BY category
                    ORDER BY allocated DESC
                """)
            )
            rows = q.mappings().all()
            return [
                {
                    "category": r["category"],
                    "allocated": float(r["allocated"]),
                    "spent": float(r["spent"]),
                    "usage_pct": round(
                        float(r["spent"]) / float(r["allocated"]) * 100, 1
                    ) if float(r["allocated"]) else 0,
                }
                for r in rows
            ]
        except Exception:
            return []

    # ── Cashflow Trend ──────────────────────────────────

    async def get_cashflow_trend(self, days: int = 90) -> list[dict[str, Any]]:
        try:
            q = await self.db.execute(
                text("""
                    SELECT entry_date,
                           SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END) AS inflow,
                           SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END) AS outflow
                    FROM cashflow_entries
                    WHERE entry_date >= CURRENT_DATE - INTERVAL ':days days'
                    GROUP BY entry_date
                    ORDER BY entry_date
                """),
                {"days": days},
            )
            rows = q.mappings().all()
            running = 0.0
            trend = []
            for r in rows:
                net = float(r["inflow"]) - float(r["outflow"])
                running += net
                trend.append({
                    "date": r["entry_date"].isoformat() if r["entry_date"] else None,
                    "inflow": float(r["inflow"]),
                    "outflow": float(r["outflow"]),
                    "net": round(net, 2),
                    "cumulative": round(running, 2),
                })
            return trend
        except Exception:
            return []

    # ── Contracts ───────────────────────────────────────

    async def get_contract_summary(self) -> list[dict[str, Any]]:
        try:
            q = await self.db.execute(
                text("""
                    SELECT id, vendor_name, annual_value, start_date, end_date, status
                    FROM contracts
                    ORDER BY annual_value DESC
                    LIMIT 10
                """)
            )
            rows = q.mappings().all()
            return [
                {
                    "id": str(r["id"]),
                    "vendor": r["vendor_name"],
                    "annual_value": float(r["annual_value"]),
                    "start": r["start_date"].isoformat() if r["start_date"] else None,
                    "end": r["end_date"].isoformat() if r["end_date"] else None,
                    "status": r["status"],
                }
                for r in rows
            ]
        except Exception:
            return []
