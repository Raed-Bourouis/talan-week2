"""
Query Orchestrator
Route and optimize queries across different search strategies
"""

from typing import Dict, Any, List, Optional
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of financial queries"""
    BUDGET = "budget"
    CONTRACT = "contract"
    INVOICE = "invoice"
    PAYMENT = "payment"
    ANALYSIS = "analysis"
    SIMULATION = "simulation"
    GENERAL = "general"


class QueryOrchestrator:
    """Orchestrate query routing and execution"""
    
    def __init__(self, hybrid_retriever, episodic_memory, llm_client=None):
        self.hybrid_retriever = hybrid_retriever
        self.episodic_memory = episodic_memory
        self.llm_client = llm_client
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language query
        
        Args:
            query: Natural language query
            context: Optional context information
            
        Returns:
            Query results with answer
        """
        logger.info(f"Processing query: {query[:100]}")
        
        # Classify query type
        query_type = self._classify_query(query)
        
        # Retrieve relevant data
        retrieval_results = self.hybrid_retriever.retrieve(query, top_k=5)
        
        # Get relevant historical patterns
        patterns = self.episodic_memory.retrieve_relevant_patterns(query, top_k=3)
        
        # Build response
        response = {
            'query': query,
            'query_type': query_type.value,
            'results': retrieval_results,
            'patterns': patterns,
            'answer': self._generate_answer(query, retrieval_results, patterns)
        }
        
        return response
    
    def _classify_query(self, query: str) -> QueryType:
        """Classify the type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['budget', 'variance', 'allocated', 'spent']):
            return QueryType.BUDGET
        elif any(word in query_lower for word in ['contract', 'supplier', 'vendor']):
            return QueryType.CONTRACT
        elif any(word in query_lower for word in ['invoice', 'bill']):
            return QueryType.INVOICE
        elif any(word in query_lower for word in ['payment', 'paid', 'late']):
            return QueryType.PAYMENT
        elif any(word in query_lower for word in ['simulate', 'forecast', 'predict']):
            return QueryType.SIMULATION
        elif any(word in query_lower for word in ['analyze', 'analysis', 'why', 'how']):
            return QueryType.ANALYSIS
        else:
            return QueryType.GENERAL
    
    def _generate_answer(self, query: str, retrieval_results: Dict[str, Any], 
                        patterns: List[Dict[str, Any]]) -> str:
        """Generate natural language answer"""
        
        # Extract key information
        graph_results = retrieval_results.get('graph_results', [])
        
        if not graph_results:
            return "No relevant financial data found for your query."
        
        # Build answer based on results
        answer_parts = []
        
        # Summarize graph results
        if graph_results:
            first_result = graph_results[0]
            
            if 'department' in first_result:
                answer_parts.append(f"Found budget information for {first_result['department']} department.")
                if 'variance' in first_result:
                    variance_pct = first_result['variance'] * 100
                    if variance_pct < 0:
                        answer_parts.append(f"They are {abs(variance_pct):.1f}% over budget.")
                    else:
                        answer_parts.append(f"They are {variance_pct:.1f}% under budget.")
            
            elif 'contract_id' in first_result:
                answer_parts.append(f"Found contract: {first_result.get('contract_name', first_result['contract_id'])}.")
                answer_parts.append(f"Status: {first_result.get('status', 'unknown')}")
            
            elif 'invoice_id' in first_result:
                answer_parts.append(f"Found invoice: {first_result.get('invoice_number', first_result['invoice_id'])}.")
                if first_result.get('days_late', 0) > 0:
                    answer_parts.append(f"Payment was {first_result['days_late']} days late.")
        
        # Add pattern insights
        if patterns:
            answer_parts.append("\n\nHistorical insights:")
            for pattern in patterns[:2]:
                answer_parts.append(f"- {pattern['description']}")
        
        return " ".join(answer_parts)
