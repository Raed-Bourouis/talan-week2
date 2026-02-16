"""
Monte Carlo Simulation
Probabilistic cash flow modeling
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class MonteCarloSimulator:
    """Run Monte Carlo simulations for financial forecasting"""
    
    def __init__(self, num_simulations: int = 1000):
        self.num_simulations = num_simulations
    
    def simulate_cash_flow(self, days: int = 90,
                          initial_balance: float = 1000000,
                          avg_daily_inflow: float = 80000,
                          avg_daily_outflow: float = 75000,
                          volatility: float = 0.2) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for cash flow
        
        Args:
            days: Number of days to simulate
            initial_balance: Starting cash balance
            avg_daily_inflow: Average daily inflow
            avg_daily_outflow: Average daily outflow
            volatility: Volatility factor (0.2 = 20% variation)
            
        Returns:
            Simulation results with percentiles
        """
        logger.info(f"Running {self.num_simulations} Monte Carlo simulations for {days} days")
        
        # Run simulations
        all_simulations = []
        for sim in range(self.num_simulations):
            simulation = self._run_single_simulation(
                days, initial_balance, avg_daily_inflow, avg_daily_outflow, volatility
            )
            all_simulations.append(simulation)
        
        # Calculate statistics
        results = self._calculate_statistics(all_simulations, days)
        
        # Identify risk periods
        risks = self._identify_risk_periods(results)
        
        return {
            'parameters': {
                'num_simulations': self.num_simulations,
                'days': days,
                'initial_balance': initial_balance,
                'avg_daily_inflow': avg_daily_inflow,
                'avg_daily_outflow': avg_daily_outflow,
                'volatility': volatility
            },
            'results': results,
            'risks': risks,
            'summary': {
                'mean_final_balance': results[-1]['mean'],
                'p10_final_balance': results[-1]['p10'],
                'p50_final_balance': results[-1]['p50'],
                'p90_final_balance': results[-1]['p90'],
                'probability_negative': self._calculate_probability_negative(all_simulations)
            }
        }
    
    def _run_single_simulation(self, days: int, initial_balance: float,
                               avg_inflow: float, avg_outflow: float,
                               volatility: float) -> List[float]:
        """Run a single simulation path"""
        balances = [initial_balance]
        
        for day in range(days):
            # Add random variation to flows
            daily_inflow = max(0, random.gauss(avg_inflow, avg_inflow * volatility))
            daily_outflow = max(0, random.gauss(avg_outflow, avg_outflow * volatility))
            
            net_flow = daily_inflow - daily_outflow
            new_balance = balances[-1] + net_flow
            
            balances.append(new_balance)
        
        return balances
    
    def _calculate_statistics(self, all_simulations: List[List[float]], 
                             days: int) -> List[Dict[str, float]]:
        """Calculate statistics across all simulations"""
        statistics = []
        
        for day in range(days + 1):
            day_balances = [sim[day] for sim in all_simulations]
            day_balances.sort()
            
            statistics.append({
                'day': day,
                'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                'mean': sum(day_balances) / len(day_balances),
                'p10': day_balances[int(len(day_balances) * 0.10)],
                'p25': day_balances[int(len(day_balances) * 0.25)],
                'p50': day_balances[int(len(day_balances) * 0.50)],
                'p75': day_balances[int(len(day_balances) * 0.75)],
                'p90': day_balances[int(len(day_balances) * 0.90)],
                'min': min(day_balances),
                'max': max(day_balances)
            })
        
        return statistics
    
    def _identify_risk_periods(self, results: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Identify periods with high risk of negative balance"""
        risks = []
        
        for day_result in results:
            if day_result['p10'] < 250000:  # 10th percentile below threshold
                risks.append({
                    'date': day_result['date'],
                    'day': day_result['day'],
                    'risk_level': 'high' if day_result['p10'] < 100000 else 'medium',
                    'p10_balance': day_result['p10'],
                    'description': f"10th percentile balance: ${day_result['p10']:,.0f}"
                })
        
        return risks
    
    def _calculate_probability_negative(self, all_simulations: List[List[float]]) -> float:
        """Calculate probability of going negative at any point"""
        negative_count = 0
        
        for simulation in all_simulations:
            if any(balance < 0 for balance in simulation):
                negative_count += 1
        
        return (negative_count / len(all_simulations)) * 100
    
    def simulate_investment_returns(self, initial_investment: float,
                                    expected_return: float,
                                    volatility: float,
                                    years: int) -> Dict[str, Any]:
        """
        Simulate investment returns
        
        Args:
            initial_investment: Initial investment amount
            expected_return: Expected annual return (e.g., 0.07 for 7%)
            volatility: Annual volatility (e.g., 0.15 for 15%)
            years: Number of years to simulate
            
        Returns:
            Simulation results
        """
        all_final_values = []
        
        for _ in range(self.num_simulations):
            value = initial_investment
            
            for year in range(years):
                # Simulate annual return with volatility
                annual_return = random.gauss(expected_return, volatility)
                value = value * (1 + annual_return)
            
            all_final_values.append(value)
        
        all_final_values.sort()
        
        return {
            'initial_investment': initial_investment,
            'years': years,
            'expected_return': expected_return * 100,
            'volatility': volatility * 100,
            'results': {
                'mean': sum(all_final_values) / len(all_final_values),
                'median': all_final_values[len(all_final_values) // 2],
                'p10': all_final_values[int(len(all_final_values) * 0.10)],
                'p90': all_final_values[int(len(all_final_values) * 0.90)],
                'min': min(all_final_values),
                'max': max(all_final_values)
            },
            'probability_of_loss': sum(1 for v in all_final_values if v < initial_investment) / len(all_final_values) * 100
        }
