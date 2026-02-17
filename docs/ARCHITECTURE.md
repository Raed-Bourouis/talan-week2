# GraphRAG System Architecture

## Overview

The GraphRAG system implements a hybrid retrieval approach that combines:
- **Vector Search**: Semantic similarity using embeddings
- **Graph Search**: Structured knowledge traversal
- **Episodic Memory**: Conversation context tracking
- **LLM Generation**: Response synthesis

## System Components

### 1. Embedding Service

**Technology**: sentence-transformers

**Purpose**: Convert text into dense vector representations for semantic similarity

**Key Features**:
- Pre-trained models (no training required)
- Batch processing support
- Configurable model selection
- Dimension: 384 (default with all-MiniLM-L6-v2)

**Implementation**: `graphrag/core/embeddings.py`

### 2. Vector Store

**Technology**: Qdrant

**Purpose**: Store and search document embeddings efficiently

**Key Features**:
- HNSW index for fast approximate nearest neighbor search
- Cosine similarity distance metric
- Metadata storage alongside vectors
- Scalable to millions of vectors

**Implementation**: `graphrag/core/vector_store.py`

**Operations**:
- Create collections
- Add vectors with metadata
- Similarity search
- Batch operations

### 3. Graph Store

**Technology**: Neo4j

**Purpose**: Store and query structured knowledge as a graph

**Key Features**:
- Property graph model
- Cypher query language
- Relationship traversal
- ACID transactions

**Implementation**: `graphrag/core/graph_store.py`

**Operations**:
- Add nodes (entities)
- Add relationships (edges)
- Graph traversal
- Pattern matching
- Text-based search

### 4. LLM Service

**Technology**: Ollama (Llama 3.1)

**Purpose**: Generate natural language responses

**Key Features**:
- Local inference (no API keys)
- Multiple model support
- Streaming responses
- Context-aware generation

**Implementation**: `graphrag/core/llm.py`

**Capabilities**:
- Text generation
- Conversation handling
- Context-based answering
- Configurable temperature

### 5. Episodic Memory

**Technology**: Redis

**Purpose**: Store conversation history and session context

**Key Features**:
- Fast in-memory storage
- Session-based organization
- TTL support
- Context management

**Implementation**: `graphrag/core/episodic_memory.py`

**Storage Patterns**:
- Interaction history per session
- Context variables with expiration
- Recent context retrieval

### 6. Hybrid Retriever

**Purpose**: Combine multiple retrieval sources

**Implementation**: `graphrag/core/retriever.py`

**Process**:
1. Query embedding generation
2. Parallel vector and graph search
3. Episodic memory retrieval
4. Result combination and ranking
5. Context preparation for LLM
6. Response generation
7. Memory storage

## Data Flow

### Indexing Flow

```
Document Text
     ↓
Embedding Service
     ↓
Vector + Metadata
     ↓
Vector Store (Qdrant)
```

```
Entity + Properties
     ↓
Graph Store (Neo4j)
     ↓
Node Creation
```

### Query Flow

```
User Query
     ↓
┌────────────────────────────────┐
│     Hybrid Retriever           │
├────────────────────────────────┤
│ 1. Generate query embedding    │
│ 2. Vector search (Qdrant)      │
│ 3. Graph search (Neo4j)        │
│ 4. Get episodic memory (Redis) │
│ 5. Combine results             │
│ 6. Generate answer (Ollama)    │
│ 7. Store interaction (Redis)   │
└────────────────────────────────┘
     ↓
Response + Updated Memory
```

## API Layer

### FastAPI Application

**Implementation**: `graphrag/api/app.py`

**Endpoints**:
- `POST /documents`: Add documents to vector store
- `POST /nodes`: Add knowledge nodes to graph
- `POST /relationships`: Create graph relationships
- `POST /query`: Query with answer generation
- `POST /retrieve`: Retrieve without generation
- `GET /conversations/{session_id}`: Get history
- `DELETE /conversations/{session_id}`: Clear history
- `GET /health`: Health check

**Features**:
- CORS support
- Error handling
- Request validation (Pydantic)
- Async operations
- OpenAPI documentation

## Python SDK

### Client Interface

