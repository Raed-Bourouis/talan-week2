"""
F360 – Financial Command Center
Main FastAPI Application Entry Point
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.neo4j_client import close_neo4j_driver
from app.api.v1 import router as api_v1_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # ── Startup ──
    settings.upload_path  # ensure upload directory exists
    yield
    # ── Shutdown ──
    await close_neo4j_driver()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-native financial intelligence platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
