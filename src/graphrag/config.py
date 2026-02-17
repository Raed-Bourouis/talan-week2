"""
GraphRAG Configuration
======================
Configuration management for the GraphRAG component.
Uses environment variables with sensible defaults.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class GraphRAGConfig(BaseSettings):
    """Configuration for GraphRAG component."""
    
    # ── Graph Database (Neo4j) ──
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    neo4j_max_connection_lifetime: int = 3600
    neo4j_max_connection_pool_size: int = 50
    neo4j_connection_timeout: int = 30
    
    # ── LLM Provider ──
    llm_provider: str = "openai"  # openai, mistral, local
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 2000
    
    # Mistral (alternative)
    mistral_api_key: Optional[str] = None
    mistral_model: str = "mistral-large-latest"
    
    # Local models (Ollama, etc.)
    local_llm_url: str = "http://localhost:11434"
    local_llm_model: str = "mistral"
    
    # ── Vector Store ──
    vector_store_type: str = "pgvector"  # pgvector, chromadb, qdrant
    vector_dimension: int = 1536
    vector_similarity_threshold: float = 0.7
    
    # ChromaDB (alternative)
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    chromadb_collection_name: str = "financial_documents"
    
    # ── Episodic Memory ──
    episodic_memory_max_episodes: int = 1000
    episodic_memory_recall_top_k: int = 3
    episodic_memory_min_similarity: float = 0.5
    episodic_memory_enable_persistence: bool = True
    
    # ── RAG Orchestration ──
    rag_default_top_k: int = 5
    rag_max_top_k: int = 20
    rag_use_hybrid_search: bool = True
    rag_reranking_enabled: bool = False
    rag_context_window_size: int = 4000
    
    # ── Knowledge Graph ──
    kg_max_traversal_depth: int = 3
    kg_cache_enabled: bool = True
    kg_cache_ttl: int = 300  # seconds
    
    # ── Logging ──
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ── Performance ──
    enable_query_cache: bool = True
    cache_ttl_seconds: int = 600
    max_concurrent_queries: int = 10
    query_timeout_seconds: int = 30
    
    # ── Security ──
    enable_query_validation: bool = True
    max_query_length: int = 5000
    allowed_entity_types: Optional[list[str]] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_llm_config(self) -> dict[str, any]:
        """Get LLM configuration based on provider."""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "temperature": self.openai_temperature,
                "max_tokens": self.openai_max_tokens,
            }
        elif self.llm_provider == "mistral":
            return {
                "provider": "mistral",
                "api_key": self.mistral_api_key,
                "model": self.mistral_model,
            }
        elif self.llm_provider == "local":
            return {
                "provider": "local",
                "url": self.local_llm_url,
                "model": self.local_llm_model,
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def get_neo4j_config(self) -> dict[str, any]:
        """Get Neo4j configuration."""
        return {
            "uri": self.neo4j_uri,
            "auth": (self.neo4j_user, self.neo4j_password),
            "database": self.neo4j_database,
            "max_connection_lifetime": self.neo4j_max_connection_lifetime,
            "max_connection_pool_size": self.neo4j_max_connection_pool_size,
            "connection_timeout": self.neo4j_connection_timeout,
        }
    
    def validate_config(self) -> None:
        """Validate configuration."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
        
        if self.llm_provider == "mistral" and not self.mistral_api_key:
            raise ValueError("Mistral API key is required when using Mistral provider")
        
        if self.episodic_memory_max_episodes < 1:
            raise ValueError("episodic_memory_max_episodes must be at least 1")
        
        if not (0.0 <= self.vector_similarity_threshold <= 1.0):
            raise ValueError("vector_similarity_threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= self.openai_temperature <= 2.0):
            raise ValueError("openai_temperature must be between 0.0 and 2.0")


@lru_cache()
def get_config() -> GraphRAGConfig:
    """Get cached configuration instance."""
    return GraphRAGConfig()
