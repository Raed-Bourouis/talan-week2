"""
F360 – Génération de Scénarios IA (AI Scenario Generator)
Uses LLM reasoning and financial context to generate "what-if" scenarios,
sensitivity analyses, and AI-powered strategic recommendations.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings
from app.services.simulation.parallel_engine import ParallelSimulationEngine

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """
    AI-powered scenario generator that creates, evaluates and ranks
    financial scenarios using a combination of LLM reasoning and
    deterministic simulation.
    """

    def __init__(self, engine: ParallelSimulationEngine | None = None):
        self.engine = engine or ParallelSimulationEngine()
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.llm_available = True
        except Exception:
            self.client = None
            self.llm_available = False

    # ─────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────

    async def generate_scenarios(
        self,
        context: dict[str, Any],
        num_scenarios: int = 5,
    ) -> dict[str, Any]:
        """
        Generate a set of AI-powered what-if scenarios based on company context.

        context dict should include keys like:
        - company_name, industry, revenue, costs, budget, headcount
        - recent_events (list of event descriptions)
        - risk_factors (list of known risks)
        """
        if self.llm_available:
            return await self._generate_with_llm(context, num_scenarios)
        return self._generate_rule_based(context, num_scenarios)

    async def sensitivity_analysis(
        self,
        simulation_type: str,
        base_params: dict[str, Any],
        vary_param: str,
        range_pct: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        Run a sensitivity analysis by varying a single parameter
        across a percentage range and observing simulation output changes.
        """
        if range_pct is None:
            range_pct = [-20, -15, -10, -5, 0, 5, 10, 15, 20]

        base_value = base_params.get(vary_param)
        if base_value is None:
            raise ValueError(f"Parameter '{vary_param}' not found in base_params")

        scenarios = []
        for pct in range_pct:
            adjusted = dict(base_params)
            adjusted[vary_param] = base_value * (1 + pct / 100)
            scenarios.append({
                "simulation_type": simulation_type,
                "parameters": adjusted,
            })

        results = self.engine.run_parallel(scenarios)

        sensitivity_data = []
        for i, pct in enumerate(range_pct):
            result = results[i] if i < len(results) else {"status": "missing"}
            sensitivity_data.append({
                "variation_pct": pct,
                "param_value": round(base_value * (1 + pct / 100), 2),
                "result_summary": self._extract_summary(result),
            })

        return {
            "analysis_type": "sensitivity",
            "simulation_type": simulation_type,
            "varied_parameter": vary_param,
            "base_value": base_value,
            "data": sensitivity_data,
            "conclusion": self._sensitivity_conclusion(
                vary_param, sensitivity_data
            ),
        }

    async def compare_strategies(
        self,
        strategies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compare multiple strategic options by simulating each one
        and ranking them based on expected value and risk.
        """
        strategy_results = []
        for strategy in strategies:
            name = strategy.get("name", "Unnamed")
            sim_type = strategy.get("simulation_type", "monte_carlo")
            params = strategy.get("parameters", {})

            result = self.engine.run(sim_type, params)
            score = self._score_strategy(result)

            strategy_results.append({
                "name": name,
                "simulation_type": sim_type,
                "result": result,
                "score": score,
            })

        strategy_results.sort(key=lambda s: s["score"], reverse=True)
        for rank, s in enumerate(strategy_results, 1):
            s["rank"] = rank

        if self.llm_available:
            recommendation = await self._llm_strategy_recommendation(
                strategy_results
            )
        else:
            best = strategy_results[0]["name"]
            recommendation = f"Strategy '{best}' scores highest based on risk-adjusted return."

        return {
            "analysis_type": "strategy_comparison",
            "strategies": strategy_results,
            "recommendation": recommendation,
        }

    # ─────────────────────────────────────────────────
    # LLM-based generation
    # ─────────────────────────────────────────────────

    async def _generate_with_llm(
        self, context: dict[str, Any], n: int
    ) -> dict[str, Any]:
        prompt = self._build_scenario_prompt(context, n)
        try:
            resp = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior financial strategist. "
                            "Generate realistic what-if scenarios in JSON format."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=3000,
            )
            raw = json.loads(resp.choices[0].message.content)
            scenarios = raw.get("scenarios", [])
        except Exception as e:
            logger.warning("LLM scenario generation failed: %s", e)
            return self._generate_rule_based(context, n)

        # Run simulations for each generated scenario
        sim_inputs = []
        for sc in scenarios:
            sim_type = sc.get("simulation_type", "monte_carlo")
            params = sc.get("parameters", {})
            sim_inputs.append({
                "simulation_type": sim_type,
                "parameters": params,
            })

        sim_results = self.engine.run_parallel(sim_inputs) if sim_inputs else []

        for i, sc in enumerate(scenarios):
            if i < len(sim_results):
                sc["simulation_result"] = sim_results[i]

        return {
            "source": "llm",
            "context_summary": self._context_summary(context),
            "scenarios": scenarios,
            "count": len(scenarios),
        }

    def _build_scenario_prompt(self, ctx: dict[str, Any], n: int) -> str:
        lines = [
            f"Company: {ctx.get('company_name', 'N/A')}",
            f"Industry: {ctx.get('industry', 'N/A')}",
            f"Annual Revenue: €{ctx.get('revenue', 0):,.0f}",
            f"Annual Costs: €{ctx.get('costs', 0):,.0f}",
            f"Total Budget: €{ctx.get('budget', 0):,.0f}",
            f"Headcount: {ctx.get('headcount', 0)}",
        ]
        events = ctx.get("recent_events", [])
        if events:
            lines.append(f"Recent Events: {'; '.join(events[:5])}")
        risks = ctx.get("risk_factors", [])
        if risks:
            lines.append(f"Risk Factors: {'; '.join(risks[:5])}")

        lines.append(
            f"\nGenerate exactly {n} what-if scenarios that the CFO should consider."
        )
        lines.append(
            "For each scenario provide: "
            "name, description, probability (0-1), impact_level (LOW/MEDIUM/HIGH/CRITICAL), "
            "simulation_type (one of: budget_variation, cashflow_projection, monte_carlo, renegotiation), "
            "and parameters (matching the simulation type's expected inputs)."
        )
        lines.append('Return JSON: {"scenarios": [...]}')
        return "\n".join(lines)

    # ─────────────────────────────────────────────────
    # Rule-based fallback generation
    # ─────────────────────────────────────────────────

    def _generate_rule_based(
        self, context: dict[str, Any], n: int
    ) -> dict[str, Any]:
        revenue = context.get("revenue", 5_000_000)
        costs = context.get("costs", revenue * 0.82)
        budget = context.get("budget", revenue * 0.2)

        templates = [
            {
                "name": "Revenue Decline",
                "description": "Revenue drops by 15% due to market downturn",
                "probability": 0.20,
                "impact_level": "HIGH",
                "simulation_type": "monte_carlo",
                "parameters": {
                    "base_revenue": revenue * 0.85,
                    "base_costs": costs,
                    "revenue_volatility": 0.20,
                    "cost_volatility": 0.10,
                    "num_simulations": 5000,
                },
            },
            {
                "name": "Cost Optimization",
                "description": "10% reduction in OPEX through process automation",
                "probability": 0.60,
                "impact_level": "MEDIUM",
                "simulation_type": "budget_variation",
                "parameters": {
                    "base_budget": budget,
                    "variation_pct": [-10, -7, -5, -3, 0],
                },
            },
            {
                "name": "Supplier Renegotiation",
                "description": "Renegotiate top supplier contract for better terms",
                "probability": 0.50,
                "impact_level": "MEDIUM",
                "simulation_type": "renegotiation",
                "parameters": {
                    "current_annual_cost": costs * 0.15,
                    "proposed_discount_pct": 12,
                    "contract_duration_years": 3,
                },
            },
            {
                "name": "Cash Crunch",
                "description": "Late receivables cause 30-day cash shortage",
                "probability": 0.15,
                "impact_level": "CRITICAL",
                "simulation_type": "cashflow_projection",
                "parameters": {
                    "initial_balance": budget * 0.5,
                    "daily_avg_inflow": revenue / 365 * 0.5,
                    "daily_avg_outflow": costs / 365,
                    "days": 90,
                    "volatility": 0.25,
                },
            },
            {
                "name": "Growth Investment",
                "description": "Redirect 8% of budget to new market expansion",
                "probability": 0.40,
                "impact_level": "MEDIUM",
                "simulation_type": "monte_carlo",
                "parameters": {
                    "base_revenue": revenue * 1.12,
                    "base_costs": costs * 1.08,
                    "revenue_volatility": 0.25,
                    "cost_volatility": 0.15,
                    "num_simulations": 5000,
                },
            },
        ]

        selected = templates[:n]

        sim_inputs = [
            {"simulation_type": s["simulation_type"], "parameters": s["parameters"]}
            for s in selected
        ]
        sim_results = self.engine.run_parallel(sim_inputs)
        for i, sc in enumerate(selected):
            if i < len(sim_results):
                sc["simulation_result"] = sim_results[i]

        return {
            "source": "rule_based",
            "context_summary": self._context_summary(context),
            "scenarios": selected,
            "count": len(selected),
        }

    # ─────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────

    def _context_summary(self, ctx: dict[str, Any]) -> str:
        return (
            f"{ctx.get('company_name', 'Company')} | "
            f"Revenue €{ctx.get('revenue', 0):,.0f} | "
            f"Costs €{ctx.get('costs', 0):,.0f}"
        )

    def _extract_summary(self, result: dict[str, Any]) -> dict[str, Any]:
        """Extract key metrics from a simulation result for sensitivity data."""
        summary: dict[str, Any] = {}
        for key in [
            "mean_profit", "final_balance", "probability_of_loss",
            "value_at_risk_95", "net_savings", "risk_assessment",
        ]:
            if key in result:
                summary[key] = result[key]
        if not summary:
            summary["raw_keys"] = list(result.keys())
        return summary

    def _sensitivity_conclusion(
        self, param: str, data: list[dict[str, Any]]
    ) -> str:
        values = []
        for d in data:
            s = d.get("result_summary", {})
            v = s.get("mean_profit") or s.get("final_balance") or s.get("net_savings")
            if v is not None:
                values.append((d["variation_pct"], v))
        if len(values) < 2:
            return f"Insufficient data for sensitivity conclusion on {param}."

        elasticity = (values[-1][1] - values[0][1]) / (values[-1][0] - values[0][0])
        direction = "positively" if elasticity > 0 else "negatively"
        return (
            f"A 1% change in {param} results in approximately "
            f"€{abs(elasticity):,.0f} change in outcome ({direction} correlated). "
            f"{'High' if abs(elasticity) > 10000 else 'Moderate'} sensitivity detected."
        )

    def _score_strategy(self, result: dict[str, Any]) -> float:
        """Score a simulation result for strategy ranking (higher = better)."""
        score = 50.0
        if "mean_profit" in result:
            score += result["mean_profit"] / 100_000
        if "probability_of_loss" in result:
            score -= result["probability_of_loss"] * 100
        if "net_savings" in result:
            score += result["net_savings"] / 50_000
        if "risk_assessment" in result:
            risk_map = {"LOW": 20, "MODERATE": 10, "HIGH": -10, "CRITICAL": -30}
            score += risk_map.get(result["risk_assessment"], 0)
        if "final_balance" in result:
            if result["final_balance"] > 0:
                score += 10
            else:
                score -= 20
        return round(score, 2)

    async def _llm_strategy_recommendation(
        self, strategies: list[dict[str, Any]]
    ) -> str:
        summary = "\n".join(
            f"{s['rank']}. {s['name']} (score={s['score']})"
            for s in strategies
        )
        try:
            resp = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CFO advisor. Give a concise recommendation.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Rank and recommend among these strategies:\n{summary}\n"
                            "Provide a 2-3 sentence recommendation."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return f"Strategy '{strategies[0]['name']}' ranks highest."
