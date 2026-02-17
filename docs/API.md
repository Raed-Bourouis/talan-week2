# API Documentation

Complete API reference for the GraphRAG REST API.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production use, implement authentication using:
- API Keys
- JWT tokens
- OAuth 2.0

## Endpoints

### Root

#### GET /

Get API information.

**Response**:
```json
{
  "message": "GraphRAG API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

### Health Check

#### GET /health

Check system health and service status.

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "vector_store": true,
    "graph_store": true,
    "llm": true,
    "redis": true
  }
}
```

**Status Codes**:
- `200 OK`: System is healthy
- Status can be "healthy" or "degraded"

---

### Documents

#### POST /documents

Add documents to the vector store for semantic search.

**Request Body**:
```json
{
  "texts": [
    "First document text",
    "Second document text"
  ],
  "metadata": [
    {"source": "web", "author": "Alice"},
    {"source": "api", "author": "Bob"}
  ]
}
```

**Parameters**:
- `texts` (required): Array of document texts
- `metadata` (optional): Array of metadata objects (must match texts length)

**Response**:
```json
{
  "ids": [
    "uuid-1",
    "uuid-2"
  ]
}
```

**Status Codes**:
- `200 OK`: Documents added successfully
- `500 Internal Server Error`: Failed to add documents

**Example**:
```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Python is a programming language"],
    "metadata": [{"category": "programming"}]
  }'
```

---

### Knowledge Graph - Nodes

#### POST /nodes

Add a knowledge node to the graph database.

**Request Body**:
```json
{
  "label": "Person",
  "properties": {
    "name": "Alice",
    "age": 30,
    "occupation": "Engineer"
  }
}
```

**Parameters**:
- `label` (required): Node label/type
- `properties` (required): Key-value pairs for node properties

**Response**:
```json
{
  "id": "4:abc123:456"
}
```

**Status Codes**:
- `200 OK`: Node created successfully
- `500 Internal Server Error`: Failed to create node

**Example**:
```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Technology",
    "properties": {
      "name": "GraphRAG",
      "type": "Software"
    }
  }'
```

---

### Knowledge Graph - Relationships

#### POST /relationships

Create a relationship between two nodes.

**Request Body**:
```json
{
  "source_id": "4:abc123:456",
  "target_id": "4:def789:012",
  "rel_type": "KNOWS",
  "properties": {
    "since": "2020",
    "relationship_strength": 0.8
  }
}
```

**Parameters**:
- `source_id` (required): Source node ID
- `target_id` (required): Target node ID
- `rel_type` (required): Relationship type (e.g., KNOWS, WORKS_AT)
- `properties` (optional): Relationship properties

**Response**:
```json
{
  "message": "Relationship added successfully"
}
```

**Status Codes**:
- `201 Created`: Relationship created successfully
- `500 Internal Server Error`: Failed to create relationship

**Example**:
```bash
curl -X POST http://localhost:8000/relationships \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "4:abc123:456",
    "target_id": "4:def789:012",
    "rel_type": "RELATED_TO"
  }'
```

---

### Query

#### POST /query

Query the system and get an AI-generated answer using hybrid retrieval.

**Request Body**:
```json
{
  "query": "What is GraphRAG?",
  "session_id": "user-123"
}
```

**Parameters**:
- `query` (required): User question or query
- `session_id` (optional): Session ID for conversation tracking

**Response**:
```json
{
  "answer": "GraphRAG is a hybrid retrieval system that combines...",
  "session_id": "user-123"
}
```

**Status Codes**:
- `200 OK`: Query processed successfully
- `500 Internal Server Error`: Failed to process query

**Example**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about machine learning",
    "session_id": "session-001"
  }'
```

---

#### POST /retrieve

Retrieve relevant information without generating an answer.

**Request Body**:
```json
{
  "query": "machine learning",
  "session_id": "user-123"
}
```

**Parameters**:
- `query` (required): Search query
- `session_id` (optional): Session ID for context

**Response**:
```json
{
  "vector_results": [
    {
      "id": "uuid-1",
      "score": 0.95,
      "text": "Machine learning is...",
      "metadata": {"source": "wiki"}
    }
  ],
  "graph_results": [
    {
      "properties": {"name": "ML", "type": "Field"},
      "labels": ["Technology"]
    }
  ],
  "episodic_context": "User: Previous question\nAssistant: Previous answer",
  "combined_context": "Vector Search Results:\n1. Machine learning..."
}
```

**Status Codes**:
- `200 OK`: Retrieval successful
- `500 Internal Server Error`: Failed to retrieve

**Example**:
```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence"
  }'
```

---

### Conversations

#### GET /conversations/{session_id}

Get conversation history for a session.

**Path Parameters**:
- `session_id` (required): Session identifier

**Query Parameters**:
- `limit` (optional): Maximum number of interactions to return

**Response**:
```json
{
  "session_id": "user-123",
  "history": [
    {
      "query": "What is Python?",
      "response": "Python is a programming language...",
      "timestamp": "2024-01-01T12:00:00.000Z",
      "metadata": {
        "vector_results_count": 5,
        "graph_results_count": 3
      }
    }
  ]
}
```

**Status Codes**:
- `200 OK`: History retrieved successfully
- `500 Internal Server Error`: Failed to retrieve history

**Example**:
```bash
# Get all history
curl http://localhost:8000/conversations/user-123

# Get last 5 interactions
curl http://localhost:8000/conversations/user-123?limit=5
```

---

#### DELETE /conversations/{session_id}

Clear conversation history for a session.

**Path Parameters**:
- `session_id` (required): Session identifier

**Response**:
```json
{
  "message": "Conversation user-123 cleared successfully"
}
```

**Status Codes**:
- `200 OK`: Conversation cleared successfully
- `500 Internal Server Error`: Failed to clear conversation

**Example**:
```bash
curl -X DELETE http://localhost:8000/conversations/user-123
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Status Codes**:
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service is temporarily unavailable

## Rate Limiting

Currently, no rate limiting is implemented. For production:
- Implement rate limiting per IP or API key
- Typical limits: 100 requests/minute per user
- Return `429 Too Many Requests` when exceeded

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## SDK Usage

For Python applications, use the SDK instead of direct API calls:

```python
from graphrag import GraphRAG

client = GraphRAG()
answer = client.query("What is GraphRAG?")
```

See [README.md](../README.md) for complete SDK documentation.

## Examples

### Complete Workflow

```bash
# 1. Add documents
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["GraphRAG combines retrieval and generation"]
  }'

# 2. Create knowledge nodes
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Concept",
    "properties": {"name": "GraphRAG"}
  }'

# 3. Query the system
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is GraphRAG?",
    "session_id": "demo-session"
  }'

# 4. Check conversation history
curl http://localhost:8000/conversations/demo-session
```

### Batch Operations

```python
import requests

# Add multiple documents
texts = ["Text 1", "Text 2", "Text 3"]
response = requests.post(
    "http://localhost:8000/documents",
    json={"texts": texts}
)
print(response.json())
```

## Best Practices

1. **Use Session IDs**: Track conversations for better context
2. **Add Metadata**: Include metadata with documents for better filtering
3. **Batch Operations**: Add multiple documents at once
4. **Error Handling**: Always check response status codes
5. **Health Checks**: Monitor `/health` endpoint regularly

## Changelog

### Version 0.1.0
- Initial API release
- Basic CRUD operations
- Query and retrieval endpoints
- Conversation management
- Health checks
