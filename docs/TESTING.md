# Testing Guide

This document describes how to test the GraphRAG system.

## Prerequisites

All services must be running. Use the quick start script:

```bash
./quickstart.sh
```

Or manually:

```bash
docker-compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.1
```

## Unit Tests

Run unit tests with mocked dependencies:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_core.py -v

# Run with coverage
pytest tests/ --cov=graphrag --cov-report=html
```

## Integration Tests

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
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

### 2. Add Documents

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Test document 1", "Test document 2"]
  }'
```

Expected: Returns list of document IDs

### 3. Query System

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about test documents",
    "session_id": "test-session"
  }'
```

Expected: Returns generated answer

### 4. Add Graph Nodes

```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Test",
    "properties": {"name": "TestNode"}
  }'
```

Expected: Returns node ID

## End-to-End Tests

### Python SDK

```bash
python examples/basic_usage.py
```

This will:
1. Initialize the GraphRAG client
2. Add documents
3. Create knowledge graph
4. Query the system
5. Test retrieval
6. Check conversation history

### REST API

```bash
python examples/rest_api_usage.py
```

This will:
1. Check system health
2. Add documents via API
3. Create knowledge graph via API
4. Query via API
5. Retrieve information
6. Manage conversations

## Manual Testing Checklist

- [ ] All services start successfully
- [ ] Health endpoint returns healthy status
- [ ] Can add documents to vector store
- [ ] Can create nodes in graph database
- [ ] Can create relationships in graph
- [ ] Can query and get answers
- [ ] Can retrieve without generating
- [ ] Conversation history is tracked
- [ ] Can clear conversations
- [ ] API documentation accessible at /docs
- [ ] All dependencies are free (no API keys needed)

## Performance Tests

### Load Test

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test query endpoint
ab -n 100 -c 10 -p query.json -T application/json \
  http://localhost:8000/query
```

### Memory Test

Monitor memory usage:

```bash
docker stats
```

## Troubleshooting Tests

### Check Service Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs graphrag
docker-compose logs ollama
docker-compose logs neo4j
```

### Verify Connections

```bash
# Qdrant
curl http://localhost:6333/collections

# Neo4j
docker exec -it $(docker ps -q -f name=neo4j) \
  cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n);"

# Redis
docker exec -it $(docker ps -q -f name=redis) \
  redis-cli PING

# Ollama
curl http://localhost:11434/api/tags
```

## Test Data Cleanup

```bash
# Clear vector store
curl -X DELETE http://localhost:6333/collections/graphrag_vectors

# Clear graph database
docker exec -it $(docker ps -q -f name=neo4j) \
  cypher-shell -u neo4j -p password "MATCH (n) DETACH DELETE n;"

# Clear Redis
docker exec -it $(docker ps -q -f name=redis) \
  redis-cli FLUSHALL
```

## Continuous Integration

For CI/CD pipelines, use:

```yaml
# Example GitHub Actions workflow
name: Test GraphRAG

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt pytest
      - name: Run unit tests
        run: pytest tests/
```

## Expected Test Results

All tests should pass with:
- No syntax errors
- No import errors (when dependencies installed)
- All API endpoints returning expected responses
- All services healthy in Docker Compose
- Successful query generation and retrieval

## Common Issues

1. **Services not starting**: Check Docker resources, ensure enough memory
2. **Model not found**: Run `ollama pull llama3.1`
3. **Connection refused**: Wait for services to fully start (use health checks)
4. **Out of memory**: Reduce concurrent requests or increase Docker memory limit
