"""Configuration management for GraphRAG system."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "GraphRAG System"
    debug: bool = False
    
    # Qdrant Vector Store
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "graphrag_vectors"
    
    # Neo4j Graph Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Redis Episodic Memory
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Ollama LLM
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Retrieval
    top_k_vector: int = 5
    top_k_graph: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
