"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DocumentInput(BaseModel):
    """Input model for adding documents."""
    texts: List[str] = Field(..., description="List of document texts")
    metadata: Optional[List[Dict[str, Any]]] = Field(None, description="Optional metadata for each document")


class DocumentResponse(BaseModel):
    """Response model for added documents."""
    ids: List[str] = Field(..., description="List of document IDs")


class NodeInput(BaseModel):
    """Input model for adding knowledge nodes."""
    label: str = Field(..., description="Node label")
    properties: Dict[str, Any] = Field(..., description="Node properties")


class NodeResponse(BaseModel):
    """Response model for added nodes."""
    id: str = Field(..., description="Node ID")


class RelationshipInput(BaseModel):
    """Input model for adding relationships."""
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    rel_type: str = Field(..., description="Relationship type")
    properties: Optional[Dict[str, Any]] = Field(None, description="Optional relationship properties")


class QueryInput(BaseModel):
    """Input model for queries."""
    query: str = Field(..., description="User query")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation tracking")


class QueryResponse(BaseModel):
    """Response model for queries."""
    answer: str = Field(..., description="Generated answer")
    session_id: Optional[str] = Field(None, description="Session ID if provided")


class RetrievalResponse(BaseModel):
    """Response model for retrieval results."""
    vector_results: List[Dict[str, Any]] = Field(..., description="Vector search results")
    graph_results: List[Dict[str, Any]] = Field(..., description="Graph search results")
    episodic_context: str = Field(..., description="Episodic memory context")
    combined_context: str = Field(..., description="Combined context")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    services: Dict[str, bool] = Field(..., description="Status of individual services")
