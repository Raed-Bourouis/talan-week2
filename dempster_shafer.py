"""
Dempster-Shafer Theory (DST) for Financial Evidence Fusion

Implements the mathematical theory of evidence for combining information
from multiple independent financial sources (ERP, Knowledge Graph, IoT, etc.)

Key Concepts:
- Frame of Discernment (Θ): Set of possible financial outcomes/decisions
- Mass Function (m): Basic Probability Assignment over subsets of Θ
- Belief (Bel): Lower bound of probability (minimum support)
- Plausibility (Pl): Upper bound of probability (maximum support)
- Dempster's Rule: Combines independent evidence sources

Advantage over simple weighting:
- Models ignorance explicitly (uncertainty ≠ equal probability)
- Detects conflict between evidence sources
- Combines evidence without requiring prior probabilities
"""

from typing import Dict, Set, FrozenSet, List, Tuple, Optional
from dataclasses import dataclass, field
from itertools import combinations
import math


# ============================================================
# Core Types
# ============================================================

# A hypothesis is a frozenset of scenario IDs
Hypothesis = FrozenSet[str]

# Mass function maps hypotheses to mass values [0, 1]
MassFunction = Dict[Hypothesis, float]


@dataclass
class EvidenceSource:
    """
    An evidence source with its mass function assignment
    
    Attributes:
        name: Human-readable source name (e.g., "ERP_Invoices")
        mass_function: Mapping of hypothesis subsets to belief mass
        reliability: Source reliability factor [0, 1]
    """
    name: str
    mass_function: MassFunction
    reliability: float = 1.0
    
    def validate(self) -> bool:
        """Validate that mass assignments sum to 1.0"""
        total = sum(self.mass_function.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Mass function for '{self.name}' sums to {total:.6f}, must be 1.0"
            )
        if any(v < 0 for v in self.mass_function.values()):
            raise ValueError(f"Mass function for '{self.name}' contains negative values")
        return True


@dataclass 
class DSTResult:
    """
    Result of Dempster-Shafer evidence fusion
    
    Attributes:
        combined_mass: Final combined mass function
        belief: Belief values for each singleton hypothesis
        plausibility: Plausibility values for each singleton hypothesis
        uncertainty_interval: [Bel, Pl] intervals per hypothesis
        conflict_degree: Degree of conflict between sources (k)
        decision: Best hypothesis based on belief/plausibility
        confidence: Decision confidence metric
    """
    combined_mass: MassFunction
    belief: Dict[str, float]
    plausibility: Dict[str, float]
    uncertainty_interval: Dict[str, Tuple[float, float]]
    conflict_degree: float
    decision: str
    confidence: float
    pignistic_probability: Dict[str, float]


# ============================================================
# Dempster-Shafer Engine
# ============================================================

