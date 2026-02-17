# Changelog

All notable changes to the GraphRAG project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-02-17

### Added
- Initial release of GraphRAG system
- Core components:
  - Embedding service using sentence-transformers
  - Vector store integration with Qdrant
  - Graph database integration with Neo4j
  - LLM service using Ollama with Llama 3.1
  - Redis episodic memory for conversation tracking
  - Hybrid retriever combining vector and graph search
- Python SDK with clean, intuitive interface
- FastAPI REST API with full CRUD operations
- Docker Compose configuration for all services
- Comprehensive documentation:
  - README with quick start guide
  - API documentation
  - Architecture documentation
  - Testing guide
- Example scripts:
  - Basic usage example
  - Advanced usage with knowledge graphs
  - REST API client example
- Unit tests for core components
- Integration tests for SDK
- Makefile for common operations
- Quick start script
- Contributing guidelines
- MIT License

### Security
- Updated FastAPI to 0.109.1 (fixes ReDoS vulnerability)
- Updated qdrant-client to 1.9.0 (fixes input validation)
- Updated torch to 2.6.0 (fixes heap buffer overflow, use-after-free, and RCE vulnerabilities)

### Features
- 100% free operation (no API keys required)
- Domain-agnostic design
- Modular architecture
- Full Docker containerization
- Conversation history tracking
- Multi-turn conversation support
- Metadata support for documents and relationships
- Health check endpoint
- CORS support for API
- Automatic API documentation

### Dependencies
- FastAPI 0.109.1 (security patch)
- Qdrant Client 1.9.0 (security patch)
- Neo4j 5.16.0
- sentence-transformers 2.3.1
- Ollama 0.1.6
- Redis 5.0.1
- PyTorch 2.6.0 (security patch)

## [Unreleased]

### Planned Features
- Query result caching
- Batch processing utilities
- Web UI dashboard
- Advanced graph algorithms
- Multi-modal support (images, audio)
- Fine-tuning capabilities
- Performance monitoring dashboard
- Rate limiting
- Authentication and authorization
- Model versioning
- A/B testing framework
