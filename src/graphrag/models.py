"""
GraphRAG Financial Entity Models
=================================
Pydantic models for financial entities and their relationships.
These models serve as the data contracts for the GraphRAG component.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ═══════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════

class EntityType(str, Enum):
    """Entity types in the knowledge graph."""
    CLIENT = "client"
    SUPPLIER = "supplier"
    CONTRACT = "contract"
    INVOICE = "invoice"
    BUDGET_ENTRY = "budget_entry"
    ACCOUNTING_ENTRY = "accounting_entry"
    DEPARTMENT = "department"
    PROJECT = "project"
    CLAUSE = "clause"


class RelationshipType(str, Enum):
    """Relationship types between entities."""
    HAS_CONTRACT = "has_contract"
    GENERATES_INVOICE = "generates_invoice"
    PROVIDES_INVOICE = "provides_invoice"
    BELONGS_TO_DEPARTMENT = "belongs_to_department"
    ASSIGNED_TO_PROJECT = "assigned_to_project"
    CONTAINS_CLAUSE = "contains_clause"
    REFERENCES_BUDGET = "references_budget"
    RELATED_TO = "related_to"
    PAYS = "pays"
    RECEIVES_PAYMENT = "receives_payment"


class ContractStatus(str, Enum):
    """Contract lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"


