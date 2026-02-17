"""Python SDK for GraphRAG system."""
from typing import List, Dict, Any, Optional
from ..core import (
    EmbeddingService,
    VectorStore,
    GraphStore,
    LLMService,
    EpisodicMemory,
    HybridRetriever,
)
from ..config import settings


class GraphRAG:
    """Main SDK class for interacting with the GraphRAG system."""
    
    def __init__(
        self,
        qdrant_host: Optional[str] = None,
        qdrant_port: Optional[int] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        ollama_host: Optional[str] = None,
        ollama_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """Initialize the GraphRAG SDK.
        
        Args:
            qdrant_host: Qdrant host (uses settings if not provided)
            qdrant_port: Qdrant port (uses settings if not provided)
            neo4j_uri: Neo4j URI (uses settings if not provided)
            neo4j_user: Neo4j user (uses settings if not provided)
            neo4j_password: Neo4j password (uses settings if not provided)
            redis_host: Redis host (uses settings if not provided)
            redis_port: Redis port (uses settings if not provided)
            ollama_host: Ollama host (uses settings if not provided)
            ollama_model: Ollama model (uses settings if not provided)
            embedding_model: Embedding model (uses settings if not provided)
        """
        # Initialize services with provided values or settings defaults
        self.embedding_service = EmbeddingService(
            model_name=embedding_model or settings.embedding_model
        )
        
        self.vector_store = VectorStore(
            host=qdrant_host or settings.qdrant_host,
            port=qdrant_port or settings.qdrant_port,
            collection_name=settings.qdrant_collection
        )
        
        self.graph_store = GraphStore(
            uri=neo4j_uri or settings.neo4j_uri,
            user=neo4j_user or settings.neo4j_user,
            password=neo4j_password or settings.neo4j_password
        )
        
        self.llm_service = LLMService(
            host=ollama_host or settings.ollama_host,
            model=ollama_model or settings.ollama_model
        )
        
        self.episodic_memory = EpisodicMemory(
            host=redis_host or settings.redis_host,
            port=redis_port or settings.redis_port,
            db=settings.redis_db
        )
        
        self.retriever = HybridRetriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            graph_store=self.graph_store,
            llm_service=self.llm_service,
            episodic_memory=self.episodic_memory,
            top_k_vector=settings.top_k_vector,
            top_k_graph=settings.top_k_graph
        )
        
        # Initialize vector collection
        self.vector_store.create_collection(self.embedding_service.get_dimension())
    
    def add_documents(self, texts: List[str], 
                     metadata: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            texts: List of document texts
            metadata: Optional metadata for each document
            
        Returns:
            List of document IDs
        """
        embeddings = self.embedding_service.embed_batch(texts)
        return self.vector_store.add_vectors(embeddings, texts, metadata)
    
    def add_knowledge_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Add a knowledge node to the graph.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            Node ID
        """
        return self.graph_store.add_node(label, properties)
    
    def add_relationship(self, source_id: str, target_id: str, 
                        rel_type: str, properties: Optional[Dict[str, Any]] = None):
        """Add a relationship between two knowledge nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_type: Relationship type
            properties: Optional relationship properties
        """
        self.graph_store.add_relationship(source_id, target_id, rel_type, properties)
    
    def query(self, query: str, session_id: Optional[str] = None) -> str:
        """Query the GraphRAG system.
        
        Args:
            query: User query
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Generated answer
        """
        return self.retriever.query(query, session_id)
    
    def retrieve(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve relevant information without generating an answer.
        
        Args:
            query: User query
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Retrieval results
        """
        return self.retriever.retrieve(query, session_id)
    
    def get_conversation_history(self, session_id: str, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of interactions
            
        Returns:
            List of interactions
        """
        return self.episodic_memory.get_session_history(session_id, limit)
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        self.episodic_memory.clear_session(session_id)
    
    def close(self):
        """Close all connections."""
        self.graph_store.close()
