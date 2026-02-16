"""
Optimizer
Contract negotiation and resource allocation optimization
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Optimizer:
    """Optimize financial decisions"""
    
    def __init__(self):
        pass
    
    def optimize_payment_schedule(self, invoices: List[Dict[str, Any]],
                                  available_cash: float,
                                  target_days: int = 30) -> Dict[str, Any]:
        """
        Optimize payment schedule to maximize cash retention while minimizing late fees
        
        Args:
            invoices: List of pending invoices
            available_cash: Available cash for payments
            target_days: Target days to schedule payments within
            
        Returns:
            Optimized payment schedule
        """
        # Sort invoices by priority
        prioritized = self._prioritize_invoices(invoices)
        
        # Create payment schedule
        schedule = []
        remaining_cash = available_cash
        total_payments = 0
        
        for invoice in prioritized:
            if remaining_cash >= invoice['amount']:
                schedule.append({
                    'invoice_id': invoice['invoice_id'],
                    'amount': invoice['amount'],
                    'priority': invoice['priority'],
                    'due_date': invoice['due_date'],
                    'recommended_payment_date': invoice['due_date'],
                    'reason': 'Pay on time - sufficient cash available'
                })
                remaining_cash -= invoice['amount']
                total_payments += invoice['amount']
            else:
                # Defer if possible
                schedule.append({
                    'invoice_id': invoice['invoice_id'],
                    'amount': invoice['amount'],
                    'priority': invoice['priority'],
                    'due_date': invoice['due_date'],
                    'recommended_payment_date': self._calculate_deferred_date(invoice['due_date'], 7),
                    'reason': 'Defer - insufficient immediate cash',
                    'estimated_late_fee': invoice['amount'] * 0.01  # 1% late fee estimate
                })
        
        return {
            'total_invoices': len(invoices),
            'total_amount_due': sum(inv['amount'] for inv in invoices),
            'available_cash': available_cash,
            'scheduled_payments': total_payments,
            'remaining_cash': remaining_cash,
            'schedule': schedule,
            'recommendations': self._generate_payment_recommendations(schedule, remaining_cash)
        }
    
    def _prioritize_invoices(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize invoices for payment"""
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        return sorted(invoices, key=lambda x: (
            priority_order.get(x.get('priority', 'medium'), 2),
            x.get('due_date', '9999-12-31')
        ))
    
    def _calculate_deferred_date(self, due_date: str, days_defer: int) -> str:
        """Calculate deferred payment date"""
        from datetime import datetime, timedelta
        due = datetime.fromisoformat(due_date)
        deferred = due + timedelta(days=days_defer)
        return deferred.strftime('%Y-%m-%d')
    
    def _generate_payment_recommendations(self, schedule: List[Dict], remaining_cash: float) -> List[str]:
        """Generate payment optimization recommendations"""
        recommendations = []
        
        deferred_count = sum(1 for s in schedule if 'Defer' in s.get('reason', ''))
        
        if deferred_count > 0:
            recommendations.append(f"{deferred_count} payments deferred due to cash constraints")
            recommendations.append("Consider arranging short-term credit to avoid late fees")
            
            total_late_fees = sum(s.get('estimated_late_fee', 0) for s in schedule)
            if total_late_fees > 0:
                recommendations.append(f"Estimated late fees: ${total_late_fees:,.2f}")
        
        if remaining_cash > 500000:
            recommendations.append("Significant cash buffer remaining - consider investment opportunities")
        elif remaining_cash < 100000:
            recommendations.append("Low cash buffer - accelerate receivables collection")
        
        return recommendations
    
    def optimize_budget_allocation(self, departments: List[Dict[str, Any]],
                                   total_budget: float,
                                   constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize budget allocation across departments
        
        Args:
            departments: List of departments with current allocation
            total_budget: Total available budget
            constraints: Optional allocation constraints
            
        Returns:
            Optimized allocation
        """
        # Calculate current allocation
        current_total = sum(d['current_allocation'] for d in departments)
        
        # Simple proportional reallocation based on utilization
        optimized = []
        remaining_budget = total_budget
        
        # Sort by utilization rate (underutilized first)
        sorted_depts = sorted(departments, key=lambda x: x.get('utilization_rate', 1.0))
        
        for dept in sorted_depts:
            utilization = dept.get('utilization_rate', 1.0)
            performance = dept.get('performance_score', 0.5)
            
            # Calculate optimal allocation (reward high performance and high utilization)
            adjustment_factor = (utilization * 0.6) + (performance * 0.4)
            optimal_allocation = (dept['current_allocation'] / current_total) * total_budget * adjustment_factor
            
            # Apply constraints if any
            if constraints:
                min_allocation = constraints.get('min_per_dept', 0)
                max_allocation = constraints.get('max_per_dept', float('inf'))
                optimal_allocation = max(min_allocation, min(max_allocation, optimal_allocation))
            
            optimized.append({
                'department': dept['department'],
                'current_allocation': dept['current_allocation'],
                'optimal_allocation': optimal_allocation,
                'change': optimal_allocation - dept['current_allocation'],
                'change_percent': ((optimal_allocation - dept['current_allocation']) / dept['current_allocation'] * 100) if dept['current_allocation'] > 0 else 0
            })
            
            remaining_budget -= optimal_allocation
        
        # Distribute any remaining budget proportionally
        if remaining_budget > 0:
            for opt in optimized:
                additional = (opt['optimal_allocation'] / total_budget) * remaining_budget
                opt['optimal_allocation'] += additional
                opt['change'] = opt['optimal_allocation'] - opt['current_allocation']
        
        return {
            'total_budget': total_budget,
            'current_total': current_total,
            'optimized_allocations': optimized,
            'total_reallocated': sum(abs(o['change']) for o in optimized),
            'recommendations': self._generate_allocation_recommendations(optimized)
        }
    
    def _generate_allocation_recommendations(self, optimized: List[Dict]) -> List[str]:
        """Generate budget allocation recommendations"""
        recommendations = []
        
        increases = [o for o in optimized if o['change'] > 0]
        decreases = [o for o in optimized if o['change'] < 0]
        
        if increases:
            top_increase = max(increases, key=lambda x: x['change_percent'])
            recommendations.append(
                f"Increase {top_increase['department']} budget by "
                f"{top_increase['change_percent']:.1f}% (${top_increase['change']:,.0f})"
            )
        
        if decreases:
            top_decrease = min(decreases, key=lambda x: x['change_percent'])
            recommendations.append(
                f"Reduce {top_decrease['department']} budget by "
                f"{abs(top_decrease['change_percent']):.1f}% (${abs(top_decrease['change']):,.0f})"
            )
        
        recommendations.append("Review reallocation with department heads before implementing")
        
        return recommendations
