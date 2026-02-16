"""
Context Builder - Builds rich context from multiple data sources
"""

from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds contextual information from multiple sources for LLM consumption.
    """
    
    def __init__(self, retriever=None, memory=None):
        """
        Initialize context builder.
        
        Args:
            retriever: HybridRetriever instance
            memory: EpisodicMemory instance
        """
        self.retriever = retriever
        self.memory = memory
        logger.info("ContextBuilder initialized")
    
    def build_budget_context(self, graph_results: List[Dict[str, Any]]) -> str:
        """
        Build context for budget queries.
        
        Args:
            graph_results: Results from graph search
            
        Returns:
            Formatted context string
        """
        context_parts = ["=== BUDGET INFORMATION ===\n"]
        
        for result in graph_results:
            if result.get("type") == "node" and "Department" in result.get("labels", []):
                props = result.get("properties", {})
                context_parts.append(f"\nDepartment: {props.get('name', 'Unknown')}")
                context_parts.append(f"  Budget Allocated: ${props.get('budget_allocated', 0):,.2f}")
                context_parts.append(f"  Budget Spent: ${props.get('budget_spent', 0):,.2f}")
                
                if props.get('budget_allocated', 0) > 0:
                    remaining = props['budget_allocated'] - props.get('budget_spent', 0)
                    variance_pct = (props.get('budget_spent', 0) - props['budget_allocated']) / props['budget_allocated'] * 100
                    context_parts.append(f"  Remaining: ${remaining:,.2f}")
                    context_parts.append(f"  Variance: {variance_pct:.1f}%")
        
        return "\n".join(context_parts)
    
    def build_contract_context(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]]
    ) -> str:
        """
        Build context for contract queries.
        
        Args:
            vector_results: Results from vector search
            graph_results: Results from graph search
            
        Returns:
            Formatted context string
        """
        context_parts = ["=== CONTRACT INFORMATION ===\n"]
        
        # Add relevant document chunks from vector search
        if vector_results:
            context_parts.append("\n--- Relevant Contract Clauses ---")
            for i, result in enumerate(vector_results[:3], 1):
                payload = result.get("payload", {})
                context_parts.append(f"\n{i}. {payload.get('content', '')[:200]}...")
                context_parts.append(f"   Relevance: {result.get('score', 0):.2f}")
        
        # Add contract entities from graph
        if graph_results:
            context_parts.append("\n\n--- Active Contracts ---")
            for result in graph_results:
                if result.get("type") == "node" and "Contract" in result.get("labels", []):
                    props = result.get("properties", {})
                    context_parts.append(f"\n- {props.get('title', 'Unknown Contract')}")
                    context_parts.append(f"  Value: ${props.get('value', 0):,.2f}")
                    context_parts.append(f"  Status: {props.get('status', 'unknown')}")
                    context_parts.append(f"  Expiration: {props.get('expiration_date', 'N/A')}")
        
        return "\n".join(context_parts)
    
    def build_cashflow_context(self, graph_results: List[Dict[str, Any]]) -> str:
        """
        Build context for cash flow queries.
        
        Args:
            graph_results: Results from graph search
            
        Returns:
            Formatted context string
        """
        context_parts = ["=== CASH FLOW INFORMATION ===\n"]
        
        invoices_pending = []
        invoices_overdue = []
        invoices_paid = []
        
        for result in graph_results:
            if result.get("type") == "node" and "Invoice" in result.get("labels", []):
                props = result.get("properties", {})
                invoice_info = {
                    "number": props.get("number", "Unknown"),
                    "amount": props.get("amount", 0),
                    "status": props.get("status", "unknown"),
                    "due_date": props.get("due_date", "N/A")
                }
                
                if props.get("status") == "overdue":
                    invoices_overdue.append(invoice_info)
                elif props.get("status") == "pending":
                    invoices_pending.append(invoice_info)
                elif props.get("status") == "paid":
                    invoices_paid.append(invoice_info)
        
        # Summarize
        if invoices_overdue:
            context_parts.append(f"\n--- OVERDUE INVOICES ({len(invoices_overdue)}) ---")
            total_overdue = sum(inv["amount"] for inv in invoices_overdue)
            context_parts.append(f"Total Overdue Amount: ${total_overdue:,.2f}")
            for inv in invoices_overdue[:5]:
                context_parts.append(f"  - {inv['number']}: ${inv['amount']:,.2f} (Due: {inv['due_date']})")
        
        if invoices_pending:
            context_parts.append(f"\n--- PENDING INVOICES ({len(invoices_pending)}) ---")
            total_pending = sum(inv["amount"] for inv in invoices_pending)
            context_parts.append(f"Total Pending Amount: ${total_pending:,.2f}")
            for inv in invoices_pending[:5]:
                context_parts.append(f"  - {inv['number']}: ${inv['amount']:,.2f} (Due: {inv['due_date']})")
        
        return "\n".join(context_parts)
    
    def build_supplier_context(
        self,
        graph_results: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]]
    ) -> str:
        """
        Build context for supplier queries.
        
        Args:
            graph_results: Results from graph search
            patterns: Detected patterns
            
        Returns:
            Formatted context string
        """
        context_parts = ["=== SUPPLIER INFORMATION ===\n"]
        
        for result in graph_results:
            if result.get("type") == "node" and "Supplier" in result.get("labels", []):
                props = result.get("properties", {})
                context_parts.append(f"\nSupplier: {props.get('name', 'Unknown')}")
                context_parts.append(f"  ID: {props.get('id', 'N/A')}")
                context_parts.append(f"  Payment Terms: {props.get('payment_terms', 'N/A')}")
                context_parts.append(f"  Reliability Score: {props.get('reliability_score', 0):.2f}")
                context_parts.append(f"  Avg Delay: {props.get('avg_delay_days', 0)} days")
        
        # Add patterns if any
        if patterns:
            context_parts.append("\n\n--- DETECTED PATTERNS ---")
            for pattern in patterns[:5]:
                context_parts.append(f"\n- {pattern.get('supplier_name', 'Unknown')}")
                context_parts.append(f"  Pattern: Late payments ({pattern.get('occurrences', 0)} occurrences)")
                context_parts.append(f"  Avg Delay: {pattern.get('avg_delay_days', 0)} days")
                context_parts.append(f"  Recommendation: {pattern.get('recommendation', 'N/A')}")
        
        return "\n".join(context_parts)
    
    def build_invoice_context(self, graph_results: List[Dict[str, Any]]) -> str:
        """
        Build context for invoice queries.
        
        Args:
            graph_results: Results from graph search
            
        Returns:
            Formatted context string
        """
        context_parts = ["=== INVOICE INFORMATION ===\n"]
        
        for result in graph_results:
            if result.get("type") == "node" and "Invoice" in result.get("labels", []):
                props = result.get("properties", {})
                context_parts.append(f"\nInvoice: {props.get('number', 'Unknown')}")
                context_parts.append(f"  Amount: ${props.get('amount', 0):,.2f}")
                context_parts.append(f"  Status: {props.get('status', 'unknown')}")
                context_parts.append(f"  Issue Date: {props.get('issue_date', 'N/A')}")
                context_parts.append(f"  Due Date: {props.get('due_date', 'N/A')}")
                if props.get('payment_date'):
                    context_parts.append(f"  Payment Date: {props.get('payment_date')}")
        
        return "\n".join(context_parts)
    
    def build_pattern_context(self, all_patterns: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Build context for pattern queries.
        
        Args:
            all_patterns: Dict of pattern types and their detections
            
        Returns:
            Formatted context string
        """
        context_parts = ["=== DETECTED FINANCIAL PATTERNS ===\n"]
        
        for pattern_type, patterns in all_patterns.items():
            if patterns:
                context_parts.append(f"\n--- {pattern_type.upper().replace('_', ' ')} PATTERNS ---")
                for pattern in patterns:
                    context_parts.append(f"\n- {pattern.get('description', pattern.get('supplier_name', 'Pattern'))}")
                    context_parts.append(f"  Confidence: {pattern.get('confidence', 0):.0%}")
                    context_parts.append(f"  Occurrences: {pattern.get('occurrences', 0)}")
                    context_parts.append(f"  Recommendation: {pattern.get('recommendation', 'N/A')}")
        
        return "\n".join(context_parts)
    
    def build_general_context(self, hybrid_results: Dict[str, Any]) -> str:
        """
        Build general context from hybrid search results.
        
        Args:
            hybrid_results: Results from hybrid search
            
        Returns:
            Formatted context string
        """
        context_parts = ["=== FINANCIAL DATA ===\n"]
        
        # Add vector search results
        vector_results = hybrid_results.get("vector_results", [])
        if vector_results:
            context_parts.append("\n--- Relevant Documents ---")
            for i, result in enumerate(vector_results[:3], 1):
                payload = result.get("payload", {})
                context_parts.append(f"\n{i}. {payload.get('content', '')[:300]}...")
                context_parts.append(f"   Relevance: {result.get('score', 0):.2f}")
        
        # Add graph search results
        graph_results = hybrid_results.get("graph_results", [])
        if graph_results:
            context_parts.append("\n\n--- Related Entities ---")
            for result in graph_results[:5]:
                if result.get("type") == "node":
                    labels = result.get("labels", [])
                    props = result.get("properties", {})
                    if labels:
                        context_parts.append(f"\n{labels[0]}: {props.get('name', props.get('title', props.get('id', 'Unknown')))}")
        
        return "\n".join(context_parts)
    
    def truncate_context(self, context: str, max_length: int = 3000) -> str:
        """
        Truncate context to fit within LLM limits.
        
        Args:
            context: Full context string
            max_length: Maximum character length
            
        Returns:
            Truncated context
        """
        if len(context) <= max_length:
            return context
        
        truncated = context[:max_length]
        truncated += "\n\n... [Context truncated for length] ..."
        logger.warning(f"Context truncated from {len(context)} to {max_length} characters")
        
        return truncated
