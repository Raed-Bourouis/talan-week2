# GraphRAG System

A complete, 100% free GraphRAG (Graph Retrieval-Augmented Generation) system with hybrid retrieval combining vector search and knowledge graphs. Built with a modular architecture and fully containerized with Docker.

## Features

- 🔍 **Hybrid Retrieval**: Combines vector similarity search with graph-based knowledge retrieval
- 🤖 **Local LLM**: Uses Ollama with Llama 3.1 (100% free, no API keys required)
- 🧠 **Embeddings**: sentence-transformers for semantic understanding
- 📊 **Graph Database**: Neo4j for structured knowledge representation
- 🔢 **Vector Database**: Qdrant for efficient similarity search
- 💾 **Episodic Memory**: Redis for conversation history and context
- 🚀 **FastAPI REST API**: Complete REST API for easy integration
- 🐍 **Python SDK**: Clean, intuitive Python interface
- 🐳 **Docker Containerized**: One-command deployment
- 🌐 **Domain Agnostic**: Works with any domain or use case

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        GraphRAG API                         │
│                      (FastAPI REST)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Python SDK (GraphRAG)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│ Hybrid Retriever│    │ Core Components  │
└────────┬────────┘    └──────────────────┘
         │
    ┌────┴────┬─────────┬────────┬─────────┐
    ▼         ▼         ▼        ▼         ▼
┌────────┐┌────────┐┌───────┐┌──────┐┌────────┐
│Qdrant  ││ Neo4j  ││Ollama ││Redis ││Sentence│
│Vector  ││Graph   ││LLM    ││Memory││Transf. │
│Store   ││Database││       ││      ││Embed   │
└────────┘└────────┘└───────┘└──────┘└────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for SDK usage)
- 8GB+ RAM recommended

### 1. Clone the Repository

```bash
git clone https://github.com/Raed-Bourouis/talan-week2.git
cd talan-week2
```

### 2. Start the System

```bash
# Start all services
docker-compose up -d

# Pull the Llama 3.1 model (one-time setup)
docker exec -it talan-week2-ollama-1 ollama pull llama3.1

# Wait for all services to be healthy
docker-compose ps
```

### 3. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Access API documentation
# Open http://localhost:8000/docs in your browser
```

## Usage

### Python SDK

```python
from graphrag import GraphRAG

# Initialize the client
client = GraphRAG()

# Add documents
texts = [
    "Python is a high-level programming language.",
    "Machine learning is a subset of artificial intelligence.",
    "Neural networks are inspired by the human brain."
]
doc_ids = client.add_documents(texts)

# Add knowledge nodes to graph
node_id = client.add_knowledge_node(
    label="Technology",
    properties={"name": "Python", "type": "Programming Language"}
)

# Query the system
answer = client.query(
    "What is Python?",
    session_id="user-123"  # Optional: for conversation tracking
)
print(answer)

# Retrieve without generating answer
results = client.retrieve("Tell me about machine learning")
print(results["vector_results"])
print(results["graph_results"])

# Get conversation history
history = client.get_conversation_history("user-123")

# Clean up
client.close()
```

### REST API

#### Add Documents

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "GraphRAG combines retrieval and generation.",
      "Vector databases enable semantic search."
    ]
  }'
```

#### Add Knowledge Nodes

```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Concept",
    "properties": {
      "name": "GraphRAG",
      "description": "A hybrid retrieval system"
    }
  }'
```

#### Query the System

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is GraphRAG?",
    "session_id": "user-123"
  }'
```

#### Get Conversation History

```bash
curl http://localhost:8000/conversations/user-123
```

### Advanced Usage

#### Adding Relationships

```python
from graphrag import GraphRAG

client = GraphRAG()

# Create nodes
node1_id = client.add_knowledge_node("Person", {"name": "Alice"})
node2_id = client.add_knowledge_node("Person", {"name": "Bob"})

# Create relationship
client.add_relationship(
    source_id=node1_id,
    target_id=node2_id,
    rel_type="KNOWS",
    properties={"since": "2020"}
)
```

#### Custom Configuration

```python
from graphrag import GraphRAG

# Use custom configuration
client = GraphRAG(
    qdrant_host="custom-qdrant-host",
    neo4j_uri="bolt://custom-neo4j:7687",
    ollama_model="llama3.1:70b"  # Use larger model
)
```

## Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key configuration options:

- `OLLAMA_MODEL`: LLM model to use (default: `llama3.1`)
- `EMBEDDING_MODEL`: Embedding model (default: `all-MiniLM-L6-v2`)
- `TOP_K_VECTOR`: Number of vector search results (default: 5)
- `TOP_K_GRAPH`: Number of graph search results (default: 5)

## API Documentation

Once running, access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Local Setup (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Start services manually
# - Qdrant: Follow https://qdrant.tech/documentation/quick-start/
# - Neo4j: Follow https://neo4j.com/docs/operations-manual/current/installation/
# - Redis: Follow https://redis.io/docs/getting-started/
# - Ollama: Follow https://ollama.ai/download

# Run the API
uvicorn graphrag.api.app:app --reload
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black graphrag/
flake8 graphrag/
```

## Use Cases

- **Question Answering**: Build intelligent Q&A systems over your documents
- **Knowledge Management**: Create and query structured knowledge graphs
- **Conversational AI**: Build context-aware chatbots with memory
- **Research Assistant**: Combine semantic search with structured knowledge
- **Document Analysis**: Extract insights from large document collections
- **Domain-Specific RAG**: Customize for legal, medical, financial, or any domain

## System Requirements

### Minimum

- 4 CPU cores
- 8GB RAM
- 20GB disk space

### Recommended

- 8 CPU cores
- 16GB RAM
- 50GB disk space
- GPU for faster embeddings (optional)

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs

# Restart specific service
docker-compose restart graphrag
```

### Ollama Model Not Found

```bash
# Pull the model
docker exec -it talan-week2-ollama-1 ollama pull llama3.1

# List available models
docker exec -it talan-week2-ollama-1 ollama list
```

### Memory Issues

If you encounter memory issues, you can:

1. Use a smaller embedding model: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
2. Use a smaller LLM: `OLLAMA_MODEL=llama3.1:8b`
3. Reduce batch sizes in your code

## Architecture Details

### Components

1. **Embedding Service**: Converts text to dense vectors using sentence-transformers
2. **Vector Store**: Stores and searches embeddings using Qdrant
3. **Graph Store**: Manages knowledge graph using Neo4j
4. **LLM Service**: Generates responses using Ollama
5. **Episodic Memory**: Tracks conversations using Redis
6. **Hybrid Retriever**: Combines vector and graph search results

### Data Flow

1. User query → Embedding Service → Query vector
2. Query vector → Vector Store → Similar documents
3. Query text → Graph Store → Related entities
4. Results + Episodic Memory → LLM Service → Answer

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [Qdrant](https://qdrant.tech/) for vector search
- [Neo4j](https://neo4j.com/) for graph database
- [sentence-transformers](https://www.sbert.net/) for embeddings
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework

## Support

For issues, questions, or contributions:

- GitHub Issues: https://github.com/Raed-Bourouis/talan-week2/issues
- Documentation: http://localhost:8000/docs (when running)

---

Built with ❤️ for the open-source community
