"""
Advanced Integration Example
Demonstrates F360 Synthesis Engine with configuration presets and external system integration patterns
"""

from datetime import datetime
from f360_synthesis_engine import (
    F360SynthesisEngine,
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation,
    Priority
)
from config import ConfigPresets, SynthesisConfig


class MockERPSystem:
    """Mock ERP system for demonstration"""
    
    def get_client_financial_snapshot(self, client_id: str) -> FinancialData:
        """Simulate ERP data retrieval"""
        # In production: query SAP/Oracle/Dynamics
        return FinancialData(
            unpaid_invoices_spike=18.0,
            client_id=client_id,
            production_output_change=-15.0,
            budget_remaining_q3=4.0,
            timestamp=datetime.now()
        )


class MockKnowledgeGraph:
    """Mock Knowledge Graph for demonstration"""
    
    def query_client_context(self, client_id: str) -> KnowledgeGraphContext:
        """Simulate Knowledge Graph query"""
        # In production: Neo4j/GraphDB query
        return KnowledgeGraphContext(
            client_parent_status="Chapter 11 bankruptcy proceedings initiated",
            similar_historical_pattern={
                "years_ago": 1.5,
                "cash_flow_delay_days": 45,
                "resolution": "Partial payment with extended terms",
                "final_outcome": "15% write-off, 85% recovered over 6 months"
            },
            external_data_signals=[
                "S&P credit rating downgrade (BBB to BB)",
                "SEC filing indicates asset restructuring",
                "Industry trade group warning on sector stress"
            ],
            risk_indicators=[
                "Payment delays: 5/6 recent invoices",
                "Communication: 60% reduction in response rate",
                "Order volume: -25% MoM"
            ]
        )


class MockScenarioSimulator:
    """Mock Scenario Simulation Engine"""
    
    def run_parallel_simulations(self, financial_data: FinancialData) -> list:
        """Simulate scenario generation"""
        # In production: Monte Carlo, ML-based simulations
        return [
            ScenarioSimulation(
                scenario_id="SCENARIO_BAU",
                description="Business as usual - no intervention",
                cash_flow_impact=-35.0,  # Severe deficit
                margin_impact=0.0,
                probability=0.80,
                time_horizon_days=45
            ),
            ScenarioSimulation(
                scenario_id="SCENARIO_EARLY_PAYMENT",
                description="Early payment discount (8% incentive)",
                cash_flow_impact=-2.0,  # Minimal deficit
                margin_impact=-8.0,
                probability=0.65,  # Lower probability - client may not accept
                time_horizon_days=20
            ),
            ScenarioSimulation(
                scenario_id="SCENARIO_PARTIAL_HEDGE",
                description="Partial payment + credit insurance hedge",
                cash_flow_impact=-8.0,
                margin_impact=-3.5,  # Insurance premium cost
                probability=0.85,
                time_horizon_days=35
            ),
            ScenarioSimulation(
                scenario_id="SCENARIO_WRITEOFF",
                description="Write-off + collections agency (aggressive)",
                cash_flow_impact=-15.0,  # Immediate write-off
                margin_impact=-12.0,  # Collection fees + relationship damage
                probability=0.90,
                time_horizon_days=15
            )
        ]


