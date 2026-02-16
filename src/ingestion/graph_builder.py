"""
Graph Builder
Build Neo4j graph relationships from financial data
"""

from typing import Dict, Any, List, Optional
import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Build financial entity graphs in Neo4j"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def build_invoice_chain(self, invoice_data: Dict[str, Any]) -> bool:
        """
        Build invoice -> contract -> supplier chain
        
        Args:
            invoice_data: Invoice information
            
        Returns:
            Success status
        """
        with self.driver.session() as session:
            try:
                # Create or update invoice node
                session.execute_write(self._create_invoice, invoice_data)
                
                # Link to contract if exists
                if invoice_data.get('contract_id'):
                    session.execute_write(self._link_invoice_to_contract, 
                                        invoice_data['id'], 
                                        invoice_data['contract_id'])
                
                # Link to supplier
                if invoice_data.get('supplier_id'):
                    session.execute_write(self._link_invoice_to_supplier,
                                        invoice_data['id'],
                                        invoice_data['supplier_id'])
                
                logger.info(f"Built invoice chain for: {invoice_data['id']}")
                return True
            except Exception as e:
                logger.error(f"Error building invoice chain: {e}")
                return False
    
    def add_episodic_pattern(self, pattern_data: Dict[str, Any]) -> bool:
        """
        Add episodic memory pattern to graph
        
        Args:
            pattern_data: Pattern information
            
        Returns:
            Success status
        """
        with self.driver.session() as session:
            try:
                session.execute_write(self._create_pattern, pattern_data)
                
                # Link pattern to entity
                if pattern_data.get('entity_id') and pattern_data.get('entity_type'):
                    session.execute_write(self._link_pattern_to_entity,
                                        pattern_data['id'],
                                        pattern_data['entity_id'],
                                        pattern_data['entity_type'])
                
                logger.info(f"Added episodic pattern: {pattern_data['id']}")
                return True
            except Exception as e:
                logger.error(f"Error adding pattern: {e}")
                return False
    
    @staticmethod
    def _create_invoice(tx, invoice_data: Dict[str, Any]):
        """Create invoice node"""
        query = """
        MERGE (i:Invoice {id: $id})
        SET i.invoice_number = $invoice_number,
            i.amount = $amount,
            i.status = $status,
            i.issue_date = date($issue_date),
            i.due_date = date($due_date),
            i.updated_at = datetime()
        RETURN i
        """
        tx.run(query, **invoice_data)
    
    @staticmethod
    def _link_invoice_to_contract(tx, invoice_id: str, contract_id: str):
        """Link invoice to contract"""
        query = """
        MATCH (i:Invoice {id: $invoice_id})
        MATCH (c:Contract {id: $contract_id})
        MERGE (c)-[:GENERATED_INVOICE]->(i)
        """
        tx.run(query, invoice_id=invoice_id, contract_id=contract_id)
    
    @staticmethod
    def _link_invoice_to_supplier(tx, invoice_id: str, supplier_id: str):
        """Link invoice to supplier"""
        query = """
        MATCH (i:Invoice {id: $invoice_id})
        MATCH (s:Supplier {id: $supplier_id})
        MERGE (s)-[:ISSUED_INVOICE]->(i)
        """
        tx.run(query, invoice_id=invoice_id, supplier_id=supplier_id)
    
    @staticmethod
    def _create_pattern(tx, pattern_data: Dict[str, Any]):
        """Create episodic pattern node"""
        query = """
        MERGE (p:Pattern {id: $id})
        SET p.type = $type,
            p.description = $description,
            p.confidence = $confidence,
            p.occurrences = $occurrences,
            p.last_observed = datetime($last_observed)
        RETURN p
        """
        tx.run(query, **pattern_data)
    
    @staticmethod
    def _link_pattern_to_entity(tx, pattern_id: str, entity_id: str, entity_type: str):
        """Link pattern to entity"""
        query = f"""
        MATCH (p:Pattern {{id: $pattern_id}})
        MATCH (e:{entity_type} {{id: $entity_id}})
        MERGE (e)-[:HAS_PATTERN]->(p)
        """
        tx.run(query, pattern_id=pattern_id, entity_id=entity_id)
    
    def query_payment_chain(self, invoice_id: str) -> List[Dict[str, Any]]:
        """Query full payment chain for an invoice"""
        with self.driver.session() as session:
            query = """
            MATCH path = (s:Supplier)-[:HAS_CONTRACT]->(c:Contract)
                        -[:GENERATED_INVOICE]->(i:Invoice {id: $invoice_id})
                        -[:HAS_PAYMENT]->(p:Payment)
            RETURN s, c, i, p
            """
            result = session.run(query, invoice_id=invoice_id)
            return [record.data() for record in result]
