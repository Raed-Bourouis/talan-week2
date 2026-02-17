"""
GraphRAG - Financial Knowledge Graph and RAG Component
========================================================

A modular, production-ready GraphRAG implementation for financial intelligence.

This component provides:
- Financial entity modeling (clients, contracts, invoices, budgets, etc.)
- Knowledge graph construction and traversal (Neo4j-based)
- Episodic memory for recalling past financial patterns
- LLM-powered reasoning with chain-of-thought capabilities
- RAG orchestration combining vector search, graph traversal, and episodic memory

## Quick Start

```python
from graphrag import RAGOrchestrator, RAGQuery, KnowledgeGraphBuilder
from graphrag.models import Contract, Client, EntityType
from datetime import date
from decimal import Decimal

# Initialize orchestrator
orchestrator = RAGOrchestrator()
await orchestrator.initialize()

# Ask a financial question
query = RAGQuery(
    question="Which contracts contain penalty clauses indexed to inflation?",
    use_vector_search=True,
    use_graph_traversal=True,
    use_episodic_memory=True,
)

response = await orchestrator.query(query)
print(response.answer)
print(f"Confidence: {response.confidence}")
print(f"Sources: {len(response.sources)}")

# Add entities to knowledge graph
kg = KnowledgeGraphBuilder()
await kg.initialize()

client = Client(
    name="Acme Corp",
    company_name="Acme Corporation",
    contact_email="contact@acme.com",
)

contract = Contract(
    name="Annual Service Agreement 2024",
    reference="CTR-2024-001",
    title="Annual Software Maintenance",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    total_amount=Decimal("50000.00"),
)

# Add with automatic relationship
contract_id, client_id = await kg.add_contract_with_client(contract, client)
```

## Architecture

The GraphRAG component follows a layered architecture:

1. **Models Layer** (`models.py`) - Pydantic data models for all financial entities
2. **Storage Layer** (`graph_store.py`) - Abstract graph database interface with Neo4j implementation
3. **Domain Layer** (`knowledge_graph.py`) - High-level knowledge graph operations
4. **Memory Layer** (`episodic_memory.py`) - Financial episodic memory and pattern detection
5. **Reasoning Layer** (`llm_reasoning.py`) - LLM-powered financial analysis
6. **Orchestration Layer** (`rag_orchestrator.py`) - Multi-source RAG pipeline

## Configuration

Configuration is managed via environment variables or a `.env` file:

```
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM Provider (openai, mistral, local)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# RAG Settings
RAG_DEFAULT_TOP_K=5
EPISODIC_MEMORY_MAX_EPISODES=1000
```

See `.env.example` for all available options.

## Public API

### Core Classes
- `RAGOrchestrator` - Main entry point for RAG queries
- `KnowledgeGraphBuilder` - High-level knowledge graph operations
- `EpisodicMemory` - Financial episodic memory management
- `ReasoningEngine` - LLM reasoning capabilities

### Models
- Entity models: `Client`, `Supplier`, `Contract`, `Invoice`, `BudgetEntry`, `Department`, `Project`, `Clause`
- Query models: `RAGQuery`, `GraphQuery`
- Response models: `RAGResponse`
- Episode models: `FinancialEpisode`, `FinancialPattern`

### Enums
- `EntityType` - Types of financial entities
- `RelationshipType` - Types of relationships between entities
- `ContractStatus`, `InvoiceStatus`, `ClauseType` - Entity-specific statuses

## Integration with Other Layers

### Layer 1 & 2: Ingestion and Vectorization
```python
# After ingesting and vectorizing documents, they become available
# for vector search in the RAG pipeline automatically
```

### Layer 4: Real-Time Feedback
```python
# When feedback indicates an issue, store it as an episode
from graphrag.models import FinancialEpisode
from datetime import datetime

episode = episodic_memory.create_episode_from_event(
    title="Budget overrun detected in IT department",
    description="Q4 IT budget exceeded by 15%",
    event_type="budget_overrun",
    entities_involved=[department_id, budget_id],
    context={"variance_pct": 15, "quarter": "Q4"},
    tags=["budget", "overrun", "IT"],
)
episodic_memory.store_episode(episode)
```

### Layer 5: Simulation
```python
# Use RAG to analyze simulation results
query = RAGQuery(
    question="Based on past trends, what's the likely outcome of this budget scenario?",
    use_episodic_memory=True,
)
response = await orchestrator.query(query)
```

## Testing

```bash
# Run unit tests
pytest tests/test_graphrag/ -v

# Run with coverage
pytest tests/test_graphrag/ --cov=src/graphrag --cov-report=html
```

## License

MIT
"""

# Version
__version__ = "1.0.0"

# Core exports
from .config import GraphRAGConfig, get_config
from .episodic_memory import EpisodicMemory
from .graph_store import GraphStore, Neo4jGraphStore, create_graph_store
from .knowledge_graph import KnowledgeGraphBuilder
from .llm_reasoning import ReasoningEngine, LLMProvider, OpenAIProvider, LocalLLMProvider
from .rag_orchestrator import RAGOrchestrator

# Models
from .models import (
    # Base models
    FinancialEntity,
    Relationship,
    # Entity models
    Client,
    Supplier,
    Contract,
    Invoice,
    BudgetEntry,
    AccountingEntry,
    Department,
    Project,
    Clause,
    # Episodic memory models
    FinancialEpisode,
    FinancialPattern,
    # Query models
    GraphQuery,
    RAGQuery,
    RAGResponse,
    # Enums
    EntityType,
    RelationshipType,
    ContractStatus,
    InvoiceStatus,
    ClauseType,
)

# Exceptions
from .exceptions import (
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

__all__ = [
    # Version
    "__version__",
    # Config
    "GraphRAGConfig",
    "get_config",
    # Core components
    "RAGOrchestrator",
    "KnowledgeGraphBuilder",
    "EpisodicMemory",
    "ReasoningEngine",
    "GraphStore",
    "Neo4jGraphStore",
    "create_graph_store",
    # LLM Providers
    "LLMProvider",
    "OpenAIProvider",
    "LocalLLMProvider",
    # Base models
    "FinancialEntity",
    "Relationship",
    # Entity models
    "Client",
    "Supplier",
    "Contract",
    "Invoice",
    "BudgetEntry",
    "AccountingEntry",
    "Department",
    "Project",
    "Clause",
    # Episodic memory
    "FinancialEpisode",
    "FinancialPattern",
    # Query models
    "GraphQuery",
    "RAGQuery",
    "RAGResponse",
    # Enums
    "EntityType",
    "RelationshipType",
    "ContractStatus",
    "InvoiceStatus",
    "ClauseType",
    # Exceptions
    "GraphRAGException",
    "ConfigurationError",
    "GraphStoreError",
    "GraphConnectionError",
    "EntityNotFoundError",
    "RelationshipNotFoundError",
    "DuplicateEntityError",
    "ValidationError",
    "EpisodicMemoryError",
    "KnowledgeGraphError",
    "RAGOrchestrationError",
    "LLMReasoningError",
    "VectorSearchError",
    "QueryExecutionError",
]
