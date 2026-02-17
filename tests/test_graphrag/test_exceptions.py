"""Tests for custom exceptions."""
import pytest
from uuid import uuid4

from graphrag.exceptions import (
    GraphRAGException,
    ConfigurationError,
    GraphStoreError,
    GraphConnectionError,
    EntityNotFoundError,
    RelationshipNotFoundError,
    DuplicateEntityError,
    ValidationError,
    EpisodicMemoryError,
    KnowledgeGraphError,
    RAGOrchestrationError,
    LLMReasoningError,
    VectorSearchError,
    QueryExecutionError,
)


class TestExceptions:
    """Test custom exception classes."""
    
    def test_base_exception(self):
        """Test base GraphRAG exception."""
        exc = GraphRAGException("Test error", {"key": "value"})
        
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}
    
    def test_configuration_error(self):
        """Test configuration error."""
        exc = ConfigurationError("Invalid config")
        
        assert isinstance(exc, GraphRAGException)
        assert "Invalid config" in str(exc)
    
    def test_entity_not_found_error(self):
        """Test entity not found error."""
        entity_id = str(uuid4())
        exc = EntityNotFoundError(entity_id, "contract")
        
        assert entity_id in str(exc)
        assert "contract" in str(exc)
        assert exc.details["entity_id"] == entity_id
        assert exc.details["entity_type"] == "contract"
    
    def test_entity_not_found_error_no_type(self):
        """Test entity not found error without type."""
        entity_id = str(uuid4())
        exc = EntityNotFoundError(entity_id)
        
        assert entity_id in str(exc)
        assert exc.details["entity_type"] is None
    
    def test_relationship_not_found_error(self):
        """Test relationship not found error."""
        rel_id = "rel-123"
        exc = RelationshipNotFoundError(rel_id)
        
        assert rel_id in str(exc)
        assert exc.details["relationship_id"] == rel_id
    
    def test_duplicate_entity_error(self):
        """Test duplicate entity error."""
        entity_id = str(uuid4())
        exc = DuplicateEntityError(entity_id, "client")
        
        assert entity_id in str(exc)
        assert "client" in str(exc)
        assert "already exists" in str(exc)
    
    def test_graph_connection_error(self):
        """Test graph connection error."""
        exc = GraphConnectionError(
            "Could not connect to Neo4j",
            {"uri": "bolt://localhost:7687"}
        )
        
        assert isinstance(exc, GraphStoreError)
        assert "Could not connect" in str(exc)
        assert exc.details["uri"] == "bolt://localhost:7687"
    
    def test_validation_error(self):
        """Test validation error."""
        exc = ValidationError("Invalid data format")
        
        assert isinstance(exc, GraphRAGException)
        assert "Invalid data format" in str(exc)
    
    def test_episodic_memory_error(self):
        """Test episodic memory error."""
        exc = EpisodicMemoryError("Memory storage failed")
        
        assert isinstance(exc, GraphRAGException)
        assert "Memory storage failed" in str(exc)
    
    def test_knowledge_graph_error(self):
        """Test knowledge graph error."""
        exc = KnowledgeGraphError("Graph operation failed")
        
        assert isinstance(exc, GraphRAGException)
        assert "Graph operation failed" in str(exc)
    
    def test_rag_orchestration_error(self):
        """Test RAG orchestration error."""
        exc = RAGOrchestrationError("Query orchestration failed")
        
        assert isinstance(exc, GraphRAGException)
        assert "Query orchestration failed" in str(exc)
    
    def test_llm_reasoning_error(self):
        """Test LLM reasoning error."""
        exc = LLMReasoningError("LLM API call failed")
        
        assert isinstance(exc, GraphRAGException)
        assert "LLM API call failed" in str(exc)
    
    def test_vector_search_error(self):
        """Test vector search error."""
        exc = VectorSearchError("Vector index not found")
        
        assert isinstance(exc, GraphRAGException)
        assert "Vector index not found" in str(exc)
    
    def test_query_execution_error(self):
        """Test query execution error."""
        exc = QueryExecutionError("Query timeout")
        
        assert isinstance(exc, GraphRAGException)
        assert "Query timeout" in str(exc)
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from GraphRAGException."""
        exceptions = [
            ConfigurationError,
            GraphStoreError,
            GraphConnectionError,
            EntityNotFoundError,
            RelationshipNotFoundError,
            DuplicateEntityError,
            ValidationError,
            EpisodicMemoryError,
            KnowledgeGraphError,
            RAGOrchestrationError,
            LLMReasoningError,
            VectorSearchError,
            QueryExecutionError,
        ]
        
        for exc_class in exceptions:
            exc = exc_class("Test")
            assert isinstance(exc, GraphRAGException)
            assert isinstance(exc, Exception)
