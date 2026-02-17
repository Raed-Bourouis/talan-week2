# Frequently Asked Questions (FAQ)

## General Questions

### Q: Is GraphRAG really 100% free?

**A**: Yes! All components use free, open-source software:
- Ollama: Free LLM inference
- Qdrant: Free vector database
- Neo4j Community: Free graph database
- Redis: Free key-value store
- sentence-transformers: Free embeddings

No API keys or subscriptions required.

### Q: What are the system requirements?

**A**: Minimum:
- 4 CPU cores
- 8GB RAM
- 20GB disk space
- Docker & Docker Compose

Recommended:
- 8 CPU cores
- 16GB RAM
- 50GB disk space
- GPU for faster inference (optional)

### Q: Can I use this in production?

**A**: The system is production-ready but consider:
- Add authentication/authorization
- Implement rate limiting
- Set up monitoring and logging
- Use managed services for databases
- Configure backups

### Q: Is my data private?

**A**: Yes! All processing happens locally:
- No external API calls
- No data sent to third parties
- All data stays on your infrastructure

### Q: What domains/use cases does this support?

**A**: GraphRAG is domain-agnostic and works for:
- Question answering systems
- Knowledge management
- Research assistants
- Conversational AI
- Document analysis
- Any RAG application

## Setup Questions

### Q: How do I get started quickly?

**A**: Run the quick start script:
```bash
./quickstart.sh
```

Or follow README instructions.

### Q: Which LLM models can I use?

**A**: Any Ollama-supported model:
- llama3.1 (default, 8B parameters)
- llama3.1:70b (larger, more capable)
- mistral
- mixtral
- codellama
- And many more

Change in `.env` or docker-compose.yml:
```
OLLAMA_MODEL=llama3.1:70b
```

### Q: Can I use a different embedding model?

**A**: Yes! Change `EMBEDDING_MODEL` in settings:
```python
client = GraphRAG(embedding_model="all-mpnet-base-v2")
```

Popular options:
- all-MiniLM-L6-v2 (fast, 384 dim)
- all-mpnet-base-v2 (better quality, 768 dim)
- multi-qa-MiniLM-L6-cos-v1 (optimized for Q&A)

### Q: How do I use a GPU?

**A**: For Ollama (LLM inference):
1. Install NVIDIA Docker toolkit
2. Update docker-compose.yml:
```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

For embeddings (sentence-transformers):
- Automatically uses GPU if available
- PyTorch detects CUDA

## Usage Questions

### Q: How do I add my own documents?

**A**: Use the SDK or API:

Python SDK:
```python
from graphrag import GraphRAG
client = GraphRAG()
ids = client.add_documents(["Document 1", "Document 2"])
```

REST API:
```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Document 1", "Document 2"]}'
```

### Q: How do I build a knowledge graph?

**A**: Create nodes and relationships:

```python
# Add nodes
person_id = client.add_knowledge_node("Person", {"name": "Alice"})
org_id = client.add_knowledge_node("Organization", {"name": "Acme"})

# Add relationship
client.add_relationship(person_id, org_id, "WORKS_AT")
```

### Q: How does conversation memory work?

**A**: Use session IDs to track conversations:

```python
# First query
answer1 = client.query("What is Python?", session_id="user-123")

# Follow-up (uses context from previous query)
answer2 = client.query("What is it used for?", session_id="user-123")

# View history
history = client.get_conversation_history("user-123")
```

### Q: Can I query without generating an answer?

**A**: Yes! Use the retrieve method:

```python
results = client.retrieve("my query")
print(results["vector_results"])  # Similar documents
print(results["graph_results"])   # Related graph nodes
```

## Troubleshooting

### Q: Services won't start

**A**: Common issues:
1. **Port conflicts**: Stop other services using ports 6333, 6379, 7474, 7687, 8000, 11434
2. **Insufficient memory**: Increase Docker memory limit
3. **Docker not running**: Start Docker daemon

Check logs:
```bash
docker-compose logs
```

### Q: "Model not found" error

**A**: Pull the model:
```bash
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.1
```

List available models:
```bash
docker exec -it $(docker ps -q -f name=ollama) ollama list
```

### Q: Slow response times

**A**: Several solutions:
1. **Use smaller model**: `llama3.1:8b` instead of `llama3.1:70b`
2. **Use GPU**: Enable GPU for Ollama
3. **Reduce Top-K**: Lower `TOP_K_VECTOR` and `TOP_K_GRAPH` in config
4. **Use faster embedding model**: Switch to `all-MiniLM-L6-v2`

### Q: Out of memory errors

**A**: Solutions:
1. **Increase Docker memory**: Docker settings → Resources
2. **Use smaller models**: Switch to smaller LLM and embedding models
3. **Reduce batch sizes**: Process fewer documents at once
4. **Close other applications**: Free up system memory

### Q: Connection refused errors

**A**: Wait for services to fully start:
```bash
# Check service status
docker-compose ps

