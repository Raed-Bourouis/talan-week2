# System Architecture

## Overview

FINCENTER uses a microservices architecture with GraphRAG capabilities to provide intelligent financial analysis.

## Core Components

### 1. Data Layer

**Neo4j (Graph Database)**
- Stores financial entity relationships
- Enables graph traversal queries
- Powers episodic memory patterns
- Schema: Departments, Budgets, Contracts, Invoices, Payments, Suppliers

**Qdrant (Vector Database)**
- Semantic search on documents
- Stores embeddings for contracts, invoices, patterns
- Collections: financial_documents, contract_clauses, episodic_memory

**PostgreSQL + pgvector**
- Structured financial metadata
- Hybrid search capabilities
- Audit trails and session data

**Redis**
- Caching layer
- Session management
- Real-time data

### 2. Application Layer

**Ingestion Pipeline**
- Multi-format document parsing (PDF, Excel, CSV)
- Entity extraction using LLMs
- Vectorization with OpenAI embeddings
- Graph relationship building

**GraphRAG Core**
- Hybrid retriever (vector + graph)
- Episodic memory system
- Query orchestrator
- Context builder for LLM

**Financial Intelligence**
- Budget analyzer
- Contract monitor
- Cash flow predictor
- Anomaly detector

**Simulation Engine**
- Scenario generator
- Monte Carlo simulator
- Payment optimizer

### 3. API Layer

**FastAPI Backend**
- RESTful API endpoints
- Natural language query processing
- Health checks and monitoring
- Error handling and validation

### 4. Presentation Layer

**Streamlit Dashboard**
- 5 interactive pages
- Real-time visualizations
- Natural language interface

## Data Flow

1. **Document Upload** → Document Parser → Entity Extractor
2. **Entity Extraction** → Vectorizer (Qdrant) + Graph Builder (Neo4j)
3. **User Query** → Query Orchestrator → Hybrid Retriever
4. **Retrieval** → Context Builder → LLM → Response
5. **Response** → Dashboard/API → User

## Key Design Patterns

- **Microservices**: Independent, scalable services
- **Event-Driven**: Async processing where appropriate
- **CQRS**: Separate read/write models
- **Repository Pattern**: Database abstraction
- **Factory Pattern**: Service initialization

## Scalability

- Horizontal scaling of API containers
- Database replication support
- Redis cluster for high availability
- Load balancing ready

## Security

- Environment-based configuration
- Secrets management
- Input validation
- Parameterized queries
- CORS configuration
