"""FastAPI REST API for GraphRAG system."""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import logging

from .models import (
    DocumentInput,
    DocumentResponse,
    NodeInput,
    NodeResponse,
    RelationshipInput,
    QueryInput,
    QueryResponse,
    RetrievalResponse,
    HealthResponse,
)
from ..sdk import GraphRAG
from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global GraphRAG instance
graphrag_instance: GraphRAG = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global graphrag_instance
    
    # Startup
    logger.info("Initializing GraphRAG system...")
    graphrag_instance = GraphRAG()
    logger.info("GraphRAG system initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GraphRAG system...")
    if graphrag_instance:
        graphrag_instance.close()
    logger.info("GraphRAG system shut down")


# Create FastAPI app
app = FastAPI(
    title="GraphRAG API",
    description="REST API for GraphRAG system with hybrid retrieval (vector + graph)",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "GraphRAG API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check the health of the system and its services."""
    services_status = {
        "vector_store": True,
        "graph_store": True,
        "llm": True,
        "redis": True,
    }
    
    try:
        # Test vector store
        graphrag_instance.vector_store.client.get_collections()
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        services_status["vector_store"] = False
    
    try:
        # Test graph store
        with graphrag_instance.graph_store.driver.session() as session:
            session.run("RETURN 1")
    except Exception as e:
        logger.error(f"Graph store health check failed: {e}")
        services_status["graph_store"] = False
    
    try:
        # Test Redis
        graphrag_instance.episodic_memory.client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services_status["redis"] = False
    
    all_healthy = all(services_status.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        services=services_status
    )


@app.post("/documents", response_model=DocumentResponse, tags=["Documents"])
async def add_documents(input_data: DocumentInput):
    """Add documents to the vector store."""
    try:
        ids = graphrag_instance.add_documents(input_data.texts, input_data.metadata)
        return DocumentResponse(ids=ids)
    except Exception as e:
        logger.error(f"Error adding documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add documents: {str(e)}"
        )


@app.post("/nodes", response_model=NodeResponse, tags=["Knowledge Graph"])
async def add_node(input_data: NodeInput):
    """Add a knowledge node to the graph."""
    try:
        node_id = graphrag_instance.add_knowledge_node(
            input_data.label,
            input_data.properties
        )
        return NodeResponse(id=node_id)
    except Exception as e:
        logger.error(f"Error adding node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add node: {str(e)}"
        )


@app.post("/relationships", status_code=status.HTTP_201_CREATED, tags=["Knowledge Graph"])
async def add_relationship(input_data: RelationshipInput):
    """Add a relationship between two knowledge nodes."""
    try:
        graphrag_instance.add_relationship(
            input_data.source_id,
            input_data.target_id,
            input_data.rel_type,
            input_data.properties
        )
        return {"message": "Relationship added successfully"}
    except Exception as e:
        logger.error(f"Error adding relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add relationship: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(input_data: QueryInput):
    """Query the GraphRAG system and get an answer."""
    try:
        answer = graphrag_instance.query(input_data.query, input_data.session_id)
        return QueryResponse(answer=answer, session_id=input_data.session_id)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@app.post("/retrieve", response_model=RetrievalResponse, tags=["Query"])
async def retrieve(input_data: QueryInput):
    """Retrieve relevant information without generating an answer."""
    try:
        results = graphrag_instance.retrieve(input_data.query, input_data.session_id)
        return RetrievalResponse(**results)
    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve information: {str(e)}"
        )


@app.get("/conversations/{session_id}", tags=["Conversations"])
async def get_conversation_history(session_id: str, limit: int = None):
    """Get conversation history for a session."""
    try:
        history = graphrag_instance.get_conversation_history(session_id, limit)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@app.delete("/conversations/{session_id}", tags=["Conversations"])
async def clear_conversation(session_id: str):
    """Clear conversation history for a session."""
    try:
        graphrag_instance.clear_conversation(session_id)
        return {"message": f"Conversation {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear conversation: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
