"""
Budget Analyzer
Budget variance analysis and forecasting
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class BudgetAnalyzer:
    """Analyze budget variance and provide forecasting"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def analyze_budget(self, department_id: str, year: int) -> Dict[str, Any]:
        """
        Analyze budget for a specific department and year
        
        Args:
            department_id: Department identifier
            year: Fiscal year
            
        Returns:
            Budget analysis results
        """
        # Get budget data
        budget_data = self._get_budget_data(department_id, year)
        
        if not budget_data:
            return {'error': 'No budget data found'}
        
        # Calculate metrics
        variance = budget_data['spent_amount'] - budget_data['allocated_amount']
        variance_percent = (variance / budget_data['allocated_amount']) * 100 if budget_data['allocated_amount'] > 0 else 0
        
        # Determine status
        if variance_percent > 10:
            status = 'significantly_over_budget'
            severity = 'critical'
        elif variance_percent > 0:
            status = 'over_budget'
            severity = 'warning'
        elif variance_percent < -10:
            status = 'significantly_under_budget'
            severity = 'info'
        else:
            status = 'on_track'
            severity = 'normal'
        
        # Get top spending categories
        top_expenses = self._get_top_expenses(department_id, year)
        
        # Generate recommendations
        recommendations = self._generate_budget_recommendations(
            variance_percent, budget_data, top_expenses
        )
        
        return {
            'department_id': department_id,
            'year': year,
            'allocated': float(budget_data['allocated_amount']),
            'spent': float(budget_data['spent_amount']),
            'remaining': float(budget_data['allocated_amount'] - budget_data['spent_amount']),
            'variance': float(variance),
            'variance_percent': float(variance_percent),
            'status': status,
            'severity': severity,
            'top_expenses': top_expenses,
            'recommendations': recommendations
        }
    
    def _get_budget_data(self, department_id: str, year: int) -> Optional[Dict[str, Any]]:
        """Retrieve budget data from database"""
        # This would query the actual database
        # For now, return mock data
        return {
            'allocated_amount': Decimal('500000.00'),
            'spent_amount': Decimal('575000.00')
        }
    
    def _get_top_expenses(self, department_id: str, year: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top expenses for the department"""
        # Mock data
        return [
            {'category': 'Marketing Campaigns', 'amount': 250000, 'percent': 43.5},
            {'category': 'Events', 'amount': 150000, 'percent': 26.1},
            {'category': 'Software', 'amount': 100000, 'percent': 17.4},
            {'category': 'Consulting', 'amount': 50000, 'percent': 8.7},
            {'category': 'Other', 'amount': 25000, 'percent': 4.3},
        ]
    
    def _generate_budget_recommendations(self, variance_percent: float, 
                                        budget_data: Dict[str, Any],
                                        top_expenses: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if variance_percent > 10:
            recommendations.append("Immediate action required: Budget significantly exceeded")
            recommendations.append("Review and approve any remaining non-critical expenses")
            recommendations.append("Consider requesting supplemental budget allocation")
            
            if top_expenses and top_expenses[0]['percent'] > 40:
                recommendations.append(
                    f"Focus on {top_expenses[0]['category']} which represents "
                    f"{top_expenses[0]['percent']:.1f}% of spending"
                )
        
        elif variance_percent > 0:
            recommendations.append("Monitor spending closely to prevent further overrun")
            recommendations.append("Review remaining planned expenses for potential cuts")
        
        else:
            recommendations.append("Budget tracking is on target")
            recommendations.append("Continue monitoring to maintain current trajectory")
        
        return recommendations
    
    def forecast_year_end(self, department_id: str, year: int) -> Dict[str, Any]:
        """
        Forecast year-end budget position
        
        Args:
            department_id: Department identifier
            year: Fiscal year
            
        Returns:
            Forecast results
        """
        budget_data = self._get_budget_data(department_id, year)
        
        if not budget_data:
            return {'error': 'No budget data found'}
        
        # Simple linear projection based on current burn rate
        # In production, this would use more sophisticated forecasting
        months_elapsed = datetime.now().month
        months_remaining = 12 - months_elapsed
        
        if months_elapsed > 0:
            monthly_burn_rate = budget_data['spent_amount'] / months_elapsed
            projected_spending = budget_data['spent_amount'] + (monthly_burn_rate * months_remaining)
        else:
            projected_spending = budget_data['spent_amount']
        
        projected_variance = projected_spending - budget_data['allocated_amount']
        projected_variance_percent = (projected_variance / budget_data['allocated_amount']) * 100
        
        return {
            'department_id': department_id,
            'year': year,
            'current_spent': float(budget_data['spent_amount']),
            'projected_year_end': float(projected_spending),
            'projected_variance': float(projected_variance),
            'projected_variance_percent': float(projected_variance_percent),
            'months_remaining': months_remaining,
            'confidence': 'medium' if months_elapsed >= 3 else 'low'
        }