class DempsterShaferEngine:
    """
    Dempster-Shafer Theory engine for financial evidence fusion
    
    Combines evidence from multiple independent sources using
    Dempster's Rule of Combination to produce belief functions
    over financial decision hypotheses.
    """
    
    def __init__(self, frame_of_discernment: Set[str]):
        """
        Initialize DST engine
        
        Args:
            frame_of_discernment: Set of all possible decisions/outcomes
                e.g., {"SCENARIO_A", "SCENARIO_B", "SCENARIO_C"}
        """
        self.theta = frame_of_discernment
        self.theta_frozen = frozenset(self.theta)
        self.power_set = self._generate_power_set()
        
    def _generate_power_set(self) -> List[FrozenSet[str]]:
        """Generate the power set of Θ (excluding empty set)"""
        elements = list(self.theta)
        power = []
        for r in range(1, len(elements) + 1):
            for combo in combinations(elements, r):
                power.append(frozenset(combo))
        return power
    
    def create_mass_function(self, 
                            assignments: Dict[str, float],
                            ignorance: Optional[float] = None) -> MassFunction:
        """
        Create a mass function from simple assignments
        
        Args:
            assignments: Mapping of scenario_id or "theta" to mass values
                e.g., {"SCENARIO_A": 0.3, "SCENARIO_B": 0.5}
            ignorance: Mass assigned to full frame Θ (total ignorance).
                If None, remainder is assigned to Θ automatically.
        
        Returns:
            Properly formatted MassFunction
        """
        mass: MassFunction = {}
        assigned = 0.0
        
        for key, value in assignments.items():
            if key == "theta" or key == "Θ":
                # Full frame of discernment
                mass[self.theta_frozen] = value
            else:
                # Singleton or subset
                hypothesis = frozenset([key]) if isinstance(key, str) else frozenset(key)
                mass[hypothesis] = value
            assigned += value
        
        # Assign remaining mass to Θ (ignorance)
        if ignorance is not None:
            mass[self.theta_frozen] = mass.get(self.theta_frozen, 0.0) + ignorance
        elif abs(assigned - 1.0) > 1e-6:
            remaining = 1.0 - assigned
            if remaining > 0:
                mass[self.theta_frozen] = mass.get(self.theta_frozen, 0.0) + remaining
        
        return mass
    
    def discount_evidence(self, 
                         mass: MassFunction, 
                         reliability: float) -> MassFunction:
        """
        Discount evidence based on source reliability
        
        Discounting transfers mass to Θ based on unreliability:
        m'(A) = α × m(A) for A ≠ Θ
        m'(Θ) = 1 - α × (1 - m(Θ))
        
        Args:
            mass: Original mass function
            reliability: Source reliability [0, 1] (α)
        
        Returns:
            Discounted mass function
        """
        if reliability >= 1.0:
            return mass.copy()
        
        discounted: MassFunction = {}
        theta_mass = 0.0
        
        for hypothesis, value in mass.items():
            if hypothesis == self.theta_frozen:
                theta_mass = value
            else:
                discounted[hypothesis] = reliability * value
        
        discounted[self.theta_frozen] = 1.0 - reliability * (1.0 - theta_mass)
        
        return discounted
    
    def combine(self, m1: MassFunction, m2: MassFunction) -> Tuple[MassFunction, float]:
        """
        Dempster's Rule of Combination
        
        Combines two independent mass functions:
        m₁₂(A) = (1 / (1-k)) × Σ{m₁(B)×m₂(C) : B∩C=A}
        
        where k = Σ{m₁(B)×m₂(C) : B∩C=∅} is the conflict
        
        Args:
            m1: First mass function
            m2: Second mass function
        
        Returns:
            Tuple of (combined mass function, conflict degree k)
        """
        combined: MassFunction = {}
        conflict = 0.0
        
        for h1, v1 in m1.items():
            for h2, v2 in m2.items():
                intersection = h1 & h2
                product = v1 * v2
                
                if len(intersection) == 0:
                    # Conflict: intersection is empty
                    conflict += product
                else:
                    combined[intersection] = combined.get(intersection, 0.0) + product
        
        # Normalize by (1 - k) — Dempster's normalization
        if conflict >= 1.0 - 1e-10:
            # Total conflict — sources completely contradictory
            # Return vacuous mass function
            return {self.theta_frozen: 1.0}, conflict
        
        normalization = 1.0 / (1.0 - conflict)
        for hypothesis in combined:
            combined[hypothesis] *= normalization
        
        return combined, conflict
    
    def combine_multiple(self, 
                        sources: List[EvidenceSource]) -> Tuple[MassFunction, float]:
        """
        Combine multiple evidence sources sequentially
        
        Args:
            sources: List of evidence sources with mass functions
        
        Returns:
            Tuple of (final combined mass, maximum conflict)
        """
        if not sources:
            return {self.theta_frozen: 1.0}, 0.0
        
        # Apply reliability discounting
        discounted = []
        for source in sources:
            source.validate()
            dm = self.discount_evidence(source.mass_function, source.reliability)
            discounted.append(dm)
        
        # Combine sequentially
        result = discounted[0]
        max_conflict = 0.0
        
        for i in range(1, len(discounted)):
            result, conflict = self.combine(result, discounted[i])
            max_conflict = max(max_conflict, conflict)
        
        return result, max_conflict
    
    def belief(self, mass: MassFunction, hypothesis: Hypothesis) -> float:
        """
        Calculate Belief (Bel) for a hypothesis
        
        Bel(A) = Σ{m(B) : B ⊆ A, B ≠ ∅}
        
        Represents the minimum support (lower probability bound)
        """
        bel = 0.0
        for h, v in mass.items():
            if h <= hypothesis and len(h) > 0:
                bel += v
        return bel
    
    def plausibility(self, mass: MassFunction, hypothesis: Hypothesis) -> float:
        """
        Calculate Plausibility (Pl) for a hypothesis
        
        Pl(A) = Σ{m(B) : B ∩ A ≠ ∅}
        
        Represents the maximum support (upper probability bound)
        """
        pl = 0.0
        for h, v in mass.items():
            if len(h & hypothesis) > 0:
                pl += v
        return pl
    
    def pignistic_transform(self, mass: MassFunction) -> Dict[str, float]:
        """
        Pignistic Probability Transform (BetP)
        
        Converts mass function to point probability for decision making:
        BetP(x) = Σ{m(A) / |A| : x ∈ A, A ⊆ Θ}  × 1/(1 - m(∅))
        
        This is the preferred method for converting DST results to
        actionable probabilities.
        """
        bet_p: Dict[str, float] = {s: 0.0 for s in self.theta}
        
        for hypothesis, value in mass.items():
            if len(hypothesis) > 0:
                share = value / len(hypothesis)
                for element in hypothesis:
                    if element in bet_p:
                        bet_p[element] += share
        
        # Normalize
        total = sum(bet_p.values())
        if total > 0:
            for key in bet_p:
                bet_p[key] /= total
        
        return bet_p
    
    def fuse(self, sources: List[EvidenceSource]) -> DSTResult:
        """
        Execute complete DST fusion pipeline
        
        Args:
            sources: List of evidence sources
        
        Returns:
            DSTResult with belief, plausibility, and decision
        """
        # Combine all sources
        combined_mass, conflict = self.combine_multiple(sources)
        
        # Calculate belief and plausibility for each singleton
        bel_values: Dict[str, float] = {}
        pl_values: Dict[str, float] = {}
        intervals: Dict[str, Tuple[float, float]] = {}
        
        for scenario in self.theta:
            singleton = frozenset([scenario])
            bel = self.belief(combined_mass, singleton)
            pl = self.plausibility(combined_mass, singleton)
            bel_values[scenario] = bel
            pl_values[scenario] = pl
            intervals[scenario] = (bel, pl)
        
        # Pignistic probability for decision making
        pignistic = self.pignistic_transform(combined_mass)
        
        # Decision: highest pignistic probability
        best_decision = max(pignistic, key=pignistic.get)
        
        # Confidence: based on belief and separation from next best
        sorted_probs = sorted(pignistic.values(), reverse=True)
        if len(sorted_probs) > 1:
            confidence = sorted_probs[0] - sorted_probs[1]  # margin of victory
        else:
            confidence = sorted_probs[0]
        
        # Adjust confidence by conflict level
        confidence *= (1.0 - conflict * 0.5)
        
        return DSTResult(
            combined_mass=combined_mass,
            belief=bel_values,
            plausibility=pl_values,
            uncertainty_interval=intervals,
            conflict_degree=conflict,
            decision=best_decision,
            confidence=confidence,
            pignistic_probability=pignistic
        )


