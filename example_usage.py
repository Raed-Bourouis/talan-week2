"""
F360 Financial Synthesis Engine - Example Usage
Demonstrates the complete decision fusion pipeline with synthetic financial data
"""

from datetime import datetime
from f360_synthesis_engine import (
    F360SynthesisEngine,
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation
)


def run_example_synthesis():
    """
    Execute F360 Synthesis with the provided synthetic financial streams
    
    Scenario:
    - 15% spike in unpaid invoices from key client
    - IoT logs show production output slowdown
    - Q3 budget at 5% remaining
    - Client parent company undergoing restructuring
    - Similar pattern occurred 2 years ago (30-day cash flow delay)
    - Two parallel scenarios evaluated
    """
    
    print("=" * 80)
    print("F360 FINANCIAL SYNTHESIS ENGINE")
    print("Weighted Decision Fusion & Multi-source Aggregation")
    print("=" * 80)
    
    # ==================== INPUT DATA ====================
    
    # 1. Financial Data Universe (S3/Kafka/ERP)
    financial_data = FinancialData(
        unpaid_invoices_spike=15.0,  # 15% spike
        client_id="CLIENT_X_001",
        production_output_change=-12.0,  # 12% slowdown
        budget_remaining_q3=5.0,  # 5% remaining
        timestamp=datetime.now()
    )
    
    print("\n[1] FINANCIAL DATA UNIVERSE (ERP/S3/Kafka/IoT)")
    print(f"  • Unpaid Invoices Spike: {financial_data.unpaid_invoices_spike}%")
    print(f"  • Client ID: {financial_data.client_id}")
    print(f"  • Production Output Change: {financial_data.production_output_change}%")
    print(f"  • Q3 Budget Remaining: {financial_data.budget_remaining_q3}%")
    
    # 2. RAGraph (Episodic Memory & Knowledge Graph)
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
            "Industry sector experiencing 8% YoY contraction",
            "Regional economic uncertainty index elevated"
        ],
        risk_indicators=[
            "Payment delays trending upward (3 consecutive months)",
            "Communication frequency decreased by 40%"
        ]
    )
    
    print("\n[2] RAGRAPH (Knowledge Graph & Episodic Memory)")
    print(f"  • Client Parent Status: {kg_context.client_parent_status}")
    print(f"  • Historical Pattern Match: {kg_context.similar_historical_pattern['years_ago']} years ago")
    print(f"  • Historical Outcome: {kg_context.similar_historical_pattern['cash_flow_delay_days']}-day delay")
    print(f"  • External Risk Signals: {len(kg_context.external_data_signals)} detected")
    
    # 3. Scenario Simulation (Parallel Simulations)
    scenarios = [
        ScenarioSimulation(
            scenario_id="SCENARIO_A",
            description="Business as usual (no intervention)",
            cash_flow_impact=-20.0,  # 20% deficit
            margin_impact=0.0,
            probability=0.85,
            time_horizon_days=60
        ),
        ScenarioSimulation(
            scenario_id="SCENARIO_B",
            description="Early payment discount (5% incentive)",
            cash_flow_impact=0.0,  # 100% stability
            margin_impact=-5.0,  # 5% margin loss
            probability=0.90,
            time_horizon_days=30
        ),
        ScenarioSimulation(
            scenario_id="SCENARIO_C",
            description="Payment term renegotiation (extended 60-day terms)",
            cash_flow_impact=-10.0,  # 10% deficit
            margin_impact=-2.0,  # 2% margin loss from concessions
            probability=0.70,
            time_horizon_days=45
        )
    ]
    
    print("\n[3] PARALLEL SCENARIO SIMULATIONS")
    for scenario in scenarios:
        print(f"  • {scenario.scenario_id}: {scenario.description}")
        print(f"    - Cash Flow Impact: {scenario.cash_flow_impact}%")
        print(f"    - Margin Impact: {scenario.margin_impact}%")
        print(f"    - Probability: {scenario.probability * 100}%")
    
    # ==================== SYNTHESIS EXECUTION ====================
    
    print("\n" + "=" * 80)
    print("EXECUTING WEIGHTED DECISION FUSION")
    print("=" * 80)
    
    # Initialize engine with risk-focused weighting
    engine = F360SynthesisEngine(
        risk_weight=0.6,  # 60% weight on risk mitigation
        profitability_weight=0.4  # 40% weight on profitability
    )
    
    # Execute full synthesis pipeline
    decision = engine.synthesize(
        financial_data=financial_data,
        kg_context=kg_context,
        scenarios=scenarios
    )
    
    # ==================== OUTPUT ====================
    
    print("\n" + "=" * 80)
    print("TACTICAL DECISION OUTPUT")
    print("=" * 80)
    
    print(f"\n🎯 TACTICAL PRIORITY: {decision.tactical_priority.value}")
    print(f"📋 RECOMMENDED ACTION: {decision.recommended_action}")
    print(f"💯 CONFIDENCE SCORE: {decision.confidence_score:.2%}")
    
    print("\n📊 PREDICTED FINANCIAL OUTCOME:")
    for key, value in decision.predicted_financial_outcome.items():
        print(f"  • {key}: {value}")
    
    print("\n⚠️  WEAK SIGNAL ALERTS:")
    for i, signal in enumerate(decision.weak_signal_alert, 1):
        print(f"\n  Signal {i}: {signal.signal_type}")
        print(f"  • Risk Level: {signal.risk_level.value}")
        print(f"  • Correlation Strength: {signal.correlation_strength:.2%}")
        print(f"  • Source Indices: {', '.join(signal.source_indices)}")
        print(f"  • Description: {signal.description}")
    
    print("\n📝 EXPLANATION:")
    print(decision.explanation)
    
    if decision.alternative_actions:
        print("\n🔄 ALTERNATIVE ACTIONS:")
        for i, alt in enumerate(decision.alternative_actions, 1):
            print(f"  {i}. {alt}")
    
    # ==================== JSON OUTPUT ====================
    
    print("\n" + "=" * 80)
    print("JSON OUTPUT (for Real-Time Feedback Loop)")
    print("=" * 80)
    print(decision.to_json())
    
    print("\n" + "=" * 80)
    print("SYNTHESIS COMPLETE")
    print("=" * 80)
    
    return decision


