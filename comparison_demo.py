"""
Fusion Strategy Comparison Demo

Runs the same financial scenario through all three fusion algorithms
and compares their decisions side by side:
1. Weighted Average (original F360)
2. Dempster-Shafer Theory (evidence-based)
3. Bayesian Inference (probabilistic)
4. Meta-Fusion (combined)
"""

from datetime import datetime
from f360_synthesis_engine import (
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation
)
from multi_strategy_engine import MultiStrategyEngine, FusionStrategy


def print_separator(title: str = ""):
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}")
    else:
        print(f"{'─' * 80}")


def run_comparison():
    """
    Compare all fusion strategies on the same high-risk financial scenario
    """
    print_separator("F360 MULTI-STRATEGY FUSION COMPARISON")
    print("  Weighted Average vs Dempster-Shafer vs Bayesian vs Meta-Fusion")
    print("=" * 80)
    
    # ==================== INPUT DATA ====================
    
    financial_data = FinancialData(
        unpaid_invoices_spike=15.0,
        client_id="CLIENT_X_001",
        production_output_change=-12.0,
        budget_remaining_q3=5.0,
        timestamp=datetime.now()
    )
    
    kg_context = KnowledgeGraphContext(
        client_parent_status="Undergoing corporate restructuring (Merger Phase)",
        similar_historical_pattern={
            "years_ago": 2,
            "cash_flow_delay_days": 30,
            "resolution": "Early payment discount applied",
            "final_outcome": "Cash flow stabilized with 4% margin reduction"
        },
        external_data_signals=[
            "Parent company credit rating downgrade",
            "Industry sector 8% YoY contraction",
            "Regional economic uncertainty elevated"
        ],
        risk_indicators=[
            "Payment delays trending upward",
            "Communication frequency decreased by 40%"
        ]
    )
    
    scenarios = [
        ScenarioSimulation(
            scenario_id="SCENARIO_A",
            description="Business as usual (no intervention)",
            cash_flow_impact=-20.0,
            margin_impact=0.0,
            probability=0.85,
            time_horizon_days=60
        ),
        ScenarioSimulation(
            scenario_id="SCENARIO_B",
            description="Early payment discount (5% incentive)",
            cash_flow_impact=0.0,
            margin_impact=-5.0,
            probability=0.90,
            time_horizon_days=30
        ),
        ScenarioSimulation(
            scenario_id="SCENARIO_C",
            description="Payment term renegotiation (extended terms)",
            cash_flow_impact=-10.0,
            margin_impact=-2.0,
            probability=0.70,
            time_horizon_days=45
        )
    ]
    
    # ==================== INPUT SUMMARY ====================
    
    print_separator("INPUT DATA SUMMARY")
    print(f"\n  Client: {financial_data.client_id}")
    print(f"  Invoice Spike: {financial_data.unpaid_invoices_spike}%")
    print(f"  Production Change: {financial_data.production_output_change}%")
    print(f"  Budget Remaining: {financial_data.budget_remaining_q3}%")
    print(f"  Client Status: {kg_context.client_parent_status}")
    print(f"  Historical Match: {kg_context.similar_historical_pattern['years_ago']} years ago")
    
    print(f"\n  Scenarios:")
    for s in scenarios:
        print(f"    {s.scenario_id}: {s.description}")
        print(f"      Cash Flow: {s.cash_flow_impact}% | Margin: {s.margin_impact}% | P: {s.probability}")
    
    # ==================== RUN MULTI-STRATEGY ENGINE ====================
    
    engine = MultiStrategyEngine(
        risk_weight=0.6,
        profitability_weight=0.4,
        strategy_weights={
            FusionStrategy.WEIGHTED_AVERAGE: 0.30,
            FusionStrategy.DEMPSTER_SHAFER: 0.40,
            FusionStrategy.BAYESIAN: 0.30
        }
    )
    
    print_separator("EXECUTING ALL FUSION STRATEGIES")
    result = engine.synthesize(financial_data, kg_context, scenarios)
    
    # ==================== INDIVIDUAL STRATEGY RESULTS ====================
    
    print_separator("STRATEGY-BY-STRATEGY RESULTS")
    
    for strategy, strat_result in result.strategy_results.items():
        print(f"\n  ┌─ {strategy.value} {'─' * (55 - len(strategy.value))}")
        print(f"  │  Recommendation: {strat_result.recommended_scenario}")
        print(f"  │  Confidence:     {strat_result.confidence:.1%}")
        print(f"  │")
        print(f"  │  Scenario Scores:")
        
        # Sort by score
        sorted_scores = sorted(
            strat_result.scenario_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for scenario_id, score in sorted_scores:
            bar = "█" * int(score * 30) + "░" * (30 - int(score * 30))
            marker = " ◄ BEST" if scenario_id == strat_result.recommended_scenario else ""
            print(f"  │    {scenario_id}: {bar} {score:.1%}{marker}")
        
        # Strategy-specific diagnostics
        print(f"  │")
        if strategy == FusionStrategy.DEMPSTER_SHAFER:
            conflict = strat_result.diagnostics.get("conflict_degree", 0)
            intervals = strat_result.diagnostics.get("uncertainty_intervals", {})
            print(f"  │  DST Diagnostics:")
            print(f"  │    Inter-source conflict: {conflict:.1%}")
            print(f"  │    Uncertainty intervals [Bel, Pl]:")
            for sid, (bel, pl) in intervals.items():
                print(f"  │      {sid}: [{bel:.3f}, {pl:.3f}]")
        
        elif strategy == FusionStrategy.BAYESIAN:
            entropy = strat_result.diagnostics.get("entropy", 0)
            kl = strat_result.diagnostics.get("kl_divergence", 0)
            bayes_factors = strat_result.diagnostics.get("bayes_factors", {})
            print(f"  │  Bayesian Diagnostics:")
            print(f"  │    Posterior entropy: {entropy:.3f} bits")
            print(f"  │    KL divergence from uniform prior: {kl:.3f}")
            print(f"  │    Bayes factors:")
            for comp, bf in bayes_factors.items():
                strength = (
                    "Very Strong" if bf > 10 else
                    "Strong" if bf > 3 else
                    "Moderate" if bf > 1 else
                    "Weak"
                )
                print(f"  │      {comp}: {bf:.2f} ({strength})")
        
        elif strategy == FusionStrategy.WEIGHTED_AVERAGE:
            print(f"  │  Weighted Average Diagnostics:")
            print(f"  │    Risk weight: {strat_result.diagnostics.get('risk_weight')}")
            print(f"  │    Weak signals: {strat_result.diagnostics.get('weak_signals_count')}")
            print(f"  │    Priority: {strat_result.diagnostics.get('priority')}")
        
        print(f"  └{'─' * 60}")
    
    # ==================== HEAD-TO-HEAD COMPARISON TABLE ====================
    
    print_separator("HEAD-TO-HEAD COMPARISON")
    
    # Header
    strategies = list(result.strategy_results.keys())
    header = f"{'Metric':<25}"
    for s in strategies:
        header += f" | {s.value:<20}"
    header += f" | {'META-FUSION':<20}"
    print(f"\n  {header}")
    print(f"  {'─' * len(header)}")
    
    # Recommendation row
    row = f"{'Recommendation':<25}"
    for s in strategies:
        row += f" | {result.strategy_results[s].recommended_scenario:<20}"
    row += f" | {result.consensus_scenario:<20}"
    print(f"  {row}")
    
    # Confidence row
    row = f"{'Confidence':<25}"
    for s in strategies:
        row += f" | {result.strategy_results[s].confidence:<20.1%}"
    row += f" | {result.consensus_confidence:<20.1%}"
    print(f"  {row}")
    
    # Scores per scenario
    for scenario in scenarios:
        row = f"{scenario.scenario_id:<25}"
        for s in strategies:
            score = result.strategy_results[s].scenario_scores.get(
                scenario.scenario_id, 0
            )
            row += f" | {score:<20.1%}"
        consensus_score = result.consensus_scores.get(scenario.scenario_id, 0)
        row += f" | {consensus_score:<20.1%}"
        print(f"  {row}")
    
    # ==================== META-FUSION CONSENSUS ====================
    
    print_separator("META-FUSION CONSENSUS")
    
    print(f"\n  🎯 CONSENSUS DECISION: {result.consensus_scenario}")
    print(f"  💯 CONSENSUS CONFIDENCE: {result.consensus_confidence:.1%}")
    print(f"  🤝 STRATEGY AGREEMENT: {result.agreement_level:.0%}")
    
    # Agreement visualization
    recs = [r.recommended_scenario for r in result.strategy_results.values()]
    agreement_text = (
        "UNANIMOUS" if result.agreement_level >= 0.99 else
        "MAJORITY" if result.agreement_level >= 0.66 else
        "SPLIT DECISION"
    )
    print(f"  📊 AGREEMENT TYPE: {agreement_text}")
    print(f"     Individual votes: {' | '.join(recs)}")
    
    # ==================== TACTICAL DECISION ====================
    
    print_separator("FINAL TACTICAL DECISION")
    
    decision = result.tactical_decision
    print(f"\n  Priority:    {decision.tactical_priority.value}")
    print(f"  Action:      {decision.recommended_action}")
    print(f"  Confidence:  {decision.confidence_score:.1%}")
    
    print(f"\n  Predicted Outcome:")
    for k, v in decision.predicted_financial_outcome.items():
        print(f"    • {k}: {v}")
    
    print(f"\n  Weak Signals: {len(decision.weak_signal_alert)}")
    for ws in decision.weak_signal_alert:
        print(f"    ⚠ {ws.signal_type} ({ws.risk_level.value}, {ws.correlation_strength:.0%})")
    
    # ==================== JSON OUTPUT ====================
    
    print_separator("COMPLETE JSON OUTPUT")
    print(result.to_json())
    
    print_separator("COMPARISON COMPLETE")
    
    return result


def run_divergent_scenario():
    """
    Run a scenario where strategies are more likely to disagree,
    demonstrating the value of meta-fusion
    """
    print_separator("DIVERGENT SCENARIO — Strategies May Disagree")
    
    # Ambiguous financial data — mixed signals
    financial_data = FinancialData(
        unpaid_invoices_spike=8.0,      # Moderate spike
        client_id="AMBIGUOUS_CLIENT",
        production_output_change=-4.0,  # Slight slowdown
        budget_remaining_q3=18.0        # Somewhat low
    )
    
    # Contradictory signals
    kg_context = KnowledgeGraphContext(
        client_parent_status="Stable but exploring acquisition opportunities",
        similar_historical_pattern=None,  # No historical match
        external_data_signals=["Mixed industry outlook"],
        risk_indicators=["Minor payment irregularities"]
    )
    
    # Close scenarios — hard to distinguish
    scenarios = [
        ScenarioSimulation(
            scenario_id="MAINTAIN",
            description="Business as usual",
            cash_flow_impact=-8.0,
            margin_impact=0.0,
            probability=0.75,
            time_horizon_days=60
        ),
        ScenarioSimulation(
            scenario_id="INCENTIVE",
            description="Early payment discount (3%)",
            cash_flow_impact=-1.0,
            margin_impact=-3.0,
            probability=0.80,
            time_horizon_days=30
        ),
        ScenarioSimulation(
            scenario_id="RENEGOTIATE",
            description="Renegotiate payment terms",
            cash_flow_impact=-4.0,
            margin_impact=-1.5,
            probability=0.85,
            time_horizon_days=45
        )
    ]
    
    engine = MultiStrategyEngine(risk_weight=0.5, profitability_weight=0.5)
    result = engine.synthesize(financial_data, kg_context, scenarios)
    
    # Summary
    print(f"\n  Strategy Results:")
    for strategy, strat_result in result.strategy_results.items():
        scores_str = ", ".join(
            f"{k}: {v:.1%}" 
            for k, v in sorted(
                strat_result.scenario_scores.items(), 
                key=lambda x: x[1], reverse=True
            )
        )
        print(f"    {strategy.value:<25} → {strat_result.recommended_scenario}"
              f" ({strat_result.confidence:.1%}) [{scores_str}]")
    
    print(f"\n  🎯 Meta-Fusion Consensus: {result.consensus_scenario}")
    print(f"  🤝 Agreement: {result.agreement_level:.0%}")
    print(f"  💯 Confidence: {result.consensus_confidence:.1%}")
    
    # Check for disagreement
    recs = set(r.recommended_scenario for r in result.strategy_results.values())
    if len(recs) > 1:
        print(f"\n  ⚠ STRATEGIES DISAGREE: {recs}")
        print(f"  → Meta-fusion resolves conflict via weighted consensus voting")
    else:
        print(f"\n  ✓ All strategies agree on {result.consensus_scenario}")
    
    print_separator()
    return result


if __name__ == "__main__":
    # 1. Main comparison with high-risk scenario
    main_result = run_comparison()
    
    # 2. Divergent scenario where strategies may disagree
    divergent_result = run_divergent_scenario()
    
    print("\n✅ Multi-strategy comparison complete!")
    print("   The engine successfully compared Weighted Average, Dempster-Shafer,")
    print("   and Bayesian fusion approaches with meta-fusion consensus.")
