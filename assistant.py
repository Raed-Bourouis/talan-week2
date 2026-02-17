"""
F360 Financial Assistant — Rule-Based Q&A with Decision Fusion

A simple rule-based assistant that:
1. Parses the user query to detect intent (search / peers / simulate / general)
2. Uses keyword_search (Personne 2) to find relevant enterprises
3. Enriches with graph peers (Personne 3) when relationships are relevant
4. Runs decision-fusion simulation (Personne 4) when the user asks for it
5. Returns a formatted textual response + sources list

Usage:
    from assistant import ask
    response = ask("Quelles entreprises sont en restructuration ?")
    print(response.text)
    print(response.sources)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from keyword_search import (
    KeywordSearchEngine,
    Company,
    SearchResult,
    build_sample_knowledge_base,
)
from graph_peers import (
    KnowledgeGraph,
    GraphEnrichment,
    PeerInfo,
    RelationType,
)
from simulation_bridge import (
    SimulationBridge,
    SimulationRequest,
    SimulationSummary,
)


# ============================================================
# Response data structure
# ============================================================

@dataclass
class AssistantResponse:
    """Response returned by the ask() function."""
    text: str                           # Formatted response text
    sources: List[str]                  # List of source labels
    companies_found: List[Dict[str, Any]] = field(default_factory=list)
    graph_enrichments: List[Dict[str, Any]] = field(default_factory=list)
    simulations: List[Dict[str, Any]] = field(default_factory=list)
    intent: str = ""                    # Detected intent label


# ============================================================
# Intent detection — rule-based
# ============================================================

class IntentDetector:
    """
    Simple rule-based intent detector using keyword patterns.
    
    Intents:
        SEARCH      →  User wants to find / list companies
        PEER        →  User wants relationships / peers / graph info
        SIMULATE    →  User wants a decision fusion simulation
        RISK        →  User asks about risk / exposure
        COMPARE     →  User wants to compare companies
        GENERAL     →  Catch-all
    """

    INTENT_PATTERNS: Dict[str, List[str]] = {
        "SIMULATE": [
            r"simul",
            r"decision\s*fusion",
            r"scénario|scenario",
            r"prédiction|prediction",
            r"que\s*(faire|recommand|suggest)",
            r"what\s+(should|would|could|to\s+do)",
            r"recommend",
            r"action",
            r"forecast",
        ],
        "PEER": [
            r"pair|peer|peers",
            r"graph",
            r"relation|relationship",
            r"lié|liée|linked|connected",
            r"filiale|subsidiary",
            r"parent",
            r"supply\s*chain|chaîne",
            r"contagion",
            r"voisin|neighbor",
        ],
        "RISK": [
            r"risque|risk",
            r"exposure|exposition",
            r"danger",
            r"critical|critique",
            r"alert|alerte",
            r"watchlist",
            r"restructur",
            r"default|défaut",
            r"debt|dette",
            r"crisis|crise",
        ],
        "COMPARE": [
            r"compar",
            r"versus|vs\b",
            r"différence|difference",
            r"between",
            r"entre",
        ],
        "SEARCH": [
            r"cherch|search|find|trouv",
            r"list|liste",
            r"quelles|which|what",
            r"montre|show|display|affich",
            r"entreprise|company|société",
            r"secteur|sector",
        ],
    }

    @classmethod
    def detect(cls, query: str) -> str:
        """Detect the primary intent of a query."""
        q = query.lower()
        scores: Dict[str, int] = {}
        for intent, patterns in cls.INTENT_PATTERNS.items():
            count = sum(1 for p in patterns if re.search(p, q))
            scores[intent] = count

        best = max(scores, key=scores.get)  # type: ignore
        if scores[best] == 0:
            return "GENERAL"
        return best


# ============================================================
# Assistant core
# ============================================================

class FinancialAssistant:
    """
    Rule-based financial assistant integrating:
    - keyword_search (Personne 2)
    - graph_peers    (Personne 3)
    - simulation     (Personne 4)
    """

    def __init__(self):
        # Initialise components
        kb = build_sample_knowledge_base()
        self.search_engine = KeywordSearchEngine(kb)
        self.knowledge_graph = KnowledgeGraph()
        self.simulation_bridge = SimulationBridge()

    # ---- Main entry point ------------------------------------------

    def ask(self, query: str) -> AssistantResponse:
        """
        Answer a natural-language financial question.

        Steps:
            1. Detect intent
            2. Search for relevant companies
            3. Enrich with graph peers if needed
            4. Run simulation if requested
            5. Format and return response

        Args:
            query: Free-text question (FR or EN)

        Returns:
            AssistantResponse with .text, .sources, and structured data
        """
        intent = IntentDetector.detect(query)
        sources: List[str] = []

        # ---- Step 1: Keyword Search (always) ----
        search_results = self.search_engine.search(query, top_k=5)
        sources.append("keyword_search (Personne 2)")

        # ---- Step 2: Graph enrichment (if PEER / SIMULATE / RISK) ----
        enrichments: List[GraphEnrichment] = []
        if intent in ("PEER", "SIMULATE", "RISK", "COMPARE") and search_results:
            for sr in search_results[:3]:  # enrich top-3
                enr = self.knowledge_graph.enrich(sr.company.company_id)
                enrichments.append(enr)
            sources.append("graph_peers (Personne 3)")

        # ---- Step 3: Simulation (if SIMULATE) ----
        simulations: List[SimulationSummary] = []
        if intent == "SIMULATE" and search_results:
            # Simulate top-1 company
            target = search_results[0]
            enr = (enrichments[0]
                   if enrichments
                   else self.knowledge_graph.enrich(target.company.company_id))
            sim = self.simulation_bridge.simulate(
                SimulationRequest(company=target.company, graph_enrichment=enr)
            )
            simulations.append(sim)
            sources.append("decision_fusion_simulation (Personne 4)")

        # ---- Step 4: Format response ----
        text = self._format_response(intent, query, search_results,
                                      enrichments, simulations)

        return AssistantResponse(
            text=text,
            sources=sources,
            companies_found=[sr.to_dict() for sr in search_results],
            graph_enrichments=[
                {
                    "company": e.company_name,
                    "peers": len(e.peers),
                    "contagion_score": e.risk_contagion_score,
                    "sector_health": e.sector_health,
                    "supply_chain_risk": e.supply_chain_risk,
                    "summary": e.summary,
                }
                for e in enrichments
            ],
            simulations=[
                {
                    "company": s.company_name,
                    "action": s.recommended_action,
                    "priority": s.priority,
                    "confidence": round(s.confidence, 3),
                    "agreement": round(s.agreement_level, 3),
                }
                for s in simulations
            ],
            intent=intent,
        )

    # ---- Formatting ------------------------------------------------

    def _format_response(
        self,
        intent: str,
        query: str,
        results: List[SearchResult],
        enrichments: List[GraphEnrichment],
        simulations: List[SimulationSummary],
    ) -> str:
        """Build the formatted textual answer."""
        parts: List[str] = []

        # Header
        if not results:
            return (
                f"Aucune entreprise trouvée pour la requête : « {query} ».\n"
                f"Essayez d'autres mots-clés (ex: restructuration, dette, "
                f"cash flow, technology, energy…)."
            )

        # ---- SEARCH / GENERAL : list companies ----
        parts.append(f"🔍  {len(results)} entreprise(s) trouvée(s) :\n")
        for i, sr in enumerate(results, 1):
            c = sr.company
            parts.append(
                f"  {i}. {c.name} ({c.sector})\n"
                f"     Risque: {c.risk_level.upper()}  |  "
                f"Statut: {c.status}  |  "
                f"Pertinence: {sr.relevance_score:.0%}\n"
                f"     Mots-clés matchés: {', '.join(sr.matched_keywords)}\n"
            )

        # ---- PEER : show graph relationships ----
        if intent in ("PEER", "RISK", "COMPARE") and enrichments:
            parts.append("\n📊  Enrichissement via le graphe de connaissances :\n")
            for enr in enrichments:
                parts.append(f"  ▸ {enr.company_name}:")
                parts.append(f"    Pairs connectés : {len(enr.peers)}")
                parts.append(
                    f"    Score de contagion : {enr.risk_contagion_score:.0%}"
                )
                parts.append(f"    Santé sectorielle : {enr.sector_health}")
                parts.append(
                    f"    Risque supply chain : {enr.supply_chain_risk}"
                )
                # Show top peers
                if enr.peers:
                    parts.append(f"    Pairs notables :")
                    for peer in enr.peers[:4]:
                        parts.append(
                            f"      • {peer.company_name} "
                            f"({peer.relation.value}) "
                            f"— risque: {peer.risk_level}, "
                            f"statut: {peer.status}"
                        )
                parts.append("")

        # ---- RISK : highlight risk factors ----
        if intent == "RISK":
            parts.append("\n⚠  Analyse de risque :\n")
            high_risk = [
                sr for sr in results
                if sr.company.risk_level in ("high", "critical")
            ]
            if high_risk:
                for sr in high_risk:
                    c = sr.company
                    parts.append(
                        f"  🔴 {c.name} — {c.risk_level.upper()}\n"
                        f"     {c.description}\n"
                    )
            else:
                parts.append(
                    "  Aucune entreprise à risque élevé trouvée dans les résultats.\n"
                )

        # ---- SIMULATE : show simulation results ----
        if intent == "SIMULATE" and simulations:
            parts.append("\n🎯  Simulation — Decision Fusion :\n")
            for sim in simulations:
                parts.append(sim.to_text())
                parts.append("")

        # ---- COMPARE : side-by-side ----
        if intent == "COMPARE" and len(results) >= 2:
            parts.append("\n📋  Comparaison :\n")
            parts.append(
                f"  {'Critère':<25} "
                + "  ".join(f"{sr.company.name:<20}" for sr in results[:3])
            )
            parts.append("  " + "─" * 70)
            for attr in ("sector", "risk_level", "status", "revenue_m"):
                row = f"  {attr:<25} "
                for sr in results[:3]:
                    val = getattr(sr.company, attr, "—")
                    row += f"{str(val):<22}"
                parts.append(row)

        # Footer — sources
        parts.append("")

        return "\n".join(parts)


# ============================================================
# Module-level convenience function
# ============================================================

# Singleton instance
_assistant: Optional[FinancialAssistant] = None


def ask(query: str) -> AssistantResponse:
    """
    Ask a financial question. Returns an AssistantResponse.

    This is the main entry point. It initialises the assistant
    on first call (lazy singleton).

    Examples:
        >>> r = ask("Quelles entreprises sont en restructuration ?")
        >>> print(r.text)
        >>> print(r.sources)

        >>> r = ask("Simulate decision fusion for Atos")
        >>> print(r.text)

        >>> r = ask("What are the peers of Casino ?")
        >>> print(r.text)
    """
    global _assistant
    if _assistant is None:
        _assistant = FinancialAssistant()
    return _assistant.ask(query)


# ============================================================
# Quick demo when run directly
# ============================================================

if __name__ == "__main__":
    print("=" * 72)
    print("  F360 Financial Assistant — Demo")
    print("=" * 72)

    queries = [
        "Quelles entreprises sont en restructuration ?",
        "Show me companies with debt risk in energy sector",
        "Quels sont les pairs d'Atos dans le graphe ?",
        "Simulate decision fusion for Casino Guichard",
        "Compare Atos and Sopra Steria",
    ]

    for q in queries:
        print(f"\n{'─' * 72}")
        print(f"  USER: {q}")
        print(f"{'─' * 72}\n")
        response = ask(q)
        print(response.text)
        print(f"\n  📌 Sources: {', '.join(response.sources)}")
        print(f"  🏷  Intent détecté: {response.intent}")
        print()
