"""
Pydantic Models for API Requests and Responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class QueryType(str, Enum):
    """Types of financial queries."""
    BUDGET = "budget"
    CONTRACT = "contract"
    CASH_FLOW = "cash_flow"
    SUPPLIER = "supplier"
    INVOICE = "invoice"
    PATTERN = "pattern"
    GENERAL = "general"


class Severity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Generic status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"


# Request Models
class QueryRequest(BaseModel):
    """Request model for financial queries."""
    question: str = Field(..., description="Natural language financial question")
    query_type: Optional[QueryType] = Field(None, description="Optional query type hint")
    max_results: Optional[int] = Field(10, description="Maximum number of results", ge=1, le=100)


class ContractFilter(BaseModel):
    """Filter model for contract queries."""
    status: Optional[str] = None
    expiring_days: Optional[int] = None
    supplier_id: Optional[str] = None


class InvoiceFilter(BaseModel):
    """Filter model for invoice queries."""
    status: Optional[str] = None
    overdue_only: bool = False
    supplier_id: Optional[str] = None


# Response Models
class QueryResponse(BaseModel):
    """Response model for financial queries."""
    success: bool
    query: str
    answer: str
    query_type: str
    timestamp: str
    sources: Optional[Any] = None
    context: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """System health check response."""
    status: str = Field(..., description="Overall system status")
    timestamp: str
    services: Dict[str, bool]


class BudgetItem(BaseModel):
    """Budget allocation item."""
    department_id: str
    department_name: str
    allocated: float
    spent: float
    remaining: float
    variance_pct: float
    status: str


class BudgetResponse(BaseModel):
    """Budget query response."""
    success: bool
    total_allocated: float
    total_spent: float
    total_remaining: float
    departments: List[BudgetItem]
    timestamp: str


class ContractItem(BaseModel):
    """Contract information item."""
    contract_id: str
    title: str
    supplier_name: str
    value: float
    start_date: date
    expiration_date: date
    status: str
    auto_renewal: bool
    days_until_expiration: Optional[int] = None


class ContractResponse(BaseModel):
    """Contract query response."""
    success: bool
    contracts: List[ContractItem]
    total_value: float
    expiring_soon_count: int
    timestamp: str


class SupplierItem(BaseModel):
    """Supplier information item."""
    supplier_id: str
    name: str
    payment_terms: str
    reliability_score: float
    avg_delay_days: int
    total_contracts: int
    total_paid: float


class SupplierResponse(BaseModel):
    """Supplier query response."""
    success: bool
    suppliers: List[SupplierItem]
    timestamp: str


class InvoiceItem(BaseModel):
    """Invoice information item."""
    invoice_id: str
    invoice_number: str
    supplier_name: str
    amount: float
    issue_date: date
    due_date: date
    payment_date: Optional[date] = None
    status: str
    days_overdue: Optional[int] = None


class InvoiceResponse(BaseModel):
    """Invoice query response."""
    success: bool
    invoices: List[InvoiceItem]
    total_amount: float
    overdue_count: int
    overdue_amount: float
    timestamp: str


class Pattern(BaseModel):
    """Detected financial pattern."""
    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    occurrences: int
    recommendation: str
    entities: Optional[List[str]] = None


class PatternResponse(BaseModel):
    """Pattern detection response."""
    success: bool
    patterns: List[Pattern]
    total_patterns: int
    timestamp: str


class Alert(BaseModel):
    """Financial alert."""
    alert_id: str
    alert_type: str
    severity: Severity
    title: str
    description: str
    entity_type: str
    entity_id: str
    recommendation: str
    status: str
    created_at: datetime


class AlertResponse(BaseModel):
    """Alert query response."""
    success: bool
    alerts: List[Alert]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    timestamp: str


class CashFlowPrediction(BaseModel):
    """Cash flow prediction for a specific date."""
    prediction_date: date
    predicted_inflow: float
    predicted_outflow: float
    predicted_balance: float
    confidence_lower: float
    confidence_upper: float


class CashFlowForecast(BaseModel):
    """Cash flow forecast response."""
    success: bool
    forecast_days: int
    predictions: List[CashFlowPrediction]
    current_balance: float
    total_predicted_inflow: float
    total_predicted_outflow: float
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: str


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: str
