"""
F360 Decision Fusion — REST API

FastAPI service that exposes the decision fusion engine as HTTP endpoints.
Designed to receive REAL data from upstream services:
  - Contexte Financier  → POST /api/v1/fuse
  - Knowledge Graph      → enrichment fields in the request body
  - Scenario Simulator   → scenario list in the request body
  - Real-time Feedback   → POST /api/v1/feedback

Other PFE modules call this API instead of synthetic data.
"""

from __future__ import annotations

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# ── Internal imports ────────────────────────────────────────────
from f360_synthesis_engine import (
    F360SynthesisEngine,
    FinancialData,
    KnowledgeGraphContext,
    ScenarioSimulation,
)
from multi_strategy_engine import (
    MultiStrategyEngine,
    MetaFusionResult,
    FusionStrategy,
)
from keyword_search import (
    KeywordSearchEngine,
    build_sample_knowledge_base,
)
from graph_peers import KnowledgeGraph
from simulation_bridge import SimulationBridge, SimulationRequest
from assistant import FinancialAssistant, AssistantResponse

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("f360-api")

# ── App ─────────────────────────────────────────────────────────
app = FastAPI(
    title="F360 Decision Fusion API",
    description=(
        "Week 2 — Weighted Decision Fusion & Multi-source Aggregation.\n\n"
        "Receives real financial data from upstream PFE modules "
        "(ERP extraction, Knowledge Graph, Scenario Simulator) and "
        "returns explainable tactical decisions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow cross-origin so the Streamlit UI (or any frontend) can call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ──────────────────────────────────────────────────
_engine: Optional[MultiStrategyEngine] = None
_assistant: Optional[FinancialAssistant] = None


def get_engine() -> MultiStrategyEngine:
    global _engine
    if _engine is None:
        risk_w = float(os.getenv("RISK_WEIGHT", "0.6"))
        prof_w = float(os.getenv("PROFITABILITY_WEIGHT", "0.4"))
        _engine = MultiStrategyEngine(risk_w, prof_w)
        logger.info("MultiStrategyEngine initialised (risk=%.2f, profit=%.2f)",
                     risk_w, prof_w)
    return _engine


def get_assistant() -> FinancialAssistant:
    global _assistant
    if _assistant is None:
        _assistant = FinancialAssistant()
        logger.info("FinancialAssistant initialised")
    return _assistant


# ================================================================
#  Pydantic request / response models
# ================================================================

# ── Inputs ──────────────────────────────────────────────────────

class FinancialDataIn(BaseModel):
    """Financial data from ERP / Kafka / contexte financier."""
    unpaid_invoices_spike: float = Field(..., description="Invoice spike %")
    client_id: str = Field(..., description="Client identifier")
    production_output_change: float = Field(
        ..., description="Production change % (negative = slowdown)")
    budget_remaining_q3: float = Field(
        ..., description="Budget remaining %")

    class Config:
        json_schema_extra = {
            "example": {
                "unpaid_invoices_spike": 15.0,
                "client_id": "CLIENT_X",
                "production_output_change": -12.0,
                "budget_remaining_q3": 5.0,
            }
        }


class KnowledgeGraphIn(BaseModel):
    """Knowledge graph context from RAGraph / Mémoire Épisodique."""
    client_parent_status: str = Field(
        ..., description="Parent company status")
    similar_historical_pattern: Optional[Dict[str, Any]] = Field(
        None, description="Matched episodic memory pattern")
    external_data_signals: List[str] = Field(
        default_factory=list, description="External risk signals")
    risk_indicators: List[str] = Field(
        default_factory=list, description="Risk indicators from KG")

    class Config:
        json_schema_extra = {
            "example": {
                "client_parent_status": "Undergoing restructuring",
                "similar_historical_pattern": {
                    "years_ago": 2,
                    "cash_flow_delay_days": 30,
                },
                "external_data_signals": [],
                "risk_indicators": ["parent_restructuring"],
            }
        }


class ScenarioIn(BaseModel):
    """One scenario from the Scenario Simulator module."""
    scenario_id: str
    description: str
    cash_flow_impact: float = Field(
        ..., description="Cash-flow impact %")
    margin_impact: float = Field(
        ..., description="Margin impact %")
    probability: float = Field(
        ..., ge=0.0, le=1.0, description="Scenario probability")
    time_horizon_days: int = Field(
        ..., description="Time horizon in days")

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "SCENARIO_A",
                "description": "Business as usual",
                "cash_flow_impact": -20.0,
                "margin_impact": 0.0,
                "probability": 0.85,
                "time_horizon_days": 60,
            }
        }


