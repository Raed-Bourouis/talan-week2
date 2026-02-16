"""
FastAPI Main Application - Financial Intelligence Hub
100% FREE - No API keys required!
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import os
from datetime import datetime

# Import our free local modules
from src.graphrag.query_orchestrator import QueryOrchestrator
from src.graphrag.local_llm import get_llm
from src.graphrag.local_embeddings import get_embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FINCENTER - Financial Intelligence Hub",
    description="GraphRAG-based Financial Analysis using 100% FREE local LLMs (Ollama) and embeddings",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components (lazy loading)
orchestrator: Optional[QueryOrchestrator] = None


def get_orchestrator() -> QueryOrchestrator:
    """Get or create query orchestrator instance."""
    global orchestrator
    if orchestrator is None:
        logger.info("Initializing QueryOrchestrator...")
        orchestrator = QueryOrchestrator()
    return orchestrator


# Pydantic models
class QueryRequest(BaseModel):
    question: str
    query_type: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    query: str
    answer: str
    query_type: str
    timestamp: str
    sources: Optional[Any] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, bool]


# Routes
@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FINCENTER API",
        "version": "1.0.0",
        "description": "Financial Intelligence Hub using FREE local LLMs",
        "features": [
            "100% FREE - No API keys required",
            "Local LLM (Ollama - Llama 3.1 / Mistral)",
            "Local embeddings (sentence-transformers)",
            "GraphRAG with Neo4j + Qdrant",
            "Budget analysis, Contract monitoring, Cash flow forecasting"
        ],
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    Verifies all services are accessible.
    """
    services_status = {
        "api": True,
        "ollama": False,
        "neo4j": False,
        "qdrant": False
    }
    
    try:
        # Check Ollama
        llm = get_llm()
        services_status["ollama"] = llm.check_health()
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
    
    try:
        # Check orchestrator (which checks Neo4j and Qdrant)
        orch = get_orchestrator()
        services_status["neo4j"] = True
        services_status["qdrant"] = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
    
    overall_status = "healthy" if all(services_status.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        services=services_status
    )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(request: QueryRequest):
    """
    Process a natural language financial query.
    
    Examples:
    - "Which departments are over budget?"
    - "Show me contracts expiring in the next 90 days"
    - "What's the cash flow forecast for next month?"
    - "Which suppliers consistently pay late?"
    """
    try:
        logger.info(f"Processing query: {request.question}")
        
        orch = get_orchestrator()
        result = orch.process_query(request.question)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Query processing failed"))
        
        return QueryResponse(
            success=True,
            query=result["query"],
            answer=result["answer"],
            query_type=result["query_type"],
            timestamp=result["timestamp"],
            sources=result.get("sources")
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/budgets", tags=["Budget"])
async def get_budgets():
    """Get budget information for all departments."""
    try:
        orch = get_orchestrator()
        result = orch.process_query("Show me budget information for all departments")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contracts", tags=["Contracts"])
async def get_contracts(
    status: Optional[str] = Query(None, description="Filter by status: active, expired, pending"),
    expiring_days: Optional[int] = Query(None, description="Show contracts expiring in N days")
):
    """Get contract information."""
    try:
        orch = get_orchestrator()
        
        if expiring_days:
            query = f"Show me contracts expiring in the next {expiring_days} days"
        elif status:
            query = f"Show me all {status} contracts"
        else:
            query = "Show me all contracts"
        
        result = orch.process_query(query)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suppliers", tags=["Suppliers"])
async def get_suppliers():
    """Get supplier information and performance metrics."""
    try:
        orch = get_orchestrator()
        result = orch.process_query("Show me supplier performance and reliability scores")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/invoices", tags=["Invoices"])
async def get_invoices(
    status: Optional[str] = Query(None, description="Filter by status: paid, pending, overdue")
):
    """Get invoice information."""
    try:
        orch = get_orchestrator()
        
        if status:
            query = f"Show me all {status} invoices"
        else:
            query = "Show me invoice summary"
        
        result = orch.process_query(query)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patterns", tags=["Intelligence"])
async def get_patterns():
    """Get detected financial patterns and insights."""
    try:
        orch = get_orchestrator()
        result = orch.process_query("What financial patterns have been detected?")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts", tags=["Intelligence"])
async def get_alerts():
    """Get active alerts and recommendations."""
    try:
        orch = get_orchestrator()
        result = orch.process_query("Show me all active alerts and recommendations")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cashflow/forecast", tags=["Cash Flow"])
async def get_cashflow_forecast(days: int = Query(90, description="Forecast horizon in days")):
    """Get cash flow forecast."""
    try:
        orch = get_orchestrator()
        result = orch.process_query(f"Forecast cash flow for the next {days} days")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 Starting FINCENTER API...")
    logger.info("✅ Using 100% FREE local components:")
    logger.info("   - Ollama (Local LLM)")
    logger.info("   - sentence-transformers (Local Embeddings)")
    logger.info("   - Neo4j Community (Graph DB)")
    logger.info("   - Qdrant (Vector DB)")
    logger.info("   - PostgreSQL (Relational DB)")
    logger.info("💰 Total API costs: $0.00")
    
    try:
        # Pre-initialize components
        get_embeddings()
        get_llm()
        logger.info("✅ Local LLM and embeddings loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not pre-load models: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down FINCENTER API...")
    global orchestrator
    if orchestrator:
        orchestrator.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
