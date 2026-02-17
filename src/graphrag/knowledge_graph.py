"""
GraphRAG Knowledge Graph Builder
=================================
Builds and maintains the financial knowledge graph.
Provides high-level operations for entity and relationship management.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from .config import GraphRAGConfig, get_config
from .exceptions import (
    KnowledgeGraphError,
    EntityNotFoundError,
    ValidationError,
)
from .graph_store import GraphStore, create_graph_store
from .models import (
    FinancialEntity,
    Relationship,
    Client,
    Supplier,
    Contract,
    Invoice,
    BudgetEntry,
    Department,
    Project,
    Clause,
    EntityType,
    RelationshipType,
    GraphQuery,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """
    High-level knowledge graph builder for financial entities.
    Provides domain-specific operations and relationship inference.
    """
    
    def __init__(
        self,
        graph_store: Optional[GraphStore] = None,
        config: Optional[GraphRAGConfig] = None,
    ):
        self.config = config or get_config()
        self.graph_store = graph_store or create_graph_store(config=self.config)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the knowledge graph (connect to DB, create indexes)."""
        try:
            await self.graph_store.connect()
            
            # Create indexes if using Neo4j
            if hasattr(self.graph_store, 'create_indexes'):
                await self.graph_store.create_indexes()
            
            self._initialized = True
            logger.info("Knowledge graph initialized")
        
        except Exception as e:
            raise KnowledgeGraphError(f"Failed to initialize knowledge graph: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
        await self.graph_store.disconnect()
        self._initialized = False
        logger.info("Knowledge graph shutdown")
    
    # ═══════════════════════════════════════════════════════════════
    # ENTITY OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    async def add_entity(self, entity: FinancialEntity) -> str:
        """Add an entity to the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        try:
            entity_id = await self.graph_store.create_entity(entity)
            logger.info(f"Added entity {entity_id} ({entity.entity_type.value})")
            return entity_id
        
        except Exception as e:
            raise KnowledgeGraphError(f"Failed to add entity: {e}")
    
    async def get_entity(self, entity_id: UUID) -> Optional[dict[str, Any]]:
        """Retrieve an entity from the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        return await self.graph_store.get_entity(entity_id)
    
    async def update_entity(
        self,
        entity_id: UUID,
        updates: dict[str, Any]
    ) -> bool:
        """Update an entity in the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        # Add updated timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        return await self.graph_store.update_entity(entity_id, updates)
    
    async def delete_entity(self, entity_id: UUID) -> bool:
        """Delete an entity from the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        return await self.graph_store.delete_entity(entity_id)
    
    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIP OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    async def create_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: RelationshipType,
        properties: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a relationship between two entities."""
        if not self._initialized:
            await self.initialize()
        
        try:
            rel_id = await self.graph_store.create_relationship(
                source_id, target_id, relationship_type, properties
            )
            logger.info(f"Created relationship: {source_id} -[{relationship_type.value}]-> {target_id}")
            return rel_id
        
        except Exception as e:
            raise KnowledgeGraphError(f"Failed to create relationship: {e}")
    
    async def get_related_entities(
        self,
        entity_id: UUID,
        relationship_types: Optional[list[RelationshipType]] = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        """Get all entities related to the given entity."""
        if not self._initialized:
            await self.initialize()
        
        return await self.graph_store.get_relationships(
            entity_id, direction, relationship_types
        )
    
    # ═══════════════════════════════════════════════════════════════
    # DOMAIN-SPECIFIC OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    async def add_contract_with_client(
        self,
        contract: Contract,
        client: Optional[Client] = None,
    ) -> tuple[str, Optional[str]]:
        """Add a contract and optionally link it to a client."""
        if not self._initialized:
            await self.initialize()
        
        # Add client first if provided
        client_id = None
        if client:
            client_id = await self.add_entity(client)
            contract.client_id = UUID(client_id)
        
        # Add contract
        contract_id = await self.add_entity(contract)
        
        # Create relationship if client exists
        if client_id:
            await self.create_relationship(
                UUID(client_id),
                UUID(contract_id),
                RelationshipType.HAS_CONTRACT,
                {"created_at": datetime.utcnow().isoformat()}
            )
        
        return contract_id, client_id
    
    async def add_invoice_for_contract(
        self,
        invoice: Invoice,
        contract_id: UUID,
    ) -> str:
        """Add an invoice and link it to a contract."""
        if not self._initialized:
            await self.initialize()
        
        # Verify contract exists
        contract = await self.get_entity(contract_id)
        if not contract:
            raise EntityNotFoundError(str(contract_id), "contract")
        
        invoice.contract_id = contract_id
        
        # Add invoice
        invoice_id = await self.add_entity(invoice)
        
        # Create relationship
        await self.create_relationship(
            contract_id,
            UUID(invoice_id),
            RelationshipType.GENERATES_INVOICE,
            {
                "invoice_date": invoice.issue_date.isoformat(),
                "amount": str(invoice.amount_ttc),
            }
        )
        
        return invoice_id
    
    async def link_budget_to_department(
        self,
        budget_id: UUID,
        department_id: UUID,
    ) -> str:
        """Link a budget entry to a department."""
        if not self._initialized:
            await self.initialize()
        
        return await self.create_relationship(
            budget_id,
            department_id,
            RelationshipType.BELONGS_TO_DEPARTMENT,
        )
    
    async def add_clause_to_contract(
        self,
        clause: Clause,
        contract_id: UUID,
    ) -> str:
        """Add a clause and link it to a contract."""
        if not self._initialized:
            await self.initialize()
        
        clause.applies_to_contract_id = contract_id
        
        # Add clause
        clause_id = await self.add_entity(clause)
        
        # Create relationship
        await self.create_relationship(
            UUID(contract_id),
            UUID(clause_id),
            RelationshipType.CONTAINS_CLAUSE,
            {"clause_type": clause.clause_type.value}
        )
        
        return clause_id
    
    # ═══════════════════════════════════════════════════════════════
    # GRAPH TRAVERSAL & QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    async def traverse_from_entity(
        self,
        entity_id: UUID,
        max_depth: int = 2,
        relationship_types: Optional[list[RelationshipType]] = None,
        target_entity_types: Optional[list[EntityType]] = None,
    ) -> list[dict[str, Any]]:
        """Traverse the graph starting from an entity."""
        if not self._initialized:
            await self.initialize()
        
        query = GraphQuery(
            start_entity_id=entity_id,
            relationship_types=relationship_types,
            target_entity_types=target_entity_types,
            max_depth=max_depth,
        )
        
        return await self.graph_store.traverse(query)
    
    async def find_contracts_with_penalty_clauses(
        self,
        company_id: Optional[UUID] = None,
    ) -> list[dict[str, Any]]:
        """Find all contracts that contain penalty clauses."""
        if not self._initialized:
            await self.initialize()
        
        cypher = """
        MATCH (contract:contract)-[:CONTAINS_CLAUSE]->(clause:clause)
        WHERE clause.clause_type = 'penalty'
        RETURN contract.id as contract_id, contract.reference as reference,
               contract.title as title, clause.text as penalty_text,
               clause.penalty_amount as penalty_amount
        """
        
        results = await self.graph_store.execute_cypher(cypher)
        return results
    
    async def find_overdue_invoices(self) -> list[dict[str, Any]]:
        """Find all invoices that are overdue."""
        if not self._initialized:
            await self.initialize()
        
        cypher = """
        MATCH (invoice:invoice)
        WHERE invoice.status = 'overdue'
        RETURN invoice.id as invoice_id, invoice.invoice_number as invoice_number,
               invoice.due_date as due_date, invoice.amount_ttc as amount,
               invoice.payment_delay_days as delay_days
        ORDER BY invoice.due_date
        """
        
        results = await self.graph_store.execute_cypher(cypher)
        return results
    
    async def find_client_payment_history(
        self,
        client_id: UUID,
    ) -> list[dict[str, Any]]:
        """Find payment history for a specific client."""
        if not self._initialized:
            await self.initialize()
        
        cypher = """
        MATCH (client:client {id: $client_id})-[:HAS_CONTRACT]->(contract:contract)
              -[:GENERATES_INVOICE]->(invoice:invoice)
        RETURN contract.reference as contract_ref, invoice.invoice_number as invoice_number,
               invoice.issue_date as issue_date, invoice.due_date as due_date,
               invoice.payment_date as payment_date, invoice.payment_delay_days as delay_days,
               invoice.status as status, invoice.amount_ttc as amount
        ORDER BY invoice.issue_date DESC
        """
        
        results = await self.graph_store.execute_cypher(
            cypher,
            {"client_id": str(client_id)}
        )
        return results
    
    async def find_department_budget_status(
        self,
        department_id: UUID,
    ) -> dict[str, Any]:
        """Get budget status for a department."""
        if not self._initialized:
            await self.initialize()
        
        cypher = """
        MATCH (dept:department {id: $dept_id})
        OPTIONAL MATCH (budget:budget_entry)-[:BELONGS_TO_DEPARTMENT]->(dept)
        RETURN dept.name as department_name,
               dept.budget_allocated as allocated,
               dept.budget_consumed as consumed,
               collect({
                   category: budget.category,
                   planned: budget.planned_amount,
                   actual: budget.actual_amount,
                   variance: budget.variance
               }) as budget_entries
        """
        
        results = await self.graph_store.execute_cypher(
            cypher,
            {"dept_id": str(department_id)}
        )
        
        return results[0] if results else {}
    
    async def find_supplier_performance(
        self,
        supplier_id: UUID,
    ) -> dict[str, Any]:
        """Analyze supplier performance based on invoice history."""
        if not self._initialized:
            await self.initialize()
        
        cypher = """
        MATCH (supplier:supplier {id: $supplier_id})
        OPTIONAL MATCH (supplier)-[:PROVIDES_INVOICE]->(invoice:invoice)
        WITH supplier, invoice,
             CASE WHEN invoice.status = 'paid' THEN 1 ELSE 0 END as paid_count,
             CASE WHEN invoice.status = 'overdue' THEN 1 ELSE 0 END as overdue_count
        RETURN supplier.company_name as supplier_name,
               supplier.performance_rating as rating,
               count(invoice) as total_invoices,
               sum(paid_count) as paid_invoices,
               sum(overdue_count) as overdue_invoices,
               avg(invoice.payment_delay_days) as avg_delay_days
        """
        
        results = await self.graph_store.execute_cypher(
            cypher,
            {"supplier_id": str(supplier_id)}
        )
        
        return results[0] if results else {}
    
    async def find_contracts_expiring_soon(
        self,
        days_threshold: int = 90,
    ) -> list[dict[str, Any]]:
        """Find contracts expiring within the specified number of days."""
        if not self._initialized:
            await self.initialize()
        
        cypher = """
        MATCH (contract:contract)
        WHERE contract.status IN ['active', 'expiring_soon']
          AND date(contract.end_date) <= date() + duration({days: $days})
        OPTIONAL MATCH (client:client)-[:HAS_CONTRACT]->(contract)
        RETURN contract.id as contract_id, contract.reference as reference,
               contract.title as title, contract.end_date as end_date,
               contract.total_amount as amount, contract.auto_renewal as auto_renewal,
               client.company_name as client_name
        ORDER BY contract.end_date
        """
        
        results = await self.graph_store.execute_cypher(
            cypher,
            {"days": days_threshold}
        )
        return results
