"""
Unit Tests for F360 Financial Synthesis Engine
"""

import unittest
from datetime import datetime
from f360_synthesis_engine import (
    F360SynthesisEngine,
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation,
    Priority,
    RiskLevel,
    WeakSignal
)


class TestFinancialData(unittest.TestCase):
    """Test FinancialData dataclass"""
    
    def test_financial_data_creation(self):
        """Test creation of FinancialData"""
        data = FinancialData(
            unpaid_invoices_spike=15.0,
            client_id="TEST_CLIENT",
            production_output_change=-10.0,
            budget_remaining_q3=5.0
        )
        
        self.assertEqual(data.unpaid_invoices_spike, 15.0)
        self.assertEqual(data.client_id, "TEST_CLIENT")
        self.assertIsInstance(data.timestamp, datetime)


class TestKnowledgeGraphContext(unittest.TestCase):
    """Test KnowledgeGraphContext dataclass"""
    
    def test_kg_context_with_historical_pattern(self):
        """Test KG context with historical pattern"""
        context = KnowledgeGraphContext(
            client_parent_status="Restructuring",
            similar_historical_pattern={
                "years_ago": 2,
                "cash_flow_delay_days": 30
            }
        )
        
        self.assertEqual(context.client_parent_status, "Restructuring")
        self.assertIsNotNone(context.similar_historical_pattern)
        self.assertEqual(context.similar_historical_pattern["years_ago"], 2)


class TestScenarioSimulation(unittest.TestCase):
    """Test ScenarioSimulation dataclass"""
    
    def test_scenario_creation(self):
        """Test scenario simulation creation"""
        scenario = ScenarioSimulation(
            scenario_id="TEST_SCENARIO",
            description="Test scenario",
            cash_flow_impact=-20.0,
            margin_impact=-5.0,
            probability=0.85,
            time_horizon_days=60
        )
        
        self.assertEqual(scenario.scenario_id, "TEST_SCENARIO")
        self.assertEqual(scenario.cash_flow_impact, -20.0)


