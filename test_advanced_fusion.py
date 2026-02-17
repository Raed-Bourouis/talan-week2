"""
Unit Tests for Advanced Fusion Algorithms
Tests Dempster-Shafer Theory, Bayesian Fusion, and Multi-Strategy Engine
"""

import unittest
import math
from dempster_shafer import (
    DempsterShaferEngine,
    EvidenceSource,
    FinancialEvidenceBuilder
)
from bayesian_fusion import (
    BayesianFusionEngine,
    BayesianEvidence,
    BayesianEvidenceBuilder
)
from multi_strategy_engine import (
    MultiStrategyEngine,
    FusionStrategy
)
from f360_synthesis_engine import (
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation,
    Priority
)
from datetime import datetime


# ============================================================
# Dempster-Shafer Tests
# ============================================================

class TestDempsterShaferEngine(unittest.TestCase):
    """Test DST core functionality"""
    
    def setUp(self):
        self.frame = {"A", "B", "C"}
        self.engine = DempsterShaferEngine(self.frame)
    
    def test_power_set_generation(self):
        """Power set should have 2^n - 1 elements (excluding empty set)"""
        self.assertEqual(len(self.engine.power_set), 7)  # 2^3 - 1
    
    def test_mass_function_creation(self):
        """Create mass function with auto-ignorance"""
        mass = self.engine.create_mass_function({"A": 0.3, "B": 0.2})
        total = sum(mass.values())
        self.assertAlmostEqual(total, 1.0, places=5)
    
    def test_vacuous_mass(self):
        """Vacuous mass function (total ignorance)"""
        mass = self.engine.create_mass_function({}, ignorance=1.0)
        theta = frozenset(self.frame)
        self.assertAlmostEqual(mass[theta], 1.0, places=5)
    
    def test_dempster_combination_basic(self):
        """Basic Dempster combination of two sources"""
        m1 = {
            frozenset(["A"]): 0.6,
            frozenset(self.frame): 0.4
        }
        m2 = {
            frozenset(["A"]): 0.5,
            frozenset(self.frame): 0.5
        }
        combined, conflict = self.engine.combine(m1, m2)
        
        # Should strengthen belief in A
        a_mass = combined.get(frozenset(["A"]), 0)
        self.assertGreater(a_mass, 0.6)  # Combined > individual
        self.assertLess(conflict, 0.5)
    
    def test_conflicting_evidence(self):
        """High conflict between contradictory sources"""
        m1 = {
            frozenset(["A"]): 0.9,
            frozenset(self.frame): 0.1
        }
        m2 = {
            frozenset(["B"]): 0.9,
            frozenset(self.frame): 0.1
        }
        combined, conflict = self.engine.combine(m1, m2)
        
        # Should have high conflict
        self.assertGreater(conflict, 0.5)
    
    def test_belief_plausibility_ordering(self):
        """Belief ≤ Plausibility always"""
        mass = {
            frozenset(["A"]): 0.4,
            frozenset(["A", "B"]): 0.3,
            frozenset(self.frame): 0.3
        }
        
        for scenario in self.frame:
            singleton = frozenset([scenario])
            bel = self.engine.belief(mass, singleton)
            pl = self.engine.plausibility(mass, singleton)
            self.assertLessEqual(bel, pl + 1e-10)
    
    def test_pignistic_probability_sums_to_one(self):
        """Pignistic transform should produce valid probability distribution"""
        mass = {
            frozenset(["A"]): 0.4,
            frozenset(["B"]): 0.2,
            frozenset(self.frame): 0.4
        }
        bet_p = self.engine.pignistic_transform(mass)
        total = sum(bet_p.values())
        self.assertAlmostEqual(total, 1.0, places=5)
    
    def test_discount_evidence(self):
        """Discounting should transfer mass to theta"""
        mass = {
            frozenset(["A"]): 0.8,
            frozenset(self.frame): 0.2
        }
        discounted = self.engine.discount_evidence(mass, reliability=0.5)
        
        # A should have less mass
        self.assertLess(
            discounted[frozenset(["A"])], 
            mass[frozenset(["A"])]
        )
        # Theta should have more mass
        self.assertGreater(
            discounted[frozenset(self.frame)],
            mass[frozenset(self.frame)]
        )
    
    def test_full_fusion_pipeline(self):
        """Test complete DST fusion"""
        sources = [
            EvidenceSource(
                name="Source1",
                mass_function={
                    frozenset(["A"]): 0.5,
                    frozenset(self.frame): 0.5
                },
                reliability=0.8
            ),
            EvidenceSource(
                name="Source2",
                mass_function={
                    frozenset(["A"]): 0.6,
                    frozenset(["B"]): 0.1,
                    frozenset(self.frame): 0.3
                },
                reliability=0.9
            )
        ]
        
        result = self.engine.fuse(sources)
        
        self.assertEqual(result.decision, "A")  # A should win
        self.assertGreater(result.confidence, 0.0)
        self.assertIn("A", result.pignistic_probability)
    
    def test_evidence_validation(self):
        """Invalid mass function should raise error"""
        source = EvidenceSource(
            name="Invalid",
            mass_function={frozenset(["A"]): 0.5}  # Doesn't sum to 1
        )
        with self.assertRaises(ValueError):
            source.validate()


