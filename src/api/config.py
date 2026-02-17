"""Configuration management."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # GraphRAG Configuration
    graphrag_storage_path: str = "./data/graphrag"
    graphrag_embedding_model: str = "llama2"
    
    # Document Processing
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: str = ".pdf,.docx,.xlsx"
    
    # Logging
    log_level: str = "INFO"
    
    # Embedding Configuration
    embedding_dimension: int = 4096  # Default for llama2


settings = Settings()