**Implementation**: `graphrag/sdk/client.py`

**Class**: `GraphRAG`

**Methods**:
- `add_documents()`: Index documents
- `add_knowledge_node()`: Create graph nodes
- `add_relationship()`: Create graph edges
- `query()`: Ask questions
- `retrieve()`: Get raw results
- `get_conversation_history()`: Access memory
- `clear_conversation()`: Reset session

**Design Patterns**:
- Builder pattern for initialization
- Context manager support
- Connection pooling
- Error handling

## Configuration Management

**Implementation**: `graphrag/config/settings.py`

**Technology**: Pydantic Settings

**Features**:
- Environment variable loading
- Type validation
- Default values
- .env file support

**Configuration Groups**:
- Application settings
- Service connections
- Model parameters
- Retrieval parameters

## Deployment Architecture

### Docker Compose Stack

**Services**:
1. **qdrant**: Vector database (port 6333)
2. **neo4j**: Graph database (ports 7474, 7687)
3. **redis**: Key-value store (port 6379)
4. **ollama**: LLM service (port 11434)
5. **graphrag**: Main application (port 8000)

**Volumes**:
- `qdrant_storage`: Persistent vector data
- `neo4j_data`: Graph database data
- `neo4j_logs`: Neo4j logs
- `redis_data`: Redis persistence
- `ollama_models`: Downloaded models

**Health Checks**:
- All services have health checks
- Dependencies enforced with `depends_on`
- Graceful startup and shutdown

## Scalability Considerations

### Horizontal Scaling

- **API Layer**: Can run multiple instances behind load balancer
- **Vector Store**: Qdrant supports clustering
- **Graph Store**: Neo4j supports clustering (Enterprise)
- **Redis**: Can use Redis Cluster

### Vertical Scaling

- **Embeddings**: Batch processing for throughput
- **LLM**: GPU acceleration for faster inference
- **Vector Search**: HNSW index tuning
- **Graph Queries**: Index optimization

### Performance Optimization

1. **Caching**:
   - Embedding cache in Redis
   - Query result cache
   - Model output cache

2. **Batching**:
   - Batch document indexing
   - Batch embedding generation
   - Parallel searches

3. **Indexing**:
   - Vector index optimization
   - Graph indexes on frequently queried properties
   - Redis key expiration

## Security Considerations

### Network Security

- Internal service communication
- API authentication (to be added)
- Rate limiting (to be added)

### Data Security

- No external API calls
- Local data storage
- Secure credentials via environment variables

### Best Practices

1. Use secrets management for production
2. Enable authentication on all databases
3. Use HTTPS for API in production
4. Regular security updates
5. Monitor access logs

## Monitoring and Observability

### Health Checks

- Service availability checks
- Component health endpoint
- Dependency status

### Logging

- Structured logging with levels
- Service-specific logs
- Error tracking

### Metrics (Future)

- Query latency
- Retrieval accuracy
- Resource utilization
- Cache hit rates

## Extension Points

### Custom Embeddings

Replace `EmbeddingService` with custom implementation:
```python
class CustomEmbeddingService:
    def embed_text(self, text: str) -> List[float]:
        # Custom implementation
        pass
```

### Custom Retrievers

Extend `HybridRetriever`:
```python
class CustomRetriever(HybridRetriever):
    def retrieve(self, query: str) -> Dict[str, Any]:
        # Custom retrieval logic
        pass
```

### Custom LLM

Replace `LLMService`:
```python
class CustomLLMService:
    def generate(self, prompt: str) -> str:
        # Custom LLM implementation
        pass
```

## Development Workflow

1. **Local Development**: Use Docker Compose for services
2. **Testing**: Unit tests with mocked services
3. **Integration Testing**: Full stack tests
4. **Deployment**: Docker container to cloud
5. **Monitoring**: Health checks and logs

## Future Enhancements

- [ ] Multi-modal support (images, audio)
- [ ] Advanced caching strategies
- [ ] Query optimization
- [ ] Fine-tuned embeddings
- [ ] Graph reasoning algorithms
- [ ] Distributed deployment
- [ ] Web UI dashboard
- [ ] Monitoring dashboard
- [ ] A/B testing framework
- [ ] Model versioning
