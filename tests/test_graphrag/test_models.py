"""Tests for GraphRAG models."""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from graphrag.models import (
    Client,
    Supplier,
    Contract,
    Invoice,
    BudgetEntry,
    Department,
    Project,
    Clause,
    FinancialEpisode,
    FinancialPattern,
    EntityType,
    RelationshipType,
    ContractStatus,
    InvoiceStatus,
    ClauseType,
    GraphQuery,
    RAGQuery,
    RAGResponse,
)


class TestEntityModels:
    """Test financial entity models."""
    
    def test_client_creation(self):
        """Test creating a client entity."""
        client = Client(
            name="Test Client",
            company_name="Test Corp",
            contact_email="test@example.com",
            tax_id="FR12345678901",
        )
        
        assert client.entity_type == EntityType.CLIENT
        assert client.company_name == "Test Corp"
        assert client.contact_email == "test@example.com"
        assert client.id is not None
    
    def test_contract_creation(self):
        """Test creating a contract entity."""
        contract = Contract(
            name="Test Contract",
            reference="CTR-2024-001",
            title="Annual Service Agreement",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            total_amount=Decimal("50000.00"),
        )
        
        assert contract.entity_type == EntityType.CONTRACT
        assert contract.reference == "CTR-2024-001"
        assert contract.total_amount == Decimal("50000.00")
        assert contract.status == ContractStatus.DRAFT
    
    def test_contract_validation_negative_amount(self):
        """Test that negative contract amounts are rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Contract(
                name="Bad Contract",
                reference="CTR-BAD",
                title="Invalid",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                total_amount=Decimal("-1000.00"),
            )
    
    def test_invoice_creation(self):
        """Test creating an invoice entity."""
        invoice = Invoice(
            name="Test Invoice",
            invoice_number="INV-2024-001",
            issue_date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            amount_ht=Decimal("10000.00"),
            amount_ttc=Decimal("12000.00"),
            tax_amount=Decimal("2000.00"),
        )
        
        assert invoice.entity_type == EntityType.INVOICE
        assert invoice.invoice_number == "INV-2024-001"
        assert invoice.status == InvoiceStatus.PENDING
        assert invoice.amount_ttc == Decimal("12000.00")
    
    def test_budget_entry_variance_calculation(self):
        """Test budget variance calculation."""
        budget = BudgetEntry(
            name="Q1 Budget",
            category="IT",
            planned_amount=Decimal("100000.00"),
            actual_amount=Decimal("115000.00"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),
        )
        
        budget.calculate_variance()
        
        assert budget.variance == Decimal("15000.00")
        assert budget.variance_pct == 15.0
    
    def test_clause_creation(self):
        """Test creating a contract clause."""
        clause = Clause(
            name="Penalty Clause",
            clause_type=ClauseType.PENALTY,
            text="Late payment penalty: 1% per week",
            risk_level="high",
            penalty_amount=Decimal("5000.00"),
        )
        
        assert clause.entity_type == EntityType.CLAUSE
        assert clause.clause_type == ClauseType.PENALTY
        assert clause.risk_level == "high"


class TestEpisodicMemoryModels:
    """Test episodic memory models."""
    
    def test_financial_episode_creation(self):
        """Test creating a financial episode."""
        entity_ids = [uuid4(), uuid4()]
        
        episode = FinancialEpisode(
            title="Late Payment Detected",
            description="Client XYZ paid 20 days late",
            event_date=datetime.utcnow(),
            entities_involved=entity_ids,
            event_type="late_payment",
            context={"delay_days": 20, "amount": 50000},
            tags=["payment", "risk"],
        )
        
        assert episode.title == "Late Payment Detected"
        assert episode.event_type == "late_payment"
        assert len(episode.entities_involved) == 2
        assert episode.context["delay_days"] == 20
        assert "payment" in episode.tags
    
    def test_financial_pattern_creation(self):
        """Test creating a financial pattern."""
        pattern = FinancialPattern(
            pattern_type="recurring_late_payment",
            description="Client pays late consistently",
            confidence=0.85,
            occurrences=5,
        )
        
        assert pattern.pattern_type == "recurring_late_payment"
        assert pattern.confidence == 0.85
        assert pattern.occurrences == 5


class TestQueryModels:
    """Test query and response models."""
    
    def test_graph_query_creation(self):
        """Test creating a graph query."""
        query = GraphQuery(
            start_entity_id=uuid4(),
            relationship_types=[RelationshipType.HAS_CONTRACT],
            target_entity_types=[EntityType.CONTRACT],
            max_depth=2,
        )
        
        assert query.max_depth == 2
        assert RelationshipType.HAS_CONTRACT in query.relationship_types
    
    def test_rag_query_creation(self):
        """Test creating a RAG query."""
        query = RAGQuery(
            question="Which contracts are expiring soon?",
            use_vector_search=True,
            use_graph_traversal=True,
            use_episodic_memory=True,
            top_k=5,
        )
        
        assert query.question == "Which contracts are expiring soon?"
        assert query.use_vector_search is True
        assert query.top_k == 5
    
    def test_rag_response_creation(self):
        """Test creating a RAG response."""
        response = RAGResponse(
            answer="Based on the data, 3 contracts are expiring within 90 days.",
            sources=[
                {"type": "knowledge_graph", "excerpt": "Contract CTR-001..."},
                {"type": "vector", "similarity": 0.95},
            ],
            confidence=0.92,
        )
        
        assert "3 contracts" in response.answer
        assert len(response.sources) == 2
        assert response.confidence == 0.92


class TestEnums:
    """Test enum types."""
    
    def test_entity_types(self):
        """Test entity type enum."""
        assert EntityType.CLIENT == "client"
        assert EntityType.CONTRACT == "contract"
        assert EntityType.INVOICE == "invoice"
    
    def test_relationship_types(self):
        """Test relationship type enum."""
        assert RelationshipType.HAS_CONTRACT == "has_contract"
        assert RelationshipType.GENERATES_INVOICE == "generates_invoice"
    
    def test_contract_status(self):
        """Test contract status enum."""
        assert ContractStatus.ACTIVE == "active"
        assert ContractStatus.EXPIRED == "expired"
    
    def test_invoice_status(self):
        """Test invoice status enum."""
        assert InvoiceStatus.PAID == "paid"
        assert InvoiceStatus.OVERDUE == "overdue"
