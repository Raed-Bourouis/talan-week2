"""
Tests for the F360 Financial Assistant

Tests cover:
- Keyword search engine (Personne 2)
- Graph peers / knowledge graph (Personne 3)
- Simulation bridge (Personne 4)
- Assistant ask() function (integration)
- Intent detection
"""

import unittest
from keyword_search import (
    KeywordSearchEngine, Company, SearchResult,
    build_sample_knowledge_base, MatchType,
)
from graph_peers import (
    KnowledgeGraph, GraphEnrichment, RelationType,
)
from simulation_bridge import (
    SimulationBridge, SimulationRequest, SimulationSummary,
)
from assistant import (
    ask, FinancialAssistant, IntentDetector, AssistantResponse,
)


# ============================================================
# 1. Keyword Search Tests
# ============================================================

class TestKeywordSearch(unittest.TestCase):
    """Tests for keyword_search module."""

    def setUp(self):
        self.engine = KeywordSearchEngine(build_sample_knowledge_base())

    def test_search_restructuring(self):
        results = self.engine.search("restructuration")
        self.assertTrue(len(results) > 0)
        names = [r.company.name for r in results]
        # Orpea, Atos, Casino are restructuring
        self.assertTrue(
            any(n in names for n in ["Orpea", "Atos", "Casino Guichard"]),
            f"Expected restructuring companies, got {names}"
        )

    def test_search_technology(self):
        results = self.engine.search("technology")
        names = [r.company.name for r in results]
        self.assertIn("Atos", names)
        self.assertIn("Dassault Systèmes", names)

    def test_search_debt(self):
        results = self.engine.search("dette")  # French synonym of "debt"
        self.assertTrue(len(results) > 0)
        # Should find companies with debt keyword
        for r in results:
            has_debt = (
                "debt" in r.company.financial_keywords
                or "dette" in str(r.company.description).lower()
                or "debt" in r.company.tags
            )
            if has_debt:
                break
        else:
            self.fail("No debt-related company found via synonym 'dette'")

    def test_search_returns_scores(self):
        results = self.engine.search("Airbus")
        self.assertTrue(len(results) > 0)
        self.assertGreater(results[0].relevance_score, 0.0)
        self.assertIn("Airbus", results[0].company.name)

    def test_search_no_results(self):
        results = self.engine.search("xyznonexistent123")
        self.assertEqual(len(results), 0)

    def test_search_top_k(self):
        results = self.engine.search("cash flow", top_k=2)
        self.assertLessEqual(len(results), 2)

    def test_search_sector_filter(self):
        results = self.engine.search("production", sector_filter="Energy")
        for r in results:
            self.assertEqual(r.company.sector, "Energy")

    def test_search_risk_filter(self):
        results = self.engine.search("cash flow", risk_filter="critical")
        for r in results:
            self.assertEqual(r.company.risk_level, "critical")

    def test_synonym_matching(self):
        # "trésorerie" is a synonym of "cash flow"
        results = self.engine.search("trésorerie")
        self.assertTrue(len(results) > 0)

    def test_multi_keyword_query(self):
        results = self.engine.search("energy production growth")
        self.assertTrue(len(results) > 0)
        # TotalEnergies should be top
        self.assertEqual(results[0].company.name, "TotalEnergies")


# ============================================================
# 2. Knowledge Graph Tests
# ============================================================

class TestKnowledgeGraph(unittest.TestCase):
    """Tests for graph_peers module."""

    def setUp(self):
        self.graph = KnowledgeGraph()

    def test_get_peers_atos(self):
        peers = self.graph.get_peers("ENT-004")  # Atos
        self.assertTrue(len(peers) > 0)
        names = [p.company_name for p in peers]
        # Atos should have tech sector peers
        self.assertTrue(
            any(n in names for n in ["Dassault Systèmes", "Sopra Steria"]),
            f"Atos peers: {names}"
        )

    def test_get_peers_with_filter(self):
        peers = self.graph.get_peers(
            "ENT-004", relation_filter=RelationType.SECTOR_PEER
        )
        for p in peers:
            self.assertEqual(p.relation, RelationType.SECTOR_PEER)

    def test_enrich_casino(self):
        enrichment = self.graph.enrich("ENT-006")  # Casino
        self.assertEqual(enrichment.company_name, "Casino Guichard")
        self.assertTrue(len(enrichment.peers) > 0)
        self.assertGreater(enrichment.risk_contagion_score, 0.0)
        self.assertIn(enrichment.sector_health, ("healthy", "stressed", "critical", "unknown"))

    def test_enrich_summary_text(self):
        enrichment = self.graph.enrich("ENT-001")  # Airbus
        self.assertIn("Airbus", enrichment.summary)
        self.assertIn("connected entities", enrichment.summary)

    def test_risk_contagion(self):
        enrichment = self.graph.enrich("ENT-006")  # Casino — high contagion
        # Casino is connected to Orpea (critical) via risk contagion
        self.assertGreater(enrichment.risk_contagion_score, 0.0)

    def test_two_hop_traversal(self):
        peers_1hop = self.graph.get_peers("ENT-001", max_depth=1)
        peers_2hop = self.graph.get_peers("ENT-001", max_depth=2)
        self.assertGreaterEqual(len(peers_2hop), len(peers_1hop))


# ============================================================
# 3. Simulation Bridge Tests
# ============================================================

