# System Architecture

## Overview

This document describes the architecture of the Document Processing & RAG System.

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (curl, Python, JavaScript, Web Browser)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ HTTP/REST
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      FastAPI REST API                        │
│  (Document Upload, Entity Extraction, RAG Queries)           │
└─────────────┬──────────────────────┬─────────────────────────┘
              │                      │
              │                      │
    ┌─────────▼─────────┐   ┌───────▼──────────┐
    │   Parser Layer    │   │  LLM Integration  │
    │  - PDF Parser     │   │   (Ollama)        │
    │  - Excel Parser   │   │  - Entity Extract │
    │  - Word Parser    │   │  - Embeddings     │
    └─────────┬─────────┘   └───────┬──────────┘
              │                     │
              │                     │
    ┌─────────▼─────────────────────▼──────────┐
    │         GraphRAG Manager                  │
    │  - Document Indexing                      │
    │  - Vector Search                          │
    │  - Context Retrieval                      │
    └─────────┬───────────────────────────────────┘
              │
              │
    ┌─────────▼─────────┐
    │    ChromaDB       │
    │  (Vector Store)   │
    └───────────────────┘
```

## Modules

### 1. Document Parsers (`src/parsers/`)

**Purpose**: Extract structured text and metadata from various document formats.

**Components**:
- `pdf_parser.py`: PDF parsing using PyPDF2 and pdfplumber
  - Extracts text, metadata, and tables
  - Handles multiple pages
  - Supports both text and image-based PDFs (via pdfplumber)

- `excel_parser.py`: Excel parsing using openpyxl
  - Extracts data from all sheets
  - Preserves structure (rows, columns)
  - Handles formulas and values

- `word_parser.py`: Word document parsing using python-docx
  - Extracts paragraphs with styles
  - Extracts tables
  - Preserves document structure

**Design Pattern**: Strategy pattern with `BaseParser` abstract class.

### 2. Entity Extraction (`src/entities/`)

**Purpose**: Extract named entities from documents using LLMs.

**Components**:
- `extractor.py`: Main entity extraction service
  - Connects to Ollama for LLM inference
  - Supports custom entity types
  - Returns structured entity data (type, value, context)

**Entity Types Supported**:
- Financial: company_name, stock_symbol, monetary_amount, revenue, profit, loss, financial_ratio
- Temporal: date, fiscal_year, quarter
- General: person_name, location

**Design Pattern**: Service pattern with Pydantic models for validation.

### 3. GraphRAG Manager (`src/graphrag/`)

**Purpose**: Implement Retrieval-Augmented Generation using graph-based knowledge.

**Components**:
- `manager.py`: Main GraphRAG orchestrator
  - Document indexing with chunking
  - Vector embedding generation via Ollama
  - Semantic search using ChromaDB
  - Context-aware response generation

**Key Features**:
- Configurable chunk size and overlap
- Automatic embedding generation
- Persistent vector storage
- Query-time context retrieval
- LLM-powered response synthesis

**Design Pattern**: Facade pattern wrapping ChromaDB and Ollama.

### 4. REST API (`src/api/`)

**Purpose**: Expose system functionality via HTTP endpoints.

**Components**:
- `main.py`: FastAPI application
  - Document parsing endpoints
  - Entity extraction endpoints
  - GraphRAG indexing and query endpoints
  - Health check and status endpoints

- `config.py`: Configuration management
  - Environment variable loading
  - Pydantic-based settings validation
  - Default values for all settings

**Endpoints**:
```
GET  /                             - API info
GET  /health                       - Health check
POST /api/v1/parse                 - Parse document
POST /api/v1/extract-entities      - Extract entities
POST /api/v1/graphrag/index        - Index document
GET  /api/v1/graphrag/query        - Query documents
GET  /api/v1/graphrag/documents    - List documents
DELETE /api/v1/graphrag/documents/{id} - Delete document
```

**Design Pattern**: MVC pattern with FastAPI dependency injection.

## Data Flow

### Document Parsing Flow

```
1. Client uploads document
2. API receives file and validates size/type
3. File saved to temporary location
4. Appropriate parser selected based on extension
5. Parser extracts text and metadata
6. Temporary file cleaned up
7. Structured data returned to client
```

### Entity Extraction Flow

```
1. Client uploads document
2. Document parsed to extract text
3. Text sent to Ollama with extraction prompt
4. LLM identifies and extracts entities
5. Response parsed as JSON
6. Entities returned with types and contexts
```

### GraphRAG Indexing Flow

```
1. Document parsed to extract text
2. Text split into overlapping chunks
3. For each chunk:
   a. Generate embedding via Ollama
   b. Store in ChromaDB with metadata