class TestFinancialEvidenceBuilder(unittest.TestCase):
    """Test DST financial evidence builders"""
    
    def test_invoice_evidence_high_spike(self):
        """High invoice spike should favor risk scenario"""
        evidence = FinancialEvidenceBuilder.from_invoice_data(
            ["RISK", "SAFE"], 25.0, "RISK", "SAFE"
        )
        risk_mass = evidence.mass_function.get(frozenset(["RISK"]), 0)
        safe_mass = evidence.mass_function.get(frozenset(["SAFE"]), 0)
        self.assertGreater(risk_mass, safe_mass)
    
    def test_invoice_evidence_low_spike(self):
        """Low invoice spike should favor safe scenario"""
        evidence = FinancialEvidenceBuilder.from_invoice_data(
            ["RISK", "SAFE"], 2.0, "RISK", "SAFE"
        )
        risk_mass = evidence.mass_function.get(frozenset(["RISK"]), 0)
        safe_mass = evidence.mass_function.get(frozenset(["SAFE"]), 0)
        self.assertLess(risk_mass, safe_mass)
    
    def test_production_evidence(self):
        """Production decline should favor risk"""
        evidence = FinancialEvidenceBuilder.from_production_data(
            ["RISK", "SAFE"], -20.0, "RISK", "SAFE"
        )
        evidence.validate()  # Should not raise
    
    def test_budget_evidence_critical(self):
        """Critical budget should strongly favor risk"""
        evidence = FinancialEvidenceBuilder.from_budget_data(
            ["RISK", "SAFE"], 3.0, "RISK", "SAFE"
        )
        risk_mass = evidence.mass_function.get(frozenset(["RISK"]), 0)
        self.assertGreater(risk_mass, 0.5)


# ============================================================
# Bayesian Fusion Tests
# ============================================================

