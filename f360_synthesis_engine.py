"""
F360 Financial Synthesis Engine
Weighted Decision Fusion and Multi-source Aggregation System

Transforms multimodal financial data and simulated scenarios into prioritized,
explainable tactical decisions for self-adaptive financial modeling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class Priority(Enum):
    """Tactical decision priority levels"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskLevel(Enum):
    """Risk assessment levels"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class FinancialData:
    """Financial data from ERP/S3/Kafka streams"""
    unpaid_invoices_spike: float  # percentage
    client_id: str
    production_output_change: float  # percentage (negative = slowdown)
    budget_remaining_q3: float  # percentage
    timestamp: datetime = field(default_factory=datetime.now)
    
    
@dataclass
class KnowledgeGraphContext:
    """RAGraph episodic memory and knowledge graph data"""
    client_parent_status: str
    similar_historical_pattern: Optional[Dict[str, Any]] = None
    external_data_signals: List[str] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)


@dataclass
class ScenarioSimulation:
    """Parallel scenario simulation results"""
    scenario_id: str
    description: str
    cash_flow_impact: float  # percentage
    margin_impact: float  # percentage
    probability: float
    time_horizon_days: int
    

@dataclass
class WeakSignal:
    """Identified weak signal correlation"""
    signal_type: str
    correlation_strength: float  # 0.0 to 1.0
    source_indices: List[str]
    risk_level: RiskLevel
    description: str


@dataclass
class TacticalDecision:
    """Output tactical decision with full explainability"""
    tactical_priority: Priority
    recommended_action: str
    explanation: str
    weak_signal_alert: List[WeakSignal]
    predicted_financial_outcome: Dict[str, float]
    confidence_score: float
    alternative_actions: List[str] = field(default_factory=list)
    
    def to_json(self) -> str:
        """Convert decision to JSON format"""
        return json.dumps({
            "tactical_priority": self.tactical_priority.value,
            "recommended_action": self.recommended_action,
            "explanation": self.explanation,
            "weak_signal_alert": [
                {
                    "signal_type": ws.signal_type,
                    "correlation_strength": ws.correlation_strength,
                    "source_indices": ws.source_indices,
                    "risk_level": ws.risk_level.value,
                    "description": ws.description
                }
                for ws in self.weak_signal_alert
            ],
            "predicted_financial_outcome": self.predicted_financial_outcome,
            "confidence_score": self.confidence_score,
            "alternative_actions": self.alternative_actions
        }, indent=2)


class F360SynthesisEngine:
    """
    F360 Financial Synthesis Engine
    
    Performs weighted decision fusion, multi-source aggregation, and weak signal
    correlation to generate prioritized tactical decisions.
    """
    
    def __init__(self, 
                 risk_weight: float = 0.6,
                 profitability_weight: float = 0.4):
        """
        Initialize the synthesis engine
        
        Args:
            risk_weight: Weight for risk mitigation (default 0.6)
            profitability_weight: Weight for profitability (default 0.4)
        """
        self.risk_weight = risk_weight
        self.profitability_weight = profitability_weight
        
    def aggregate_sources(self,
                         financial_data: FinancialData,
                         kg_context: KnowledgeGraphContext,
                         scenarios: List[ScenarioSimulation]) -> Dict[str, Any]:
        """
        Multi-source Aggregation: Correlate ERP, Knowledge Graph, and IoT data
        
        Args:
            financial_data: Financial data from ERP/Kafka/S3
            kg_context: Knowledge graph and episodic memory context
            scenarios: List of parallel scenario simulations
            
        Returns:
            Aggregated intelligence dictionary
        """
        aggregated = {
            "financial_stress_score": self._calculate_financial_stress(financial_data),
            "historical_pattern_match": kg_context.similar_historical_pattern is not None,
            "external_risk_factors": len(kg_context.external_data_signals),
            "scenario_risk_range": self._calculate_scenario_risk_range(scenarios),
            "production_financial_correlation": self._correlate_production_finance(
                financial_data.production_output_change,
                financial_data.unpaid_invoices_spike
            )
        }
        return aggregated
    
    def detect_weak_signals(self,
                           financial_data: FinancialData,
                           kg_context: KnowledgeGraphContext,
                           aggregated: Dict[str, Any]) -> List[WeakSignal]:
        """
        Weak Signal Correlation: Identify systemic risks from multi-source indices
        
        Args:
            financial_data: Financial data
            kg_context: Knowledge graph context
            aggregated: Aggregated intelligence
            
        Returns:
            List of identified weak signals
        """
        weak_signals = []
        
        # Signal 1: Production slowdown + Client parent restructuring
        if (financial_data.production_output_change < -5 and 
            "restructuring" in kg_context.client_parent_status.lower()):
            
            correlation_strength = min(
                abs(financial_data.production_output_change) / 20.0,
                1.0
            )
            
            weak_signals.append(WeakSignal(
                signal_type="Production-Client_Systemic_Risk",
                correlation_strength=correlation_strength,
                source_indices=["IoT_Production", "KG_Client_Parent", "ERP_Invoices"],
                risk_level=RiskLevel.HIGH if correlation_strength > 0.6 else RiskLevel.MEDIUM,
                description=f"Production slowdown of {financial_data.production_output_change}% "
                           f"combined with client parent restructuring indicates supply chain "
                           f"and payment risk convergence"
            ))
        
        # Signal 2: Budget depletion + Cash flow risk
        if financial_data.budget_remaining_q3 < 10:
            weak_signals.append(WeakSignal(
                signal_type="Budget_Liquidity_Squeeze",
                correlation_strength=0.8,
                source_indices=["ERP_Budget", "ERP_Invoices"],
                risk_level=RiskLevel.CRITICAL,
                description=f"Only {financial_data.budget_remaining_q3}% budget remaining "
                           f"with {financial_data.unpaid_invoices_spike}% spike in unpaid invoices"
            ))
        
        # Signal 3: Historical pattern recurrence
        if kg_context.similar_historical_pattern:
            historical_delay = kg_context.similar_historical_pattern.get("cash_flow_delay_days", 0)
            weak_signals.append(WeakSignal(
                signal_type="Historical_Pattern_Recurrence",
                correlation_strength=0.75,
                source_indices=["RAGraph_Episodic_Memory", "ERP_Invoices"],
                risk_level=RiskLevel.HIGH,
                description=f"Current pattern matches historical incident from "
                           f"{kg_context.similar_historical_pattern.get('years_ago', 'N/A')} years ago, "
                           f"which resulted in {historical_delay}-day cash flow delay"
            ))
        
        return weak_signals
    
    def weighted_decision_fusion(self,
                                 scenarios: List[ScenarioSimulation],
                                 weak_signals: List[WeakSignal],
                                 aggregated: Dict[str, Any]) -> ScenarioSimulation:
        """
        Weighted Decision Fusion: Apply weights to Risk Mitigation vs Profitability
        
        Args:
            scenarios: List of scenario simulations
            weak_signals: Detected weak signals
            aggregated: Aggregated intelligence
            
        Returns:
            Best scenario based on weighted fusion
        """
        scored_scenarios = []
        
        for scenario in scenarios:
            # Risk score (lower cash flow impact = better)
            risk_score = 1.0 - abs(scenario.cash_flow_impact) / 100.0
            
            # Profitability score (lower margin impact = better)
            profit_score = 1.0 - abs(scenario.margin_impact) / 100.0
            
            # Adjust for weak signals - increase risk weight if critical signals present
            adjusted_risk_weight = self.risk_weight
            if any(ws.risk_level == RiskLevel.CRITICAL for ws in weak_signals):
                adjusted_risk_weight = min(0.8, self.risk_weight + 0.2)
            
            adjusted_profit_weight = 1.0 - adjusted_risk_weight
            
            # Weighted fusion score
            fusion_score = (
                adjusted_risk_weight * risk_score +
                adjusted_profit_weight * profit_score
            ) * scenario.probability
            
            scored_scenarios.append((scenario, fusion_score))
        
        # Return scenario with highest fusion score
        best_scenario = max(scored_scenarios, key=lambda x: x[1])
        return best_scenario[0]
    
    def prioritize_and_explain(self,
                               best_scenario: ScenarioSimulation,
                               weak_signals: List[WeakSignal],
                               financial_data: FinancialData,
                               kg_context: KnowledgeGraphContext,
                               all_scenarios: List[ScenarioSimulation]) -> TacticalDecision:
        """
        Prioritization & Explainability: Rank decisions with clear reasoning
        
        Args:
            best_scenario: Selected best scenario
            weak_signals: Detected weak signals
            financial_data: Original financial data
            kg_context: Knowledge graph context
            all_scenarios: All available scenarios
            
        Returns:
            TacticalDecision with full explainability
        """
        # Determine priority
        priority = self._determine_priority(weak_signals, best_scenario)
        
        # Generate explanation
        explanation = self._generate_explanation(
            best_scenario, weak_signals, financial_data, kg_context, all_scenarios
        )
        
        # Generate recommended action
        action = self._generate_action(best_scenario, financial_data)
        
        # Predict financial outcome
        predicted_outcome = {
            "cash_flow_impact_pct": best_scenario.cash_flow_impact,
            "margin_impact_pct": best_scenario.margin_impact,
            "time_to_impact_days": best_scenario.time_horizon_days,
            "probability": best_scenario.probability
        }
        
        # Calculate confidence score
        confidence = self._calculate_confidence(weak_signals, best_scenario)
        
        # Alternative actions
        alternatives = [
            s.description for s in all_scenarios 
            if s.scenario_id != best_scenario.scenario_id
        ]
        
        return TacticalDecision(
            tactical_priority=priority,
            recommended_action=action,
            explanation=explanation,
            weak_signal_alert=weak_signals,
            predicted_financial_outcome=predicted_outcome,
            confidence_score=confidence,
            alternative_actions=alternatives
        )
    
    def synthesize(self,
                   financial_data: FinancialData,
                   kg_context: KnowledgeGraphContext,
                   scenarios: List[ScenarioSimulation]) -> TacticalDecision:
        """
        Main synthesis pipeline: Execute complete decision fusion process
        
        Args:
            financial_data: Financial data from ERP/Kafka/S3
            kg_context: Knowledge graph and episodic memory
            scenarios: Parallel scenario simulations
            
        Returns:
            TacticalDecision with prioritized, explainable recommendation
        """
        # Step 1: Multi-source Aggregation
        aggregated = self.aggregate_sources(financial_data, kg_context, scenarios)
        
        # Step 2: Weak Signal Correlation
        weak_signals = self.detect_weak_signals(financial_data, kg_context, aggregated)
        
        # Step 3: Weighted Decision Fusion
        best_scenario = self.weighted_decision_fusion(scenarios, weak_signals, aggregated)
        
        # Step 4: Prioritization & Explainability
        decision = self.prioritize_and_explain(
            best_scenario, weak_signals, financial_data, kg_context, scenarios
        )
        
        return decision
    
    # ---------------- Helper Methods ----------------
    
    def _calculate_financial_stress(self, financial_data: FinancialData) -> float:
        """Calculate overall financial stress score (0-1)"""
        invoice_stress = min(financial_data.unpaid_invoices_spike / 100.0, 1.0)
        budget_stress = 1.0 - (financial_data.budget_remaining_q3 / 100.0)
        production_stress = min(abs(financial_data.production_output_change) / 50.0, 1.0)
        
        return (invoice_stress * 0.4 + budget_stress * 0.3 + production_stress * 0.3)
    
    def _calculate_scenario_risk_range(self, scenarios: List[ScenarioSimulation]) -> Dict[str, float]:
        """Calculate risk range across scenarios"""
        cash_flows = [s.cash_flow_impact for s in scenarios]
        return {
            "min_cash_flow_impact": min(cash_flows),
            "max_cash_flow_impact": max(cash_flows),
            "range": max(cash_flows) - min(cash_flows)
        }
    
    def _correlate_production_finance(self, 
                                      production_change: float, 
                                      invoice_spike: float) -> float:
        """Calculate correlation between production and financial metrics"""
        # Negative production + positive invoice spike = high correlation risk
        if production_change < 0 and invoice_spike > 0:
            return min(abs(production_change) * invoice_spike / 100.0, 1.0)
        return 0.0
    
    def _determine_priority(self, 
                           weak_signals: List[WeakSignal],
                           scenario: ScenarioSimulation) -> Priority:
        """Determine tactical priority based on weak signals and scenario impact"""
        if any(ws.risk_level == RiskLevel.CRITICAL for ws in weak_signals):
            return Priority.HIGH
        
        if abs(scenario.cash_flow_impact) > 15 or len(weak_signals) >= 2:
            return Priority.HIGH
        
        if abs(scenario.cash_flow_impact) > 5 or len(weak_signals) >= 1:
            return Priority.MEDIUM
        
        return Priority.LOW
    
    def _generate_explanation(self,
                             scenario: ScenarioSimulation,
                             weak_signals: List[WeakSignal],
                             financial_data: FinancialData,
                             kg_context: KnowledgeGraphContext,
                             all_scenarios: List[ScenarioSimulation]) -> str:
        """Generate detailed explanation connecting all data sources"""
        explanation_parts = [
            f"Prioritize {scenario.scenario_id} ({scenario.description}) based on weighted decision fusion."
        ]
        
        # ERP data context
        explanation_parts.append(
            f"\n\nERP Data Analysis: Client {financial_data.client_id} shows a "
            f"{financial_data.unpaid_invoices_spike}% spike in unpaid invoices with "
            f"only {financial_data.budget_remaining_q3}% Q3 budget remaining."
        )
        
        # Knowledge graph context
        if kg_context.similar_historical_pattern:
            explanation_parts.append(
                f"\n\nKnowledge Graph Intelligence: Episodic memory indicates this pattern "
                f"occurred {kg_context.similar_historical_pattern.get('years_ago')} years ago, "
                f"resulting in a {kg_context.similar_historical_pattern.get('cash_flow_delay_days')}-day "
                f"cash flow delay. Client parent company status: {kg_context.client_parent_status}."
            )
        
        # IoT/Production context
        if financial_data.production_output_change < 0:
            explanation_parts.append(
                f"\n\nProduction Intelligence: IoT logs show {abs(financial_data.production_output_change)}% "
                f"production slowdown, correlating with payment delays."
            )
        
        # Scenario comparison
        other_scenarios = [s for s in all_scenarios if s.scenario_id != scenario.scenario_id]
        if other_scenarios:
            worst = max(other_scenarios, key=lambda s: abs(s.cash_flow_impact))
            explanation_parts.append(
                f"\n\nScenario Comparison: {scenario.scenario_id} avoids the {abs(worst.cash_flow_impact)}% "
                f"cash flow deficit predicted in {worst.scenario_id}, with acceptable "
                f"{abs(scenario.margin_impact)}% margin impact."
            )
        
        # Weak signals
        if weak_signals:
            explanation_parts.append(
                f"\n\nWeak Signal Correlations: {len(weak_signals)} systemic risk indicators detected, "
                f"including {', '.join([ws.signal_type for ws in weak_signals[:2]])}."
            )
        
        return "".join(explanation_parts)
    
    def _generate_action(self, 
                        scenario: ScenarioSimulation,
                        financial_data: FinancialData) -> str:
        """Generate specific recommended action"""
        if "early payment" in scenario.description.lower():
            return f"Trigger early payment incentive for Client {financial_data.client_id}"
        elif "renegotiate" in scenario.description.lower():
            return f"Initiate payment term renegotiation with Client {financial_data.client_id}"
        elif "hedging" in scenario.description.lower():
            return f"Activate cash flow hedging strategy for Client {financial_data.client_id}"
        else:
            return f"Execute {scenario.scenario_id}: {scenario.description}"
    
    def _calculate_confidence(self,
                             weak_signals: List[WeakSignal],
                             scenario: ScenarioSimulation) -> float:
        """Calculate confidence score for the decision"""
        base_confidence = scenario.probability
        
        # Reduce confidence if conflicting weak signals
        signal_strength_avg = (
            sum(ws.correlation_strength for ws in weak_signals) / len(weak_signals)
            if weak_signals else 0.5
        )
        
        return min(base_confidence * (0.7 + 0.3 * signal_strength_avg), 1.0)
