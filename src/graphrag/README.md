# GraphRAG - Financial Knowledge Graph & RAG Component

> **Layer 3** of the F360 Financial Command Center — Episodic memory, knowledge graph-enhanced RAG pipeline, and LLM reasoning for financial intelligence.

## Overview

GraphRAG is a modular, production-ready component that provides comprehensive financial intelligence through the combination of:

- **Knowledge Graph**: Structured financial entity relationships (Neo4j-based)
- **Episodic Memory**: Historical pattern recall and learning from past interactions
- **Vector Search Integration**: Semantic similarity search (pluggable backends)
- **LLM Reasoning**: Provider-agnostic AI reasoning (OpenAI, Mistral, local models)
- **RAG Orchestration**: Multi-source context aggregation and intelligent answering

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Orchestrator                        │
│  (Multi-source query orchestration & answer generation)      │
└────────────┬─────────────┬──────────────┬───────────────────┘
             │             │              │
    ┌────────▼────┐  ┌─────▼──────┐  ┌───▼────────────┐
    │   Vector    │  │ Knowledge  │  │   Episodic     │
    │   Search    │  │   Graph    │  │    Memory      │
    │ (pgvector/  │  │  (Neo4j)   │  │  (Patterns &   │
    │  ChromaDB)  │  │            │  │   Episodes)    │
    └─────────────┘  └────────────┘  └────────────────┘
                            │
                    ┌───────▼────────┐
                    │  LLM Reasoning │
                    │  (OpenAI/      │
                    │   Mistral/     │
                    │   Local)       │
                    └────────────────┘
```

## Features

### ✅ Modular Design
- Clean interfaces with abstract base classes
- Dependency injection for easy testing and integration
- Pluggable LLM providers (OpenAI, Mistral, local models)
- Pluggable graph stores (Neo4j, extensible to others)

### ✅ Financial Entity Models
Comprehensive Pydantic models for:
- Clients, Suppliers, Contracts, Invoices
- Budget Entries, Accounting Entries
- Departments, Projects, Clauses
- All with full type safety and validation

### ✅ Knowledge Graph Operations
- CRUD operations on entities and relationships
- Graph traversal with configurable depth and filters
- Domain-specific queries:
  - Find contracts with penalty clauses
  - Track client payment history
  - Monitor department budget status
  - Analyze supplier performance

### ✅ Episodic Memory
- Store and recall past financial events
- Pattern detection (late payments, budget overruns, seasonal trends)
- Temporal queries (what happened last Q4?)
- Similarity-based retrieval

### ✅ LLM Reasoning
- Chain-of-thought reasoning for complex questions
- Anomaly detection and analysis
- Financial period summarization
- Actionable recommendation generation

### ✅ RAG Orchestration
- Combines vector search + graph traversal + episodic memory
- Configurable retrieval strategies
- Automatic confidence scoring
- Stores all interactions for future learning

## Installation

### Prerequisites
- Python 3.11+
- Neo4j 5.x (for graph database)
- Optional: PostgreSQL with pgvector (for vector search)
- Optional: ChromaDB or Qdrant (alternative vector stores)

### Install Dependencies

```bash
# From repository root
pip install -r requirements.txt
```

Required packages (see `requirements.txt`):
- `pydantic>=2.0` - Data validation
- `pydantic-settings>=2.0` - Configuration management
- `neo4j>=5.0` - Graph database driver
- `openai>=1.0` - OpenAI API client (optional)
- `httpx>=0.24` - HTTP client for local LLMs
- `python-dotenv>=1.0` - Environment variable management

## Configuration

Create a `.env` file (see `.env.example`):

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# LLM Provider (openai, mistral, or local)
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Mistral (alternative)
# MISTRAL_API_KEY=your_mistral_key
# MISTRAL_MODEL=mistral-large-latest

# Local LLM (Ollama, etc.)
# LOCAL_LLM_URL=http://localhost:11434
# LOCAL_LLM_MODEL=mistral

# Vector Store (pgvector, chromadb, qdrant)
VECTOR_STORE_TYPE=pgvector
VECTOR_DIMENSION=1536

# Episodic Memory
EPISODIC_MEMORY_MAX_EPISODES=1000
EPISODIC_MEMORY_RECALL_TOP_K=3

# RAG Settings
RAG_DEFAULT_TOP_K=5
RAG_USE_HYBRID_SEARCH=true

# Logging
LOG_LEVEL=INFO
```