# ============================================================
# Financial Evidence Builders
# ============================================================

class FinancialEvidenceBuilder:
    """
    Utility class to convert financial data into DST mass functions
    
    Transforms raw financial metrics into evidence that can be
    fused using Dempster-Shafer theory.
    """
    
    @staticmethod
    def from_invoice_data(scenarios: List[str],
                         spike_pct: float,
                         risk_scenario: str,
                         safe_scenario: str) -> EvidenceSource:
        """
        Convert invoice spike data to mass function
        
        Higher spike → more mass on risk scenario
        """
        if spike_pct > 20:
            risk_mass = 0.7
            safe_mass = 0.05
        elif spike_pct > 10:
            risk_mass = 0.5
            safe_mass = 0.1
        elif spike_pct > 5:
            risk_mass = 0.3
            safe_mass = 0.2
        else:
            risk_mass = 0.1
            safe_mass = 0.4
        
        ignorance = 1.0 - risk_mass - safe_mass
        
        mass: MassFunction = {
            frozenset([risk_scenario]): risk_mass,
            frozenset([safe_scenario]): safe_mass,
            frozenset(scenarios): ignorance
        }
        
        return EvidenceSource(
            name="ERP_Invoice_Evidence",
            mass_function=mass,
            reliability=0.85
        )
    
    @staticmethod
    def from_production_data(scenarios: List[str],
                            output_change_pct: float,
                            risk_scenario: str,
                            safe_scenario: str) -> EvidenceSource:
        """
        Convert production output change to mass function
        
        Negative change → supports risk scenario
        """
        if output_change_pct < -15:
            risk_mass = 0.6
            safe_mass = 0.05
        elif output_change_pct < -8:
            risk_mass = 0.4
            safe_mass = 0.1
        elif output_change_pct < -3:
            risk_mass = 0.25
            safe_mass = 0.2
        else:
            risk_mass = 0.05
            safe_mass = 0.45
        
        ignorance = 1.0 - risk_mass - safe_mass
        
        mass: MassFunction = {
            frozenset([risk_scenario]): risk_mass,
            frozenset([safe_scenario]): safe_mass,
            frozenset(scenarios): ignorance
        }
        
        return EvidenceSource(
            name="IoT_Production_Evidence",
            mass_function=mass,
            reliability=0.75
        )
    
    @staticmethod
    def from_knowledge_graph(scenarios: List[str],
                            client_status: str,
                            has_historical_pattern: bool,
                            risk_scenario: str,
                            safe_scenario: str) -> EvidenceSource:
        """
        Convert knowledge graph intelligence to mass function
        """
        risk_mass = 0.1
        safe_mass = 0.3
        
        # Client parent status
        status_lower = client_status.lower()
        if "bankruptcy" in status_lower or "chapter 11" in status_lower:
            risk_mass += 0.35
            safe_mass -= 0.15
        elif "restructuring" in status_lower:
            risk_mass += 0.25
            safe_mass -= 0.10
        elif "stable" in status_lower:
            safe_mass += 0.15
        
        # Historical pattern
        if has_historical_pattern:
            risk_mass += 0.15
            safe_mass -= 0.05
        
        # Clamp values
        risk_mass = max(0.0, min(risk_mass, 0.8))
        safe_mass = max(0.0, min(safe_mass, 0.8))
        
        ignorance = max(0.0, 1.0 - risk_mass - safe_mass)
        
        mass: MassFunction = {
            frozenset([risk_scenario]): risk_mass,
            frozenset([safe_scenario]): safe_mass,
            frozenset(scenarios): ignorance
        }
        
        return EvidenceSource(
            name="KnowledgeGraph_Evidence",
            mass_function=mass,
            reliability=0.80
        )
    
    @staticmethod
    def from_budget_data(scenarios: List[str],
                        budget_remaining_pct: float,
                        risk_scenario: str,
                        safe_scenario: str) -> EvidenceSource:
        """
        Convert budget status to mass function
        """
        if budget_remaining_pct < 5:
            risk_mass = 0.65
            safe_mass = 0.05
        elif budget_remaining_pct < 10:
            risk_mass = 0.45
            safe_mass = 0.10
        elif budget_remaining_pct < 20:
            risk_mass = 0.25
            safe_mass = 0.25
        else:
            risk_mass = 0.10
            safe_mass = 0.40
        
        ignorance = 1.0 - risk_mass - safe_mass
        
        mass: MassFunction = {
            frozenset([risk_scenario]): risk_mass,
            frozenset([safe_scenario]): safe_mass,
            frozenset(scenarios): ignorance
        }
        
        return EvidenceSource(
            name="ERP_Budget_Evidence",
            mass_function=mass,
            reliability=0.90
        )
    
    @staticmethod
    def from_scenario_simulation(scenarios: List[str],
                                scenario_results: Dict[str, float]) -> EvidenceSource:
        """
        Convert scenario simulation results to mass function
        
        Args:
            scenario_results: Mapping of scenario_id to performance score [0, 1]
                Higher score = better scenario
        """
        total = sum(scenario_results.values())
        
        mass: MassFunction = {}
        assigned = 0.0
        
        for scenario_id, score in scenario_results.items():
            normalized = score / total if total > 0 else 1.0 / len(scenario_results)
            mass_value = normalized * 0.8  # Reserve 20% for ignorance
            mass[frozenset([scenario_id])] = mass_value
            assigned += mass_value
        
        # Assign remaining to full frame (ignorance)
        mass[frozenset(scenarios)] = max(0.0, 1.0 - assigned)
        
        return EvidenceSource(
            name="Scenario_Simulation_Evidence",
            mass_function=mass,
            reliability=0.70
        )
