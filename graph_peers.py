"""
Graph Peers Module (Personne 3)

Simulated knowledge graph providing peer/relationship enrichment
for companies. Models the relationships between enterprises:
- Parent ↔ Subsidiary links
- Sector peers (same industry)
- Supply chain links (client ↔ supplier)
- Risk contagion paths (companies affected by the same risks)

In production this would query Neo4j / RAGraph.
Here we provide a rule-based simulation for the assistant.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum


class RelationType(Enum):
    """Types of relationships between enterprises"""
    PARENT_SUBSIDIARY = "parent_subsidiary"
    SECTOR_PEER = "sector_peer"
    SUPPLY_CHAIN = "supply_chain"
    RISK_CONTAGION = "risk_contagion"
    JOINT_VENTURE = "joint_venture"
    COMPETITOR = "competitor"


@dataclass
class GraphEdge:
    """A relationship (edge) between two companies in the graph"""
    source_id: str
    target_id: str
    relation: RelationType
    weight: float = 1.0          # Strength of relationship
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PeerInfo:
    """Enriched peer information returned by the graph"""
    company_id: str
    company_name: str
    relation: RelationType
    relation_strength: float
    risk_level: str
    sector: str
    status: str
    detail: str


@dataclass
class GraphEnrichment:
    """Full graph enrichment result for a company"""
    company_id: str
    company_name: str
    peers: List[PeerInfo]
    risk_contagion_score: float     # 0-1: how exposed via graph
    sector_health: str              # healthy / stressed / critical
    supply_chain_risk: str          # low / medium / high
    summary: str


class KnowledgeGraph:
    """
    Simulated knowledge graph for enterprise relationships.
    
    In production → Neo4j queries via RAGraph.
    Here → rule-based in-memory graph.
    """

    def __init__(self):
        self.edges: List[GraphEdge] = []
        self._company_names: Dict[str, str] = {}
        self._company_sectors: Dict[str, str] = {}
        self._company_risks: Dict[str, str] = {}
        self._company_statuses: Dict[str, str] = {}

        # Load the built-in relationships
        self._build_default_graph()

    # ---- Public API -----------------------------------------------

    def register_company(self, company_id: str, name: str,
                         sector: str, risk_level: str, status: str):
        """Register a company in the graph."""
        self._company_names[company_id] = name
        self._company_sectors[company_id] = sector
        self._company_risks[company_id] = risk_level
        self._company_statuses[company_id] = status

    def add_edge(self, edge: GraphEdge):
        """Add a relationship."""
        self.edges.append(edge)

    def get_peers(self, company_id: str,
                  relation_filter: Optional[RelationType] = None,
                  max_depth: int = 1) -> List[PeerInfo]:
        """
        Get peers of a company from the graph.
        
        Args:
            company_id:       ID to look up
            relation_filter:  Only return this relation type
            max_depth:        Traversal depth (1 = direct, 2 = 2-hop)
        """
        visited: Set[str] = {company_id}
        peers: List[PeerInfo] = []
        frontier = [company_id]

        for depth in range(max_depth):
            next_frontier = []
            for cid in frontier:
                for edge in self.edges:
                    # Find connected nodes
                    other = None
                    if edge.source_id == cid:
                        other = edge.target_id
                    elif edge.target_id == cid:
                        other = edge.source_id

                    if other is None or other in visited:
                        continue
                    if relation_filter and edge.relation != relation_filter:
                        continue

                    visited.add(other)
                    next_frontier.append(other)

                    detail = self._describe_relation(edge, cid, other)

                    peers.append(PeerInfo(
                        company_id=other,
                        company_name=self._company_names.get(other, other),
                        relation=edge.relation,
                        relation_strength=edge.weight,
                        risk_level=self._company_risks.get(other, "unknown"),
                        sector=self._company_sectors.get(other, "unknown"),
                        status=self._company_statuses.get(other, "unknown"),
                        detail=detail,
                    ))
            frontier = next_frontier

        return peers

    def enrich(self, company_id: str) -> GraphEnrichment:
        """
        Full graph enrichment for a company.
        
        Returns peers, risk contagion score, sector health, and
        supply chain risk assessment.
        """
        company_name = self._company_names.get(company_id, company_id)
        peers = self.get_peers(company_id, max_depth=2)

        # Risk contagion: how many connected companies are high/critical risk
        risk_peers = [p for p in peers if p.risk_level in ("high", "critical")]
        contagion_score = len(risk_peers) / max(len(peers), 1)

        # Sector health
        sector = self._company_sectors.get(company_id, "")
        sector_ids = [cid for cid, s in self._company_sectors.items()
                      if s == sector and cid != company_id]
        sector_risk_levels = [self._company_risks.get(cid, "medium") for cid in sector_ids]
        critical_count = sum(1 for r in sector_risk_levels if r in ("high", "critical"))
        if not sector_risk_levels:
            sector_health = "unknown"
        elif critical_count / len(sector_risk_levels) > 0.5:
            sector_health = "critical"
        elif critical_count / len(sector_risk_levels) > 0.2:
            sector_health = "stressed"
        else:
            sector_health = "healthy"

        # Supply chain risk
        sc_peers = [p for p in peers if p.relation == RelationType.SUPPLY_CHAIN]
        sc_risk_count = sum(1 for p in sc_peers if p.risk_level in ("high", "critical"))
        if not sc_peers:
            supply_chain_risk = "low"
        elif sc_risk_count / len(sc_peers) > 0.5:
            supply_chain_risk = "high"
        elif sc_risk_count / len(sc_peers) > 0.2:
            supply_chain_risk = "medium"
        else:
            supply_chain_risk = "low"

        # Summary
        summary = self._build_summary(
            company_name, peers, contagion_score,
            sector_health, supply_chain_risk
        )

        return GraphEnrichment(
            company_id=company_id,
            company_name=company_name,
            peers=peers,
            risk_contagion_score=round(contagion_score, 3),
            sector_health=sector_health,
            supply_chain_risk=supply_chain_risk,
            summary=summary,
        )

    # ---- Internals ------------------------------------------------

    def _describe_relation(self, edge: GraphEdge,
                           from_id: str, to_id: str) -> str:
        """Human-readable description of a relationship."""
        to_name = self._company_names.get(to_id, to_id)
        from_name = self._company_names.get(from_id, from_id)

        descs = {
            RelationType.PARENT_SUBSIDIARY:
                f"{to_name} is a subsidiary/parent of {from_name}",
            RelationType.SECTOR_PEER:
                f"{to_name} operates in the same sector as {from_name}",
            RelationType.SUPPLY_CHAIN:
                f"{to_name} is in the supply chain of {from_name}",
            RelationType.RISK_CONTAGION:
                f"{to_name} shares risk exposure with {from_name}",
            RelationType.JOINT_VENTURE:
                f"{to_name} has a joint venture with {from_name}",
            RelationType.COMPETITOR:
                f"{to_name} is a competitor of {from_name}",
        }
        detail = descs.get(edge.relation, f"{to_name} is connected to {from_name}")
        meta = edge.metadata
        if meta:
            extra = ", ".join(f"{k}: {v}" for k, v in meta.items())
            detail += f" ({extra})"
        return detail

    def _build_summary(self, company_name: str,
                       peers: List[PeerInfo],
                       contagion: float,
                       sector_health: str,
                       sc_risk: str) -> str:
        """Build textual summary of graph enrichment."""
        parts = [
            f"Graph enrichment for {company_name}:",
            f"  • {len(peers)} connected entities in the knowledge graph",
        ]

        risk_peers = [p for p in peers if p.risk_level in ("high", "critical")]
        if risk_peers:
            names = ", ".join(p.company_name for p in risk_peers[:3])
            parts.append(
                f"  • ⚠ {len(risk_peers)} high/critical-risk peers: {names}"
            )

        parts.append(f"  • Risk contagion score: {contagion:.0%}")
        parts.append(f"  • Sector health: {sector_health}")
        parts.append(f"  • Supply chain risk: {sc_risk}")

        restructuring = [p for p in peers if p.status == "restructuring"]
        if restructuring:
            names = ", ".join(p.company_name for p in restructuring[:3])
            parts.append(f"  • ⚠ Peers under restructuring: {names}")

        return "\n".join(parts)

    def _build_default_graph(self):
        """Build the default enterprise relationship graph."""
        # Register companies
        companies_raw = [
            ("ENT-001", "Airbus",             "Aerospace",  "low",      "active"),
            ("ENT-002", "Renault",            "Automotive", "medium",   "active"),
            ("ENT-003", "Orpea",              "Healthcare", "critical", "restructuring"),
            ("ENT-004", "Atos",               "Technology", "high",     "restructuring"),
            ("ENT-005", "TotalEnergies",      "Energy",     "low",      "active"),
            ("ENT-006", "Casino Guichard",    "Retail",     "critical", "restructuring"),
            ("ENT-007", "Dassault Systèmes",  "Technology", "low",      "active"),
            ("ENT-008", "Alstom",             "Industrial", "medium",   "watchlist"),
            ("ENT-009", "BNP Paribas",        "Banking",    "low",      "active"),
            ("ENT-010", "Vallourec",          "Industrial", "high",     "watchlist"),
            ("ENT-011", "Sopra Steria",       "Technology", "low",      "active"),
            ("ENT-012", "EDF",                "Energy",     "high",     "watchlist"),
        ]
        for cid, name, sector, risk, status in companies_raw:
            self.register_company(cid, name, sector, risk, status)

        # Relationships
        edges = [
            # Sector peers
            GraphEdge("ENT-004", "ENT-007", RelationType.SECTOR_PEER, 0.7),
            GraphEdge("ENT-004", "ENT-011", RelationType.SECTOR_PEER, 0.8),
            GraphEdge("ENT-007", "ENT-011", RelationType.SECTOR_PEER, 0.6),
            GraphEdge("ENT-005", "ENT-012", RelationType.SECTOR_PEER, 0.5),
            GraphEdge("ENT-008", "ENT-010", RelationType.SECTOR_PEER, 0.5),
            # Supply chain
            GraphEdge("ENT-001", "ENT-008", RelationType.SUPPLY_CHAIN, 0.8,
                      {"flow": "components"}),
            GraphEdge("ENT-002", "ENT-010", RelationType.SUPPLY_CHAIN, 0.6,
                      {"flow": "steel parts"}),
            GraphEdge("ENT-005", "ENT-010", RelationType.SUPPLY_CHAIN, 0.7,
                      {"flow": "energy services"}),
            GraphEdge("ENT-001", "ENT-007", RelationType.SUPPLY_CHAIN, 0.9,
                      {"flow": "3D design software"}),
            # Risk contagion
            GraphEdge("ENT-003", "ENT-006", RelationType.RISK_CONTAGION, 0.9,
                      {"reason": "shared debt crisis pattern"}),
            GraphEdge("ENT-004", "ENT-010", RelationType.RISK_CONTAGION, 0.6,
                      {"reason": "both under restructuring pressure"}),
            GraphEdge("ENT-006", "ENT-009", RelationType.RISK_CONTAGION, 0.5,
                      {"reason": "BNP is a major creditor of Casino"}),
            # Parent-subsidiary
            GraphEdge("ENT-006", "ENT-006-P", RelationType.PARENT_SUBSIDIARY, 1.0,
                      {"parent": "Rallye SA"}),
            GraphEdge("ENT-007", "ENT-001", RelationType.PARENT_SUBSIDIARY, 0.3,
                      {"note": "Shared Dassault family heritage"}),
            # Competitors
            GraphEdge("ENT-004", "ENT-011", RelationType.COMPETITOR, 0.7),
            GraphEdge("ENT-001", "ENT-002", RelationType.COMPETITOR, 0.2,
                      {"overlap": "industrial manufacturing"}),
        ]
        # Register parent stub
        self.register_company("ENT-006-P", "Rallye SA", "Holding",
                              "critical", "restructuring")

        for e in edges:
            self.add_edge(e)