class FusionRequest(BaseModel):
    """
    Full fusion request — combines real data from all upstream modules.

    Upstream service mapping:
      financial_data  ← Contexte Financier (ERP extraction)
      kg_context      ← Knowledge Graph / Mémoire Épisodique / RAG
      scenarios       ← Scenario Simulator (Scénarios Parallèles / IA)
    """
    financial_data: FinancialDataIn
    kg_context: KnowledgeGraphIn
    scenarios: List[ScenarioIn] = Field(
        ..., min_length=2, description="At least 2 scenarios")
    strategies: Optional[List[str]] = Field(
        None,
        description=(
            "Which fusion strategies to run. "
            "Options: weighted_average, dempster_shafer, bayesian. "
            "Default: all three."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "financial_data": {
                    "unpaid_invoices_spike": 15.0,
                    "client_id": "CLIENT_X",
                    "production_output_change": -12.0,
                    "budget_remaining_q3": 5.0,
                },
                "kg_context": {
                    "client_parent_status": "Undergoing restructuring",
                    "similar_historical_pattern": {
                        "years_ago": 2,
                        "cash_flow_delay_days": 30,
                    },
                    "external_data_signals": [],
                    "risk_indicators": [],
                },
                "scenarios": [
                    {
                        "scenario_id": "SCENARIO_A",
                        "description": "Business as usual",
                        "cash_flow_impact": -20.0,
                        "margin_impact": 0.0,
                        "probability": 0.85,
                        "time_horizon_days": 60,
                    },
                    {
                        "scenario_id": "SCENARIO_B",
                        "description": "Early payment discount",
                        "cash_flow_impact": 0.0,
                        "margin_impact": -5.0,
                        "probability": 0.90,
                        "time_horizon_days": 30,
                    },
                ],
                "strategies": None,
            }
        }


class FeedbackIn(BaseModel):
    """Actual outcome sent back by the Real-time Feedback loop."""
    decision_id: str = Field(..., description="ID of the original decision")
    actual_cash_flow_impact: float
    actual_margin_impact: float
    actual_time_days: int
    notes: str = ""


class AskIn(BaseModel):
    """Natural-language query for the assistant."""
    query: str = Field(..., description="Free-text question (FR or EN)")


# ── Outputs ─────────────────────────────────────────────────────

class WeakSignalOut(BaseModel):
    signal_type: str
    correlation_strength: float
    source_indices: List[str]
    risk_level: str
    description: str


class FusionResponse(BaseModel):
    """Full decision fusion response."""
    consensus_scenario: str
    consensus_confidence: float
    agreement_level: float
    tactical_priority: str
    recommended_action: str
    explanation: str
    weak_signals: List[WeakSignalOut]
    predicted_outcome: Dict[str, Any]
    strategy_breakdown: Dict[str, Any]
    alternative_actions: List[str]


class FeedbackResponse(BaseModel):
    decision_id: str
    gap_analysis: Dict[str, float]
    status: str


class AskResponse(BaseModel):
    text: str
    sources: List[str]
    intent: str
    companies_found: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


