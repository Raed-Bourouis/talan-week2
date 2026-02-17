"""
Keyword Search Module (Personne 2)

Rule-based keyword search engine for finding relevant enterprises
in a financial knowledge base. Searches across company profiles,
financial indicators, sectors, and risk factors.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import re
from enum import Enum


class MatchType(Enum):
    """Type of keyword match"""
    EXACT = "exact"
    PARTIAL = "partial"
    SYNONYM = "synonym"


@dataclass
class Company:
    """Enterprise profile in the knowledge base"""
    company_id: str
    name: str
    sector: str
    subsector: str = ""
    country: str = "France"
    revenue_m: float = 0.0            # Revenue in millions
    employees: int = 0
    risk_level: str = "medium"        # low / medium / high / critical
    financial_keywords: List[str] = field(default_factory=list)
    description: str = ""
    parent_company: str = ""           # For group/subsidiary relationships
    status: str = "active"             # active / restructuring / watchlist / default
    tags: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """Single keyword search result"""
    company: Company
    relevance_score: float          # 0.0 - 1.0
    matched_keywords: List[str]
    match_types: List[MatchType]
    matched_fields: List[str]       # Which fields had matches

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_id": self.company.company_id,
            "company_name": self.company.name,
            "sector": self.company.sector,
            "risk_level": self.company.risk_level,
            "relevance_score": round(self.relevance_score, 3),
            "matched_keywords": self.matched_keywords,
            "match_types": [mt.value for mt in self.match_types],
            "matched_fields": self.matched_fields,
        }


# ============================================================
# Synonym dictionary for financial domain
# ============================================================
FINANCIAL_SYNONYMS: Dict[str, List[str]] = {
    "cash flow":     ["trésorerie", "flux de trésorerie", "liquidité", "liquidity"],
    "invoice":       ["facture", "facturation", "billing", "receivable"],
    "risk":          ["risque", "exposure", "exposition", "danger"],
    "restructuring": ["restructuration", "reorganisation", "turnaround", "redressement"],
    "default":       ["défaut", "défaillance", "insolvency", "faillite", "bankruptcy"],
    "payment":       ["paiement", "règlement", "settlement"],
    "delay":         ["retard", "délai", "overdue", "impayé"],
    "budget":        ["budget", "enveloppe budgétaire", "allocation"],
    "production":    ["production", "manufacturing", "fabrication", "output"],
    "supply chain":  ["chaîne d'approvisionnement", "logistique", "logistics"],
    "margin":        ["marge", "profitability", "rentabilité"],
    "growth":        ["croissance", "expansion", "développement"],
    "debt":          ["dette", "endettement", "leverage", "emprunt"],
    "acquisition":   ["acquisition", "rachat", "takeover", "merger", "fusion"],
    "client":        ["client", "customer", "acheteur"],
    "supplier":      ["fournisseur", "vendor", "prestataire"],
}


class KeywordSearchEngine:
    """
    Rule-based keyword search across a company knowledge base.
    
    Supports:
    - Exact keyword matching
    - Partial / substring matching
    - Synonym expansion (FR ↔ EN financial terms)
    - Multi-field search (name, sector, tags, description, etc.)
    - Relevance scoring with field-level weighting
    """

    # Field weights for relevance scoring
    FIELD_WEIGHTS = {
        "name":               3.0,
        "sector":             2.5,
        "subsector":          2.0,
        "financial_keywords": 2.5,
        "tags":               2.0,
        "description":        1.5,
        "status":             2.0,
        "risk_level":         1.5,
        "parent_company":     1.0,
    }

    def __init__(self, companies: Optional[List[Company]] = None):
        self.companies: List[Company] = companies or []
        self._synonym_index = self._build_synonym_index()

    # ---- public API -----------------------------------------------

    def add_company(self, company: Company) -> None:
        """Add a company to the knowledge base."""
        self.companies.append(company)

    def add_companies(self, companies: List[Company]) -> None:
        self.companies.extend(companies)

    def search(self,
               query: str,
               top_k: int = 5,
               min_score: float = 0.05,
               sector_filter: Optional[str] = None,
               risk_filter: Optional[str] = None) -> List[SearchResult]:
        """
        Search companies by keyword query.

        Args:
            query:         Free-text query (can contain multiple keywords)
            top_k:         Max results to return
            min_score:     Minimum relevance score
            sector_filter: Only return companies in this sector
            risk_filter:   Only return companies with this risk level

        Returns:
            List of SearchResult sorted by relevance descending.
        """
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        # Expand with synonyms
        expanded = self._expand_synonyms(keywords)

        results: List[SearchResult] = []

        for company in self.companies:
            # Pre-filter
            if sector_filter and company.sector.lower() != sector_filter.lower():
                continue
            if risk_filter and company.risk_level.lower() != risk_filter.lower():
                continue

            score, matched_kw, match_types, matched_fields = self._score_company(
                company, keywords, expanded
            )
            if score >= min_score:
                results.append(SearchResult(
                    company=company,
                    relevance_score=score,
                    matched_keywords=matched_kw,
                    match_types=match_types,
                    matched_fields=matched_fields,
                ))

        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_k]

    # ---- internals ------------------------------------------------

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from a query string."""
        # Lowercase and strip punctuation (keep accents for FR)
        query = query.lower().strip()
        # Keep multi-word financial terms together
        multi_word_terms = [k for k in FINANCIAL_SYNONYMS if " " in k]
        found_terms: List[str] = []
        for term in multi_word_terms:
            if term in query:
                found_terms.append(term)
                query = query.replace(term, "")

        # Also check synonym values (multi-word)
        for _key, synonyms in FINANCIAL_SYNONYMS.items():
            for syn in synonyms:
                if " " in syn and syn in query:
                    found_terms.append(syn)
                    query = query.replace(syn, "")

        # Split remaining into single tokens, remove stopwords
        stopwords = {
            "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou",
            "the", "a", "an", "of", "in", "on", "for", "with", "and", "or",
            "is", "are", "to", "at", "by", "from", "what", "which", "who",
            "how", "when", "where", "why", "do", "does", "can", "could",
            "show", "me", "find", "get", "list", "give", "tell", "about",
            "quelles", "quel", "quelle", "quels", "sont", "est", "dans",
            "pour", "avec", "sur", "par", "au", "aux", "que", "qui",
            "entreprises", "entreprise", "société", "sociétés", "companies",
            "company",
        }
        # Split on punctuation/whitespace — also split French contractions (d', l', s', n', qu')
        tokens = re.split(r"[,;.\s]+", query)
        expanded_tokens: List[str] = []
        for t in tokens:
            # Handle French contractions: d'Atos → [d, Atos], l'entreprise → [l, entreprise]
            parts = re.split(r"[''`]", t)
            expanded_tokens.extend(parts)
        single_kw = [t for t in expanded_tokens if t and t not in stopwords and len(t) > 1]

        return found_terms + single_kw

    def _build_synonym_index(self) -> Dict[str, str]:
        """Map every synonym to its canonical key."""
        index: Dict[str, str] = {}
        for canonical, synonyms in FINANCIAL_SYNONYMS.items():
            index[canonical] = canonical
            for syn in synonyms:
                index[syn] = canonical
        return index

    def _expand_synonyms(self, keywords: List[str]) -> Dict[str, List[str]]:
        """For each keyword, return list of synonyms to also search."""
        expanded: Dict[str, List[str]] = {}
        for kw in keywords:
            canonical = self._synonym_index.get(kw)
            if canonical:
                all_forms = [canonical] + FINANCIAL_SYNONYMS.get(canonical, [])
                expanded[kw] = [f for f in all_forms if f != kw]
            else:
                expanded[kw] = []
        return expanded

    def _get_field_text(self, company: Company, field_name: str) -> str:
        """Get searchable text for a field."""
        val = getattr(company, field_name, "")
        if isinstance(val, list):
            return " ".join(str(v) for v in val).lower()
        return str(val).lower()

    def _score_company(
        self,
        company: Company,
        keywords: List[str],
        expanded: Dict[str, List[str]]
    ) -> Tuple[float, List[str], List[MatchType], List[str]]:
        """Score a company against the keyword set."""
        total_score = 0.0
        matched_kw: List[str] = []
        match_types: List[MatchType] = []
        matched_fields: List[str] = []

        for kw in keywords:
            # Also try synonyms
            search_terms = [kw] + expanded.get(kw, [])
            best_field_score = 0.0
            best_match_type = None
            best_field = None

            for field_name, weight in self.FIELD_WEIGHTS.items():
                text = self._get_field_text(company, field_name)
                if not text:
                    continue

                for term in search_terms:
                    # Exact match
                    if term == text or term in text.split():
                        score = weight * 1.0
                        mtype = MatchType.EXACT if term == kw else MatchType.SYNONYM
                    # Partial / substring
                    elif term in text:
                        score = weight * 0.7
                        mtype = MatchType.PARTIAL if term == kw else MatchType.SYNONYM
                    else:
                        continue

                    if score > best_field_score:
                        best_field_score = score
                        best_match_type = mtype
                        best_field = field_name

            if best_field_score > 0 and best_match_type is not None:
                total_score += best_field_score
                matched_kw.append(kw)
                match_types.append(best_match_type)
                if best_field and best_field not in matched_fields:
                    matched_fields.append(best_field)

        # Normalize score by max possible (all keywords exact-match on highest-weight field)
        max_possible = len(keywords) * max(self.FIELD_WEIGHTS.values())
        relevance = total_score / max_possible if max_possible > 0 else 0.0
        relevance = min(relevance, 1.0)

        return relevance, matched_kw, match_types, matched_fields


