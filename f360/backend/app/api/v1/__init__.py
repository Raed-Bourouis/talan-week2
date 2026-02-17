"""
F360 – API v1 Router Aggregation (7-Layer Architecture)
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.sources import router as sources_router
from app.api.v1.budget import router as budget_router
from app.api.v1.contracts import router as contracts_router
from app.api.v1.cashflow import router as cashflow_router
from app.api.v1.simulate import router as simulate_router
from app.api.v1.recommend import router as recommend_router
from app.api.v1.ragraph import router as ragraph_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.fusion import router as fusion_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.rag import router as rag_router

router = APIRouter()

# Layer 1 – Sources Multimodales
router.include_router(sources_router, prefix="/sources", tags=["L1 – Sources Multimodales"])

# Core financial CRUD
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(budget_router, prefix="/budget", tags=["Budget"])
router.include_router(contracts_router, prefix="/contracts", tags=["Contracts"])
router.include_router(cashflow_router, prefix="/cashflow", tags=["Cashflow"])

# Layer 3 – RAGraph
router.include_router(ragraph_router, prefix="/ragraph", tags=["L3 – RAGraph"])

# Layer 4 – Real-Time Feedback
router.include_router(feedback_router, prefix="/feedback", tags=["L4 – Real-Time Feedback"])

# Layer 5 – Scenario Simulation
router.include_router(simulate_router, prefix="/simulate", tags=["L5 – Simulation"])

# Layer 6 & 7 – Decision Fusion & Recommendation
router.include_router(fusion_router, prefix="/fusion", tags=["L6/L7 – Fusion & Decisions"])
router.include_router(recommend_router, prefix="/recommendations", tags=["Recommendations"])

# Layer 2 – Cognitive Ingestion
router.include_router(ingest_router, prefix="/ingest", tags=["L2 – Ingestion"])

# RAG (separate from RAGraph)
router.include_router(rag_router, prefix="/rag", tags=["RAG"])