def run_low_risk_example():
    """
    Execute a low-risk scenario for comparison
    """
    print("\n\n" + "=" * 80)
    print("LOW-RISK SCENARIO EXAMPLE")
    print("=" * 80)
    
    # Low-risk financial data
    financial_data = FinancialData(
        unpaid_invoices_spike=3.0,  # Only 3% spike
        client_id="CLIENT_Y_002",
        production_output_change=2.0,  # 2% increase
        budget_remaining_q3=25.0,  # 25% remaining
        timestamp=datetime.now()
    )
    
    # Minimal knowledge graph context
    kg_context = KnowledgeGraphContext(
        client_parent_status="Stable financial position",
        similar_historical_pattern=None,
        external_data_signals=[],
        risk_indicators=[]
    )
    
    # Low-impact scenarios
    scenarios = [
        ScenarioSimulation(
            scenario_id="SCENARIO_STABLE",
            description="Continue current operations",
            cash_flow_impact=0.0,
            margin_impact=0.0,
            probability=0.95,
            time_horizon_days=90
        ),
        ScenarioSimulation(
            scenario_id="SCENARIO_OPTIMIZE",
            description="Optimize payment collection timing",
            cash_flow_impact=3.0,  # 3% improvement
            margin_impact=-0.5,  # Minimal cost
            probability=0.80,
            time_horizon_days=45
        )
    ]
    
    engine = F360SynthesisEngine(risk_weight=0.5, profitability_weight=0.5)
    decision = engine.synthesize(financial_data, kg_context, scenarios)
    
    print(f"\n🎯 TACTICAL PRIORITY: {decision.tactical_priority.value}")
    print(f"📋 RECOMMENDED ACTION: {decision.recommended_action}")
    print(f"💯 CONFIDENCE SCORE: {decision.confidence_score:.2%}")
    print(f"\n⚠️  WEAK SIGNALS DETECTED: {len(decision.weak_signal_alert)}")
    
    print("\n" + decision.to_json())


if __name__ == "__main__":
    # Run high-risk example (from user's specification)
    high_risk_decision = run_example_synthesis()
    
    # Run low-risk example for comparison
    low_risk_decision = run_low_risk_example()
    
    print("\n\n✅ F360 Synthesis Engine demonstration complete!")
    print("The engine successfully transformed multimodal financial data into")
    print("prioritized, explainable tactical decisions with weak signal detection.")