# ============================================================
# Sample knowledge base for demo / testing
# ============================================================

def build_sample_knowledge_base() -> List[Company]:
    """Build a sample company knowledge base for demonstrations."""
    return [
        Company(
            company_id="ENT-001",
            name="Airbus",
            sector="Aerospace",
            subsector="Aircraft Manufacturing",
            country="France",
            revenue_m=52149,
            employees=134000,
            risk_level="low",
            financial_keywords=["supply chain", "production", "defense", "aviation"],
            description="European multinational aerospace corporation. Major aircraft manufacturer.",
            parent_company="",
            status="active",
            tags=["large-cap", "export", "manufacturing", "CAC40"],
        ),
        Company(
            company_id="ENT-002",
            name="Renault",
            sector="Automotive",
            subsector="Vehicle Manufacturing",
            country="France",
            revenue_m=46391,
            employees=105000,
            risk_level="medium",
            financial_keywords=["production", "supply chain", "electric vehicle", "margin"],
            description="French automotive manufacturer undergoing electric vehicle transition.",
            parent_company="",
            status="active",
            tags=["large-cap", "transition", "manufacturing", "CAC40"],
        ),
        Company(
            company_id="ENT-003",
            name="Orpea",
            sector="Healthcare",
            subsector="Elder Care",
            country="France",
            revenue_m=4700,
            employees=72000,
            risk_level="critical",
            financial_keywords=["debt", "restructuring", "default", "cash flow"],
            description="Healthcare group specializing in elder care. Currently under financial restructuring after debt crisis.",
            parent_company="",
            status="restructuring",
            tags=["mid-cap", "crisis", "debt", "regulatory"],
        ),
        Company(
            company_id="ENT-004",
            name="Atos",
            sector="Technology",
            subsector="IT Services",
            country="France",
            revenue_m=10800,
            employees=95000,
            risk_level="high",
            financial_keywords=["restructuring", "debt", "margin", "cash flow", "acquisition"],
            description="IT services company undergoing major restructuring. High debt levels and asset disposal program.",
            parent_company="",
            status="restructuring",
            tags=["mid-cap", "restructuring", "cloud", "cybersecurity", "debt"],
        ),
        Company(
            company_id="ENT-005",
            name="TotalEnergies",
            sector="Energy",
            subsector="Oil & Gas",
            country="France",
            revenue_m=218900,
            employees=101000,
            risk_level="low",
            financial_keywords=["cash flow", "margin", "production", "growth"],
            description="Multinational energy company. Strong cash flow generation.",
            parent_company="",
            status="active",
            tags=["large-cap", "export", "energy-transition", "dividend", "CAC40"],
        ),
        Company(
            company_id="ENT-006",
            name="Casino Guichard",
            sector="Retail",
            subsector="Grocery Retail",
            country="France",
            revenue_m=9000,
            employees=40000,
            risk_level="critical",
            financial_keywords=["debt", "default", "restructuring", "cash flow", "delay"],
            description="French grocery retailer facing severe debt crisis and payment delays to suppliers.",
            parent_company="Rallye SA",
            status="restructuring",
            tags=["mid-cap", "crisis", "debt", "supplier-risk"],
        ),
        Company(
            company_id="ENT-007",
            name="Dassault Systèmes",
            sector="Technology",
            subsector="Software",
            country="France",
            revenue_m=5665,
            employees=23800,
            risk_level="low",
            financial_keywords=["growth", "margin", "acquisition", "SaaS"],
            description="3D design and product lifecycle management software. Strong recurring revenue.",
            parent_company="Groupe Dassault",
            status="active",
            tags=["large-cap", "software", "CAC40", "innovation"],
        ),
        Company(
            company_id="ENT-008",
            name="Alstom",
            sector="Industrial",
            subsector="Rail Transport",
            country="France",
            revenue_m=16500,
            employees=74000,
            risk_level="medium",
            financial_keywords=["cash flow", "acquisition", "debt", "supply chain"],
            description="Rail transport equipment manufacturer. Cash flow pressure after Bombardier acquisition.",
            parent_company="",
            status="watchlist",
            tags=["large-cap", "manufacturing", "infrastructure", "acquisition-risk"],
        ),
        Company(
            company_id="ENT-009",
            name="BNP Paribas",
            sector="Banking",
            subsector="Investment Banking",
            country="France",
            revenue_m=46200,
            employees=193000,
            risk_level="low",
            financial_keywords=["risk", "margin", "growth", "payment"],
            description="Largest French bank. Diversified financial services group.",
            parent_company="",
            status="active",
            tags=["large-cap", "banking", "CAC40", "finance"],
        ),
        Company(
            company_id="ENT-010",
            name="Vallourec",
            sector="Industrial",
            subsector="Steel Tubes",
            country="France",
            revenue_m=4100,
            employees=17000,
            risk_level="high",
            financial_keywords=["debt", "restructuring", "cash flow", "production"],
            description="Steel tube manufacturer. Emerged from restructuring, volatile cash flow.",
            parent_company="",
            status="watchlist",
            tags=["mid-cap", "steel", "energy-services", "cyclical"],
        ),
        Company(
            company_id="ENT-011",
            name="Sopra Steria",
            sector="Technology",
            subsector="IT Services",
            country="France",
            revenue_m=5100,
            employees=50000,
            risk_level="low",
            financial_keywords=["growth", "margin", "acquisition"],
            description="IT consulting and digital services company. Steady growth trajectory.",
            parent_company="",
            status="active",
            tags=["mid-cap", "consulting", "digital-transformation"],
        ),
        Company(
            company_id="ENT-012",
            name="EDF",
            sector="Energy",
            subsector="Electricity",
            country="France",
            revenue_m=143500,
            employees=165000,
            risk_level="high",
            financial_keywords=["debt", "cash flow", "production", "budget"],
            description="French electric utility. Massive debt load and nuclear fleet maintenance costs.",
            parent_company="French State",
            status="watchlist",
            tags=["large-cap", "utility", "nuclear", "sovereign"],
        ),
    ]
