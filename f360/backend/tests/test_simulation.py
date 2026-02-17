"""
F360 – Tests: Simulation Engine
"""
import pytest
from app.services.simulation.engine import SimulationEngine


@pytest.fixture
def engine():
    return SimulationEngine()


class TestBudgetVariation:
    def test_default_params(self, engine):
        result = engine.simulate_budget_variation({})
        assert result["simulation_type"] == "budget_variation"
        assert result["base_budget"] == 1_000_000
        assert len(result["scenarios"]) == 7  # [-15,-10,-5,0,5,10,15]

    def test_custom_budget(self, engine):
        result = engine.simulate_budget_variation({
            "base_budget": 2_000_000,
            "variation_pct": [-10, 0, 10],
        })
        assert result["base_budget"] == 2_000_000
        assert len(result["scenarios"]) == 3

        # Check 0% scenario
        zero_scenario = [s for s in result["scenarios"] if s["variation_pct"] == 0][0]
        assert zero_scenario["total_budget"] == 2_000_000
        assert zero_scenario["delta"] == 0

    def test_negative_variation(self, engine):
        result = engine.simulate_budget_variation({
            "base_budget": 1_000_000,
            "variation_pct": [-20],
        })
        scenario = result["scenarios"][0]
        assert scenario["total_budget"] == 800_000
        assert scenario["delta"] == -200_000


class TestCashflowProjection:
    def test_default_projection(self, engine):
        result = engine.simulate_cashflow_projection({})
        assert result["simulation_type"] == "cashflow_projection"
        assert result["initial_balance"] == 500_000
        assert result["days_projected"] == 90
        assert len(result["projections"]) == 90

    def test_custom_params(self, engine):
        result = engine.simulate_cashflow_projection({
            "initial_balance": 1_000_000,
            "daily_avg_inflow": 20_000,
            "daily_avg_outflow": 10_000,
            "days": 30,
        })
        assert result["initial_balance"] == 1_000_000
        assert result["days_projected"] == 30
        # Net positive flow: balance should grow
        assert result["final_balance"] > result["initial_balance"]


class TestMonteCarlo:
    def test_default_simulation(self, engine):
        result = engine.simulate_monte_carlo({})
        assert result["simulation_type"] == "monte_carlo"
        assert result["num_simulations"] == 10_000
        assert "percentiles" in result
        assert "probability_of_loss" in result
        assert "histogram" in result
        assert result["risk_assessment"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")

    def test_high_volatility(self, engine):
        result = engine.simulate_monte_carlo({
            "base_revenue": 1_000_000,
            "base_costs": 900_000,
            "revenue_volatility": 0.5,
            "cost_volatility": 0.4,
            "num_simulations": 1000,
        })
        # High volatility should lead to higher probability of loss
        assert result["probability_of_loss"] > 0


class TestRenegotiation:
    def test_profitable_renegotiation(self, engine):
        result = engine.simulate_renegotiation_impact({
            "current_annual_cost": 500_000,
            "proposed_discount_pct": 15,
            "contract_duration_years": 3,
            "inflation_rate": 0.03,
            "has_indexation_clause": True,
            "penalty_exit_pct": 5,
        })
        assert result["simulation_type"] == "renegotiation"
        assert result["net_savings"] > 0
        assert result["proposed_discount_pct"] == 15
        assert len(result["current_scenario"]) == 3
        assert len(result["renegotiated_scenario"]) == 3

    def test_no_indexation(self, engine):
        result = engine.simulate_renegotiation_impact({
            "current_annual_cost": 100_000,
            "proposed_discount_pct": 10,
            "contract_duration_years": 2,
            "has_indexation_clause": False,
        })
        # Without indexation, costs stay flat
        for year_data in result["current_scenario"]:
            assert year_data["cost"] == 100_000
