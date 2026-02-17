"""
GraphRAG Custom Exceptions
===========================
Custom exception classes for the GraphRAG component.
"""
from typing import Any, Optional


class GraphRAGException(Exception):
    """Base exception for GraphRAG component."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(GraphRAGException):
    """Raised when configuration is invalid or missing."""
    pass


class GraphStoreError(GraphRAGException):
    """Raised when graph database operations fail."""
    pass


class GraphConnectionError(GraphStoreError):
    """Raised when unable to connect to graph database."""
    pass


class EntityNotFoundError(GraphRAGException):
    """Raised when requested entity does not exist."""
    
    def __init__(self, entity_id: str, entity_type: Optional[str] = None):
        message = f"Entity {entity_id} not found"
        if entity_type:
            message += f" (type: {entity_type})"
        details = {"entity_id": entity_id, "entity_type": entity_type}
        super().__init__(message, details)


class RelationshipNotFoundError(GraphRAGException):
    """Raised when requested relationship does not exist."""
    
    def __init__(self, relationship_id: str):
        message = f"Relationship {relationship_id} not found"
        details = {"relationship_id": relationship_id}
        super().__init__(message, details)


class DuplicateEntityError(GraphRAGException):
    """Raised when attempting to create a duplicate entity."""
    
    def __init__(self, entity_id: str, entity_type: Optional[str] = None):
        message = f"Entity {entity_id} already exists"
        if entity_type:
            message += f" (type: {entity_type})"
        details = {"entity_id": entity_id, "entity_type": entity_type}
        super().__init__(message, details)


class ValidationError(GraphRAGException):
    """Raised when data validation fails."""
    pass


class EpisodicMemoryError(GraphRAGException):
    """Raised when episodic memory operations fail."""
    pass


class KnowledgeGraphError(GraphRAGException):
    """Raised when knowledge graph operations fail."""
    pass


class RAGOrchestrationError(GraphRAGException):
    """Raised when RAG orchestration fails."""
    pass


class LLMReasoningError(GraphRAGException):
    """Raised when LLM reasoning fails."""
    pass


class VectorSearchError(GraphRAGException):
    """Raised when vector search operations fail."""
    pass


class QueryExecutionError(GraphRAGException):
    """Raised when query execution fails."""
    pass
