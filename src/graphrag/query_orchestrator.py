"""
Query Orchestrator - Routes and optimizes queries across the system
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging
from .hybrid_retriever import HybridRetriever
from .episodic_memory import EpisodicMemory
from .local_llm import get_llm
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries the system can handle."""
    BUDGET = "budget"
    CONTRACT = "contract"
    CASH_FLOW = "cash_flow"
    SUPPLIER = "supplier"
    INVOICE = "invoice"
    PATTERN = "pattern"
    GENERAL = "general"


class QueryOrchestrator:
    """
    Routes queries to appropriate subsystems and combines results.
    """
    
    def __init__(self):
        """Initialize orchestrator with all subsystems."""
        self.retriever = HybridRetriever()
        self.memory = EpisodicMemory()
        self.llm = get_llm()
        self.context_builder = ContextBuilder(
            retriever=self.retriever,
            memory=self.memory
        )
        
        logger.info("QueryOrchestrator initialized")
    
    def classify_query(self, query: str) -> QueryType:
        """
        Classify query type based on keywords.
        
        Args:
            query: User query
            
        Returns:
            Detected query type
        """
        query_lower = query.lower()
        
        # Budget keywords
        if any(word in query_lower for word in ["budget", "spending", "allocated", "variance", "overrun", "under budget"]):
            return QueryType.BUDGET
        
        # Contract keywords
        elif any(word in query_lower for word in ["contract", "agreement", "expir", "renew", "clause"]):
            return QueryType.CONTRACT
        
        # Cash flow keywords
        elif any(word in query_lower for word in ["cash flow", "forecast", "predict", "treasury", "liquidity"]):
            return QueryType.CASH_FLOW
        
        # Supplier keywords
        elif any(word in query_lower for word in ["supplier", "vendor", "provider"]):
            return QueryType.SUPPLIER
        
        # Invoice keywords
        elif any(word in query_lower for word in ["invoice", "payment", "paid", "overdue", "due"]):
            return QueryType.INVOICE
        
        # Pattern keywords
        elif any(word in query_lower for word in ["pattern", "trend", "recurring", "always", "usually", "history"]):
            return QueryType.PATTERN
        
        # Default to general
        else:
            return QueryType.GENERAL
    
    def route_query(
        self,
        query: str,
        query_type: Optional[QueryType] = None
    ) -> Dict[str, Any]:
        """
        Route query to appropriate handler and return results.
        
        Args:
            query: User query
            query_type: Optional pre-determined query type
            
        Returns:
            Query results and metadata
        """
        # Classify if not provided
        if query_type is None:
            query_type = self.classify_query(query)
        
        logger.info(f"Routing query as type: {query_type.value}")
        
        # Route based on type
        if query_type == QueryType.BUDGET:
            return self._handle_budget_query(query)
        elif query_type == QueryType.CONTRACT:
            return self._handle_contract_query(query)
        elif query_type == QueryType.CASH_FLOW:
            return self._handle_cashflow_query(query)
        elif query_type == QueryType.SUPPLIER:
            return self._handle_supplier_query(query)
        elif query_type == QueryType.INVOICE:
            return self._handle_invoice_query(query)
        elif query_type == QueryType.PATTERN:
            return self._handle_pattern_query(query)
        else:
            return self._handle_general_query(query)
    
    def _handle_budget_query(self, query: str) -> Dict[str, Any]:
        """Handle budget-related queries."""
        # Get budget data from graph
        graph_results = self.retriever.graph_search(
            entity_type="Department",
            depth=2
        )
        
        # Build context
        context = self.context_builder.build_budget_context(graph_results)
        
        # Generate answer with LLM
        answer = self.llm.answer_financial_query(query, context)
        
        return {
            "query": query,
            "query_type": QueryType.BUDGET.value,
            "answer": answer,
            "context": context,
            "sources": graph_results[:3]  # Top 3 sources
        }
    
    def _handle_contract_query(self, query: str) -> Dict[str, Any]:
        """Handle contract-related queries."""
        # Vector search for relevant contracts
        vector_results = self.retriever.vector_search(
            query,
            collection_name="contract_clauses",
            limit=5
        )
        
        # Graph search for contract relationships
        graph_results = self.retriever.graph_search(
            entity_type="Contract",
            depth=2
        )
        
        # Build context
        context = self.context_builder.build_contract_context(
            vector_results,
            graph_results
        )
        
        # Generate answer
        answer = self.llm.answer_financial_query(query, context)
        
        return {
            "query": query,
            "query_type": QueryType.CONTRACT.value,
            "answer": answer,
            "context": context,
            "sources": {
                "vector": vector_results[:3],
                "graph": graph_results[:3]
            }
        }
    
    def _handle_cashflow_query(self, query: str) -> Dict[str, Any]:
        """Handle cash flow queries."""
        # Get invoice and payment data
        graph_results = self.retriever.graph_search(
            entity_type="Invoice",
            depth=2
        )
        
        # Build context
        context = self.context_builder.build_cashflow_context(graph_results)
        
        # Generate answer
        answer = self.llm.answer_financial_query(query, context)
        
        return {
            "query": query,
            "query_type": QueryType.CASH_FLOW.value,
            "answer": answer,
            "context": context,
            "sources": graph_results[:5]
        }
    
    def _handle_supplier_query(self, query: str) -> Dict[str, Any]:
        """Handle supplier-related queries."""
        # Get supplier data
        graph_results = self.retriever.graph_search(
            entity_type="Supplier",
            depth=2
        )
        
        # Check for patterns
        patterns = self.memory.detect_late_payment_patterns()
        
        # Build context
        context = self.context_builder.build_supplier_context(
            graph_results,
            patterns
        )
        
        # Generate answer
        answer = self.llm.answer_financial_query(query, context)
        
        return {
            "query": query,
            "query_type": QueryType.SUPPLIER.value,
            "answer": answer,
            "context": context,
            "patterns": patterns,
            "sources": graph_results[:3]
        }
    
    def _handle_invoice_query(self, query: str) -> Dict[str, Any]:
        """Handle invoice-related queries."""
        # Get invoice data
        graph_results = self.retriever.graph_search(
            entity_type="Invoice",
            depth=1
        )
        
        # Build context
        context = self.context_builder.build_invoice_context(graph_results)
        
        # Generate answer
        answer = self.llm.answer_financial_query(query, context)
        
        return {
            "query": query,
            "query_type": QueryType.INVOICE.value,
            "answer": answer,
            "context": context,
            "sources": graph_results[:5]
        }
    
    def _handle_pattern_query(self, query: str) -> Dict[str, Any]:
        """Handle pattern detection queries."""
        # Detect all patterns
        all_patterns = self.memory.detect_all_patterns()
        
        # Build context from patterns
        context = self.context_builder.build_pattern_context(all_patterns)
        
        # Generate answer
        answer = self.llm.answer_financial_query(query, context)
        
        return {
            "query": query,
            "query_type": QueryType.PATTERN.value,
            "answer": answer,
            "patterns": all_patterns,
            "context": context
        }
    
    def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries with hybrid search."""
        # Hybrid search
        hybrid_results = self.retriever.hybrid_search(query, limit=10)
        
        # Build general context
        context = self.context_builder.build_general_context(hybrid_results)
        
        # Generate answer
        answer = self.llm.answer_financial_query(query, context)
        
        return {
            "query": query,
            "query_type": QueryType.GENERAL.value,
            "answer": answer,
            "context": context,
            "sources": hybrid_results
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point for query processing.
        
        Args:
            query: User's natural language query
            
        Returns:
            Complete query response
        """
        logger.info(f"Processing query: {query}")
        
        try:
            # Route and process
            result = self.route_query(query)
            
            # Add metadata
            result["success"] = True
            result["timestamp"] = __import__('datetime').datetime.now().isoformat()
            
            logger.info(f"Query processed successfully: {result['query_type']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def close(self):
        """Close all connections."""
        self.retriever.close()
        self.memory.close()
        logger.info("QueryOrchestrator closed")