4. Index confirmation returned
```

### GraphRAG Query Flow

```
1. Query received from client
2. Query embedding generated via Ollama
3. Semantic search in ChromaDB
4. Top-k relevant chunks retrieved
5. Chunks used as context for LLM
6. LLM generates answer based on context
7. Response with answer and sources returned
```

## Storage

### File System Storage

```
data/
├── sample_docs/        - Sample documents
├── processed/          - Processed document cache (optional)
└── graphrag/           - ChromaDB persistent storage
    └── chroma.sqlite3  - Vector embeddings database
```

### Vector Storage (ChromaDB)

- **Collection**: documents
- **Embeddings**: 4096-dimensional (llama2 default)
- **Metadata**: doc_id, chunk_index, filename, file_type
- **Index**: Approximate nearest neighbor (ANN)

## Configuration

### Environment Variables

All configuration via environment variables (see `.env.example`):

- **API Configuration**: HOST, PORT
- **Ollama Configuration**: BASE_URL, MODEL
- **GraphRAG Configuration**: STORAGE_PATH, EMBEDDING_MODEL, EMBEDDING_DIMENSION
- **Document Processing**: MAX_FILE_SIZE, ALLOWED_EXTENSIONS
- **Logging**: LOG_LEVEL

### Docker Configuration

**Services**:
1. `ollama`: LLM inference service
   - Image: ollama/ollama:latest
   - Port: 11434
   - Persistent volume for models

2. `api`: FastAPI application
   - Built from Dockerfile
   - Port: 8000
   - Depends on ollama
   - Mounts source code and data volumes

## Security Considerations

### Current Implementation

- No authentication (development mode)
- File size limits enforced (10MB default)
- File type validation
- Temporary file cleanup
- No external network access from containers

### Production Recommendations

1. Add authentication (OAuth2, JWT)
2. Implement rate limiting
3. Add input sanitization
4. Enable HTTPS/TLS
5. Implement request logging
6. Add CORS configuration
7. Use secrets management
8. Enable container security scanning

## Scalability

### Current Limitations

- Single instance (no horizontal scaling)
- In-process file handling
- Synchronous LLM calls
- Local vector storage

### Scaling Strategies

1. **Horizontal Scaling**:
   - Add load balancer
   - Use distributed vector store (Qdrant, Weaviate)
   - Implement request queuing (RabbitMQ, Redis)

2. **Performance Optimization**:
   - Add caching layer (Redis)
   - Batch LLM requests
   - Async processing with Celery
   - Use faster embedding models

3. **Storage Scaling**:
   - Separate ChromaDB service
   - Use cloud object storage (S3)
   - Implement sharding

## Monitoring & Observability

### Recommended Tools

- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger or OpenTelemetry
- **Health Checks**: Built-in `/health` endpoint

### Key Metrics to Track

- Request rate and latency
- Document processing time
- Entity extraction accuracy
- Embedding generation time
- Vector search performance
- Error rates

## Extension Points

### Adding New Document Types

1. Create new parser in `src/parsers/`
2. Extend `BaseParser` class
3. Implement `parse()` and `extract_text()` methods
4. Update `get_parser()` in `main.py`
5. Add file extension to `ALLOWED_EXTENSIONS`

### Adding New Entity Types

1. Update entity types list in `extractor.py`
2. Modify extraction prompt
3. Update documentation

### Custom LLM Models

1. Pull model: `ollama pull <model-name>`
2. Update `OLLAMA_MODEL` in `.env`
3. Adjust `EMBEDDING_DIMENSION` if needed

## Dependencies

### Core Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Ollama**: LLM inference
- **ChromaDB**: Vector database
- **LangChain**: LLM orchestration
- **Pydantic**: Data validation

### Document Processing

- **PyPDF2**: PDF metadata
- **pdfplumber**: PDF text extraction
- **python-docx**: Word documents
- **openpyxl**: Excel files

### Development

- **pytest**: Testing framework
- **Docker**: Containerization
- **Docker Compose**: Service orchestration

## Testing Strategy

### Unit Tests

- Parser tests (`tests/test_parsers.py`)
- Isolated component testing
- Mock external dependencies

### Integration Tests

- API endpoint testing
- End-to-end workflows
- Docker environment testing

### Manual Testing

- Sample documents provided
- `validate.sh` script for quick checks
- API documentation with examples
