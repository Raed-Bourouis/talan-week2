"""
FastAPI Main Application
Financial Intelligence Hub API
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os
from typing import Dict, Any

from .models import (
    QueryRequest, QueryResponse,
    HealthResponse
)
from .routers import budget, contracts, cashflow, alerts

# Import query orchestrator at module level for better performance
try:
    from src.graphrag.query_orchestrator import QueryOrchestrator
    QUERY_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    QUERY_ORCHESTRATOR_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Financial Intelligence Hub API",
    description="GraphRAG-based Financial Analysis and Decision Support System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(budget.router, prefix="/api/budget", tags=["Budget"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["Contracts"])
app.include_router(cashflow.router, prefix="/api/cashflow", tags=["Cash Flow"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])


# Database connection dependency
def get_db_connections():
    """Get database connections (implement actual connection logic)"""
    # This would return actual database connections
    # For now, return None as placeholder
    return {
        'postgres': None,
        'neo4j': None,
        'qdrant': None,
        'redis': None
    }


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Intelligence Hub API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {}
    
    # Check Neo4j
    try:
        from neo4j import GraphDatabase
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'financehub123')
        
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        driver.verify_connectivity()
        driver.close()
        services['neo4j'] = 'healthy'
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        services['neo4j'] = 'unhealthy'
    
    # Check Qdrant
    try:
        from qdrant_client import QdrantClient
        qdrant_host = os.getenv('QDRANT_HOST', 'qdrant')
        qdrant_port = int(os.getenv('QDRANT_PORT', '6333'))
        
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        collections = client.get_collections()
        services['qdrant'] = 'healthy'
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        services['qdrant'] = 'unhealthy'
    
    # Check PostgreSQL
    try:
        import psycopg2
        pg_host = os.getenv('POSTGRES_HOST', 'postgres')
        pg_port = int(os.getenv('POSTGRES_PORT', '5432'))
        pg_user = os.getenv('POSTGRES_USER', 'fincenter')
        pg_password = os.getenv('POSTGRES_PASSWORD', 'fincenter_secure_pass')
        pg_db = os.getenv('POSTGRES_DB', 'fincenter')
        
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            database=pg_db,
            connect_timeout=3
        )
        conn.close()
        services['postgres'] = 'healthy'
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        services['postgres'] = 'unhealthy'
    
    # Check Redis
    try:
        import redis
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', 'redis_secure_pass')
        
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            socket_connect_timeout=3
        )
        r.ping()
        services['redis'] = 'healthy'
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services['redis'] = 'unhealthy'
    
    # Overall status
    all_healthy = all(status == 'healthy' for status in services.values())
    overall_status = 'healthy' if all_healthy else 'degraded'
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        services=services
    )


@app.post("/query", response_model=QueryResponse)
async def query_financial_data(request: QueryRequest):
    """
    Natural language query endpoint
    
    Process financial queries using hybrid retrieval and LLM
    """
    try:
        logger.info(f"Processing query: {request.question}")
        
        # This is a placeholder response
        # In production, initialize actual components and process query
        # QueryOrchestrator imported at module level for performance
        response = QueryResponse(
            query=request.question,
            query_type="general",
            answer="Query processing functionality requires LLM API key configuration. Please configure OPENAI_API_KEY in environment variables.",
            results={
                "vector_results": [],
                "graph_results": [],
                "combined_results": []
            },
            patterns=[]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