## Quick Start

### 1. Initialize the System

```python
import asyncio
from graphrag import RAGOrchestrator, KnowledgeGraphBuilder

async def main():
    # Create orchestrator
    orchestrator = RAGOrchestrator()
    await orchestrator.initialize()
    
    print("GraphRAG initialized and ready!")
    
    await orchestrator.shutdown()

asyncio.run(main())
```

### 2. Add Entities to Knowledge Graph

```python
from graphrag import KnowledgeGraphBuilder
from graphrag.models import Client, Contract, EntityType
from datetime import date
from decimal import Decimal

async def add_financial_data():
    kg = KnowledgeGraphBuilder()
    await kg.initialize()
    
    # Create a client
    client = Client(
        name="Acme Corporation",
        company_name="Acme Corporation",
        contact_email="finance@acme.com",
        tax_id="FR12345678901",
    )
    
    # Create a contract
    contract = Contract(
        name="Annual Support Contract 2024",
        reference="CTR-2024-001",
        title="Annual Software Support and Maintenance",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        total_amount=Decimal("120000.00"),
        currency="EUR",
    )
    
    # Add both with automatic relationship
    contract_id, client_id = await kg.add_contract_with_client(contract, client)
    print(f"Added contract {contract_id} for client {client_id}")
    
    await kg.shutdown()

asyncio.run(add_financial_data())
```

### 3. Query the System

```python
from graphrag import RAGOrchestrator, RAGQuery

async def ask_question():
    orchestrator = RAGOrchestrator()
    await orchestrator.initialize()
    
    # Create a query
    query = RAGQuery(
        question="Which contracts contain penalty clauses indexed to inflation?",
        use_vector_search=True,
        use_graph_traversal=True,
        use_episodic_memory=True,
        top_k=5,
    )
    
    # Get answer
    response = await orchestrator.query(query)
    
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}")
    print(f"Sources: {len(response.sources)}")
    
    for source in response.sources:
        print(f"  - {source['type']}: {source.get('excerpt', '')[:100]}...")
    
    await orchestrator.shutdown()

asyncio.run(ask_question())
```

### 4. Chain-of-Thought Reasoning

```python
async def analyze_with_cot():
    orchestrator = RAGOrchestrator()
    await orchestrator.initialize()
    
    result = await orchestrator.reason_with_chain_of_thought(
        question="What are the risks in our current contract portfolio?",
        steps=[
            "Identify all active contracts",
            "Analyze contractual terms and clauses",
            "Assess financial exposure",
            "Evaluate timing risks (expiring contracts)",
            "Formulate risk mitigation strategy",
        ]
    )
    
    print(f"Conclusion: {result['conclusion']}")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    print("\nReasoning Steps:")
    for step in result.get('steps', []):
        print(f"  {step['step']}: {step['reasoning']}")
    
    await orchestrator.shutdown()

asyncio.run(analyze_with_cot())
```

### 5. Work with Episodic Memory

```python
from graphrag import EpisodicMemory
from graphrag.models import FinancialEpisode
from datetime import datetime
from uuid import UUID

memory = EpisodicMemory()

# Store an episode
episode = FinancialEpisode(
    title="Client XYZ late payment pattern detected",
    description="Client XYZ has paid late 3 times in the last 6 months, average delay 18 days",
    event_date=datetime.utcnow(),
    entities_involved=[UUID("client-xyz-id")],
    event_type="late_payment_pattern",
    context={"avg_delay_days": 18, "occurrences": 3},
    tags=["payment", "risk", "client-xyz"],
)

memory.store_episode(episode)

# Recall similar episodes
similar = memory.recall_similar(
    "Are there clients with payment issues?",
    top_k=5,
)

for ep in similar:
    print(f"{ep.title} (similarity: {ep.similarity_score:.2f})")
```