class TestF360SynthesisEngine(unittest.TestCase):
    """Test F360SynthesisEngine core functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = F360SynthesisEngine(risk_weight=0.6, profitability_weight=0.4)
        
        self.financial_data = FinancialData(
            unpaid_invoices_spike=15.0,
            client_id="TEST_CLIENT",
            production_output_change=-12.0,
            budget_remaining_q3=5.0
        )
        
        self.kg_context = KnowledgeGraphContext(
            client_parent_status="Undergoing restructuring",
            similar_historical_pattern={
                "years_ago": 2,
                "cash_flow_delay_days": 30,
                "resolution": "Early payment discount"
            }
        )
        
        self.scenarios = [
            ScenarioSimulation(
                scenario_id="SCENARIO_A",
                description="Business as usual",
                cash_flow_impact=-20.0,
                margin_impact=0.0,
                probability=0.85,
                time_horizon_days=60
            ),
            ScenarioSimulation(
                scenario_id="SCENARIO_B",
                description="Early payment discount",
                cash_flow_impact=0.0,
                margin_impact=-5.0,
                probability=0.90,
                time_horizon_days=30
            )
        ]
    
    def test_engine_initialization(self):
        """Test engine initialization with weights"""
        self.assertEqual(self.engine.risk_weight, 0.6)
        self.assertEqual(self.engine.profitability_weight, 0.4)
    
    def test_aggregate_sources(self):
        """Test multi-source aggregation"""
        aggregated = self.engine.aggregate_sources(
            self.financial_data,
            self.kg_context,
            self.scenarios
        )
        
        self.assertIn("financial_stress_score", aggregated)
        self.assertIn("historical_pattern_match", aggregated)
        self.assertIn("scenario_risk_range", aggregated)
        self.assertTrue(aggregated["historical_pattern_match"])
    
    def test_detect_weak_signals(self):
        """Test weak signal detection"""
        aggregated = self.engine.aggregate_sources(
            self.financial_data,
            self.kg_context,
            self.scenarios
        )
        
        weak_signals = self.engine.detect_weak_signals(
            self.financial_data,
            self.kg_context,
            aggregated
        )
        
        self.assertIsInstance(weak_signals, list)
        self.assertGreater(len(weak_signals), 0)
        
        # Check for production-client systemic risk signal
        signal_types = [ws.signal_type for ws in weak_signals]
        self.assertIn("Production-Client_Systemic_Risk", signal_types)
    
    def test_weak_signal_structure(self):
        """Test weak signal data structure"""
        aggregated = self.engine.aggregate_sources(
            self.financial_data,
            self.kg_context,
            self.scenarios
        )
        
        weak_signals = self.engine.detect_weak_signals(
            self.financial_data,
            self.kg_context,
            aggregated
        )
        
        for signal in weak_signals:
            self.assertIsInstance(signal, WeakSignal)
            self.assertIsInstance(signal.signal_type, str)
            self.assertIsInstance(signal.correlation_strength, float)
            self.assertIsInstance(signal.source_indices, list)
            self.assertIsInstance(signal.risk_level, RiskLevel)
    
    def test_weighted_decision_fusion(self):
        """Test weighted decision fusion algorithm"""
        aggregated = self.engine.aggregate_sources(
            self.financial_data,
            self.kg_context,
            self.scenarios
        )
        
        weak_signals = self.engine.detect_weak_signals(
            self.financial_data,
            self.kg_context,
            aggregated
        )
        
        best_scenario = self.engine.weighted_decision_fusion(
            self.scenarios,
            weak_signals,
            aggregated
        )
        
        self.assertIsInstance(best_scenario, ScenarioSimulation)
        # Should select SCENARIO_B (early payment) due to risk weighting
        self.assertEqual(best_scenario.scenario_id, "SCENARIO_B")
    
    def test_prioritize_and_explain(self):
        """Test prioritization and explainability"""
        aggregated = self.engine.aggregate_sources(
            self.financial_data,
            self.kg_context,
            self.scenarios
        )
        
        weak_signals = self.engine.detect_weak_signals(
            self.financial_data,
            self.kg_context,
            aggregated
        )
        
        best_scenario = self.engine.weighted_decision_fusion(
            self.scenarios,
            weak_signals,
            aggregated
        )
        
        decision = self.engine.prioritize_and_explain(
            best_scenario,
            weak_signals,
            self.financial_data,
            self.kg_context,
            self.scenarios
        )
        
        self.assertIsInstance(decision.tactical_priority, Priority)
        self.assertEqual(decision.tactical_priority, Priority.HIGH)
        self.assertIsInstance(decision.recommended_action, str)
        self.assertIsInstance(decision.explanation, str)
        self.assertGreater(len(decision.explanation), 50)
    
    def test_full_synthesis_pipeline(self):
        """Test complete synthesis pipeline"""
        decision = self.engine.synthesize(
            self.financial_data,
            self.kg_context,
            self.scenarios
        )
        
        self.assertIsInstance(decision.tactical_priority, Priority)
        self.assertIsInstance(decision.recommended_action, str)
        self.assertIsInstance(decision.explanation, str)
        self.assertIsInstance(decision.weak_signal_alert, list)
        self.assertIsInstance(decision.predicted_financial_outcome, dict)
        self.assertIsInstance(decision.confidence_score, float)
        
        # Validate JSON output
        json_output = decision.to_json()
        self.assertIn("tactical_priority", json_output)
        self.assertIn("recommended_action", json_output)
    
    def test_calculate_financial_stress(self):
        """Test financial stress score calculation"""
        stress_score = self.engine._calculate_financial_stress(self.financial_data)
        
        self.assertIsInstance(stress_score, float)
        self.assertGreaterEqual(stress_score, 0.0)
        self.assertLessEqual(stress_score, 1.0)
    
    def test_correlate_production_finance(self):
        """Test production-finance correlation"""
        correlation = self.engine._correlate_production_finance(-10.0, 15.0)
        
        self.assertIsInstance(correlation, float)
        self.assertGreater(correlation, 0.0)  # Negative production + positive invoice = correlation
    
    def test_low_risk_scenario(self):
        """Test engine behavior with low-risk data"""
        low_risk_data = FinancialData(
            unpaid_invoices_spike=2.0,
            client_id="LOW_RISK_CLIENT",
            production_output_change=5.0,
            budget_remaining_q3=30.0
        )
        
        low_risk_kg = KnowledgeGraphContext(
            client_parent_status="Stable",
            similar_historical_pattern=None
        )
        
        low_risk_scenarios = [
            ScenarioSimulation(
                scenario_id="STABLE",
                description="Continue operations",
                cash_flow_impact=0.0,
                margin_impact=0.0,
                probability=0.95,
                time_horizon_days=90
            )
        ]
        
        decision = self.engine.synthesize(
            low_risk_data,
            low_risk_kg,
            low_risk_scenarios
        )
        
        # Should have low/medium priority
        self.assertIn(decision.tactical_priority, [Priority.LOW, Priority.MEDIUM])
        # Should have fewer weak signals
        self.assertLessEqual(len(decision.weak_signal_alert), 1)


class TestWeightAdjustment(unittest.TestCase):
    """Test dynamic weight adjustment based on weak signals"""
    
    def test_risk_weight_increase_on_critical_signal(self):
        """Test that risk weight increases when critical signals detected"""
        engine = F360SynthesisEngine(risk_weight=0.6, profitability_weight=0.4)
        
        # Create critical weak signal
        critical_signal = WeakSignal(
            signal_type="CRITICAL_TEST",
            correlation_strength=0.9,
            source_indices=["TEST"],
            risk_level=RiskLevel.CRITICAL,
            description="Test critical signal"
        )
        
        scenarios = [
            ScenarioSimulation(
                scenario_id="SAFE",
                description="Safe option",
                cash_flow_impact=0.0,
                margin_impact=-10.0,  # High margin cost
                probability=0.9,
                time_horizon_days=30
            ),
            ScenarioSimulation(
                scenario_id="RISKY",
                description="Risky option",
                cash_flow_impact=-15.0,  # Cash flow risk
                margin_impact=0.0,
                probability=0.9,
                time_horizon_days=30
            )
        ]
        
        # With critical signal, should prefer SAFE (cash flow protection)
        best_scenario = engine.weighted_decision_fusion(
            scenarios,
            [critical_signal],
            {}
        )
        
        self.assertEqual(best_scenario.scenario_id, "SAFE")


class TestJSONOutput(unittest.TestCase):
    """Test JSON output format"""
    
    def test_json_output_format(self):
        """Test that JSON output contains all required fields"""
        engine = F360SynthesisEngine()
        
        financial_data = FinancialData(
            unpaid_invoices_spike=10.0,
            client_id="JSON_TEST",
            production_output_change=-5.0,
            budget_remaining_q3=15.0
        )
        
        kg_context = KnowledgeGraphContext(
            client_parent_status="Test status"
        )
        
        scenarios = [
            ScenarioSimulation(
                scenario_id="TEST",
                description="Test scenario",
                cash_flow_impact=-10.0,
                margin_impact=-2.0,
                probability=0.8,
                time_horizon_days=45
            )
        ]
        
        decision = engine.synthesize(financial_data, kg_context, scenarios)
        json_output = decision.to_json()
        
        # Validate JSON structure
        import json
        parsed = json.loads(json_output)
        
        self.assertIn("tactical_priority", parsed)
        self.assertIn("recommended_action", parsed)
        self.assertIn("explanation", parsed)
        self.assertIn("weak_signal_alert", parsed)
        self.assertIn("predicted_financial_outcome", parsed)
        self.assertIn("confidence_score", parsed)
        
        # Validate predicted outcome structure
        outcome = parsed["predicted_financial_outcome"]
        self.assertIn("cash_flow_impact_pct", outcome)
        self.assertIn("margin_impact_pct", outcome)
        self.assertIn("time_to_impact_days", outcome)
        self.assertIn("probability", outcome)


if __name__ == "__main__":
    unittest.main(verbosity=2)
