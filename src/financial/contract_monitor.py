"""
Contract Monitor
Contract clause extraction and expiration alerts
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from dateutil import parser

logger = logging.getLogger(__name__)


class ContractMonitor:
    """Monitor contracts and extract important clauses"""
    
    def __init__(self, db_connection, neo4j_driver):
        self.db = db_connection
        self.neo4j_driver = neo4j_driver
    
    def get_expiring_contracts(self, days_ahead: int = 90) -> List[Dict[str, Any]]:
        """
        Get contracts expiring within specified days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiring contracts
        """
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        with self.neo4j_driver.session() as session:
            query = """
            MATCH (s:Supplier)-[:HAS_CONTRACT]->(c:Contract)
            WHERE c.end_date <= date($cutoff_date)
            AND c.status = 'active'
            RETURN c.id as contract_id, c.name as name, s.name as supplier,
                   c.end_date as end_date, c.value as value, c.auto_renew as auto_renew,
                   c.clauses as clauses
            ORDER BY c.end_date ASC
            """
            
            result = session.run(query, cutoff_date=cutoff_date.strftime('%Y-%m-%d'))
            
            contracts = []
            for record in result:
                end_date = record['end_date']
                days_until_expiry = (end_date - datetime.now().date()).days
                
                contracts.append({
                    'contract_id': record['contract_id'],
                    'name': record['name'],
                    'supplier': record['supplier'],
                    'end_date': str(end_date),
                    'days_until_expiry': days_until_expiry,
                    'value': float(record['value']),
                    'auto_renew': record['auto_renew'],
                    'urgency': self._calculate_urgency(days_until_expiry, record['auto_renew']),
                    'clauses': record['clauses']
                })
            
            logger.info(f"Found {len(contracts)} expiring contracts")
            return contracts
    
    def _calculate_urgency(self, days_until: int, auto_renew: bool) -> str:
        """Calculate urgency level"""
        if auto_renew:
            if days_until <= 30:
                return 'medium'
            return 'low'
        else:
            if days_until <= 14:
                return 'critical'
            elif days_until <= 30:
                return 'high'
            elif days_until <= 60:
                return 'medium'
            return 'low'
    
    def extract_clauses(self, contract_id: str) -> Dict[str, Any]:
        """
        Extract and categorize contract clauses
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            Categorized clauses
        """
        with self.neo4j_driver.session() as session:
            query = """
            MATCH (c:Contract {id: $contract_id})
            RETURN c.name as name, c.clauses as clauses, c.value as value
            """
            
            result = session.run(query, contract_id=contract_id)
            record = result.single()
            
            if not record:
                return {'error': 'Contract not found'}
            
            clauses = record['clauses'] or []
            
            categorized = {
                'payment_terms': [],
                'auto_renewal': [],
                'price_indexation': [],
                'sla': [],
                'penalties': [],
                'other': []
            }
            
            # Categorize clauses
            for clause in clauses:
                clause_lower = clause.lower()
                if 'payment' in clause_lower or 'net' in clause_lower:
                    categorized['payment_terms'].append(clause)
                elif 'auto-renew' in clause_lower or 'renewal' in clause_lower:
                    categorized['auto_renewal'].append(clause)
                elif 'indexation' in clause_lower or 'price' in clause_lower or '%' in clause:
                    categorized['price_indexation'].append(clause)
                elif 'sla' in clause_lower or 'service level' in clause_lower:
                    categorized['sla'].append(clause)
                elif 'penalty' in clause_lower or 'fine' in clause_lower:
                    categorized['penalties'].append(clause)
                else:
                    categorized['other'].append(clause)
            
            return {
                'contract_id': contract_id,
                'contract_name': record['name'],
                'contract_value': float(record['value']),
                'clauses': categorized,
                'risks': self._identify_clause_risks(categorized)
            }
    
    def _identify_clause_risks(self, categorized_clauses: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Identify potential risks in clauses"""
        risks = []
        
        if categorized_clauses['auto_renewal']:
            risks.append({
                'type': 'auto_renewal',
                'severity': 'medium',
                'description': 'Contract has auto-renewal clause - requires proactive cancellation',
                'recommendation': 'Review 90 days before expiry'
            })
        
        if categorized_clauses['price_indexation']:
            risks.append({
                'type': 'price_increase',
                'severity': 'low',
                'description': 'Contract includes price indexation',
                'recommendation': 'Factor into next year budget planning'
            })
        
        if not categorized_clauses['sla']:
            risks.append({
                'type': 'no_sla',
                'severity': 'medium',
                'description': 'No SLA clause identified',
                'recommendation': 'Consider adding SLA in next negotiation'
            })
        
        return risks
    
    def score_supplier_performance(self, supplier_id: str) -> Dict[str, Any]:
        """
        Score supplier performance based on invoice/payment history
        
        Args:
            supplier_id: Supplier identifier
            
        Returns:
            Performance score and metrics
        """
        with self.neo4j_driver.session() as session:
            query = """
            MATCH (s:Supplier {id: $supplier_id})-[:HAS_CONTRACT]->(c:Contract)
                  -[:GENERATED_INVOICE]->(i:Invoice)
            RETURN count(i) as total_invoices,
                   sum(CASE WHEN i.days_late > 0 THEN 1 ELSE 0 END) as late_invoices,
                   avg(i.days_late) as avg_days_late,
                   sum(i.amount) as total_value
            """
            
            result = session.run(query, supplier_id=supplier_id)
            record = result.single()
            
            if not record or record['total_invoices'] == 0:
                return {'error': 'No invoice history found'}
            
            total = record['total_invoices']
            late = record['late_invoices'] or 0
            on_time_percent = ((total - late) / total) * 100
            
            # Calculate performance score (0-100)
            score = on_time_percent * 0.7  # 70% weight on on-time delivery
            score += min(30, 30 * (1 - (record['avg_days_late'] or 0) / 30))  # 30% weight on lateness
            
            if score >= 90:
                rating = 'excellent'
            elif score >= 75:
                rating = 'good'
            elif score >= 60:
                rating = 'fair'
            else:
                rating = 'poor'
            
            return {
                'supplier_id': supplier_id,
                'performance_score': round(score, 1),
                'rating': rating,
                'total_invoices': total,
                'on_time_invoices': total - late,
                'late_invoices': late,
                'on_time_percent': round(on_time_percent, 1),
                'avg_days_late': round(record['avg_days_late'] or 0, 1),
                'total_contract_value': float(record['total_value'] or 0)
            }
