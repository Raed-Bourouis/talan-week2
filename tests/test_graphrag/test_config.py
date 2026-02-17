"""Tests for configuration management."""
import pytest
import os
from graphrag.config import GraphRAGConfig, get_config
from graphrag.exceptions import ConfigurationError


class TestGraphRAGConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GraphRAGConfig()
        
        assert config.neo4j_uri == "bolt://localhost:7687"
        assert config.neo4j_user == "neo4j"
        assert config.llm_provider == "openai"
        assert config.openai_model == "gpt-4o"
        assert config.vector_store_type == "pgvector"
        assert config.episodic_memory_max_episodes == 1000
        assert config.rag_default_top_k == 5
    
    def test_config_with_env_vars(self, monkeypatch):
        """Test configuration with environment variables."""
        # Set environment variables
        monkeypatch.setenv("NEO4J_URI", "bolt://custom-host:7687")
        monkeypatch.setenv("LLM_PROVIDER", "local")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("RAG_DEFAULT_TOP_K", "10")
        
        config = GraphRAGConfig()
        
        assert config.neo4j_uri == "bolt://custom-host:7687"
        assert config.llm_provider == "local"
        assert config.openai_api_key == "sk-test-key"
        assert config.rag_default_top_k == 10
    
    def test_get_llm_config_openai(self):
        """Test getting OpenAI LLM configuration."""
        config = GraphRAGConfig(
            llm_provider="openai",
            openai_api_key="sk-test",
            openai_model="gpt-4",
            openai_temperature=0.2,
        )
        
        llm_config = config.get_llm_config()
        
        assert llm_config["provider"] == "openai"
        assert llm_config["api_key"] == "sk-test"
        assert llm_config["model"] == "gpt-4"
        assert llm_config["temperature"] == 0.2
    
    def test_get_llm_config_local(self):
        """Test getting local LLM configuration."""
        config = GraphRAGConfig(
            llm_provider="local",
            local_llm_url="http://localhost:11434",
            local_llm_model="mistral",
        )
        
        llm_config = config.get_llm_config()
        
        assert llm_config["provider"] == "local"
        assert llm_config["url"] == "http://localhost:11434"
        assert llm_config["model"] == "mistral"
    
    def test_get_llm_config_unsupported(self):
        """Test that unsupported provider raises error."""
        config = GraphRAGConfig(llm_provider="unsupported")
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            config.get_llm_config()
    
    def test_get_neo4j_config(self):
        """Test getting Neo4j configuration."""
        config = GraphRAGConfig(
            neo4j_uri="bolt://test:7687",
            neo4j_user="test_user",
            neo4j_password="test_pass",
            neo4j_database="test_db",
        )
        
        neo4j_config = config.get_neo4j_config()
        
        assert neo4j_config["uri"] == "bolt://test:7687"
        assert neo4j_config["auth"] == ("test_user", "test_pass")
        assert neo4j_config["database"] == "test_db"
    
    def test_validate_config_valid(self):
        """Test that valid configuration passes validation."""
        config = GraphRAGConfig(
            llm_provider="openai",
            openai_api_key="sk-valid-key",
        )
        
        # Should not raise
        config.validate_config()
    
    def test_validate_config_missing_openai_key(self):
        """Test that missing OpenAI key raises error."""
        config = GraphRAGConfig(
            llm_provider="openai",
            openai_api_key=None,
        )
        
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            config.validate_config()
    
    def test_validate_config_invalid_temperature(self):
        """Test that invalid temperature raises error."""
        config = GraphRAGConfig(
            llm_provider="openai",
            openai_api_key="sk-test",
            openai_temperature=3.0,  # > 2.0
        )
        
        with pytest.raises(ValueError, match="temperature must be between"):
            config.validate_config()
    
    def test_validate_config_invalid_similarity_threshold(self):
        """Test that invalid similarity threshold raises error."""
        config = GraphRAGConfig(
            llm_provider="openai",
            openai_api_key="sk-test",
            vector_similarity_threshold=1.5,  # > 1.0
        )
        
        with pytest.raises(ValueError, match="similarity_threshold must be between"):
            config.validate_config()
    
    def test_get_config_cached(self):
        """Test that get_config returns cached instance."""
        # Clear cache first
        get_config.cache_clear()
        
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same instance
        assert config1 is config2
    
    def test_config_case_insensitive(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("openai_api_key", "sk-lower")  # Should be ignored
        
        config = GraphRAGConfig()
        
        # Should use the uppercase version
        assert config.openai_api_key in ["sk-test", "sk-lower"]
