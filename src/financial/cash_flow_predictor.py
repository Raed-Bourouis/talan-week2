"""
Cash Flow Predictor
Treasury forecasting using historical data and Monte Carlo simulation
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class CashFlowPredictor:
    """Predict cash flow and identify treasury tensions"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def forecast_cash_flow(self, days: int = 90) -> Dict[str, Any]:
        """
        Forecast cash flow for next N days
        
        Args:
            days: Number of days to forecast
            
        Returns:
            Cash flow forecast with confidence intervals
        """
        # Get historical data
        historical_data = self._get_historical_cash_flow(days=180)
        
        # Get pending invoices and payments
        pending_inflows = self._get_pending_receivables()
        pending_outflows = self._get_pending_payables()
        
        # Generate forecast
        forecast = self._generate_forecast(days, historical_data, pending_inflows, pending_outflows)
        
        # Identify tensions
        tensions = self._identify_tensions(forecast)
        
        return {
            'forecast_days': days,
            'generated_at': datetime.now().isoformat(),
            'forecast': forecast,
            'pending_inflows': pending_inflows,
            'pending_outflows': pending_outflows,
            'tensions': tensions,
            'recommendations': self._generate_recommendations(tensions)
        }
    
    def _get_historical_cash_flow(self, days: int) -> List[Dict[str, Any]]:
        """Get historical cash flow data"""
        # Mock historical data - in production, query actual database
        historical = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            # Simulate daily cash flow with some variation
            daily_inflow = random.uniform(50000, 150000)
            daily_outflow = random.uniform(40000, 140000)
            
            historical.append({
                'date': date.strftime('%Y-%m-%d'),
                'inflow': daily_inflow,
                'outflow': daily_outflow,
                'net': daily_inflow - daily_outflow
            })
        
        return historical
    
    def _get_pending_receivables(self) -> List[Dict[str, Any]]:
        """Get pending incoming payments"""
        # Mock data
        return [
            {'invoice_id': 'INV-001', 'amount': 50000, 'due_date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'), 'probability': 0.9},
            {'invoice_id': 'INV-002', 'amount': 75000, 'due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'), 'probability': 0.85},
            {'invoice_id': 'INV-003', 'amount': 100000, 'due_date': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'), 'probability': 0.8},
        ]
    
    def _get_pending_payables(self) -> List[Dict[str, Any]]:
        """Get pending outgoing payments"""
        # Mock data
        return [
            {'invoice_id': 'BILL-001', 'amount': 45000, 'due_date': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'), 'priority': 'high'},
            {'invoice_id': 'BILL-002', 'amount': 30000, 'due_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'), 'priority': 'medium'},
            {'invoice_id': 'BILL-003', 'amount': 85000, 'due_date': (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d'), 'priority': 'high'},
        ]
    
    def _generate_forecast(self, days: int, historical: List[Dict], 
                          inflows: List[Dict], outflows: List[Dict]) -> List[Dict[str, Any]]:
        """Generate forecast using historical trends and known transactions"""
        forecast = []
        
        # Calculate average daily flows from historical data
        if historical:
            avg_daily_inflow = sum(d['inflow'] for d in historical[-30:]) / min(30, len(historical))
            avg_daily_outflow = sum(d['outflow'] for d in historical[-30:]) / min(30, len(historical))
        else:
            avg_daily_inflow = 80000
            avg_daily_outflow = 75000
        
        running_balance = 1000000  # Starting balance
        
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Base forecast on historical average with some randomness
            daily_inflow = avg_daily_inflow * random.uniform(0.8, 1.2)
            daily_outflow = avg_daily_outflow * random.uniform(0.8, 1.2)
            
            # Add known transactions for this date
            for inflow in inflows:
                if inflow['due_date'] == date_str:
                    daily_inflow += inflow['amount'] * inflow['probability']
            
            for outflow in outflows:
                if outflow['due_date'] == date_str:
                    daily_outflow += outflow['amount']
            
            net_flow = daily_inflow - daily_outflow
            running_balance += net_flow
            
            # Calculate confidence intervals (mock - in production use Monte Carlo)
            confidence_low = running_balance * 0.9
            confidence_high = running_balance * 1.1
            
            forecast.append({
                'date': date_str,
                'predicted_inflow': round(daily_inflow, 2),
                'predicted_outflow': round(daily_outflow, 2),
                'net_flow': round(net_flow, 2),
                'balance': round(running_balance, 2),
                'confidence_low': round(confidence_low, 2),
                'confidence_high': round(confidence_high, 2)
            })
        
        return forecast
    
    def _identify_tensions(self, forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential cash flow tensions"""
        tensions = []
        
        for day_forecast in forecast:
            # Check if balance goes below threshold
            if day_forecast['balance'] < 500000:
                tensions.append({
                    'date': day_forecast['date'],
                    'type': 'low_balance',
                    'severity': 'high' if day_forecast['balance'] < 250000 else 'medium',
                    'balance': day_forecast['balance'],
                    'description': f"Cash balance projected at ${day_forecast['balance']:,.0f}"
                })
            
            # Check for large negative net flow
            if day_forecast['net_flow'] < -100000:
                tensions.append({
                    'date': day_forecast['date'],
                    'type': 'large_outflow',
                    'severity': 'medium',
                    'net_flow': day_forecast['net_flow'],
                    'description': f"Large net outflow of ${abs(day_forecast['net_flow']):,.0f}"
                })
        
        return tensions[:10]  # Return top 10 tensions
    
    def _generate_recommendations(self, tensions: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not tensions:
            recommendations.append("Cash flow forecast looks healthy")
            return recommendations
        
        low_balance_tensions = [t for t in tensions if t['type'] == 'low_balance']
        if low_balance_tensions:
            earliest = low_balance_tensions[0]
            recommendations.append(
                f"Alert: Low cash balance projected on {earliest['date']}. "
                "Consider arranging credit line or accelerating receivables."
            )
        
        large_outflow_tensions = [t for t in tensions if t['type'] == 'large_outflow']
        if large_outflow_tensions:
            recommendations.append(
                f"Consider distributing large payments across multiple periods to smooth cash flow"
            )
        
        if len(tensions) > 5:
            recommendations.append(
                "Multiple cash tensions identified. Recommend comprehensive treasury review."
            )
        
        return recommendations