class TestBayesianFusionEngine(unittest.TestCase):
    """Test Bayesian fusion core functionality"""
    
    def setUp(self):
        self.scenarios = ["A", "B", "C"]
        self.engine = BayesianFusionEngine(self.scenarios)
    
    def test_uniform_prior(self):
        """Default prior should be uniform"""
        for scenario in self.scenarios:
            self.assertAlmostEqual(
                self.engine.prior[scenario], 
                1.0 / 3.0, 
                places=5
            )
    
    def test_custom_prior(self):
        """Custom prior should be preserved"""
        prior = {"A": 0.5, "B": 0.3, "C": 0.2}
        engine = BayesianFusionEngine(self.scenarios, prior=prior)
        self.assertAlmostEqual(engine.prior["A"], 0.5)
    
    def test_single_update(self):
        """Single evidence update should shift posterior"""
        evidence = BayesianEvidence(
            name="Test",
            likelihoods={"A": 0.9, "B": 0.3, "C": 0.1}
        )
        
        posterior = self.engine.update(self.engine.prior, evidence)
        
        # A should now have highest probability
        self.assertGreater(posterior["A"], posterior["B"])
        self.assertGreater(posterior["A"], posterior["C"])
        
        # Should still sum to 1
        total = sum(posterior.values())
        self.assertAlmostEqual(total, 1.0, places=5)
    
    def test_multiple_updates_strengthen(self):
        """Consistent evidence should strengthen belief"""
        evidence1 = BayesianEvidence(
            name="E1",
            likelihoods={"A": 0.8, "B": 0.3, "C": 0.1}
        )
        evidence2 = BayesianEvidence(
            name="E2",
            likelihoods={"A": 0.7, "B": 0.4, "C": 0.2}
        )
        
        result = self.engine.fuse([evidence1, evidence2])
        
        self.assertEqual(result.decision, "A")
        self.assertGreater(result.posterior["A"], 0.5)
    
    def test_evidence_weight(self):
        """Lower weight should mean less influence"""
        strong = BayesianEvidence(
            name="Strong",
            likelihoods={"A": 0.9, "B": 0.1, "C": 0.1},
            weight=1.0
        )
        weak = BayesianEvidence(
            name="Weak",
            likelihoods={"A": 0.9, "B": 0.1, "C": 0.1},
            weight=0.3
        )
        
        result_strong = self.engine.fuse([strong])
        result_weak = self.engine.fuse([weak])
        
        # Strong evidence → more extreme posterior
        self.assertGreater(
            result_strong.posterior["A"],
            result_weak.posterior["A"]
        )
    
    def test_entropy_decreases_with_evidence(self):
        """Entropy should decrease as evidence is added"""
        evidence = BayesianEvidence(
            name="Clear",
            likelihoods={"A": 0.9, "B": 0.1, "C": 0.1}
        )
        
        result = self.engine.fuse([evidence])
        
        # Prior entropy (uniform) should be higher
        prior_entropy = self.engine._compute_entropy(self.engine.prior)
        self.assertGreater(prior_entropy, result.entropy)
    
    def test_kl_divergence_positive(self):
        """KL divergence from prior should be positive with informative evidence"""
        evidence = BayesianEvidence(
            name="Informative",
            likelihoods={"A": 0.8, "B": 0.2, "C": 0.1}
        )
        
        result = self.engine.fuse([evidence])
        self.assertGreater(result.kl_divergence_from_prior, 0.0)
    
    def test_evidence_trail_length(self):
        """Evidence trail should have n+1 entries (prior + n updates)"""
        evidence_list = [
            BayesianEvidence(name="E1", likelihoods={"A": 0.7, "B": 0.3, "C": 0.2}),
            BayesianEvidence(name="E2", likelihoods={"A": 0.6, "B": 0.4, "C": 0.3})
        ]
        
        result = self.engine.fuse(evidence_list)
        self.assertEqual(len(result.evidence_trail), 3)  # prior + 2 updates
    
    def test_bayes_factors(self):
        """Bayes factors should be computed for all alternatives"""
        evidence = BayesianEvidence(
            name="Test",
            likelihoods={"A": 0.8, "B": 0.2, "C": 0.1}
        )
        
        result = self.engine.fuse([evidence])
        
        # Should have factors comparing best to each alternative
        self.assertGreater(len(result.bayes_factors), 0)


class TestBayesianEvidenceBuilder(unittest.TestCase):
    """Test Bayesian evidence builders"""
    
    def test_invoice_likelihood(self):
        """Invoice evidence should produce valid likelihoods"""
        evidence = BayesianEvidenceBuilder.from_invoice_data(
            ["RISK", "SAFE"], 15.0, "RISK", "SAFE"
        )
        
        for scenario, likelihood in evidence.likelihoods.items():
            self.assertGreaterEqual(likelihood, 0.0)
            self.assertLessEqual(likelihood, 1.0)
    
    def test_kg_bankruptcy_high_risk(self):
        """Bankruptcy status should produce high risk likelihood"""
        evidence = BayesianEvidenceBuilder.from_knowledge_graph(
            ["RISK", "SAFE"], "Chapter 11 bankruptcy", True, "RISK", "SAFE"
        )
        
        self.assertGreater(
            evidence.likelihoods["RISK"],
            evidence.likelihoods["SAFE"]
        )


# ============================================================
# Multi-Strategy Engine Tests
# ============================================================