def demonstrate_crisis_mode():
    """
    Demonstrate F360 Synthesis in Crisis Mode
    Scenario: Critical client financial distress detected
    """
    print("=" * 80)
    print("F360 SYNTHESIS ENGINE - CRISIS MODE DEMONSTRATION")
    print("=" * 80)
    
    # Initialize with crisis mode configuration
    crisis_config = ConfigPresets.crisis()
    print(f"\n[CONFIG] Crisis Mode Activated")
    print(f"  • Risk Weight: {crisis_config.risk_weight} (90% risk focus)")
    print(f"  • Profitability Weight: {crisis_config.profitability_weight}")
    print(f"  • Sensitivity: Maximum (early warning thresholds lowered)")
    
    engine = F360SynthesisEngine(
        risk_weight=crisis_config.risk_weight,
        profitability_weight=crisis_config.profitability_weight
    )
    
    # Simulate external system integration
    erp = MockERPSystem()
    kg = MockKnowledgeGraph()
    simulator = MockScenarioSimulator()
    
    client_id = "CRITICAL_CLIENT_XYZ"
    
    print(f"\n[INTEGRATION] Retrieving data for client: {client_id}")
    
    # Step 1: Query ERP
    print("  1. ERP System Query...")
    financial_data = erp.get_client_financial_snapshot(client_id)
    print(f"     ✓ Retrieved: {financial_data.unpaid_invoices_spike}% invoice spike")
    
    # Step 2: Query Knowledge Graph
    print("  2. Knowledge Graph Query...")
    kg_context = kg.query_client_context(client_id)
    print(f"     ✓ Retrieved: {len(kg_context.external_data_signals)} external signals")
    
    # Step 3: Run Scenario Simulations
    print("  3. Scenario Simulation Engine...")
    scenarios = simulator.run_parallel_simulations(financial_data)
    print(f"     ✓ Generated: {len(scenarios)} parallel scenarios")
    
    # Step 4: Execute Synthesis
    print("\n[SYNTHESIS] Executing Weighted Decision Fusion...")
    decision = engine.synthesize(financial_data, kg_context, scenarios)
    
    # Output Results
    print("\n" + "=" * 80)
    print("CRISIS MODE TACTICAL DECISION")
    print("=" * 80)
    
    print(f"\n🚨 TACTICAL PRIORITY: {decision.tactical_priority.value}")
    print(f"📋 RECOMMENDED ACTION: {decision.recommended_action}")
    print(f"💯 CONFIDENCE: {decision.confidence_score:.1%}")
    
    print(f"\n📊 PREDICTED OUTCOME:")
    for key, val in decision.predicted_financial_outcome.items():
        print(f"  • {key}: {val}")
    
    print(f"\n⚠️  WEAK SIGNALS DETECTED: {len(decision.weak_signal_alert)}")
    for i, signal in enumerate(decision.weak_signal_alert, 1):
        print(f"\n  [{i}] {signal.signal_type}")
        print(f"      Risk: {signal.risk_level.value} | Correlation: {signal.correlation_strength:.0%}")
        print(f"      {signal.description}")
    
    print(f"\n📝 EXECUTIVE SUMMARY:")
    print(decision.explanation)
    
    print("\n" + "=" * 80)
    
    return decision


def demonstrate_mode_comparison():
    """
    Compare decision output across different operational modes
    Same financial situation, different risk appetites
    """
    print("\n\n" + "=" * 80)
    print("MODE COMPARISON: Same Data, Different Risk Tolerances")
    print("=" * 80)
    
    # Single financial scenario
    financial_data = FinancialData(
        unpaid_invoices_spike=12.0,
        client_id="COMPARISON_CLIENT",
        production_output_change=-8.0,
        budget_remaining_q3=12.0
    )
    
    kg_context = KnowledgeGraphContext(
        client_parent_status="Stable but industry headwinds",
        similar_historical_pattern={
            "years_ago": 3,
            "cash_flow_delay_days": 20,
            "resolution": "Payment plan negotiated"
        }
    )
    
    scenarios = [
        ScenarioSimulation("BAU", "Business as usual", -15.0, 0.0, 0.8, 60),
        ScenarioSimulation("DISCOUNT", "Early payment discount", -3.0, -6.0, 0.75, 30),
        ScenarioSimulation("HEDGE", "Hedge strategy", -7.0, -2.0, 0.85, 40)
    ]
    
    modes = [
        ("Conservative", ConfigPresets.conservative()),
        ("Balanced", ConfigPresets.balanced()),
        ("Aggressive", ConfigPresets.aggressive())
    ]
    
    results = []
    
    for mode_name, config in modes:
        engine = F360SynthesisEngine(
            risk_weight=config.risk_weight,
            profitability_weight=config.profitability_weight
        )
        
        decision = engine.synthesize(financial_data, kg_context, scenarios)
        results.append((mode_name, decision))
    
    # Display comparison
    print("\n{:<15} | {:<10} | {:<30} | {:<12}".format(
        "Mode", "Priority", "Recommended Action", "Confidence"
    ))
    print("-" * 80)
    
    for mode_name, decision in results:
        print("{:<15} | {:<10} | {:<30} | {:<12}".format(
            mode_name,
            decision.tactical_priority.value,
            decision.recommended_action[:28] + "..." if len(decision.recommended_action) > 28 
                else decision.recommended_action,
            f"{decision.confidence_score:.0%}"
        ))
    
    print("\n" + "=" * 80)
    
    # Detailed comparison
    print("\nDETAILED ANALYSIS:")
    for mode_name, decision in results:
        print(f"\n{mode_name} Mode:")
        print(f"  Cash Flow Impact: {decision.predicted_financial_outcome['cash_flow_impact_pct']}%")
        print(f"  Margin Impact: {decision.predicted_financial_outcome['margin_impact_pct']}%")
        print(f"  Weak Signals: {len(decision.weak_signal_alert)}")


