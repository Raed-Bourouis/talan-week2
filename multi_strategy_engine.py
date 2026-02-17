"""
Enhanced Multi-Strategy Decision Fusion Engine

Integrates three fusion strategies under a unified interface:
1. Weighted Averaging (original F360 engine)
2. Dempster-Shafer Theory (evidence-based fusion)
3. Bayesian Inference (probabilistic fusion)

Provides meta-fusion: combining all three strategies' outputs
for maximum decision robustness.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import math

from f360_synthesis_engine import (
    F360SynthesisEngine,
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation,
    TacticalDecision,
    Priority,
    RiskLevel,
    WeakSignal
)
from dempster_shafer import (
    DempsterShaferEngine,
    FinancialEvidenceBuilder,
    EvidenceSource,
    DSTResult
)
from bayesian_fusion import (
    BayesianFusionEngine,
    BayesianEvidenceBuilder,
    BayesianEvidence,
    BayesianResult
)


class FusionStrategy(Enum):
    """Available fusion strategies"""
    WEIGHTED_AVERAGE = "Weighted Average"
    DEMPSTER_SHAFER = "Dempster-Shafer Theory"
    BAYESIAN = "Bayesian Inference"
    META_FUSION = "Meta-Fusion (All Combined)"


@dataclass
class StrategyResult:
    """Result from a single fusion strategy"""
    strategy: FusionStrategy
    recommended_scenario: str
    confidence: float
    scenario_scores: Dict[str, float]
    diagnostics: Dict[str, Any]


@dataclass
class MetaFusionResult:
    """Result from meta-fusion combining all strategies"""
    strategy_results: Dict[FusionStrategy, StrategyResult]
    consensus_scenario: str
    consensus_confidence: float
    consensus_scores: Dict[str, float]
    agreement_level: float  # How much strategies agree (0-1)
    tactical_decision: TacticalDecision
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps({
            "meta_fusion": {
                "consensus_scenario": self.consensus_scenario,
                "consensus_confidence": round(self.consensus_confidence, 4),
                "agreement_level": round(self.agreement_level, 4),
                "consensus_scores": {
                    k: round(v, 4) for k, v in self.consensus_scores.items()
                }
            },
            "strategy_breakdown": {
                strategy.value: {
                    "recommended": result.recommended_scenario,
                    "confidence": round(result.confidence, 4),
                    "scores": {
                        k: round(v, 4) for k, v in result.scenario_scores.items()
                    }
                }
                for strategy, result in self.strategy_results.items()
            },
            "tactical_decision": json.loads(self.tactical_decision.to_json())
        }, indent=2)


class MultiStrategyEngine:
    """
    Multi-Strategy Decision Fusion Engine
    
    Runs Weighted Average, Dempster-Shafer, and Bayesian fusion
    in parallel, then combines results via meta-fusion.
    """
    
    def __init__(self,
                 risk_weight: float = 0.6,
                 profitability_weight: float = 0.4,
                 strategy_weights: Optional[Dict[FusionStrategy, float]] = None):
        """
        Initialize multi-strategy engine
        
        Args:
            risk_weight: Weight for risk mitigation
            profitability_weight: Weight for profitability
            strategy_weights: Weights for meta-fusion of strategies
                Default: equal weights
        """
        self.risk_weight = risk_weight
        self.profitability_weight = profitability_weight
        
        self.strategy_weights = strategy_weights or {
            FusionStrategy.WEIGHTED_AVERAGE: 0.30,
            FusionStrategy.DEMPSTER_SHAFER: 0.40,
            FusionStrategy.BAYESIAN: 0.30
        }
        
        # Initialize sub-engines
        self.weighted_engine = F360SynthesisEngine(risk_weight, profitability_weight)
    
    def run_weighted_average(self,
                            financial_data: FinancialData,
                            kg_context: KnowledgeGraphContext,
                            scenarios: List[ScenarioSimulation]) -> StrategyResult:
        """Execute Weighted Average fusion strategy"""
        decision = self.weighted_engine.synthesize(
            financial_data, kg_context, scenarios
        )
        
        # Extract scenario scores from the decision
        scores = {}
        for scenario in scenarios:
            # Risk score
            risk_score = 1.0 - abs(scenario.cash_flow_impact) / 100.0
            profit_score = 1.0 - abs(scenario.margin_impact) / 100.0
            fusion_score = (
                self.risk_weight * risk_score + 
                self.profitability_weight * profit_score
            ) * scenario.probability
            scores[scenario.scenario_id] = fusion_score
        
        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        
        # Determine recommended
        recommended = max(scores, key=scores.get)
        
        return StrategyResult(
            strategy=FusionStrategy.WEIGHTED_AVERAGE,
            recommended_scenario=recommended,
            confidence=decision.confidence_score,
            scenario_scores=scores,
            diagnostics={
                "risk_weight": self.risk_weight,
                "profitability_weight": self.profitability_weight,
                "weak_signals_count": len(decision.weak_signal_alert),
                "priority": decision.tactical_priority.value
            }
        )
    
    def run_dempster_shafer(self,
                           financial_data: FinancialData,
                           kg_context: KnowledgeGraphContext,
                           scenarios: List[ScenarioSimulation]) -> StrategyResult:
        """Execute Dempster-Shafer fusion strategy"""
        scenario_ids = [s.scenario_id for s in scenarios]
        
        # Identify risk and safe scenarios
        risk_scenario = max(scenarios, key=lambda s: abs(s.cash_flow_impact)).scenario_id
        safe_scenario = min(scenarios, key=lambda s: abs(s.cash_flow_impact)).scenario_id
        
        # Initialize DST engine
        dst_engine = DempsterShaferEngine(set(scenario_ids))
        
        # Build evidence sources from financial data
        evidence_sources = [
            FinancialEvidenceBuilder.from_invoice_data(
                scenario_ids, financial_data.unpaid_invoices_spike,
                risk_scenario, safe_scenario
            ),
            FinancialEvidenceBuilder.from_production_data(
                scenario_ids, financial_data.production_output_change,
                risk_scenario, safe_scenario
            ),
            FinancialEvidenceBuilder.from_budget_data(
                scenario_ids, financial_data.budget_remaining_q3,
                risk_scenario, safe_scenario
            ),
            FinancialEvidenceBuilder.from_knowledge_graph(
                scenario_ids, kg_context.client_parent_status,
                kg_context.similar_historical_pattern is not None,
                risk_scenario, safe_scenario
            )
        ]
        
        # Add scenario simulation evidence
        scenario_scores = {}
        for s in scenarios:
            # Score: combine cash flow stability + margin preservation + probability
            cf_score = 1.0 - abs(s.cash_flow_impact) / 100.0
            margin_score = 1.0 - abs(s.margin_impact) / 100.0
            score = (cf_score * 0.5 + margin_score * 0.3 + s.probability * 0.2)
            scenario_scores[s.scenario_id] = max(0.01, score)
        
        evidence_sources.append(
            FinancialEvidenceBuilder.from_scenario_simulation(
                scenario_ids, scenario_scores
            )
        )
        
        # Execute DST fusion
        dst_result = dst_engine.fuse(evidence_sources)
        
        return StrategyResult(
            strategy=FusionStrategy.DEMPSTER_SHAFER,
            recommended_scenario=dst_result.decision,
            confidence=dst_result.confidence,
            scenario_scores=dst_result.pignistic_probability,
            diagnostics={
                "conflict_degree": dst_result.conflict_degree,
                "belief": dst_result.belief,
                "plausibility": dst_result.plausibility,
                "uncertainty_intervals": {
                    k: (round(v[0], 4), round(v[1], 4))
                    for k, v in dst_result.uncertainty_interval.items()
                }
            }
        )
    
    def run_bayesian(self,
                    financial_data: FinancialData,
                    kg_context: KnowledgeGraphContext,
                    scenarios: List[ScenarioSimulation]) -> StrategyResult:
        """Execute Bayesian fusion strategy"""
        scenario_ids = [s.scenario_id for s in scenarios]
        
        # Identify risk and safe scenarios
        risk_scenario = max(scenarios, key=lambda s: abs(s.cash_flow_impact)).scenario_id
        safe_scenario = min(scenarios, key=lambda s: abs(s.cash_flow_impact)).scenario_id
        
        # Initialize Bayesian engine with uniform prior
        bayes_engine = BayesianFusionEngine(scenario_ids)
        
        # Build evidence sources
        evidence_sources = [
            BayesianEvidenceBuilder.from_invoice_data(
                scenario_ids, financial_data.unpaid_invoices_spike,
                risk_scenario, safe_scenario
            ),
            BayesianEvidenceBuilder.from_production_data(
                scenario_ids, financial_data.production_output_change,
                risk_scenario, safe_scenario
            ),
            BayesianEvidenceBuilder.from_budget_data(
                scenario_ids, financial_data.budget_remaining_q3,
                risk_scenario, safe_scenario
            ),
            BayesianEvidenceBuilder.from_knowledge_graph(
                scenario_ids, kg_context.client_parent_status,
                kg_context.similar_historical_pattern is not None,
                risk_scenario, safe_scenario
            )
        ]
        
        # Add scenario simulation scores as evidence
        sim_scores = {}
        for s in scenarios:
            cf_score = 1.0 - abs(s.cash_flow_impact) / 100.0
            margin_score = 1.0 - abs(s.margin_impact) / 100.0
            combined = cf_score * 0.5 + margin_score * 0.3 + s.probability * 0.2
            sim_scores[s.scenario_id] = max(0.05, min(0.95, combined))
        
        evidence_sources.append(
            BayesianEvidenceBuilder.from_scenario_scores(scenario_ids, sim_scores)
        )
        
        # Execute Bayesian fusion
        bayes_result = bayes_engine.fuse(evidence_sources)
        
        return StrategyResult(
            strategy=FusionStrategy.BAYESIAN,
            recommended_scenario=bayes_result.decision,
            confidence=bayes_result.confidence,
            scenario_scores=bayes_result.posterior,
            diagnostics={
                "entropy": bayes_result.entropy,
                "kl_divergence": bayes_result.kl_divergence_from_prior,
                "bayes_factors": bayes_result.bayes_factors,
                "prior": bayes_result.prior,
                "evidence_updates": len(bayes_result.evidence_trail) - 1
            }
        )
    
    def meta_fuse(self, 
                  results: Dict[FusionStrategy, StrategyResult]) -> Dict[str, float]:
        """
        Meta-fusion: Combine outputs of all strategies
    
        Uses weighted voting across strategies, with weights based on
        strategy_weights and individual confidence scores.
        """
        consensus_scores: Dict[str, float] = {}
        
        for strategy, result in results.items():
            weight = self.strategy_weights.get(strategy, 0.33)
            adjusted_weight = weight * result.confidence
            
            for scenario, score in result.scenario_scores.items():
                consensus_scores[scenario] = (
                    consensus_scores.get(scenario, 0.0) + 
                    adjusted_weight * score
                )
        
        # Normalize
        total = sum(consensus_scores.values())
        if total > 0:
            consensus_scores = {k: v / total for k, v in consensus_scores.items()}
        
        return consensus_scores
    
    def calculate_agreement(self, 
                           results: Dict[FusionStrategy, StrategyResult]) -> float:
        """
        Calculate agreement level between strategies
        
        1.0 = all strategies agree on the same scenario
        0.0 = all strategies recommend different scenarios
        """
        recommendations = [r.recommended_scenario for r in results.values()]
        
        if not recommendations:
            return 0.0
        
        # Count most common recommendation
        from collections import Counter
        counts = Counter(recommendations)
        most_common_count = counts.most_common(1)[0][1]
        
        return most_common_count / len(recommendations)
    
    def synthesize(self,
                   financial_data: FinancialData,
                   kg_context: KnowledgeGraphContext,
                   scenarios: List[ScenarioSimulation],
                   strategies: Optional[List[FusionStrategy]] = None) -> MetaFusionResult:
        """
        Execute multi-strategy synthesis
        
        Args:
            financial_data: Financial data from ERP/Kafka
            kg_context: Knowledge graph context
            scenarios: Parallel scenario simulations
            strategies: Which strategies to run (default: all three)
        
        Returns:
            MetaFusionResult with consensus decision and strategy breakdown
        """
        if strategies is None:
            strategies = [
                FusionStrategy.WEIGHTED_AVERAGE,
                FusionStrategy.DEMPSTER_SHAFER,
                FusionStrategy.BAYESIAN
            ]
        
        results: Dict[FusionStrategy, StrategyResult] = {}
        
        # Run each strategy
        if FusionStrategy.WEIGHTED_AVERAGE in strategies:
            results[FusionStrategy.WEIGHTED_AVERAGE] = self.run_weighted_average(
                financial_data, kg_context, scenarios
            )
        
        if FusionStrategy.DEMPSTER_SHAFER in strategies:
            results[FusionStrategy.DEMPSTER_SHAFER] = self.run_dempster_shafer(
                financial_data, kg_context, scenarios
            )
        
        if FusionStrategy.BAYESIAN in strategies:
            results[FusionStrategy.BAYESIAN] = self.run_bayesian(
                financial_data, kg_context, scenarios
            )
        
        # Meta-fusion
        consensus_scores = self.meta_fuse(results)
        consensus_scenario = max(consensus_scores, key=consensus_scores.get)
        
        # Agreement
        agreement = self.calculate_agreement(results)
        
        # Consensus confidence (weighted average of individual confidences)
        total_weight = sum(
            self.strategy_weights.get(s, 0.33) for s in results
        )
        consensus_confidence = sum(
            self.strategy_weights.get(s, 0.33) * r.confidence 
            for s, r in results.items()
        ) / total_weight if total_weight > 0 else 0.5
        
        # Build tactical decision
        best_scenario_data = next(
            s for s in scenarios if s.scenario_id == consensus_scenario
        )
        
        weak_signals = self.weighted_engine.detect_weak_signals(
            financial_data, kg_context,
            self.weighted_engine.aggregate_sources(financial_data, kg_context, scenarios)
        )
        
        # Generate comprehensive explanation
        explanation = self._build_meta_explanation(
            results, consensus_scenario, agreement, 
            financial_data, kg_context, scenarios
        )
        
        # Priority
        priority = self._determine_priority(
            weak_signals, agreement, consensus_confidence
        )
        
        # Predicted outcome
        predicted_outcome = {
            "cash_flow_impact_pct": best_scenario_data.cash_flow_impact,
            "margin_impact_pct": best_scenario_data.margin_impact,
            "time_to_impact_days": best_scenario_data.time_horizon_days,
            "probability": best_scenario_data.probability,
            "meta_consensus_score": consensus_scores[consensus_scenario],
            "strategy_agreement": agreement
        }
        
        tactical = TacticalDecision(
            tactical_priority=priority,
            recommended_action=self._generate_action(
                best_scenario_data, financial_data
            ),
            explanation=explanation,
            weak_signal_alert=weak_signals,
            predicted_financial_outcome=predicted_outcome,
            confidence_score=consensus_confidence,
            alternative_actions=[
                s.description for s in scenarios 
                if s.scenario_id != consensus_scenario
            ]
        )
        
        return MetaFusionResult(
            strategy_results=results,
            consensus_scenario=consensus_scenario,
            consensus_confidence=consensus_confidence,
            consensus_scores=consensus_scores,
            agreement_level=agreement,
            tactical_decision=tactical
        )
    
    def _build_meta_explanation(self,
                               results: Dict[FusionStrategy, StrategyResult],
                               consensus: str,
                               agreement: float,
                               financial_data: FinancialData,
                               kg_context: KnowledgeGraphContext,
                               scenarios: List[ScenarioSimulation]) -> str:
        """Generate comprehensive multi-strategy explanation"""
        parts = []
        
        parts.append(
            f"META-FUSION DECISION: {consensus} selected via multi-strategy consensus "
            f"({agreement:.0%} agreement across {len(results)} fusion algorithms)."
        )
        
        # Strategy breakdown
        parts.append("\n\nSTRATEGY ANALYSIS:")
        
        for strategy, result in results.items():
            parts.append(
                f"\n• {strategy.value}: Recommends {result.recommended_scenario} "
                f"(confidence: {result.confidence:.1%})"
            )
            
            if strategy == FusionStrategy.DEMPSTER_SHAFER:
                conflict = result.diagnostics.get("conflict_degree", 0)
                parts.append(
                    f"  → Inter-source conflict: {conflict:.1%} "
                    f"({'Low' if conflict < 0.3 else 'Moderate' if conflict < 0.6 else 'High'})"
                )
            
            elif strategy == FusionStrategy.BAYESIAN:
                entropy = result.diagnostics.get("entropy", 0)
                kl = result.diagnostics.get("kl_divergence", 0)
                parts.append(
                    f"  → Posterior entropy: {entropy:.3f} bits | "
                    f"KL divergence from prior: {kl:.3f}"
                )
        
        # Financial context
        parts.append(
            f"\n\nFINANCIAL CONTEXT: Client {financial_data.client_id} — "
            f"{financial_data.unpaid_invoices_spike}% invoice spike, "
            f"{abs(financial_data.production_output_change)}% production slowdown, "
            f"{financial_data.budget_remaining_q3}% budget remaining."
        )
        
        if kg_context.similar_historical_pattern:
            parts.append(
                f"\n\nHISTORICAL INTELLIGENCE: Episodic memory matches pattern from "
                f"{kg_context.similar_historical_pattern.get('years_ago')} years ago "
                f"({kg_context.similar_historical_pattern.get('cash_flow_delay_days')}-day "
                f"cash flow delay)."
            )
        
        # Agreement assessment
        if agreement >= 0.9:
            parts.append(
                "\n\nCONSENSUS: Strong agreement — all fusion methods converge on the same decision."
            )
        elif agreement >= 0.66:
            parts.append(
                "\n\nCONSENSUS: Majority agreement — most fusion methods agree, minor divergence detected."
            )
        else:
            disagreeing = [
                f"{s.value}: {r.recommended_scenario}" 
                for s, r in results.items() 
                if r.recommended_scenario != consensus
            ]
            parts.append(
                f"\n\nCONSENSUS WARNING: Strategies disagree. "
                f"Divergent recommendations: {'; '.join(disagreeing)}. "
                f"Decision made by weighted meta-fusion voting."
            )
        
        return "".join(parts)
    
    def _determine_priority(self,
                           weak_signals: List[WeakSignal],
                           agreement: float,
                           confidence: float) -> Priority:
        """Determine priority considering strategy agreement"""
        # Critical weak signals → always HIGH
        if any(ws.risk_level == RiskLevel.CRITICAL for ws in weak_signals):
            return Priority.HIGH
        
        # Low agreement between strategies → elevate priority (uncertain situation)
        if agreement < 0.5:
            return Priority.HIGH
        
        # Multiple weak signals
        if len(weak_signals) >= 2:
            return Priority.HIGH
        
        if len(weak_signals) >= 1 or confidence < 0.5:
            return Priority.MEDIUM
        
        return Priority.LOW
    
    def _generate_action(self,
                        scenario: ScenarioSimulation,
                        financial_data: FinancialData) -> str:
        """Generate recommended action"""
        desc = scenario.description.lower()
        if "early payment" in desc:
            return f"Trigger early payment incentive for Client {financial_data.client_id}"
        elif "renegotiat" in desc:
            return f"Initiate payment term renegotiation with Client {financial_data.client_id}"
        elif "hedge" in desc or "insurance" in desc:
            return f"Activate hedging/insurance strategy for Client {financial_data.client_id}"
        elif "business as usual" in desc:
            return f"Maintain current operations for Client {financial_data.client_id} (monitor closely)"
        else:
            return f"Execute {scenario.scenario_id}: {scenario.description}"