class TestMultiStrategyEngine(unittest.TestCase):
    """Test multi-strategy fusion"""
    
    def setUp(self):
        self.engine = MultiStrategyEngine(
            risk_weight=0.6,
            profitability_weight=0.4
        )
        
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
                "cash_flow_delay_days": 30
            }
        )
        
        self.scenarios = [
            ScenarioSimulation("A", "Business as usual", -20.0, 0.0, 0.85, 60),
            ScenarioSimulation("B", "Early payment discount", 0.0, -5.0, 0.90, 30),
            ScenarioSimulation("C", "Renegotiate terms", -10.0, -2.0, 0.70, 45)
        ]
    
    def test_weighted_average_strategy(self):
        """Weighted average should return valid result"""
        result = self.engine.run_weighted_average(
            self.financial_data, self.kg_context, self.scenarios
        )
        
        self.assertEqual(result.strategy, FusionStrategy.WEIGHTED_AVERAGE)
        self.assertIn(result.recommended_scenario, ["A", "B", "C"])
        self.assertAlmostEqual(sum(result.scenario_scores.values()), 1.0, places=3)
    
    def test_dempster_shafer_strategy(self):
        """DST should return valid result"""
        result = self.engine.run_dempster_shafer(
            self.financial_data, self.kg_context, self.scenarios
        )
        
        self.assertEqual(result.strategy, FusionStrategy.DEMPSTER_SHAFER)
        self.assertIn("conflict_degree", result.diagnostics)
        self.assertAlmostEqual(sum(result.scenario_scores.values()), 1.0, places=3)
    
    def test_bayesian_strategy(self):
        """Bayesian should return valid result"""
        result = self.engine.run_bayesian(
            self.financial_data, self.kg_context, self.scenarios
        )
        
        self.assertEqual(result.strategy, FusionStrategy.BAYESIAN)
        self.assertIn("entropy", result.diagnostics)
        self.assertAlmostEqual(sum(result.scenario_scores.values()), 1.0, places=3)
    
    def test_full_meta_fusion(self):
        """Full multi-strategy synthesis should work"""
        result = self.engine.synthesize(
            self.financial_data, self.kg_context, self.scenarios
        )
        
        # Should have all 3 strategy results
        self.assertEqual(len(result.strategy_results), 3)
        
        # Consensus should be a valid scenario
        self.assertIn(result.consensus_scenario, ["A", "B", "C"])
        
        # Agreement should be valid
        self.assertGreaterEqual(result.agreement_level, 0.0)
        self.assertLessEqual(result.agreement_level, 1.0)
        
        # Should produce valid tactical decision
        self.assertIsNotNone(result.tactical_decision)
        self.assertIsInstance(result.tactical_decision.tactical_priority, Priority)
    
    def test_meta_fusion_json_output(self):
        """JSON output should contain all required fields"""
        result = self.engine.synthesize(
            self.financial_data, self.kg_context, self.scenarios
        )
        
        import json
        parsed = json.loads(result.to_json())
        
        self.assertIn("meta_fusion", parsed)
        self.assertIn("strategy_breakdown", parsed)
        self.assertIn("tactical_decision", parsed)
        self.assertIn("consensus_scenario", parsed["meta_fusion"])
        self.assertIn("agreement_level", parsed["meta_fusion"])
    
    def test_agreement_calculation_unanimous(self):
        """All same recommendations → agreement = 1.0"""
        from multi_strategy_engine import StrategyResult
        
        results = {
            FusionStrategy.WEIGHTED_AVERAGE: StrategyResult(
                FusionStrategy.WEIGHTED_AVERAGE, "B", 0.8, {"A": 0.2, "B": 0.8}, {}
            ),
            FusionStrategy.DEMPSTER_SHAFER: StrategyResult(
                FusionStrategy.DEMPSTER_SHAFER, "B", 0.7, {"A": 0.3, "B": 0.7}, {}
            ),
            FusionStrategy.BAYESIAN: StrategyResult(
                FusionStrategy.BAYESIAN, "B", 0.9, {"A": 0.1, "B": 0.9}, {}
            )
        }
        
        agreement = self.engine.calculate_agreement(results)
        self.assertAlmostEqual(agreement, 1.0)
    
    def test_agreement_calculation_split(self):
        """All different recommendations → low agreement"""
        from multi_strategy_engine import StrategyResult
        
        results = {
            FusionStrategy.WEIGHTED_AVERAGE: StrategyResult(
                FusionStrategy.WEIGHTED_AVERAGE, "A", 0.8, {}, {}
            ),
            FusionStrategy.DEMPSTER_SHAFER: StrategyResult(
                FusionStrategy.DEMPSTER_SHAFER, "B", 0.7, {}, {}
            ),
            FusionStrategy.BAYESIAN: StrategyResult(
                FusionStrategy.BAYESIAN, "C", 0.9, {}, {}
            )
        }
        
        agreement = self.engine.calculate_agreement(results)
        self.assertAlmostEqual(agreement, 1.0 / 3.0, places=2)
    
    def test_single_strategy_execution(self):
        """Should work with only one strategy selected"""
        result = self.engine.synthesize(
            self.financial_data, self.kg_context, self.scenarios,
            strategies=[FusionStrategy.DEMPSTER_SHAFER]
        )
        
        self.assertEqual(len(result.strategy_results), 1)
        self.assertIn(FusionStrategy.DEMPSTER_SHAFER, result.strategy_results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
