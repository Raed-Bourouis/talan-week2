"""
F360 – Moteur Physique Simulation Parallèle (Parallel Simulation Engine)
Enhanced simulation engine with parallel execution, scenario batching,
and result aggregation. Wraps the core simulation types.
"""
from __future__ import annotations

import logging
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ParallelSimulationEngine:
    """
    Production-grade parallel simulation engine.
    Runs multiple simulation scenarios concurrently for faster results.
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def run(self, simulation_type: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Route to the appropriate simulation function."""
        handlers = {
            "budget_variation": self.simulate_budget_variation,
            "cashflow_projection": self.simulate_cashflow_projection,
            "monte_carlo": self.simulate_monte_carlo,
            "renegotiation": self.simulate_renegotiation_impact,
        }
        handler = handlers.get(simulation_type)
        if not handler:
            raise ValueError(
                f"Unknown simulation type: {simulation_type}. "
                f"Available: {list(handlers.keys())}"
            )
        return handler(parameters)

    def run_parallel(
        self,
        scenarios: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Run multiple simulation scenarios in parallel.
        Each scenario is a dict with 'simulation_type' and 'parameters'.
        """
        results: list[dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {}
            for idx, scenario in enumerate(scenarios):
                future = executor.submit(
                    self.run,
                    scenario["simulation_type"],
                    scenario["parameters"],
                )
                future_to_idx[future] = idx

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    result["scenario_index"] = idx
                    results.append(result)
                except Exception as e:
                    results.append({
                        "scenario_index": idx,
                        "status": "error",
                        "error": str(e),
                    })

        results.sort(key=lambda r: r.get("scenario_index", 0))
        return results

    # ─────────────────────────────────────────────────
    # 1. Budget Variation Simulation
    # ─────────────────────────────────────────────────

    def simulate_budget_variation(self, params: dict[str, Any]) -> dict[str, Any]:
        base_budget = params.get("base_budget", 1_000_000)
        variations = params.get("variation_pct", [-15, -10, -5, 0, 5, 10, 15])
        categories = params.get("categories", ["OPEX", "CAPEX", "HR", "IT", "Marketing"])

        weights = {
            "OPEX": 0.35, "CAPEX": 0.20, "HR": 0.25,
            "IT": 0.12, "Marketing": 0.08,
        }

        scenarios = []
        for var_pct in variations:
            factor = 1 + var_pct / 100
            adjusted_total = base_budget * factor
            breakdown = {}
            for cat in categories:
                w = weights.get(cat, 1 / len(categories))
                breakdown[cat] = {
                    "original": round(base_budget * w, 2),
                    "adjusted": round(adjusted_total * w, 2),
                    "delta": round((adjusted_total - base_budget) * w, 2),
                }
            scenarios.append({
                "variation_pct": var_pct,
                "total_budget": round(adjusted_total, 2),
                "delta": round(adjusted_total - base_budget, 2),
                "breakdown": breakdown,
            })

        return {
            "simulation_type": "budget_variation",
            "base_budget": base_budget,
            "scenarios": scenarios,
            "recommendation": self._budget_recommendation(base_budget, variations),
        }

    def _budget_recommendation(self, base: float, variations: list[float]) -> str:
        max_cut = min(variations)
        return (
            f"A {abs(max_cut)}% budget reduction would save "
            f"€{abs(base * max_cut / 100):,.0f}. "
            f"Consider prioritizing OPEX optimization before CAPEX cuts."
        )

    # ─────────────────────────────────────────────────
    # 2. Cashflow Projection (J+90)
    # ─────────────────────────────────────────────────

    def simulate_cashflow_projection(self, params: dict[str, Any]) -> dict[str, Any]:
        initial = params.get("initial_balance", 500_000)
        avg_in = params.get("daily_avg_inflow", 15_000)
        avg_out = params.get("daily_avg_outflow", 12_000)
        days = params.get("days", 90)
        volatility = params.get("volatility", 0.15)
        pending_in = params.get("pending_inflows", [])
        pending_out = params.get("pending_outflows", [])

        today = date.today()
        projections = []
        balance = initial

        pending_events: dict[int, float] = {}
        for p in pending_in:
            day_offset = p.get("day_offset", 0)
            pending_events[day_offset] = pending_events.get(day_offset, 0) + p.get("amount", 0)
        for p in pending_out:
            day_offset = p.get("day_offset", 0)
            pending_events[day_offset] = pending_events.get(day_offset, 0) - p.get("amount", 0)

        min_balance = initial
        min_balance_day = 0

        for day in range(days):
            current_date = today + timedelta(days=day)
            noise_in = random.gauss(0, avg_in * volatility)
            noise_out = random.gauss(0, avg_out * volatility)
            weekend_factor = 0.1 if current_date.weekday() >= 5 else 1.0

            daily_in = max(0, (avg_in + noise_in) * weekend_factor)
            daily_out = max(0, (avg_out + noise_out) * weekend_factor)

            event = pending_events.get(day, 0)
            if event > 0:
                daily_in += event
            else:
                daily_out += abs(event)

            balance += daily_in - daily_out

            if balance < min_balance:
                min_balance = balance
                min_balance_day = day

            projections.append({
                "day": day,
                "date": str(current_date),
                "inflow": round(daily_in, 2),
                "outflow": round(daily_out, 2),
                "net": round(daily_in - daily_out, 2),
                "balance": round(balance, 2),
            })

        return {
            "simulation_type": "cashflow_projection",
            "initial_balance": initial,
            "final_balance": round(balance, 2),
            "min_balance": round(min_balance, 2),
            "min_balance_day": min_balance_day,
            "days_projected": days,
            "avg_daily_net": round((balance - initial) / days, 2),
            "projections": projections,
            "risk_alert": balance < 0 or min_balance < 0,
        }

    # ─────────────────────────────────────────────────
    # 3. Monte Carlo Risk Simulation
    # ─────────────────────────────────────────────────

    def simulate_monte_carlo(self, params: dict[str, Any]) -> dict[str, Any]:
        base_rev = params.get("base_revenue", 5_000_000)
        base_cost = params.get("base_costs", 4_200_000)
        rev_vol = params.get("revenue_volatility", 0.15)
        cost_vol = params.get("cost_volatility", 0.10)
        n_sims = min(params.get("num_simulations", 10_000), 50_000)
        periods = params.get("periods", 12)

        np.random.seed(42)
        results = []

        for _ in range(n_sims):
            total_profit = 0
            for _ in range(periods):
                rev = base_rev / periods * (1 + np.random.normal(0, rev_vol))
                cost = base_cost / periods * (1 + np.random.normal(0, cost_vol))
                total_profit += rev - cost
            results.append(total_profit)

        results = np.array(results)

        percentiles = {
            "p5": round(float(np.percentile(results, 5)), 2),
            "p10": round(float(np.percentile(results, 10)), 2),
            "p25": round(float(np.percentile(results, 25)), 2),
            "p50_median": round(float(np.percentile(results, 50)), 2),
            "p75": round(float(np.percentile(results, 75)), 2),
            "p90": round(float(np.percentile(results, 90)), 2),
            "p95": round(float(np.percentile(results, 95)), 2),
        }

        hist, bin_edges = np.histogram(results, bins=50)
        histogram = [
            {
                "bin_start": round(float(bin_edges[i]), 2),
                "bin_end": round(float(bin_edges[i + 1]), 2),
                "count": int(hist[i]),
            }
            for i in range(len(hist))
        ]

        prob_loss = float(np.mean(results < 0))
        var_95 = float(np.percentile(results, 5))

        return {
            "simulation_type": "monte_carlo",
            "num_simulations": n_sims,
            "periods": periods,
            "mean_profit": round(float(results.mean()), 2),
            "std_dev": round(float(results.std()), 2),
            "percentiles": percentiles,
            "probability_of_loss": round(prob_loss, 4),
            "value_at_risk_95": round(var_95, 2),
            "histogram": histogram,
            "risk_assessment": (
                "LOW" if prob_loss < 0.05
                else "MODERATE" if prob_loss < 0.15
                else "HIGH" if prob_loss < 0.30
                else "CRITICAL"
            ),
        }

    # ─────────────────────────────────────────────────
    # 4. Contract Renegotiation Impact
    # ─────────────────────────────────────────────────

    def simulate_renegotiation_impact(self, params: dict[str, Any]) -> dict[str, Any]:
        current_cost = params.get("current_annual_cost", 500_000)
        discount = params.get("proposed_discount_pct", 10)
        duration = params.get("contract_duration_years", 3)
        inflation = params.get("inflation_rate", 0.03)
        has_indexation = params.get("has_indexation_clause", True)
        exit_penalty = params.get("penalty_exit_pct", 5)

        current_scenario = []
        total_current = 0
        for year in range(duration):
            annual = current_cost * (1 + inflation) ** year if has_indexation else current_cost
            total_current += annual
            current_scenario.append({
                "year": year + 1,
                "cost": round(annual, 2),
                "cumulative": round(total_current, 2),
            })

        renegotiated_cost = current_cost * (1 - discount / 100)
        renego_scenario = []
        total_renego = 0
        for year in range(duration):
            annual = renegotiated_cost * (1 + inflation) ** year if has_indexation else renegotiated_cost
            total_renego += annual
            renego_scenario.append({
                "year": year + 1,
                "cost": round(annual, 2),
                "cumulative": round(total_renego, 2),
            })

        savings = total_current - total_renego
        exit_cost = current_cost * exit_penalty / 100
        net_savings = savings - exit_cost

        return {
            "simulation_type": "renegotiation",
            "current_annual_cost": current_cost,
            "proposed_discount_pct": discount,
            "duration_years": duration,
            "current_scenario": current_scenario,
            "renegotiated_scenario": renego_scenario,
            "total_current_cost": round(total_current, 2),
            "total_renegotiated_cost": round(total_renego, 2),
            "gross_savings": round(savings, 2),
            "exit_penalty_cost": round(exit_cost, 2),
            "net_savings": round(net_savings, 2),
            "roi_pct": round(net_savings / exit_cost * 100, 1) if exit_cost else None,
            "recommendation": (
                f"Renegotiation yields net savings of €{net_savings:,.0f} "
                f"over {duration} years ({discount}% discount). "
                f"{'Recommended.' if net_savings > 0 else 'Not financially viable.'}"
            ),
        }
