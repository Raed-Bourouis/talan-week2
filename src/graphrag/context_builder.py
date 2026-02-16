"""
Context Builder
Build rich context from multiple sources
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build comprehensive context for LLM queries"""
    
    def __init__(self, hybrid_retriever, episodic_memory):
        self.hybrid_retriever = hybrid_retriever
        self.episodic_memory = episodic_memory
    
    def build_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        Build context for LLM from retrieved data
        
        Args:
            query: User query
            max_tokens: Maximum context length
            
        Returns:
            Formatted context string
        """
        # Retrieve relevant data
        retrieval_results = self.hybrid_retriever.retrieve(query, top_k=5)
        patterns = self.episodic_memory.retrieve_relevant_patterns(query, top_k=2)
        
        # Build context sections
        context_parts = []
        
        # Add vector search results
        vector_results = retrieval_results.get('vector_results', [])
        if vector_results:
            context_parts.append("=== Relevant Documents ===")
            for result in vector_results[:3]:
                payload = result.get('payload', {})
                context_parts.append(f"Document: {payload.get('file_name', 'Unknown')}")
                context_parts.append(f"Type: {payload.get('document_type', 'Unknown')}")
                if 'text_content' in payload:
                    context_parts.append(f"Content: {payload['text_content'][:200]}...")
                context_parts.append("")
        
        # Add graph search results
        graph_results = retrieval_results.get('graph_results', [])
        if graph_results:
            context_parts.append("=== Financial Data ===")
            for result in graph_results[:5]:
                if 'department' in result:
                    context_parts.append(
                        f"Budget - {result['department']}: "
                        f"Allocated ${result.get('allocated', 0):,.0f}, "
                        f"Spent ${result.get('spent', 0):,.0f}, "
                        f"Variance {result.get('variance', 0)*100:.1f}%"
                    )
                elif 'contract_name' in result:
                    context_parts.append(
                        f"Contract - {result['contract_name']}: "
                        f"Supplier {result.get('supplier', 'Unknown')}, "
                        f"Value ${result.get('value', 0):,.0f}, "
                        f"Status {result.get('status', 'Unknown')}"
                    )
                elif 'invoice_number' in result:
                    context_parts.append(
                        f"Invoice - {result['invoice_number']}: "
                        f"Amount ${result.get('amount', 0):,.0f}, "
                        f"Status {result.get('status', 'Unknown')}, "
                        f"Days Late {result.get('days_late', 0)}"
                    )
            context_parts.append("")
        
        # Add historical patterns
        if patterns:
            context_parts.append("=== Historical Patterns ===")
            for pattern in patterns:
                context_parts.append(
                    f"- {pattern['description']} "
                    f"(Confidence: {pattern.get('confidence', 0):.0%})"
                )
            context_parts.append("")
        
        # Combine and truncate if needed
        full_context = "\n".join(context_parts)
        
        # Simple token estimation (4 chars per token)
        max_chars = max_tokens * 4
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars] + "..."
        
        return full_context
    
    def build_prompt(self, query: str, context: str) -> str:
        """Build complete prompt for LLM"""
        prompt = f"""You are a financial intelligence assistant. Answer the following query based on the provided context.

Context:
{context}

Query: {query}

Provide a clear, concise answer based on the financial data and patterns shown above. If the data suggests recommendations, include them."""
        
        return prompt
