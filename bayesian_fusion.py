"""
Bayesian Fusion Engine for Financial Decision Making

Implements Bayesian inference for combining multiple financial evidence
sources with prior beliefs to produce posterior probabilities over
financial scenarios/decisions.

Key Concepts:
- Prior: Initial belief about scenario likelihood (before evidence)
- Likelihood: P(evidence | scenario) — how likely data is given scenario
- Posterior: Updated belief after observing evidence (via Bayes' theorem)
- Sequential Update: Each evidence source updates the posterior

Mathematical Foundation:
    P(H|E₁,E₂,...Eₙ) ∝ P(E₁|H) × P(E₂|H) × ... × P(Eₙ|H) × P(H)

Advantage over simple weighting:
- Principled probabilistic framework with theoretical guarantees
- Naturally updates beliefs as new evidence arrives
- Handles sequential evidence integration
- Provides calibrated probability estimates
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import math


@dataclass
class BayesianEvidence:
    """
    Evidence source for Bayesian updating
    
    Attributes:
        name: Evidence source identifier
        likelihoods: P(evidence | scenario) for each scenario
        weight: Evidence weight/reliability (0-1)
        metadata: Additional context about the evidence
    """
    name: str
    likelihoods: Dict[str, float]  # scenario_id -> P(evidence | scenario)
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate likelihood values"""
        for scenario, likelihood in self.likelihoods.items():
            if not (0.0 <= likelihood <= 1.0):
                raise ValueError(
                    f"Likelihood for '{scenario}' in '{self.name}' is {likelihood}, "
                    f"must be in [0, 1]"
                )
        return True


@dataclass
class BayesianResult:
    """
    Result of Bayesian fusion
    
    Attributes:
        posterior: Final posterior probabilities for each scenario
        prior: Initial prior probabilities
        evidence_trail: Sequential posterior after each evidence update
        log_likelihood: Total log-likelihood of the evidence
        decision: Best scenario based on posterior probability
        confidence: Confidence in the decision
        bayes_factors: Strength of evidence between top two scenarios
        entropy: Shannon entropy of posterior (uncertainty measure)
    """
    posterior: Dict[str, float]
    prior: Dict[str, float]
    evidence_trail: List[Dict[str, float]]
    log_likelihood: float
    decision: str
    confidence: float
    bayes_factors: Dict[str, float]
    entropy: float
    kl_divergence_from_prior: float


