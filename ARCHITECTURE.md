# 🏗️ FINCENTER System Architecture

## Overview

FINCENTER is a GraphRAG-based Financial Intelligence Hub that combines graph databases, vector search, and local LLMs to provide comprehensive financial analysis without any API costs.

## Architecture Layers

### 1. Presentation Layer (Frontend)
**Technology**: Streamlit
**Components**:
- Interactive dashboard with 5 pages
- Natural language query interface
- Real-time visualizations
- Export capabilities

### 2. API Layer
**Technology**: FastAPI
**Endpoints**:
- `/query` - Natural language queries
- `/health` - System health check
- `/budgets` - Budget data
- `/contracts` - Contract information
- `/suppliers` - Supplier metrics
- `/invoices` - Invoice status
- `/patterns` - Detected patterns
- `/alerts` - Active alerts

### 3. Business Logic Layer

#### Query Orchestrator
Routes queries to appropriate handlers:
- Budget queries → Budget analyzer
- Contract queries → Contract monitor
- Cash flow queries → Cash flow predictor
- Pattern queries → Episodic memory

#### GraphRAG Core
**Components**:
1. **Hybrid Retriever**: Combines vector and graph search
2. **Episodic Memory**: Detects and learns from patterns
3. **Context Builder**: Builds rich context from multiple sources
4. **Local LLM**: Ollama integration for NLP tasks
5. **Local Embeddings**: sentence-transformers for semantic search

### 4. Data Layer

#### Neo4j (Graph Database)
**Purpose**: Store financial entity relationships
**Schema**:
- Nodes: Department, Project, Contract, Supplier, Invoice, Payment, Budget, Expense
- Relationships: OWNS, WITH_SUPPLIER, FOR_CONTRACT, FROM_SUPPLIER, FOR_INVOICE, CHARGED_TO, ALLOCATED_TO
- Pattern nodes for episodic memory

#### Qdrant (Vector Database)
**Purpose**: Semantic search on financial documents
**Collections**:
- `financial_documents`: All document embeddings
- `contract_clauses`: Extracted clause embeddings
- `financial_entities`: Entity embeddings
- `queries`: Query pattern embeddings

#### PostgreSQL (Relational Database)
**Purpose**: Structured metadata storage
**Key Tables**:
- documents, document_chunks (with pgvector)
- departments, projects, suppliers
- contracts, invoices, payments
- budgets, expenses
- patterns, alerts, predictions

#### Redis (Cache)
**Purpose**: Session management and caching
**Use Cases**:
- Query result caching
- Session state
- Temporary data storage

### 5. Model Layer

#### Ollama (Local LLM)
**Models**:
- Llama 3.1 8B (default)
- Mistral 7B (alternative)
- Phi-3 3B (lightweight)

**Capabilities**:
- Contract clause extraction
- Entity recognition
- Question answering
- Recommendation generation

#### sentence-transformers (Embeddings)
**Model**: all-MiniLM-L6-v2 (384 dimensions)
**Purpose**:
- Document vectorization
- Semantic similarity
- Query understanding

## Data Flow

### Query Processing Flow
```
User Query
    ↓
Streamlit UI
    ↓
FastAPI Backend
    ↓
Query Orchestrator
    ├→ Classify Query
    ├→ Route to Handler
    ↓
Handler (Budget/Contract/etc)
    ├→ Hybrid Retriever
    │   ├→ Vector Search (Qdrant)
    │   └→ Graph Search (Neo4j)
    ├→ Episodic Memory (Patterns)
    └→ Context Builder
    ↓
Local LLM (Ollama)
    ↓
Response
    ↓
Streamlit UI
```

### Document Ingestion Flow
```
Financial Document (PDF/Excel/CSV)
    ↓
Document Parser
    ├→ Extract Text
    ├→ Parse Structure
    ↓
Entity Extractor (Ollama)
    ├→ Amounts
    ├→ Dates
    ├→ Parties
    └→ Categories
    ↓
Vectorizer (sentence-transformers)
    ├→ Create Embeddings
    └→ Store in Qdrant
    ↓
Graph Builder
    ├→ Create Nodes
    ├→ Create Relationships
    └→ Store in Neo4j
    ↓
Metadata Storage
    └→ Store in PostgreSQL
```

## Component Details

### GraphRAG Implementation