## Integration with Other F360 Layers

### Layer 1 & 2: Sources & Cognitive Ingestion
After documents are ingested and vectorized, they automatically become available for vector search in RAG queries.

### Layer 4: Real-Time Feedback
When feedback loops detect anomalies, store them as episodes:

```python
episode = memory.create_episode_from_event(
    title="Budget overrun detected",
    description="IT department Q4 budget exceeded by 15%",
    event_type="budget_overrun",
    entities_involved=[department_id],
    context={"variance_pct": 15, "quarter": "Q4"},
    tags=["budget", "overrun"],
)
memory.store_episode(episode)
```

### Layer 5: Simulation
Use RAG to provide context for simulations:

```python
query = RAGQuery(
    question="Based on past trends, what's the likely outcome of reducing budget by 10%?",
    use_episodic_memory=True,
)
response = await orchestrator.query(query)
```

### Layer 6 & 7: Decision Fusion & Recommendations
RAG provides enriched context for decision-making:

```python
# Get comprehensive analysis before making a decision
context = await orchestrator.analyze_entity_context(contract_id, depth=3)
# Feed this into decision fusion layer
```

## Testing

Run tests:

```bash
# All tests
pytest tests/test_graphrag/ -v

# Specific module
pytest tests/test_graphrag/test_knowledge_graph.py -v

# With coverage
pytest tests/test_graphrag/ --cov=src/graphrag --cov-report=html
```

## API Reference

See inline docstrings for detailed API documentation. Key classes:

### `RAGOrchestrator`
Main entry point for RAG operations.

**Methods:**
- `initialize()` - Initialize all components
- `query(RAGQuery)` - Execute a RAG query
- `reason_with_chain_of_thought(question, context, steps)` - Multi-step reasoning
- `analyze_entity_context(entity_id, depth)` - Comprehensive entity analysis

### `KnowledgeGraphBuilder`
High-level knowledge graph operations.

**Methods:**
- `add_entity(entity)` - Add entity to graph
- `create_relationship(source_id, target_id, type)` - Link entities
- `add_contract_with_client(contract, client)` - Domain-specific helper
- `find_contracts_with_penalty_clauses()` - Domain query
- `traverse_from_entity(entity_id, max_depth)` - Graph traversal

### `EpisodicMemory`
Financial episodic memory management.

**Methods:**
- `store_episode(episode)` - Store an episode
- `recall_similar(query, top_k)` - Similarity-based recall
- `recall_by_entity(entity_id)` - Entity-specific recall
- `detect_pattern(pattern_type, condition_func)` - Pattern detection

### `ReasoningEngine`
LLM-powered financial reasoning.

**Methods:**
- `generate_answer(question, context)` - Generate answer
- `chain_of_thought(question, context, steps)` - Multi-step reasoning
- `analyze_anomaly(data, expected)` - Anomaly analysis
- `generate_recommendation(situation, options)` - Generate recommendations

## Design Principles

1. **Modularity**: Each component is independent and can be replaced
2. **Type Safety**: Full type hints throughout
3. **Testability**: Designed for easy mocking and unit testing
4. **Provider Agnostic**: Swap LLM providers, graph stores, or vector stores easily
5. **Production Ready**: Proper error handling, logging, and resource management
6. **Documentation**: Comprehensive docstrings and examples

## Troubleshooting

### Neo4j Connection Issues
```python
# Check connection
from graphrag import Neo4jGraphStore
store = Neo4jGraphStore()
await store.connect()  # Will raise GraphConnectionError if it fails
```

### LLM Provider Issues
```python
# Validate config
from graphrag import get_config
config = get_config()
config.validate_config()  # Will raise errors if invalid
```

### Memory Usage
```python
# Check memory statistics
stats = memory.get_statistics()
print(f"Episodes: {stats['total_episodes']}/{stats['max_episodes']}")
```

## Contributing

This component follows clean architecture principles. When extending:

1. Add new entity types in `models.py`
2. Implement new providers by extending abstract base classes
3. Add domain-specific queries in `knowledge_graph.py`
4. Write tests for all new functionality

## License

MIT
