"""
Anomaly Detector
Detect unusual patterns in financial data
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect anomalies in financial transactions"""
    
    def __init__(self, db_connection, neo4j_driver):
        self.db = db_connection
        self.neo4j_driver = neo4j_driver
    
    def detect_invoice_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in invoices"""
        anomalies = []
        
        # Check for duplicate invoices
        duplicates = self._detect_duplicate_invoices()
        anomalies.extend(duplicates)
        
        # Check for unusual amounts
        unusual_amounts = self._detect_unusual_amounts()
        anomalies.extend(unusual_amounts)
        
        # Check for suspicious patterns
        suspicious_patterns = self._detect_suspicious_patterns()
        anomalies.extend(suspicious_patterns)
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies
    
    def _detect_duplicate_invoices(self) -> List[Dict[str, Any]]:
        """Detect potential duplicate invoices"""
        with self.neo4j_driver.session() as session:
            query = """
            MATCH (i1:Invoice), (i2:Invoice)
            WHERE i1.id < i2.id
            AND i1.supplier_id = i2.supplier_id
            AND i1.amount = i2.amount
            AND abs(duration.between(i1.issue_date, i2.issue_date).days) <= 7
            RETURN i1.id as invoice1, i2.id as invoice2, i1.amount as amount,
                   i1.supplier_id as supplier_id
            LIMIT 10
            """
            
            result = session.run(query)
            
            anomalies = []
            for record in result:
                anomalies.append({
                    'type': 'duplicate_invoice',
                    'severity': 'high',
                    'description': f"Potential duplicate invoices: {record['invoice1']} and {record['invoice2']}",
                    'invoice_ids': [record['invoice1'], record['invoice2']],
                    'amount': float(record['amount']),
                    'supplier_id': record['supplier_id'],
                    'detected_at': datetime.now().isoformat()
                })
            
            return anomalies
    
    def _detect_unusual_amounts(self) -> List[Dict[str, Any]]:
        """Detect invoices with unusual amounts"""
        with self.neo4j_driver.session() as session:
            # Get statistical baseline
            query = """
            MATCH (i:Invoice)
            RETURN avg(i.amount) as avg_amount, stdev(i.amount) as std_amount
            """
            
            result = session.run(query)
            record = result.single()
            
            if not record:
                return []
            
            avg_amount = record['avg_amount']
            std_amount = record['std_amount']
            
            if not std_amount:
                return []
            
            # Find outliers (more than 3 standard deviations)
            threshold = avg_amount + (3 * std_amount)
            
            query = """
            MATCH (s:Supplier)-[:ISSUED_INVOICE]->(i:Invoice)
            WHERE i.amount > $threshold
            RETURN i.id as invoice_id, i.amount as amount, s.name as supplier,
                   i.invoice_number as invoice_number
            LIMIT 10
            """
            
            result = session.run(query, threshold=threshold)
            
            anomalies = []
            for record in result:
                anomalies.append({
                    'type': 'unusual_amount',
                    'severity': 'medium',
                    'description': f"Invoice {record['invoice_number']} has unusually high amount",
                    'invoice_id': record['invoice_id'],
                    'amount': float(record['amount']),
                    'supplier': record['supplier'],
                    'threshold': float(threshold),
                    'detected_at': datetime.now().isoformat()
                })
            
            return anomalies
    
    def _detect_suspicious_patterns(self) -> List[Dict[str, Any]]:
        """Detect suspicious payment patterns"""
        with self.neo4j_driver.session() as session:
            # Check for invoices paid before issue date (suspicious)
            query = """
            MATCH (i:Invoice)-[:HAS_PAYMENT]->(p:Payment)
            WHERE p.date < i.issue_date
            RETURN i.id as invoice_id, i.invoice_number as invoice_number,
                   i.issue_date as issue_date, p.date as payment_date
            LIMIT 10
            """
            
            result = session.run(query)
            
            anomalies = []
            for record in result:
                anomalies.append({
                    'type': 'suspicious_pattern',
                    'severity': 'high',
                    'description': f"Invoice {record['invoice_number']} paid before issue date",
                    'invoice_id': record['invoice_id'],
                    'issue_date': str(record['issue_date']),
                    'payment_date': str(record['payment_date']),
                    'detected_at': datetime.now().isoformat()
                })
            
            return anomalies
    
    def analyze_vendor_risk(self, supplier_id: str) -> Dict[str, Any]:
        """
        Analyze risk factors for a specific vendor
        
        Args:
            supplier_id: Supplier identifier
            
        Returns:
            Risk analysis
        """
        with self.neo4j_driver.session() as session:
            # Get supplier information
            query = """
            MATCH (s:Supplier {id: $supplier_id})
            OPTIONAL MATCH (s)-[:HAS_CONTRACT]->(c:Contract)-[:GENERATED_INVOICE]->(i:Invoice)
            RETURN s.name as name, s.risk_score as base_risk_score,
                   count(DISTINCT c) as num_contracts,
                   count(i) as num_invoices,
                   sum(i.amount) as total_value,
                   sum(CASE WHEN i.days_late > 0 THEN 1 ELSE 0 END) as late_invoices
            """
            
            result = session.run(query, supplier_id=supplier_id)
            record = result.single()
            
            if not record:
                return {'error': 'Supplier not found'}
            
            # Calculate risk factors
            late_payment_rate = (record['late_invoices'] / record['num_invoices'] * 100) if record['num_invoices'] > 0 else 0
            
            risk_factors = []
            risk_score = record['base_risk_score'] or 0.5
            
            if late_payment_rate > 20:
                risk_factors.append('High late payment rate')
                risk_score += 0.2
            
            if record['num_contracts'] > 5:
                risk_factors.append('High dependency - multiple contracts')
                risk_score += 0.1
            
            if record['total_value'] and record['total_value'] > 1000000:
                risk_factors.append('High value concentration')
                risk_score += 0.15
            
            risk_score = min(risk_score, 1.0)  # Cap at 1.0
            
            if risk_score < 0.3:
                risk_level = 'low'
            elif risk_score < 0.6:
                risk_level = 'medium'
            else:
                risk_level = 'high'
            
            return {
                'supplier_id': supplier_id,
                'supplier_name': record['name'],
                'risk_score': round(risk_score, 2),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'metrics': {
                    'num_contracts': record['num_contracts'],
                    'num_invoices': record['num_invoices'],
                    'total_value': float(record['total_value'] or 0),
                    'late_payment_rate': round(late_payment_rate, 1)
                }
            }
