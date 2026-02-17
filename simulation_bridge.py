"""
Simulation Bridge (Personne 4)

Bridges the keyword_search + graph_peers results into the
F360 decision fusion engine by generating scenario simulations
on-the-fly for any company found by the assistant.

Provides:
- Auto-generate ScenarioSimulation objects from company profiles
- Run the multi-strategy fusion engine (Weighted / DST / Bayesian)
- Return a human-readable simulation summary
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from keyword_search import Company
from graph_peers import GraphEnrichment, PeerInfo, RelationType
from f360_synthesis_engine import (
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation,
)
from multi_strategy_engine import (
    MultiStrategyEngine,
    MetaFusionResult,
    FusionStrategy,
)


@dataclass
class SimulationRequest:
    """Request to simulate decision fusion for a company."""
    company: Company
    graph_enrichment: Optional[GraphEnrichment] = None
    custom_scenarios: Optional[List[ScenarioSimulation]] = None


@dataclass
class SimulationSummary:
    """Human-readable simulation output."""
    company_name: str
    company_id: str
    recommended_action: str
    priority: str
    confidence: float
    agreement_level: float
    strategy_breakdown: Dict[str, str]
    weak_signals: List[str]
    predicted_outcome: Dict[str, Any]
    full_explanation: str

    def to_text(self) -> str:
        """Format as readable text block."""
        lines = [
            f"══════ SIMULATION RESULTS: {self.company_name} ══════",
            f"",
            f"  Priority:           {self.priority}",
            f"  Recommended Action: {self.recommended_action}",
            f"  Confidence:         {self.confidence:.1%}",
            f"  Strategy Agreement: {self.agreement_level:.0%}",
            f"",
            f"  Strategy Breakdown:",
        ]
        for strat, rec in self.strategy_breakdown.items():
            lines.append(f"    • {strat}: {rec}")

        if self.weak_signals:
            lines.append(f"")
            lines.append(f"  Weak Signals Detected:")
            for ws in self.weak_signals:
                lines.append(f"    ⚠ {ws}")

        lines.append(f"")
        lines.append(f"  Predicted Outcome:")
        for k, v in self.predicted_outcome.items():
            lines.append(f"    • {k}: {v}")

        lines.append(f"")
        lines.append(f"  Explanation:")
        # Wrap explanation lines
        for part in self.full_explanation.split("\n\n"):
            lines.append(f"    {part.strip()}")

        lines.append(f"{'═' * (30 + len(self.company_name))}")
        return "\n".join(lines)


class SimulationBridge:
    """
    Creates scenario simulations from company data and runs
    the multi-strategy decision fusion engine.
    """

    def __init__(self, risk_weight: float = 0.6, profitability_weight: float = 0.4):
        self.engine = MultiStrategyEngine(
            risk_weight=risk_weight,
            profitability_weight=profitability_weight,
        )

    def simulate(self, request: SimulationRequest) -> SimulationSummary:
        """
        Run full decision fusion simulation for a company.
        
        1. Generate financial data from company profile
        2. Generate knowledge graph context from enrichment
        3. Generate scenarios (or use custom ones)
        4. Run multi-strategy fusion
        5. Return SimulationSummary
        """
        company = request.company
        enrichment = request.graph_enrichment

        # ---- Step 1: Generate FinancialData ----
        financial_data = self._generate_financial_data(company, enrichment)

        # ---- Step 2: Generate KnowledgeGraphContext ----
        kg_context = self._generate_kg_context(company, enrichment)

        # ---- Step 3: Generate Scenarios ----
        if request.custom_scenarios:
            scenarios = request.custom_scenarios
        else:
            scenarios = self._generate_scenarios(company, enrichment)

        # ---- Step 4: Run Multi-strategy fusion ----
        result: MetaFusionResult = self.engine.synthesize(
            financial_data, kg_context, scenarios
        )

        # ---- Step 5: Build summary ----
        return self._build_summary(company, result)

    # ---- Generation helpers ----------------------------------------

    def _generate_financial_data(self, company: Company,
                                  enrichment: Optional[GraphEnrichment]) -> FinancialData:
        """
        Generate synthetic financial data from a company profile.
        In production, this would pull live ERP data.
        """
        # Map risk level to invoice spike
        risk_to_spike = {
            "low": 2.0, "medium": 8.0, "high": 15.0, "critical": 25.0,
        }
        spike = risk_to_spike.get(company.risk_level, 8.0)

        # Map status to production change
        status_to_prod = {
            "active": -2.0, "watchlist": -8.0,
            "restructuring": -15.0, "default": -25.0,
        }
        prod_change = status_to_prod.get(company.status, -5.0)

        # Budget remaining based on risk
        risk_to_budget = {
            "low": 45.0, "medium": 25.0, "high": 10.0, "critical": 3.0,
        }
        budget = risk_to_budget.get(company.risk_level, 25.0)

        # If graph shows contagion, worsen numbers
        if enrichment and enrichment.risk_contagion_score > 0.5:
            spike *= 1.3
            prod_change *= 1.2
            budget *= 0.7

        return FinancialData(
            unpaid_invoices_spike=round(spike, 1),
            client_id=company.company_id,
            production_output_change=round(prod_change, 1),
            budget_remaining_q3=round(budget, 1),
        )

    def _generate_kg_context(self, company: Company,
                              enrichment: Optional[GraphEnrichment]) -> KnowledgeGraphContext:
        """Generate KG context from company + graph enrichment."""
        parent_status = "Stable operations"
        historical_pattern = None
        risk_indicators: List[str] = []

        if company.status == "restructuring":
            parent_status = "Undergoing restructuring"
            historical_pattern = {"years_ago": 2, "cash_flow_delay_days": 45}
        elif company.status == "watchlist":
            parent_status = "Under financial surveillance"
            historical_pattern = {"years_ago": 1, "cash_flow_delay_days": 20}

        if company.parent_company:
            parent_status += f" (parent: {company.parent_company})"

        if enrichment:
            for peer in enrichment.peers:
                if peer.risk_level in ("high", "critical"):
                    risk_indicators.append(
                        f"Peer {peer.company_name} at {peer.risk_level} risk"
                    )
            if enrichment.supply_chain_risk == "high":
                risk_indicators.append("Supply chain risk elevated")

        return KnowledgeGraphContext(
            client_parent_status=parent_status,
            similar_historical_pattern=historical_pattern,
            risk_indicators=risk_indicators,
        )

    def _generate_scenarios(self, company: Company,
                            enrichment: Optional[GraphEnrichment]) -> List[ScenarioSimulation]:
        """
        Generate 3 standard scenarios based on company risk profile.
        """
        risk_multiplier = {
            "low": 0.3, "medium": 0.6, "high": 1.0, "critical": 1.5,
        }.get(company.risk_level, 0.6)

        scenarios = [
            ScenarioSimulation(
                scenario_id="SCENARIO_A",
                description="Business as usual (no intervention)",
                cash_flow_impact=round(-20.0 * risk_multiplier, 1),
                margin_impact=0.0,
                probability=0.85,
                time_horizon_days=60,
            ),
            ScenarioSimulation(
                scenario_id="SCENARIO_B",
                description="Early payment discount to reduce exposure",
                cash_flow_impact=round(-3.0 * risk_multiplier, 1),
                margin_impact=round(-5.0 * risk_multiplier, 1),
                probability=0.90,
                time_horizon_days=30,
            ),
            ScenarioSimulation(
                scenario_id="SCENARIO_C",
                description="Payment renegotiation with extended terms",
                cash_flow_impact=round(-10.0 * risk_multiplier, 1),
                margin_impact=round(-2.0 * risk_multiplier, 1),
                probability=0.75,
                time_horizon_days=90,
            ),
        ]
        return scenarios

    def _build_summary(self, company: Company,
                       result: MetaFusionResult) -> SimulationSummary:
        """Build a SimulationSummary from the MetaFusionResult."""
        td = result.tactical_decision

        strategy_breakdown: Dict[str, str] = {}
        for strat, sr in result.strategy_results.items():
            strategy_breakdown[strat.value] = (
                f"{sr.recommended_scenario} ({sr.confidence:.1%})"
            )

        weak_signals = [
            f"{ws.signal_type} — {ws.risk_level.value} "
            f"(correlation: {ws.correlation_strength:.0%})"
            for ws in td.weak_signal_alert
        ]

        return SimulationSummary(
            company_name=company.name,
            company_id=company.company_id,
            recommended_action=td.recommended_action,
            priority=td.tactical_priority.value,
            confidence=result.consensus_confidence,
            agreement_level=result.agreement_level,
            strategy_breakdown=strategy_breakdown,
            weak_signals=weak_signals,
            predicted_outcome=td.predicted_financial_outcome,
            full_explanation=td.explanation,
        )
