"""
F360 – Pydantic Schemas for API request/response validation
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════

class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


# ═══════════════════════════════════════════
# COMPANY
# ═══════════════════════════════════════════

class CompanyCreate(BaseModel):
    name: str
    siren: Optional[str] = None
    sector: Optional[str] = None
    country: str = "France"


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    siren: Optional[str]
    sector: Optional[str]
    country: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════
# CONTRACT
# ═══════════════════════════════════════════

class ContractCreate(BaseModel):
    company_id: uuid.UUID
    counterparty_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    reference: str
    title: Optional[str] = None
    contract_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    currency: str = "EUR"
    payment_terms: Optional[str] = None
    penalty_clauses: Optional[str] = None
    indexation_clause: Optional[str] = None


class ContractResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    reference: str
    title: Optional[str]
    contract_type: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    total_amount: Optional[Decimal]
    currency: str
    status: str
    payment_terms: Optional[str]
    penalty_clauses: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractAlert(BaseModel):
    contract_id: uuid.UUID
    reference: str
    alert_type: str  # 'expiring_soon', 'budget_exceeded', 'penalty_risk'
    message: str
    severity: str  # 'info', 'warning', 'critical'


# ═══════════════════════════════════════════
# INVOICE
# ═══════════════════════════════════════════

class InvoiceCreate(BaseModel):
    company_id: uuid.UUID
    contract_id: Optional[uuid.UUID] = None
    counterparty_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    amount_ht: Decimal
    amount_tax: Decimal = Decimal("0")
    amount_ttc: Decimal
    currency: str = "EUR"
    direction: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    amount_ht: Decimal
    amount_ttc: Decimal
    currency: str
    status: str
    direction: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════
# BUDGET
# ═══════════════════════════════════════════

class BudgetCreate(BaseModel):
    company_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    fiscal_year: int
    category: Optional[str] = None
    planned_amount: Decimal
    actual_amount: Decimal = Decimal("0")
    currency: str = "EUR"


class BudgetResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    fiscal_year: int
    category: Optional[str]
    planned_amount: Decimal
    actual_amount: Decimal
    currency: str
    deviation_pct: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetOverview(BaseModel):
    fiscal_year: int
    total_planned: Decimal
    total_actual: Decimal
    deviation_pct: float
    by_category: list[dict[str, Any]]
    by_department: list[dict[str, Any]]


# ═══════════════════════════════════════════
# CASHFLOW
# ═══════════════════════════════════════════

class CashflowForecast(BaseModel):
    date: date
    cumulative_balance: Decimal
    inflows: Decimal
    outflows: Decimal
    is_projected: bool = False


# ═══════════════════════════════════════════
# SIMULATION
# ═══════════════════════════════════════════

class SimulationRequest(BaseModel):
    simulation_type: str  # 'budget_variation', 'cashflow_projection', 'monte_carlo', 'renegotiation'
    parameters: dict[str, Any]


class SimulationResponse(BaseModel):
    id: uuid.UUID
    simulation_type: str
    parameters: dict[str, Any]
    results: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════
# RECOMMENDATION
# ═══════════════════════════════════════════

class RecommendationResponse(BaseModel):
    id: uuid.UUID
    category: Optional[str]
    severity: Optional[str]
    title: Optional[str]
    description: Optional[str]
    suggested_action: Optional[str]
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════
# INGESTION
# ═══════════════════════════════════════════

class IngestionResult(BaseModel):
    document_id: uuid.UUID
    filename: str
    file_type: str
    entities_extracted: dict[str, Any]
    chunks_created: int
    status: str  # 'success', 'partial', 'error'
    message: Optional[str] = None


# ═══════════════════════════════════════════
# RAG
# ═══════════════════════════════════════════

class RAGQuery(BaseModel):
    question: str
    company_id: Optional[uuid.UUID] = None
    top_k: int = 5


class RAGResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    confidence: Optional[float] = None


# ═══════════════════════════════════════════
# CHAIN-OF-THOUGHT (Layer 3 – RAGraph)
# ═══════════════════════════════════════════

class ChainOfThoughtRequest(BaseModel):
    question: str
    context: dict[str, Any] = {}


class ChainOfThoughtResponse(BaseModel):
    question: str
    steps: list[dict[str, Any]]
    conclusion: str
    model: str = "unknown"


# ═══════════════════════════════════════════
# CONNECTOR (Layer 1 – Sources)
# ═══════════════════════════════════════════

class ConnectorTestResult(BaseModel):
    connector_type: str
    status: str  # 'success' | 'error'
    message: str
    sample_keys: list[str] = []


class IoTIngestPayload(BaseModel):
    events: list[dict[str, Any]]


# ═══════════════════════════════════════════
# GAP ANALYSIS (Layer 4 – Feedback)
# ═══════════════════════════════════════════

class GapAnalysisRequest(BaseModel):
    company_id: uuid.UUID
    fiscal_year: int = 2025


class GapAnalysisResponse(BaseModel):
    company_id: uuid.UUID
    gaps: list[dict[str, Any]]
    total_gaps: int


# ═══════════════════════════════════════════
# DECISION FUSION (Layer 6)
# ═══════════════════════════════════════════

class FusionRequest(BaseModel):
    gaps: Optional[list[dict[str, Any]]] = None
    simulation_results: Optional[list[dict[str, Any]]] = None


class FusionResponse(BaseModel):
    decisions: list[dict[str, Any]]
    aggregation_summary: dict[str, Any]
    generated_at: str


# ═══════════════════════════════════════════
# WEAK SIGNALS (Layer 7)
# ═══════════════════════════════════════════

class WeakSignalResponse(BaseModel):
    company_id: uuid.UUID
    signal_count: int
    correlations: list[dict[str, Any]]