def demonstrate_feedback_loop():
    """
    Demonstrate Real-Time Feedback Loop integration
    Shows how predicted outcomes can be validated against actuals
    """
    print("\n\n" + "=" * 80)
    print("REAL-TIME FEEDBACK LOOP DEMONSTRATION")
    print("=" * 80)
    
    # Initial synthesis
    engine = F360SynthesisEngine()
    
    financial_data = FinancialData(
        unpaid_invoices_spike=10.0,
        client_id="FEEDBACK_CLIENT",
        production_output_change=-6.0,
        budget_remaining_q3=15.0
    )
    
    kg_context = KnowledgeGraphContext(
        client_parent_status="Stable"
    )
    
    scenarios = [
        ScenarioSimulation("OPTION_A", "Maintain current terms", -12.0, 0.0, 0.8, 45),
        ScenarioSimulation("OPTION_B", "Early payment incentive", -2.0, -4.0, 0.85, 25)
    ]
    
    print("\n[PHASE 1] Initial Synthesis")
    decision = engine.synthesize(financial_data, kg_context, scenarios)
    
    predicted_outcome = decision.predicted_financial_outcome
    print(f"  Recommended: {decision.recommended_action}")
    print(f"  Predicted Cash Flow Impact: {predicted_outcome['cash_flow_impact_pct']}%")
    print(f"  Predicted Margin Impact: {predicted_outcome['margin_impact_pct']}%")
    print(f"  Time Horizon: {predicted_outcome['time_to_impact_days']} days")
    
    # Simulate action execution and actual results
    print(f"\n[PHASE 2] Action Executed: {decision.recommended_action}")
    print(f"  Waiting {predicted_outcome['time_to_impact_days']} days...")
    
    # Simulate actual outcome (slightly different from prediction)
    actual_outcome = {
        "cash_flow_impact_pct": predicted_outcome['cash_flow_impact_pct'] + 0.5,  # Slight variance
        "margin_impact_pct": predicted_outcome['margin_impact_pct'] - 0.3,
        "time_to_impact_days": predicted_outcome['time_to_impact_days'] - 2
    }
    
    print("\n[PHASE 3] Actual Results Measured")
    print(f"  Actual Cash Flow Impact: {actual_outcome['cash_flow_impact_pct']}%")
    print(f"  Actual Margin Impact: {actual_outcome['margin_impact_pct']}%")
    print(f"  Actual Time: {actual_outcome['time_to_impact_days']} days")
    
    # Calculate gap
    print("\n[PHASE 4] Gap Analysis (Predicted vs Actual)")
    cash_flow_gap = abs(predicted_outcome['cash_flow_impact_pct'] - actual_outcome['cash_flow_impact_pct'])
    margin_gap = abs(predicted_outcome['margin_impact_pct'] - actual_outcome['margin_impact_pct'])
    time_gap = abs(predicted_outcome['time_to_impact_days'] - actual_outcome['time_to_impact_days'])
    
    print(f"  Cash Flow Gap: {cash_flow_gap:.2f}%")
    print(f"  Margin Gap: {margin_gap:.2f}%")
    print(f"  Time Gap: {time_gap} days")
    
    accuracy = 100 - ((cash_flow_gap + margin_gap) / 2)
    print(f"\n  Model Accuracy: {accuracy:.1f}%")
    
    if accuracy > 95:
        print("  ✓ Model performing excellently - no adjustments needed")
    elif accuracy > 85:
        print("  ⚠ Model performing well - minor calibration recommended")
    else:
        print("  ⚠ Model requires recalibration - significant variance detected")
    
    print("\n  → Feedback loop complete: Results fed back to improve future synthesis")


if __name__ == "__main__":
    # Run all demonstrations
    
    # 1. Crisis mode with critical client
    crisis_decision = demonstrate_crisis_mode()
    
    # 2. Compare different operational modes
    demonstrate_mode_comparison()
    
    # 3. Demonstrate feedback loop
    demonstrate_feedback_loop()
    
    print("\n\n" + "=" * 80)
    print("✅ ADVANCED INTEGRATION DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • Crisis mode prioritizes cash flow protection over profitability")
    print("  • Different modes produce different tactical decisions")
    print("  • Feedback loop enables continuous model improvement")
    print("  • Multi-source integration provides comprehensive risk assessment")