#### 1. Hybrid Retrieval
Combines two search strategies:
- **Vector Search**: Semantic similarity using embeddings
- **Graph Traversal**: Relationship-based discovery

Benefits:
- Vector search finds semantically similar content
- Graph search discovers related entities
- Combined results provide comprehensive context

#### 2. Episodic Memory
Pattern detection algorithms:
- **Late Payment Patterns**: Identifies suppliers with consistent delays
- **Budget Overrun Patterns**: Detects departments exceeding budgets
- **Seasonal Patterns**: Recognizes time-based spending trends

#### 3. Context Building
Creates rich context for LLM:
- Relevant documents from vector search
- Related entities from graph traversal
- Historical patterns from episodic memory
- Structured data from PostgreSQL

### Financial Intelligence Modules

#### Budget Analyzer
- Real-time variance calculation
- Trend analysis
- Forecasting using traditional ML (Prophet)
- Anomaly detection

#### Contract Monitor
- Automatic clause extraction using LLM
- Expiration tracking
- Renewal reminders
- Supplier performance scoring

#### Cash Flow Predictor
- 90-day rolling forecasts
- Confidence intervals
- Scenario simulation
- Treasury tension alerts

## Scalability Considerations

### Horizontal Scaling
- **API Layer**: Multiple FastAPI instances behind load balancer
- **Database Layer**: 
  - Neo4j: Read replicas for queries
  - PostgreSQL: Primary-replica setup
  - Qdrant: Distributed mode

### Vertical Scaling
- **Ollama**: GPU acceleration for 3-5x speedup
- **Embeddings**: Batch processing for large documents
- **Cache**: Redis cluster for high availability

### Performance Optimization
1. **Query Caching**: Cache frequent queries in Redis
2. **Embedding Cache**: Reuse embeddings for known documents
3. **Connection Pooling**: Reuse database connections
4. **Lazy Loading**: Load models only when needed
5. **Batch Processing**: Process multiple documents together

## Security Considerations

### Data Privacy
- All data stays within your infrastructure
- No external API calls
- No data sent to third parties
- Complete control over data

### Access Control
- API authentication (implement as needed)
- Database access controls
- Network isolation via Docker networks
- Role-based access (implement as needed)

## Monitoring & Observability

### Health Checks
- `/health` endpoint checks all services
- Docker health checks for containers
- Service discovery and registration

### Logging
- Centralized logging configuration
- Log levels per service
- Structured logging format

### Metrics (Future Enhancement)
- Query latency
- LLM inference time
- Cache hit rates
- Database query performance

## Technology Stack Summary

| Component | Technology | License | Cost |
|-----------|------------|---------|------|
| LLM | Ollama (Llama 3.1) | MIT | $0 |
| Embeddings | sentence-transformers | Apache 2.0 | $0 |
| Graph DB | Neo4j Community | GPL | $0 |
| Vector DB | Qdrant | Apache 2.0 | $0 |
| Relational DB | PostgreSQL | PostgreSQL | $0 |
| Cache | Redis | BSD | $0 |
| API | FastAPI | MIT | $0 |
| Dashboard | Streamlit | Apache 2.0 | $0 |
| Container | Docker | Apache 2.0 | $0 |

**Total Cost: $0.00** ✨

## Future Enhancements

### Short Term
- [ ] Additional dashboard pages
- [ ] More ML forecasting models
- [ ] Enhanced pattern detection
- [ ] API authentication

### Medium Term
- [ ] Multi-tenancy support
- [ ] Advanced visualizations
- [ ] Automated report generation
- [ ] Email notifications

### Long Term
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Advanced ML models
- [ ] Integration marketplace

## Deployment Architectures

### Development
```
Single Machine
├── All containers on one host
├── Shared Docker network
└── Local volumes
```

### Production (Small)
```
Single Server (16GB+ RAM)
├── Docker Compose
├── Named volumes
└── Backup strategy
```

### Production (Large)
```
Kubernetes Cluster
├── API: 3 replicas
├── Databases: Separate nodes
├── Load Balancer
├── Persistent volumes
└── Auto-scaling
```

## Conclusion

FINCENTER's architecture provides:
- ✅ **Zero Cost**: All components are free and open-source
- ✅ **Privacy**: Data never leaves your infrastructure
- ✅ **Scalability**: Can grow from single machine to cluster
- ✅ **Flexibility**: Easy to customize and extend
- ✅ **Maintainability**: Clear separation of concerns