class TestSimulationBridge(unittest.TestCase):
    """Tests for simulation_bridge module."""

    def setUp(self):
        self.bridge = SimulationBridge()
        self.graph = KnowledgeGraph()
        self.company = Company(
            company_id="ENT-004",
            name="Atos",
            sector="Technology",
            risk_level="high",
            financial_keywords=["restructuring", "debt"],
            description="IT services under restructuring",
            status="restructuring",
            tags=["mid-cap"],
        )

    def test_simulate_returns_summary(self):
        enrichment = self.graph.enrich("ENT-004")
        result = self.bridge.simulate(
            SimulationRequest(company=self.company, graph_enrichment=enrichment)
        )
        self.assertIsInstance(result, SimulationSummary)
        self.assertEqual(result.company_name, "Atos")
        self.assertIn(result.priority, ("High", "Medium", "Low"))
        self.assertGreater(result.confidence, 0.0)

    def test_simulate_text_output(self):
        result = self.bridge.simulate(
            SimulationRequest(company=self.company)
        )
        text = result.to_text()
        self.assertIn("Atos", text)
        self.assertIn("SIMULATION RESULTS", text)

    def test_simulate_low_risk_company(self):
        low_risk = Company(
            company_id="ENT-007",
            name="Dassault Systèmes",
            sector="Technology",
            risk_level="low",
            financial_keywords=["growth"],
            description="Software company",
            status="active",
            tags=["large-cap"],
        )
        result = self.bridge.simulate(SimulationRequest(company=low_risk))
        # Low-risk should have higher confidence, lower priority
        self.assertGreater(result.confidence, 0.3)

    def test_strategy_breakdown(self):
        result = self.bridge.simulate(
            SimulationRequest(company=self.company)
        )
        self.assertIn("Weighted Average", result.strategy_breakdown)
        self.assertIn("Dempster-Shafer Theory", result.strategy_breakdown)
        self.assertIn("Bayesian Inference", result.strategy_breakdown)


# ============================================================
# 4. Intent Detection Tests
# ============================================================

class TestIntentDetector(unittest.TestCase):
    """Tests for the rule-based intent detector."""

    def test_detect_search(self):
        self.assertEqual(
            IntentDetector.detect("Find companies in technology"),
            "SEARCH"
        )

    def test_detect_search_french(self):
        self.assertEqual(
            IntentDetector.detect("Quelles entreprises sont dans le secteur énergie ?"),
            "SEARCH"
        )

    def test_detect_simulate(self):
        self.assertEqual(
            IntentDetector.detect("Simulate decision fusion for Atos"),
            "SIMULATE"
        )

    def test_detect_simulate_french(self):
        intent = IntentDetector.detect("Que recommandez-vous pour Casino ?")
        self.assertEqual(intent, "SIMULATE")

    def test_detect_peer(self):
        self.assertEqual(
            IntentDetector.detect("Show me the peers of Airbus in the graph"),
            "PEER"
        )

    def test_detect_risk(self):
        self.assertEqual(
            IntentDetector.detect("Which companies have critical risk?"),
            "RISK"
        )

    def test_detect_compare(self):
        self.assertEqual(
            IntentDetector.detect("Compare Atos versus Sopra Steria"),
            "COMPARE"
        )

    def test_detect_general(self):
        intent = IntentDetector.detect("hello")
        self.assertEqual(intent, "GENERAL")


# ============================================================
# 5. Full Assistant Integration Tests
# ============================================================

class TestAssistant(unittest.TestCase):
    """Integration tests for the ask() function."""

    def test_ask_returns_response(self):
        r = ask("Quelles entreprises sont en restructuration ?")
        self.assertIsInstance(r, AssistantResponse)
        self.assertTrue(len(r.text) > 0)
        self.assertTrue(len(r.sources) > 0)

    def test_ask_search_finds_companies(self):
        r = ask("technology companies")
        self.assertTrue(len(r.companies_found) > 0)
        names = [c["company_name"] for c in r.companies_found]
        self.assertTrue(any("Atos" in n or "Dassault" in n or "Sopra" in n for n in names))

    def test_ask_peer_enrichment(self):
        r = ask("What are the peers of Atos in the graph?")
        self.assertEqual(r.intent, "PEER")
        self.assertIn("graph_peers (Personne 3)", r.sources)
        self.assertTrue(len(r.graph_enrichments) > 0)

    def test_ask_simulation(self):
        r = ask("Simulate decision fusion for Casino")
        self.assertEqual(r.intent, "SIMULATE")
        self.assertIn("decision_fusion_simulation (Personne 4)", r.sources)
        self.assertTrue(len(r.simulations) > 0)
        self.assertIn("SIMULATION RESULTS", r.text)

    def test_ask_risk_analysis(self):
        r = ask("Which companies have critical risk?")
        self.assertEqual(r.intent, "RISK")
        # Should include risk analysis section
        self.assertIn("risque", r.text.lower())

    def test_ask_compare(self):
        r = ask("Compare Atos and Sopra Steria")
        self.assertEqual(r.intent, "COMPARE")
        self.assertIn("Comparaison", r.text)

    def test_ask_no_results(self):
        r = ask("xyznonexistent123")
        self.assertIn("Aucune", r.text)

    def test_ask_sources_always_present(self):
        r = ask("energy companies")
        self.assertIn("keyword_search (Personne 2)", r.sources)

    def test_ask_french_query(self):
        r = ask("Montre-moi les entreprises avec des problèmes de dette")
        self.assertTrue(len(r.companies_found) > 0)

    def test_ask_simulation_with_graph(self):
        r = ask("Simulate scenario for Atos")
        self.assertTrue(len(r.simulations) > 0)
        sim = r.simulations[0]
        self.assertIn("confidence", sim)
        self.assertGreater(sim["confidence"], 0.0)


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  F360 Assistant — Test Suite")
    print("=" * 60)
    unittest.main(verbosity=2)
