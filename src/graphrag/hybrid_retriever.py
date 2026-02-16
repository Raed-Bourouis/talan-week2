"""
Hybrid Retriever
Combine vector search and graph traversal for comprehensive retrieval
"""

from typing import Dict, Any, List, Optional
import logging
from qdrant_client import QdrantClient
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combine vector and graph search for financial queries"""
    
    def __init__(self, qdrant_client: QdrantClient, neo4j_driver, embedding_function):
        self.qdrant_client = qdrant_client
        self.neo4j_driver = neo4j_driver
        self.embedding_function = embedding_function
    
    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Hybrid retrieval combining vector and graph search
        
        Args:
            query: Natural language query
            top_k: Number of results to retrieve
            
        Returns:
            Combined results from vector and graph search
        """
        logger.info(f"Hybrid retrieval for query: {query[:100]}")
        
        # Vector search
        vector_results = self._vector_search(query, top_k)
        
        # Graph search
        graph_results = self._graph_search(query, top_k)
        
        # Combine and rank results
        combined_results = self._merge_results(vector_results, graph_results)
        
        return {
            'query': query,
            'vector_results': vector_results,
            'graph_results': graph_results,
            'combined_results': combined_results
        }
    
    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic vector search"""
        try:
            # Create query embedding
            query_vector = self.embedding_function(query)
            
            # Search in financial documents collection
            search_results = self.qdrant_client.search(
                collection_name='financial_documents',
                query_vector=query_vector,
                limit=top_k
            )
            
            results = []
            for hit in search_results:
                results.append({
                    'id': hit.id,
                    'score': hit.score,
                    'payload': hit.payload,
                    'source': 'vector'
                })
            
            logger.info(f"Vector search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def _graph_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform graph traversal search"""
        try:
            # Extract entities from query
            query_entities = self._extract_query_entities(query)
            
            with self.neo4j_driver.session() as session:
                # Search for relevant nodes and relationships
                if 'budget' in query.lower():
                    results = self._graph_search_budgets(session, query_entities)
                elif 'contract' in query.lower():
                    results = self._graph_search_contracts(session, query_entities)
                elif 'invoice' in query.lower() or 'payment' in query.lower():
                    results = self._graph_search_invoices(session, query_entities)
                else:
                    results = self._graph_search_general(session, query_entities)
                
                return results[:top_k]
                
        except Exception as e:
            logger.error(f"Graph search error: {e}")
            return []
    
    def _extract_query_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query text"""
        entities = {
            'departments': [],
            'suppliers': [],
            'amounts': [],
            'time_periods': []
        }
        
        # Simple keyword matching (could be enhanced with NER)
        query_lower = query.lower()
        
        if 'marketing' in query_lower:
            entities['departments'].append('Marketing')
        if 'r&d' in query_lower or 'research' in query_lower:
            entities['departments'].append('R&D')
        
        return entities
    
    def _graph_search_budgets(self, session, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search budget-related graph data"""
        query = """
        MATCH (d:Department)-[:HAS_BUDGET]->(b:Budget)
        WHERE b.year = 2024
        RETURN d.name as department, b.id as budget_id, b.variance_percent as variance,
               b.status as status, b.allocated_amount as allocated, b.spent_amount as spent
        ORDER BY b.variance_percent ASC
        LIMIT 10
        """
        
        result = session.run(query)
        return [
            {
                'department': record['department'],
                'budget_id': record['budget_id'],
                'variance': float(record['variance']),
                'status': record['status'],
                'allocated': float(record['allocated']),
                'spent': float(record['spent']),
                'source': 'graph'
            }
            for record in result
        ]
    
    def _graph_search_contracts(self, session, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search contract-related graph data"""
        query = """
        MATCH (s:Supplier)-[:HAS_CONTRACT]->(c:Contract)
        RETURN s.name as supplier, c.id as contract_id, c.name as contract_name,
               c.status as status, c.end_date as end_date, c.value as value
        ORDER BY c.end_date ASC
        LIMIT 10
        """
        
        result = session.run(query)
        return [
            {
                'supplier': record['supplier'],
                'contract_id': record['contract_id'],
                'contract_name': record['contract_name'],
                'status': record['status'],
                'end_date': str(record['end_date']),
                'value': float(record['value']),
                'source': 'graph'
            }
            for record in result
        ]
    
    def _graph_search_invoices(self, session, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search invoice/payment-related graph data"""
        query = """
        MATCH (c:Contract)-[:GENERATED_INVOICE]->(i:Invoice)
        OPTIONAL MATCH (i)-[:HAS_PAYMENT]->(p:Payment)
        RETURN i.id as invoice_id, i.invoice_number as number, i.amount as amount,
               i.status as status, i.days_late as days_late, p.date as payment_date
        ORDER BY i.days_late DESC NULLS LAST
        LIMIT 10
        """
        
        result = session.run(query)
        return [
            {
                'invoice_id': record['invoice_id'],
                'invoice_number': record['number'],
                'amount': float(record['amount']),
                'status': record['status'],
                'days_late': record['days_late'] or 0,
                'payment_date': str(record['payment_date']) if record['payment_date'] else None,
                'source': 'graph'
            }
            for record in result
        ]
    
    def _graph_search_general(self, session, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """General graph search"""
        query = """
        MATCH (n)
        WHERE n:Budget OR n:Contract OR n:Invoice
        RETURN labels(n)[0] as type, n.id as id, n.status as status
        LIMIT 10
        """
        
        result = session.run(query)
        return [
            {
                'type': record['type'],
                'id': record['id'],
                'status': record['status'],
                'source': 'graph'
            }
            for record in result
        ]
    
    def _merge_results(self, vector_results: List[Dict], graph_results: List[Dict]) -> List[Dict[str, Any]]:
        """Merge and rank results from both sources"""
        all_results = []
        
        # Add vector results with adjusted scores
        for vr in vector_results:
            vr['combined_score'] = vr['score'] * 0.6  # Weight vector results
            all_results.append(vr)
        
        # Add graph results with scores
        for gr in graph_results:
            gr['combined_score'] = 0.8  # Fixed score for graph results
            all_results.append(gr)
        
        # Sort by combined score
        all_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return all_results