class BayesianFusionEngine:
    """
    Bayesian Fusion Engine for financial scenario evaluation
    
    Uses Bayesian inference to sequentially update beliefs about
    financial scenarios based on evidence from multiple sources.
    """
    
    def __init__(self, scenarios: List[str], 
                 prior: Optional[Dict[str, float]] = None):
        """
        Initialize Bayesian engine
        
        Args:
            scenarios: List of scenario IDs
            prior: Prior probabilities for each scenario.
                   If None, uniform prior is used.
        """
        self.scenarios = scenarios
        
        if prior is not None:
            self.prior = prior.copy()
        else:
            # Uniform prior (maximum ignorance)
            n = len(scenarios)
            self.prior = {s: 1.0 / n for s in scenarios}
        
        self._validate_distribution(self.prior, "prior")
    
    def _validate_distribution(self, dist: Dict[str, float], name: str) -> None:
        """Validate that a distribution sums to 1.0"""
        total = sum(dist.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"{name} distribution sums to {total:.6f}, must be 1.0")
    
    def _normalize(self, dist: Dict[str, float]) -> Dict[str, float]:
        """Normalize a distribution to sum to 1.0"""
        total = sum(dist.values())
        if total == 0:
            # Fallback to uniform
            n = len(dist)
            return {k: 1.0 / n for k in dist}
        return {k: v / total for k, v in dist.items()}
    
    def update(self, 
               current_posterior: Dict[str, float],
               evidence: BayesianEvidence) -> Dict[str, float]:
        """
        Single Bayesian update step
        
        P(H|E) = P(E|H) × P(H) / P(E)
        
        Args:
            current_posterior: Current belief distribution
            evidence: New evidence to incorporate
        
        Returns:
            Updated posterior distribution
        """
        evidence.validate()
        
        unnormalized = {}
        
        for scenario in self.scenarios:
            prior_prob = current_posterior.get(scenario, 0.0)
            likelihood = evidence.likelihoods.get(scenario, 0.5)  # Default: non-informative
            
            # Apply evidence weight (tempered likelihood)
            # Weighted likelihood: L^w where w is the weight
            if evidence.weight < 1.0:
                likelihood = likelihood ** evidence.weight
            
            unnormalized[scenario] = prior_prob * likelihood
        
        return self._normalize(unnormalized)
    
    def fuse(self, evidence_sources: List[BayesianEvidence]) -> BayesianResult:
        """
        Execute complete Bayesian fusion pipeline
        
        Sequentially updates prior with each evidence source
        
        Args:
            evidence_sources: List of evidence sources to fuse
        
        Returns:
            BayesianResult with posterior, decision, and diagnostics
        """
        current = self.prior.copy()
        evidence_trail = [current.copy()]
        total_log_likelihood = 0.0
        
        # Sequential Bayesian updating
        for evidence in evidence_sources:
            # Calculate log-likelihood contribution
            for scenario in self.scenarios:
                likelihood = evidence.likelihoods.get(scenario, 0.5)
                if likelihood > 0:
                    total_log_likelihood += math.log(likelihood) * current[scenario]
            
            # Update posterior
            current = self.update(current, evidence)
            evidence_trail.append(current.copy())
        
        # Decision: highest posterior probability
        decision = max(current, key=current.get)
        
        # Confidence metrics
        sorted_probs = sorted(current.values(), reverse=True)
        confidence = sorted_probs[0]
        
        # Bayes factors (evidence strength)
        bayes_factors = self._compute_bayes_factors(current, decision)
        
        # Shannon entropy
        entropy = self._compute_entropy(current)
        
        # KL divergence from prior
        kl_div = self._compute_kl_divergence(current, self.prior)
        
        return BayesianResult(
            posterior=current,
            prior=self.prior.copy(),
            evidence_trail=evidence_trail,
            log_likelihood=total_log_likelihood,
            decision=decision,
            confidence=confidence,
            bayes_factors=bayes_factors,
            entropy=entropy,
            kl_divergence_from_prior=kl_div
        )
    
    def _compute_bayes_factors(self, 
                               posterior: Dict[str, float],
                               best: str) -> Dict[str, float]:
        """
        Compute Bayes factors comparing best scenario to each alternative
        
        BF = P(H_best|E) / P(H_alt|E) × P(H_alt) / P(H_best)
        
        Interpretation:
        - BF > 10: Strong evidence
        - BF > 3: Moderate evidence
        - BF > 1: Weak evidence
        """
        factors = {}
        best_post = posterior[best]
        best_prior = self.prior[best]
        
        for scenario in self.scenarios:
            if scenario == best:
                continue
            
            alt_post = posterior[scenario]
            alt_prior = self.prior[scenario]
            
            if alt_post > 0 and best_prior > 0:
                # Posterior odds / Prior odds
                post_odds = best_post / alt_post
                prior_odds = best_prior / alt_prior if alt_prior > 0 else 1.0
                factors[f"{best}_vs_{scenario}"] = post_odds / prior_odds
            else:
                factors[f"{best}_vs_{scenario}"] = float('inf')
        
        return factors
    
    def _compute_entropy(self, dist: Dict[str, float]) -> float:
        """
        Shannon entropy: H = -Σ p(x) × log₂(p(x))
        
        Lower entropy = more certain decision
        Max entropy = log₂(N) for N scenarios
        """
        entropy = 0.0
        for p in dist.values():
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def _compute_kl_divergence(self, 
                               posterior: Dict[str, float],
                               prior: Dict[str, float]) -> float:
        """
        KL Divergence: DKL(posterior || prior)
        
        Measures how much the posterior diverges from the prior.
        Higher = more informative evidence.
        """
        kl = 0.0
        for scenario in self.scenarios:
            p = posterior.get(scenario, 0.0)
            q = prior.get(scenario, 0.0)
            if p > 0 and q > 0:
                kl += p * math.log(p / q)
        return kl


# ============================================================
# Financial Evidence Builders for Bayesian Fusion
# ============================================================

