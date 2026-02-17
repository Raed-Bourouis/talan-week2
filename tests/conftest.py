"""Test configuration."""
import pytest


@pytest.fixture(scope="session")
def test_config():
    """Test configuration."""
    return {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama2",
    }
