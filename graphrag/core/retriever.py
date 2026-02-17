"""Hybrid retrieval combining vector and graph search."""
from typing import List, Dict, Any, Optional
from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .graph_store import GraphStore
from .llm import LLMService
from .episodic_memory import EpisodicMemory


class HybridRetriever:
    """Hybrid retrieval system combining vector and graph search."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        graph_store: GraphStore,
        llm_service: LLMService,
        episodic_memory: EpisodicMemory,
        top_k_vector: int = 5,
        top_k_graph: int = 5
    ):
        """Initialize the hybrid retriever.
        
        Args:
            embedding_service: Embedding service instance
            vector_store: Vector store instance
            graph_store: Graph store instance
            llm_service: LLM service instance
            episodic_memory: Episodic memory instance
            top_k_vector: Number of vector search results
            top_k_graph: Number of graph search results
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.llm_service = llm_service
        self.episodic_memory = episodic_memory
        self.top_k_vector = top_k_vector
        self.top_k_graph = top_k_graph
    
    def retrieve(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve relevant information using hybrid approach.
        
        Args:
            query: User query
            session_id: Optional session ID for episodic memory
            
        Returns:
            Dictionary containing vector results, graph results, and combined context
        """
        # Generate query embedding
        query_vector = self.embedding_service.embed_text(query)
        
        # Vector search
        vector_results = self.vector_store.search(query_vector, top_k=self.top_k_vector)
        
        # Graph search
        graph_results = self.graph_store.search_by_text(query, limit=self.top_k_graph)
        
        # Get episodic memory context if session provided
        episodic_context = ""
        if session_id:
            episodic_context = self.episodic_memory.get_recent_context(session_id, n=3)
        
        # Combine results
        combined_context = self._combine_results(vector_results, graph_results)
        
        return {
            "vector_results": vector_results,
            "graph_results": graph_results,
            "episodic_context": episodic_context,
            "combined_context": combined_context
        }
    
    def query(self, query: str, session_id: Optional[str] = None, 
             system_prompt: Optional[str] = None) -> str:
        """Query the system and get an answer.
        
        Args:
            query: User query
            session_id: Optional session ID for episodic memory
            system_prompt: Optional system prompt for the LLM
            
        Returns:
            Generated answer
        """
        # Retrieve relevant information
        retrieval_results = self.retrieve(query, session_id)
        
        # Prepare context
        context_parts = []
        
        if retrieval_results["episodic_context"]:
            context_parts.append(f"Previous conversation:\n{retrieval_results['episodic_context']}")
        
        context_parts.append(retrieval_results["combined_context"])
        
        # Generate answer
        answer = self.llm_service.generate_with_context(
            query=query,
            context=context_parts,
            system=system_prompt
        )
        
        # Store interaction in episodic memory
        if session_id:
            self.episodic_memory.add_interaction(
                session_id=session_id,
                query=query,
                response=answer,
                metadata={
                    "vector_results_count": len(retrieval_results["vector_results"]),
                    "graph_results_count": len(retrieval_results["graph_results"])
                }
            )
        
        return answer
    
    def _combine_results(self, vector_results: List[Dict[str, Any]], 
                        graph_results: List[Dict[str, Any]]) -> str:
        """Combine vector and graph results into a single context string.
        
        Args:
            vector_results: Results from vector search
            graph_results: Results from graph search
            
        Returns:
            Combined context string
        """
        context_parts = []
        
        # Add vector results
        if vector_results:
            context_parts.append("Vector Search Results:")
            for i, result in enumerate(vector_results):
                context_parts.append(f"{i+1}. {result['text']} (score: {result['score']:.3f})")
        
        # Add graph results
        if graph_results:
            context_parts.append("\nGraph Search Results:")
            for i, result in enumerate(graph_results):
                props = result['properties']
                labels = result.get('labels', [])
                context_parts.append(f"{i+1}. Labels: {labels}, Properties: {props}")
        
        return "\n".join(context_parts)
