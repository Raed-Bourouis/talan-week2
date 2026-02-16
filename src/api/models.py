"""
Pydantic Models for API Requests and Responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum


class QueryRequest(BaseModel):
    """Natural language query request"""
    question: str = Field(..., description="Natural language financial query")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")


class QueryResponse(BaseModel):
    """Query response"""
    query: str
    query_type: str
    answer: str
    results: Dict[str, Any]
    patterns: List[Dict[str, Any]]


class BudgetAnalysisRequest(BaseModel):
    """Budget analysis request"""
    department_id: str
    year: int = Field(..., ge=2000, le=2100)


class BudgetAnalysisResponse(BaseModel):
    """Budget analysis response"""
    department_id: str
    year: int
    allocated: float
    spent: float
    remaining: float
    variance: float
    variance_percent: float
    status: str
    severity: str
    top_expenses: List[Dict[str, Any]]
    recommendations: List[str]


class ContractExpiryRequest(BaseModel):
    """Contract expiry request"""
    days_ahead: int = Field(90, ge=1, le=365, description="Days to look ahead")


class ContractExpiryResponse(BaseModel):
    """Contract expiry response"""
    contracts: List[Dict[str, Any]]
    total_count: int
    total_value: float


class CashFlowForecastRequest(BaseModel):
    """Cash flow forecast request"""
    days: int = Field(90, ge=1, le=365, description="Days to forecast")


class CashFlowForecastResponse(BaseModel):
    """Cash flow forecast response"""
    forecast_days: int
    generated_at: str
    forecast: List[Dict[str, Any]]
    tensions: List[Dict[str, Any]]
    recommendations: List[str]


class SimulationRequest(BaseModel):
    """Simulation request"""
    simulation_type: str = Field(..., description="Type of simulation")
    parameters: Dict[str, Any] = Field(..., description="Simulation parameters")


class SimulationResponse(BaseModel):
    """Simulation response"""
    simulation_id: str
    simulation_type: str
    results: Dict[str, Any]


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertType(str, Enum):
    """Alert types"""
    budget = "budget"
    contract = "contract"
    payment = "payment"
    risk = "risk"
    compliance = "compliance"


class Alert(BaseModel):
    """Alert model"""
    id: Optional[int] = None
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    """Alert list response"""
    alerts: List[Alert]
    total_count: int
    active_count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    services: Dict[str, str]
