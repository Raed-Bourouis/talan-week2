"""
Scenario Generator
Generate what-if scenarios for financial planning
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """Generate financial scenarios for analysis"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def generate_budget_scenario(self, department_id: str, 
                                 year: int,
                                 change_percent: float) -> Dict[str, Any]:
        """
        Generate budget scenario with specified change
        
        Args:
            department_id: Department identifier
            year: Fiscal year
            change_percent: Percentage change (e.g., 0.10 for +10%, -0.05 for -5%)
            
        Returns:
            Scenario results
        """
        # Get baseline budget
        baseline = self._get_baseline_budget(department_id, year)
        
        # Apply change
        new_allocated = baseline['allocated_amount'] * (1 + change_percent)
        
        # Calculate implications
        scenario = {
            'scenario_id': f"BUDGET_SCENARIO_{department_id}_{year}_{change_percent}",
            'scenario_type': 'budget_adjustment',
            'department_id': department_id,
            'year': year,
            'change_percent': change_percent * 100,
            'baseline': {
                'allocated': baseline['allocated_amount'],
                'spent': baseline['spent_amount'],
                'variance': baseline['variance']
            },
            'adjusted': {
                'allocated': new_allocated,
                'spent': baseline['spent_amount'],  # Spending remains same
                'variance': new_allocated - baseline['spent_amount']
            },
            'impact': {
                'variance_change': (new_allocated - baseline['spent_amount']) - baseline['variance'],
                'new_variance_percent': ((new_allocated - baseline['spent_amount']) / new_allocated) * 100 if new_allocated > 0 else 0
            },
            'recommendations': self._generate_scenario_recommendations(change_percent, baseline)
        }
        
        return scenario
    
    def _get_baseline_budget(self, department_id: str, year: int) -> Dict[str, float]:
        """Get baseline budget data"""
        # Mock data - in production, query database
        return {
            'allocated_amount': 500000.0,
            'spent_amount': 575000.0,
            'variance': -75000.0
        }
    
    def _generate_scenario_recommendations(self, change_percent: float, 
                                          baseline: Dict[str, float]) -> List[str]:
        """Generate recommendations for scenario"""
        recommendations = []
        
        if change_percent > 0:
            recommendations.append(f"Additional ${baseline['allocated_amount'] * change_percent:,.0f} budget allocation")
            recommendations.append("Consider hiring additional staff or expanding projects")
            recommendations.append("Update financial forecasts and stakeholder communications")
        elif change_percent < 0:
            recommendations.append(f"Budget reduction of ${abs(baseline['allocated_amount'] * change_percent):,.0f}")
            recommendations.append("Identify non-critical expenses to defer or eliminate")
            recommendations.append("Consider reallocation of existing resources")
            recommendations.append("Communicate constraints to team early")
        
        return recommendations
    
    def generate_contract_renegotiation_scenario(self, contract_id: str,
                                                  price_change_percent: float,
                                                  term_extension_months: int = 0) -> Dict[str, Any]:
        """
        Generate contract renegotiation scenario
        
        Args:
            contract_id: Contract identifier
            price_change_percent: Price change percentage
            term_extension_months: Extension period in months
            
        Returns:
            Renegotiation scenario
        """
        # Get baseline contract
        baseline = self._get_baseline_contract(contract_id)
        
        new_value = baseline['value'] * (1 + price_change_percent)
        monthly_value = new_value / 12
        
        scenario = {
            'scenario_id': f"CONTRACT_RENEGO_{contract_id}_{price_change_percent}",
            'scenario_type': 'contract_renegotiation',
            'contract_id': contract_id,
            'baseline': baseline,
            'proposed': {
                'value': new_value,
                'price_change_percent': price_change_percent * 100,
                'term_extension_months': term_extension_months,
                'monthly_value': monthly_value
            },
            'financial_impact': {
                'annual_cost_change': new_value - baseline['value'],
                'total_extension_cost': monthly_value * term_extension_months if term_extension_months > 0 else 0
            },
            'recommendations': self._generate_negotiation_recommendations(
                price_change_percent, term_extension_months, baseline
            )
        }
        
        return scenario
    
    def _get_baseline_contract(self, contract_id: str) -> Dict[str, Any]:
        """Get baseline contract data"""
        # Mock data
        return {
            'contract_id': contract_id,
            'name': 'Software License Agreement',
            'supplier': 'TechVendor Inc',
            'value': 120000.0,
            'term_months': 12,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
    
    def _generate_negotiation_recommendations(self, price_change: float,
                                             extension: int,
                                             baseline: Dict) -> List[str]:
        """Generate negotiation recommendations"""
        recommendations = []
        
        if price_change > 0.05:
            recommendations.append("Significant price increase - negotiate alternative terms")
            recommendations.append("Consider multi-year lock-in for price protection")
            recommendations.append("Request additional services or features to justify increase")
        elif price_change < 0:
            recommendations.append("Price reduction opportunity - consider extended commitment")
            
        if extension > 12:
            recommendations.append("Long extension period - ensure flexibility clauses")
            recommendations.append("Include performance review milestones")
        
        return recommendations
    
    def compare_scenarios(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple scenarios side-by-side
        
        Args:
            scenarios: List of scenario dictionaries
            
        Returns:
            Comparison analysis
        """
        if not scenarios:
            return {'error': 'No scenarios provided'}
        
        comparison = {
            'num_scenarios': len(scenarios),
            'scenarios': scenarios,
            'analysis': {
                'best_case': None,
                'worst_case': None,
                'recommended': None
            }
        }
        
        # For budget scenarios, find best and worst by variance
        budget_scenarios = [s for s in scenarios if s.get('scenario_type') == 'budget_adjustment']
        if budget_scenarios:
            best = max(budget_scenarios, key=lambda x: x['impact']['new_variance_percent'])
            worst = min(budget_scenarios, key=lambda x: x['impact']['new_variance_percent'])
            
            comparison['analysis']['best_case'] = best['scenario_id']
            comparison['analysis']['worst_case'] = worst['scenario_id']
            comparison['analysis']['recommended'] = best['scenario_id']
        
        return comparison
