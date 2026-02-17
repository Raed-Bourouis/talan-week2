"""
Configuration settings for F360 Financial Synthesis Engine
Centralized configuration for weights, thresholds, and operational parameters
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SynthesisConfig:
    """Configuration for F360 Synthesis Engine"""
    
    # ==================== DECISION FUSION WEIGHTS ====================
    
    # Base weights for decision fusion
    risk_weight: float = 0.6  # Weight for risk mitigation (0.0 - 1.0)
    profitability_weight: float = 0.4  # Weight for profitability (0.0 - 1.0)
    
    # Weight adjustment parameters
    critical_risk_weight_boost: float = 0.2  # Additional risk weight when critical signals detected
    max_risk_weight: float = 0.8  # Maximum risk weight after adjustment
    
    # ==================== WEAK SIGNAL THRESHOLDS ====================
    
    # Production-Finance correlation
    production_slowdown_threshold: float = -5.0  # % change triggering concern
    invoice_spike_threshold: float = 10.0  # % spike triggering concern
    
    # Budget thresholds
    budget_critical_threshold: float = 10.0  # % remaining considered critical
    budget_warning_threshold: float = 20.0  # % remaining considered warning
    
    # Correlation strength thresholds
    weak_correlation_threshold: float = 0.3
    moderate_correlation_threshold: float = 0.6
    strong_correlation_threshold: float = 0.8
    
    # ==================== RISK LEVEL MAPPINGS ====================
    
    # Stress score to risk level conversion
    stress_score_critical: float = 0.7  # Above this = CRITICAL
    stress_score_high: float = 0.5  # Above this = HIGH
    stress_score_medium: float = 0.3  # Above this = MEDIUM
    
    # ==================== PRIORITY DETERMINATION ====================
    
    # Cash flow impact thresholds for priority
    high_priority_cash_flow_threshold: float = 15.0  # % impact
    medium_priority_cash_flow_threshold: float = 5.0  # % impact
    
    # Weak signal count thresholds
    high_priority_weak_signal_count: int = 2
    medium_priority_weak_signal_count: int = 1
    
    # ==================== CONFIDENCE SCORING ====================
    
    # Confidence calculation parameters
    base_confidence_weight: float = 0.7  # Weight of scenario probability
    signal_strength_weight: float = 0.3  # Weight of weak signal correlation
    
    # ==================== SCENARIO EVALUATION ====================
    
    # Minimum probability threshold for scenario consideration
    min_scenario_probability: float = 0.5
    
    # Maximum number of scenarios to evaluate
    max_scenarios: int = 10
    
    # ==================== HISTORICAL PATTERN MATCHING ====================
    
    # Historical pattern relevance decay
    pattern_relevance_decay_years: float = 3.0  # Years after which patterns lose relevance
    pattern_match_weight: float = 0.75  # Weight of historical pattern in decision
    
    # ==================== EXTERNAL INTEGRATION ====================
    
    # API timeouts (milliseconds)
    erp_api_timeout: int = 5000
    knowledge_graph_timeout: int = 3000
    scenario_simulation_timeout: int = 10000
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_ms: int = 1000
    
    def validate(self) -> bool:
        """
        Validate configuration parameters
        
        Returns:
            True if configuration is valid, raises ValueError otherwise
        """
        # Validate weights sum to 1.0
        if abs(self.risk_weight + self.profitability_weight - 1.0) > 0.01:
            raise ValueError(
                f"Risk weight ({self.risk_weight}) and profitability weight "
                f"({self.profitability_weight}) must sum to 1.0"
            )
        
        # Validate weight ranges
        if not (0.0 <= self.risk_weight <= 1.0):
            raise ValueError(f"Risk weight must be between 0.0 and 1.0, got {self.risk_weight}")
        
        if not (0.0 <= self.profitability_weight <= 1.0):
            raise ValueError(
                f"Profitability weight must be between 0.0 and 1.0, got {self.profitability_weight}"
            )
        
        # Validate threshold ordering
        if not (self.weak_correlation_threshold < 
                self.moderate_correlation_threshold < 
                self.strong_correlation_threshold):
            raise ValueError("Correlation thresholds must be in ascending order")
        
        if not (self.stress_score_medium < 
                self.stress_score_high < 
                self.stress_score_critical):
            raise ValueError("Stress score thresholds must be in ascending order")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "decision_fusion": {
                "risk_weight": self.risk_weight,
                "profitability_weight": self.profitability_weight,
                "critical_risk_weight_boost": self.critical_risk_weight_boost,
                "max_risk_weight": self.max_risk_weight
            },
            "weak_signals": {
                "production_slowdown_threshold": self.production_slowdown_threshold,
                "invoice_spike_threshold": self.invoice_spike_threshold,
                "budget_critical_threshold": self.budget_critical_threshold,
                "budget_warning_threshold": self.budget_warning_threshold
            },
            "risk_levels": {
                "stress_score_critical": self.stress_score_critical,
                "stress_score_high": self.stress_score_high,
                "stress_score_medium": self.stress_score_medium
            },
            "priorities": {
                "high_cash_flow_threshold": self.high_priority_cash_flow_threshold,
                "medium_cash_flow_threshold": self.medium_priority_cash_flow_threshold,
                "high_weak_signal_count": self.high_priority_weak_signal_count,
                "medium_weak_signal_count": self.medium_priority_weak_signal_count
            }
        }


# ==================== PRESET CONFIGURATIONS ====================

class ConfigPresets:
    """Predefined configuration presets for different operational modes"""
    
    @staticmethod
    def conservative() -> SynthesisConfig:
        """
        Conservative mode: Maximum risk mitigation
        Use when: Financial stability is paramount
        """
        return SynthesisConfig(
            risk_weight=0.8,
            profitability_weight=0.2,
            critical_risk_weight_boost=0.15,
            budget_critical_threshold=15.0,
            high_priority_cash_flow_threshold=10.0
        )
    
    @staticmethod
    def balanced() -> SynthesisConfig:
        """
        Balanced mode: Equal weight to risk and profitability
        Use when: Normal operational conditions
        """
        return SynthesisConfig(
            risk_weight=0.5,
            profitability_weight=0.5,
            critical_risk_weight_boost=0.2,
            budget_critical_threshold=10.0,
            high_priority_cash_flow_threshold=15.0
        )
    
    @staticmethod
    def aggressive() -> SynthesisConfig:
        """
        Aggressive mode: Profit-focused, higher risk tolerance
        Use when: Growth phase, strong cash position
        """
        return SynthesisConfig(
            risk_weight=0.3,
            profitability_weight=0.7,
            critical_risk_weight_boost=0.1,
            budget_critical_threshold=5.0,
            high_priority_cash_flow_threshold=20.0
        )
    
    @staticmethod
    def crisis() -> SynthesisConfig:
        """
        Crisis mode: Extreme risk aversion
        Use when: Financial emergency, liquidity crisis
        """
        return SynthesisConfig(
            risk_weight=0.9,
            profitability_weight=0.1,
            critical_risk_weight_boost=0.05,  # Already at max
            budget_critical_threshold=20.0,
            high_priority_cash_flow_threshold=5.0,
            production_slowdown_threshold=-3.0,  # More sensitive
            invoice_spike_threshold=5.0  # More sensitive
        )


# Default configuration instance
DEFAULT_CONFIG = SynthesisConfig()


if __name__ == "__main__":
    # Demonstrate configuration presets
    print("F360 Synthesis Engine Configuration Presets\n")
    
    presets = [
        ("Default", SynthesisConfig()),
        ("Conservative", ConfigPresets.conservative()),
        ("Balanced", ConfigPresets.balanced()),
        ("Aggressive", ConfigPresets.aggressive()),
        ("Crisis", ConfigPresets.crisis())
    ]
    
    for name, config in presets:
        print(f"{name} Configuration:")
        print(f"  Risk Weight: {config.risk_weight}")
        print(f"  Profitability Weight: {config.profitability_weight}")
        print(f"  Budget Critical Threshold: {config.budget_critical_threshold}%")
        print(f"  High Priority Cash Flow Threshold: {config.high_priority_cash_flow_threshold}%")
        print()