# ================================================================
#  Endpoints
# ================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Liveness / readiness probe for Docker & orchestrators."""
    return HealthResponse(
        status="healthy",
        service="f360-decision-fusion",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/api/v1/fuse", response_model=FusionResponse, tags=["Decision Fusion"])
def fuse(request: FusionRequest):
    """
    **Main endpoint** — Run multi-strategy decision fusion.

    Receives real data from upstream PFE services:
    - `financial_data` ← Contexte Financier (ERP/Kafka extraction)
    - `kg_context`     ← Knowledge Graph / Mémoire Épisodique / RAG
    - `scenarios`      ← Scenario Simulator (parallel / AI-generated)

    Returns an explainable tactical decision with confidence scores,
    weak signal alerts, and strategy-level breakdown.
    """
    engine = get_engine()

    # Convert Pydantic models → internal dataclasses
    fin = FinancialData(
        unpaid_invoices_spike=request.financial_data.unpaid_invoices_spike,
        client_id=request.financial_data.client_id,
        production_output_change=request.financial_data.production_output_change,
        budget_remaining_q3=request.financial_data.budget_remaining_q3,
    )
    kg = KnowledgeGraphContext(
        client_parent_status=request.kg_context.client_parent_status,
        similar_historical_pattern=request.kg_context.similar_historical_pattern,
        external_data_signals=request.kg_context.external_data_signals,
        risk_indicators=request.kg_context.risk_indicators,
    )
    scenarios = [
        ScenarioSimulation(
            scenario_id=s.scenario_id,
            description=s.description,
            cash_flow_impact=s.cash_flow_impact,
            margin_impact=s.margin_impact,
            probability=s.probability,
            time_horizon_days=s.time_horizon_days,
        )
        for s in request.scenarios
    ]

    # Map strategy names
    strategy_map = {
        "weighted_average": FusionStrategy.WEIGHTED_AVERAGE,
        "dempster_shafer": FusionStrategy.DEMPSTER_SHAFER,
        "bayesian": FusionStrategy.BAYESIAN,
    }
    strategies = None
    if request.strategies:
        strategies = []
        for name in request.strategies:
            if name.lower() not in strategy_map:
                raise HTTPException(
                    400,
                    f"Unknown strategy '{name}'. "
                    f"Valid: {list(strategy_map.keys())}",
                )
            strategies.append(strategy_map[name.lower()])

    # Run fusion
    try:
        result: MetaFusionResult = engine.synthesize(
            fin, kg, scenarios, strategies
        )
    except Exception as exc:
        logger.exception("Fusion failed")
        raise HTTPException(500, f"Fusion error: {exc}")

    td = result.tactical_decision

    # Build strategy breakdown
    breakdown = {}
    for strat, sr in result.strategy_results.items():
        breakdown[strat.value] = {
            "recommended": sr.recommended_scenario,
            "confidence": round(sr.confidence, 4),
            "scores": {k: round(v, 4) for k, v in sr.scenario_scores.items()},
            "diagnostics": sr.diagnostics,
        }

    return FusionResponse(
        consensus_scenario=result.consensus_scenario,
        consensus_confidence=round(result.consensus_confidence, 4),
        agreement_level=round(result.agreement_level, 4),
        tactical_priority=td.tactical_priority.value,
        recommended_action=td.recommended_action,
        explanation=td.explanation,
        weak_signals=[
            WeakSignalOut(
                signal_type=ws.signal_type,
                correlation_strength=ws.correlation_strength,
                source_indices=ws.source_indices,
                risk_level=ws.risk_level.value,
                description=ws.description,
            )
            for ws in td.weak_signal_alert
        ],
        predicted_outcome=td.predicted_financial_outcome,
        strategy_breakdown=breakdown,
        alternative_actions=td.alternative_actions,
    )


@app.post("/api/v1/fuse/simple", tags=["Decision Fusion"])
def fuse_simple(request: FusionRequest):
    """
    Lightweight fusion — returns the raw JSON from the engine
    (useful for piping directly to the UI / Streamlit).
    """
    engine = get_engine()

    fin = FinancialData(
        unpaid_invoices_spike=request.financial_data.unpaid_invoices_spike,
        client_id=request.financial_data.client_id,
        production_output_change=request.financial_data.production_output_change,
        budget_remaining_q3=request.financial_data.budget_remaining_q3,
    )
    kg = KnowledgeGraphContext(
        client_parent_status=request.kg_context.client_parent_status,
        similar_historical_pattern=request.kg_context.similar_historical_pattern,
        external_data_signals=request.kg_context.external_data_signals,
        risk_indicators=request.kg_context.risk_indicators,
    )
    scenarios = [
        ScenarioSimulation(
            scenario_id=s.scenario_id,
            description=s.description,
            cash_flow_impact=s.cash_flow_impact,
            margin_impact=s.margin_impact,
            probability=s.probability,
            time_horizon_days=s.time_horizon_days,
        )
        for s in request.scenarios
    ]

    result = engine.synthesize(fin, kg, scenarios)
    return json.loads(result.to_json())


@app.post("/api/v1/feedback", response_model=FeedbackResponse,
          tags=["Feedback Loop"])
def submit_feedback(feedback: FeedbackIn):
    """
    Receive actual outcome from the Real-time Feedback module.

    Computes gap analysis between predicted and actual results.
    In production this would persist to a database and trigger
    weight re-calibration.
    """
    # Placeholder gap analysis — in production, fetch the original
    # prediction from a store and compare.
    gap = {
        "cash_flow_gap": feedback.actual_cash_flow_impact,
        "margin_gap": feedback.actual_margin_impact,
        "time_gap_days": feedback.actual_time_days,
    }
    logger.info("Feedback received for decision %s: %s",
                feedback.decision_id, gap)

    return FeedbackResponse(
        decision_id=feedback.decision_id,
        gap_analysis=gap,
        status="recorded",
    )


@app.post("/api/v1/ask", response_model=AskResponse, tags=["Assistant"])
def ask_endpoint(body: AskIn):
    """
    Natural-language assistant endpoint.

    Accepts a free-text query (FR or EN), runs keyword search,
    graph enrichment, and optional simulation, then returns a
    formatted answer with sources.
    """
    assistant = get_assistant()
    r: AssistantResponse = assistant.ask(body.query)
    return AskResponse(
        text=r.text,
        sources=r.sources,
        intent=r.intent,
        companies_found=r.companies_found,
    )


@app.get("/api/v1/strategies", tags=["Info"])
def list_strategies():
    """List available fusion strategies."""
    return {
        "strategies": [
            {
                "id": "weighted_average",
                "name": "Weighted Average",
                "description": "Linear risk/profitability scoring",
            },
            {
                "id": "dempster_shafer",
                "name": "Dempster-Shafer Theory",
                "description": "Evidence-based fusion with conflict modeling",
            },
            {
                "id": "bayesian",
                "name": "Bayesian Inference",
                "description": "Sequential probabilistic updating",
            },
        ]
    }


@app.get("/api/v1/config", tags=["Info"])
def get_config():
    """Return current engine configuration."""
    engine = get_engine()
    return {
        "risk_weight": engine.risk_weight,
        "profitability_weight": engine.profitability_weight,
        "strategy_weights": {
            k.value: v for k, v in engine.strategy_weights.items()
        },
    }


# ================================================================
#  Entry point
# ================================================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    logger.info("Starting F360 Decision Fusion API on %s:%d", host, port)
    uvicorn.run("api:app", host=host, port=port, reload=False)