class BayesianEvidenceBuilder:
    """
    Utility class to convert financial data into Bayesian evidence
    (likelihood functions)
    """
    
    @staticmethod
    def from_invoice_data(scenarios: List[str],
                         spike_pct: float,
                         risk_scenario: str,
                         safe_scenario: str) -> BayesianEvidence:
        """
        Convert invoice data to likelihood function
        
        P(spike_observed | risky_scenario) is high
        P(spike_observed | safe_scenario) is low
        """
        likelihoods = {}
        
        # Likelihood of observing this spike under each scenario
        for scenario in scenarios:
            if scenario == risk_scenario:
                # Risk scenario: high likelihood of invoice spikes
                likelihoods[scenario] = min(0.95, 0.3 + spike_pct / 30.0)
            elif scenario == safe_scenario:
                # Safe scenario: low likelihood of invoice spikes
                likelihoods[scenario] = max(0.05, 0.8 - spike_pct / 25.0)
            else:
                # Other scenarios: moderate likelihood
                likelihoods[scenario] = max(0.1, 0.5 - spike_pct / 50.0)
        
        return BayesianEvidence(
            name="ERP_Invoice_Likelihood",
            likelihoods=likelihoods,
            weight=0.85,
            metadata={"spike_pct": spike_pct}
        )
    
    @staticmethod
    def from_production_data(scenarios: List[str],
                            output_change_pct: float,
                            risk_scenario: str,
                            safe_scenario: str) -> BayesianEvidence:
        """
        Convert production data to likelihood function
        """
        likelihoods = {}
        
        for scenario in scenarios:
            if scenario == risk_scenario:
                # Risk: high likelihood of production decline
                likelihoods[scenario] = min(0.9, 0.3 + abs(output_change_pct) / 25.0)
            elif scenario == safe_scenario:
                # Safe: low likelihood of decline
                likelihoods[scenario] = max(0.1, 0.7 + output_change_pct / 30.0)
            else:
                likelihoods[scenario] = 0.4
        
        return BayesianEvidence(
            name="IoT_Production_Likelihood",
            likelihoods=likelihoods,
            weight=0.75,
            metadata={"output_change_pct": output_change_pct}
        )
    
    @staticmethod
    def from_knowledge_graph(scenarios: List[str],
                            client_status: str,
                            has_historical_pattern: bool,
                            risk_scenario: str,
                            safe_scenario: str) -> BayesianEvidence:
        """
        Convert KG intelligence to likelihood function
        """
        likelihoods = {}
        
        status_lower = client_status.lower()
        
        # Determine risk level from KG
        if "bankruptcy" in status_lower or "chapter 11" in status_lower:
            kg_risk = 0.85
        elif "restructuring" in status_lower:
            kg_risk = 0.65
        elif "stable" in status_lower:
            kg_risk = 0.20
        else:
            kg_risk = 0.40
        
        # Historical pattern increases risk likelihood
        if has_historical_pattern:
            kg_risk = min(0.95, kg_risk + 0.15)
        
        for scenario in scenarios:
            if scenario == risk_scenario:
                likelihoods[scenario] = kg_risk
            elif scenario == safe_scenario:
                likelihoods[scenario] = 1.0 - kg_risk
            else:
                likelihoods[scenario] = 0.4
        
        return BayesianEvidence(
            name="KnowledgeGraph_Likelihood",
            likelihoods=likelihoods,
            weight=0.80,
            metadata={
                "client_status": client_status,
                "has_historical_pattern": has_historical_pattern
            }
        )
    
    @staticmethod
    def from_budget_data(scenarios: List[str],
                        budget_remaining_pct: float,
                        risk_scenario: str,
                        safe_scenario: str) -> BayesianEvidence:
        """
        Convert budget status to likelihood function
        """
        likelihoods = {}
        
        for scenario in scenarios:
            if scenario == risk_scenario:
                # Low budget → high likelihood of risk
                likelihoods[scenario] = min(0.90, 0.2 + (100 - budget_remaining_pct) / 120.0)
            elif scenario == safe_scenario:
                # Low budget → low likelihood of safe outcome
                likelihoods[scenario] = max(0.05, budget_remaining_pct / 120.0)
            else:
                likelihoods[scenario] = 0.35
        
        return BayesianEvidence(
            name="ERP_Budget_Likelihood",
            likelihoods=likelihoods,
            weight=0.90,
            metadata={"budget_remaining_pct": budget_remaining_pct}
        )
    
    @staticmethod
    def from_scenario_scores(scenarios: List[str],
                            scenario_scores: Dict[str, float]) -> BayesianEvidence:
        """
        Convert scenario simulation scores directly to likelihoods
        
        Args:
            scenario_scores: normalized performance scores [0, 1] per scenario
        """
        return BayesianEvidence(
            name="Scenario_Simulation_Likelihood",
            likelihoods=scenario_scores,
            weight=0.70,
            metadata={"scenario_scores": scenario_scores}
        )