# Wait for healthy status
docker-compose logs graphrag | grep "healthy"
```

Health checks can take 30-60 seconds.

### Q: Neo4j authentication failed

**A**: Default credentials:
- Username: `neo4j`
- Password: `password`

Change in docker-compose.yml:
```yaml
neo4j:
  environment:
    - NEO4J_AUTH=neo4j/your_password
```

### Q: Vector search returns no results

**A**: Ensure:
1. Documents were added: Check document IDs returned
2. Collection exists: Check Qdrant dashboard
3. Embeddings generated: Check logs for errors

Recreate collection:
```python
client.vector_store.delete_collection()
client.vector_store.create_collection(dimension=384)
```

## Performance Questions

### Q: How many documents can I store?

**A**: Qdrant can handle millions of vectors. Limits depend on:
- Available RAM
- Disk space
- Query performance requirements

For production, consider Qdrant clustering.

### Q: How fast is query processing?

**A**: Typical latency breakdown:
- Embedding generation: 10-50ms
- Vector search: 10-50ms
- Graph search: 20-100ms
- LLM generation: 1-5 seconds (depends on model and response length)

Total: ~2-5 seconds per query

### Q: Can I handle concurrent requests?

**A**: Yes! The API is async and can handle multiple requests:
- FastAPI handles concurrency well
- Each database supports concurrent connections
- Scale by running multiple API instances

## Integration Questions

### Q: Can I integrate with my existing application?

**A**: Yes! Two options:
1. **Python SDK**: Import and use in your Python code
2. **REST API**: Call from any language via HTTP

### Q: Can I customize the prompts?

**A**: Yes! Pass system prompts:
```python
answer = client.llm_service.generate(
    prompt="Your query",
    system="You are a helpful assistant specializing in X"
)
```

### Q: Can I use my own vector database?

**A**: Yes! Implement the interface:
```python
class MyVectorStore:
    def search(self, query_vector, top_k):
        # Your implementation
        pass
```

Same for other components.

## Advanced Questions

### Q: How do I fine-tune the embeddings?

**A**: sentence-transformers supports fine-tuning:
1. Prepare training data
2. Fine-tune model
3. Use custom model path in EmbeddingService

See sentence-transformers documentation.

### Q: Can I add custom retrievers?

**A**: Yes! Extend HybridRetriever:
```python
class CustomRetriever(HybridRetriever):
    def retrieve(self, query):
        # Custom logic
        results = super().retrieve(query)
        # Post-process results
        return results
```

### Q: How do I monitor performance?

**A**: Current monitoring options:
1. Docker stats: `docker stats`
2. Service logs: `docker-compose logs`
3. Health endpoint: `/health`

For production, add:
- Prometheus metrics
- Grafana dashboards
- Application Performance Monitoring (APM)

### Q: Can I deploy to Kubernetes?

**A**: Yes! Convert docker-compose to Kubernetes:
1. Create Deployments for each service
2. Create Services for networking
3. Create PersistentVolumeClaims for storage
4. Use Helm charts for easier management

Example Helm chart structure available in docs.

## Security Questions

### Q: Is authentication supported?

**A**: Not by default. For production, add:
- API key middleware
- JWT authentication
- OAuth 2.0
- Rate limiting

Example middleware:
```python
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != "your_secret_key":
        return Response(status_code=403)
    return await call_next(request)
```

### Q: How do I secure the databases?

**A**: Best practices:
1. Change default passwords
2. Enable authentication on all services
3. Use SSL/TLS for connections
4. Restrict network access
5. Regular security updates

### Q: Can I encrypt data at rest?

**A**: Yes:
- Qdrant: Supports encryption
- Neo4j: Enterprise edition supports encryption
- Redis: Use encrypted volumes
- Docker: Use encrypted volumes

## Support Questions

### Q: Where can I get help?

**A**: Resources:
1. GitHub Issues: Report bugs and request features
2. Documentation: Check docs/ directory
3. Examples: See examples/ directory
4. API Docs: http://localhost:8000/docs

### Q: How do I report a bug?

**A**: Create a GitHub issue with:
1. Description of the problem
2. Steps to reproduce
3. Expected vs actual behavior
4. System information
5. Relevant logs

### Q: Can I contribute?

**A**: Yes! See CONTRIBUTING.md for guidelines.

### Q: Is commercial use allowed?

**A**: Yes! MIT License allows commercial use.