class InvoiceStatus(str, Enum):
    """Invoice payment status."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class ClauseType(str, Enum):
    """Types of contract clauses."""
    PENALTY = "penalty"
    INDEXATION = "indexation"
    TERMINATION = "termination"
    LIABILITY = "liability"
    PAYMENT_TERMS = "payment_terms"
    RENEWAL = "renewal"
    CONFIDENTIALITY = "confidentiality"
    OTHER = "other"


# ═══════════════════════════════════════════════════════════════
# BASE MODELS
# ═══════════════════════════════════════════════════════════════

class FinancialEntity(BaseModel):
    """Base class for all financial entities."""
    model_config = ConfigDict(
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: str,
        }
    )
    
    id: UUID = Field(default_factory=uuid4)
    entity_type: EntityType
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    """Represents a relationship between two entities."""
    model_config = ConfigDict(
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )
    
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    target_id: UUID
    relationship_type: RelationshipType
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
# ENTITY MODELS
# ═══════════════════════════════════════════════════════════════

class Client(FinancialEntity):
    """Client entity."""
    entity_type: EntityType = Field(default=EntityType.CLIENT, frozen=True)
    company_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    payment_history: list[dict[str, Any]] = Field(default_factory=list)
    credit_rating: Optional[str] = None


class Supplier(FinancialEntity):
    """Supplier entity."""
    entity_type: EntityType = Field(default=EntityType.SUPPLIER, frozen=True)
    company_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    categories: list[str] = Field(default_factory=list)
    performance_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)


class Department(FinancialEntity):
    """Department entity."""
    entity_type: EntityType = Field(default=EntityType.DEPARTMENT, frozen=True)
    code: str
    manager: Optional[str] = None
    budget_allocated: Optional[Decimal] = None
    budget_consumed: Optional[Decimal] = None


class Project(FinancialEntity):
    """Project entity."""
    entity_type: EntityType = Field(default=EntityType.PROJECT, frozen=True)
    code: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    status: str = "active"


class Clause(FinancialEntity):
    """Contract clause entity."""
    entity_type: EntityType = Field(default=EntityType.CLAUSE, frozen=True)
    clause_type: ClauseType
    text: str
    applies_to_contract_id: Optional[UUID] = None
    risk_level: Optional[str] = None  # "low", "medium", "high"
    indexation_rate: Optional[float] = None
    penalty_amount: Optional[Decimal] = None


class Contract(FinancialEntity):
    """Contract entity."""
    entity_type: EntityType = Field(default=EntityType.CONTRACT, frozen=True)
    reference: str
    title: str
    client_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    start_date: date
    end_date: date
    total_amount: Decimal
    currency: str = "EUR"
    status: ContractStatus = ContractStatus.DRAFT
    clauses: list[Clause] = Field(default_factory=list)
    renewal_notice_days: Optional[int] = None
    auto_renewal: bool = False

    @field_validator('total_amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Contract amount cannot be negative")
        return v


class Invoice(FinancialEntity):
    """Invoice entity."""
    entity_type: EntityType = Field(default=EntityType.INVOICE, frozen=True)
    invoice_number: str
    contract_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    issue_date: date
    due_date: date
    amount_ht: Decimal  # Amount excluding tax
    amount_ttc: Decimal  # Amount including tax
    tax_amount: Decimal
    currency: str = "EUR"
    status: InvoiceStatus = InvoiceStatus.PENDING
    payment_date: Optional[date] = None
    payment_delay_days: Optional[int] = None

    @field_validator('amount_ht', 'amount_ttc', 'tax_amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Invoice amounts cannot be negative")
        return v


class BudgetEntry(FinancialEntity):
    """Budget entry entity."""
    entity_type: EntityType = Field(default=EntityType.BUDGET_ENTRY, frozen=True)
    category: str
    department_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    planned_amount: Decimal
    actual_amount: Decimal = Decimal("0")
    period_start: date
    period_end: date
    variance: Optional[Decimal] = None
    variance_pct: Optional[float] = None

    def calculate_variance(self) -> None:
        """Calculate budget variance."""
        self.variance = self.actual_amount - self.planned_amount
        if self.planned_amount != 0:
            self.variance_pct = float((self.variance / self.planned_amount) * 100)
        else:
            self.variance_pct = 0.0


class AccountingEntry(FinancialEntity):
    """Accounting entry entity."""
    entity_type: EntityType = Field(default=EntityType.ACCOUNTING_ENTRY, frozen=True)
    account_code: str
    account_name: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    entry_date: date
    reference: Optional[str] = None
    description: Optional[str] = None
    invoice_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None


# ═══════════════════════════════════════════════════════════════
# EPISODIC MEMORY MODELS
# ═══════════════════════════════════════════════════════════════

class FinancialEpisode(BaseModel):
    """Represents a financial event or pattern in episodic memory."""
    model_config = ConfigDict(
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
    )
    
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    event_date: datetime
    entities_involved: list[UUID] = Field(default_factory=list)
    event_type: str  # e.g., "late_payment", "contract_renewal", "budget_overrun"
    context: dict[str, Any] = Field(default_factory=dict)
    pattern_signature: Optional[str] = None  # For pattern matching
    similarity_score: Optional[float] = None  # When retrieved
    tags: list[str] = Field(default_factory=list)


class FinancialPattern(BaseModel):
    """Represents a recurring pattern in financial data."""
    id: UUID = Field(default_factory=uuid4)
    pattern_type: str  # e.g., "recurring_late_payment", "seasonal_overspending"
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    occurrences: int = 0
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    entities: list[UUID] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    examples: list[UUID] = Field(default_factory=list)  # Episode IDs


# ═══════════════════════════════════════════════════════════════
# QUERY MODELS
# ═══════════════════════════════════════════════════════════════

class GraphQuery(BaseModel):
    """Query for graph traversal."""
    start_entity_id: UUID
    relationship_types: Optional[list[RelationshipType]] = None
    target_entity_types: Optional[list[EntityType]] = None
    max_depth: int = Field(default=2, ge=1, le=5)
    filters: dict[str, Any] = Field(default_factory=dict)


class RAGQuery(BaseModel):
    """Query for RAG orchestration."""
    question: str
    company_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    use_vector_search: bool = True
    use_graph_traversal: bool = True
    use_episodic_memory: bool = True
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    """Response from RAG orchestration."""
    model_config = ConfigDict(
        json_encoders={
            UUID: str,
        }
    )
    
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    confidence: Optional[float] = None
    reasoning_steps: Optional[list[dict[str, Any]]] = None
    retrieved_entities: list[UUID] = Field(default_factory=list)
    episodic_context: list[FinancialEpisode] = Field(default_factory=list)
