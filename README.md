# 💰 FINCENTER - Financial Intelligence Hub

A fully containerized GraphRAG-based Financial Intelligence platform using **100% FREE and open-source components**. No API keys required!

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)
![Cost](https://img.shields.io/badge/cost-$0.00-success.svg)

## 🎯 Features

### **100% FREE - No API Keys Needed!**
- ✅ **Local LLM**: Ollama running Llama 3.1 8B or Mistral 7B
- ✅ **Local Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- ✅ **Graph Database**: Neo4j Community Edition
- ✅ **Vector Database**: Qdrant (open-source)
- ✅ **Relational Database**: PostgreSQL with pgvector
- ✅ **API**: FastAPI with auto-generated docs
- ✅ **Dashboard**: Streamlit for interactive analysis

### Financial Intelligence Capabilities
- 📊 **Budget Analysis**: Real-time variance tracking and forecasting
- 📄 **Contract Monitoring**: Automated clause extraction and expiration alerts
- 💸 **Cash Flow Forecasting**: 90-day predictions using Prophet
- 🚨 **Smart Alerts**: Pattern-based recommendations
- 🎲 **Scenario Simulation**: What-if analysis for financial decisions
- 🧠 **Episodic Memory**: Learn from historical patterns

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM (16GB recommended)
- 20GB+ disk space (for models)
- *No API keys or subscriptions required!*

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/Raed-Bourouis/talan-week2.git
cd talan-week2

# Start all services (includes automatic model download)
docker-compose up -d

# Watch Ollama download models (first time only, ~5-10 minutes)
docker logs -f fincenter-ollama-setup

# Once models are downloaded, access the system:
# - Dashboard: http://localhost:8501
# - API Docs: http://localhost:8000/docs
# - Neo4j Browser: http://localhost:7474 (user: neo4j, pass: fincenter123)
# - Ollama API: http://localhost:11434
```

That's it! No API keys, no subscriptions, no hidden costs. Everything runs locally.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FINCENTER ARCHITECTURE                   │
│                     (100% FREE & Local)                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌──────────────────────────────────┐
│  Streamlit UI   │────▶│      FastAPI Backend             │
│  (Dashboard)    │     │  ┌───────────────────────────┐   │
└─────────────────┘     │  │  Query Orchestrator       │   │
                        │  │  (Routes & Combines)      │   │
                        │  └───────────────────────────┘   │
                        │            │                      │
                        │            ▼                      │
                        │  ┌───────────────────────────┐   │
                        │  │   GraphRAG Core           │   │
                        │  │  • Hybrid Retriever       │   │
                        │  │  • Episodic Memory        │   │
                        │  │  • Context Builder        │   │
                        │  └───────────────────────────┘   │
                        └──────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌─────────────────┐        ┌──────────────┐
│   Ollama     │          │     Neo4j       │        │   Qdrant     │
│  (Local LLM) │          │  (Graph DB)     │        │ (Vector DB)  │
│              │          │                 │        │              │
│ • Llama 3.1  │          │ • Relationships │        │ • Embeddings │
│ • Mistral    │          │ • Patterns      │        │ • Semantic   │
│              │          │ • Entities      │        │   Search     │
└──────────────┘          └─────────────────┘        └──────────────┘

        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────────┐     ┌──────────────────┐      ┌──────────────┐
│   PostgreSQL     │     │  Redis Cache     │      │ sentence-    │
│  (Metadata)      │     │  (Sessions)      │      │ transformers │
│  + pgvector      │     │                  │      │ (Embeddings) │
└──────────────────┘     └──────────────────┘      └──────────────┘
```

## 📦 System Components

### 1. **Local LLM (Ollama)**
- **Models**: Llama 3.1 8B, Mistral 7B (auto-downloaded)
- **Purpose**: Contract analysis, entity extraction, Q&A
- **Performance**: 5-10s per query (CPU), 1-3s (GPU)
- **Cost**: $0.00 ✨

### 2. **Local Embeddings (sentence-transformers)**
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Purpose**: Semantic search, document similarity
- **Performance**: ~100ms per document
- **Cost**: $0.00 ✨

### 3. **Graph Database (Neo4j Community)**
- **Purpose**: Financial relationships, payment chains
- **Schema**: Departments, Contracts, Suppliers, Invoices, Payments
- **Features**: Pattern detection, graph traversal
- **Cost**: $0.00 ✨

### 4. **Vector Database (Qdrant)**
- **Purpose**: Semantic search on financial documents
- **Collections**: Documents, clauses, entities, queries
- **Cost**: $0.00 ✨

### 5. **Relational Database (PostgreSQL + pgvector)**
- **Purpose**: Structured metadata, hybrid search
- **Features**: Full SQL, triggers, views, vector similarity
- **Cost**: $0.00 ✨

## 🎯 Use Cases

### Ask Financial Questions (Natural Language)
```python
# Examples you can ask:
"Which departments are over budget?"
"Show me contracts expiring in the next 90 days"
"What suppliers consistently pay late?"
"Forecast cash flow for the next 30 days"
"What patterns have been detected in Q4?"
```

### Automatic Contract Analysis
The system automatically extracts:
- Payment terms and schedules
- Auto-renewal clauses
- Penalty clauses
- Expiration dates
- Key obligations

### Pattern Detection (Episodic Memory)
Learns patterns like:
- "Supplier X always delivers late in Q4"
- "Marketing dept consistently overspends by 15%"
- "Q4 accounts for 35% of annual spending"

### Cash Flow Forecasting
- 90-day rolling forecasts using Prophet
- Confidence intervals
- What-if scenario testing
- Treasury tension alerts

## 🔧 Configuration

### Environment Variables
Copy `.env.example` to `.env` (optional, defaults work):

```bash
# Local LLM (FREE)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b  # or mistral:7b

# Local Embeddings (FREE)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Database connections
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fincenter123

QDRANT_HOST=localhost
QDRANT_PORT=6333

POSTGRES_HOST=localhost
POSTGRES_DB=fincenter
POSTGRES_USER=fincenter
POSTGRES_PASSWORD=fincenter123
```

### Model Selection

**Llama 3.1 8B** (Default - Best Balance)
- Size: 4.7GB
- Speed: Good
- Quality: Excellent
- Use for: Most tasks

**Mistral 7B** (Fast & Efficient)
- Size: 4.1GB
- Speed: Fast
- Quality: Very Good
- Use for: Quick responses

**Phi-3 Mini 3B** (Resource-Constrained)
- Size: 2.3GB
- Speed: Very Fast
- Quality: Good
- Use for: Low-end hardware

## 📊 Dashboard Pages

### 1. Budget Analysis
- Real-time budget vs actual
- Variance alerts
- Department drill-down
- AI recommendations

### 2. Contract Monitoring
- Expiration calendar
- Extracted clauses
- Supplier performance
- Renegotiation alerts

### 3. Cash Flow & Invoices
- 90-day forecast
- Invoice aging
- Payment optimization
- Anomaly detection

### 4. Alerts & Recommendations
- Prioritized actions
- Alert categories
- One-click workflows
- Learning feedback

### 5. Scenario Simulations
- Budget variance simulator
- Contract renegotiation impact
- Cash flow stress testing
- Side-by-side comparison

## 🔍 API Endpoints

### Query Endpoint
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which departments are over budget?"}'
```

### Other Endpoints
- `GET /health` - System health check
- `GET /budgets` - Budget information
- `GET /contracts` - Contract data
- `GET /suppliers` - Supplier metrics
- `GET /invoices` - Invoice status
- `GET /patterns` - Detected patterns
- `GET /alerts` - Active alerts
- `GET /cashflow/forecast` - Cash flow prediction

Full API documentation: http://localhost:8000/docs

## 🧪 Development

### Project Structure
```
talan-week2/
├── docker-compose.yml           # All services
├── requirements.txt             # Python dependencies (all free)
├── src/
│   ├── graphrag/               # Core GraphRAG system
│   │   ├── local_llm.py       # Ollama wrapper
│   │   ├── local_embeddings.py # sentence-transformers
│   │   ├── hybrid_retriever.py # Vector + Graph search
│   │   ├── episodic_memory.py  # Pattern detection
│   │   └── query_orchestrator.py
│   ├── api/                    # FastAPI backend
│   │   └── main.py
│   ├── dashboard/              # Streamlit UI
│   │   ├── app.py
│   │   └── pages/
│   ├── ingestion/              # Document processing
│   ├── financial/              # Financial analysis
│   └── simulation/             # Scenario engine
├── schemas/                    # Database schemas
│   ├── neo4j_schema.cypher
│   ├── postgres_schema.sql
│   └── vector_collections.json
└── config/                     # Service configs
```

### Running Tests
```bash
# Run tests (when implemented)
docker-compose exec backend pytest

# Check logs
docker logs fincenter-backend
docker logs fincenter-dashboard
```

## 🚨 Troubleshooting

### Models Not Downloading
```bash
# Check Ollama logs
docker logs -f fincenter-ollama-setup

# Manual model pull
docker exec -it fincenter-ollama ollama pull llama3.1:8b
```

### Services Not Starting
```bash
# Check all service status
docker-compose ps

# View specific service logs
docker logs fincenter-neo4j
docker logs fincenter-qdrant

# Restart services
docker-compose restart
```

### Out of Memory
```bash
# Reduce memory usage:
# 1. Use smaller model (phi3:3b)
# 2. Stop unused services
# 3. Increase Docker memory limit
```

### Slow Response Times
- **CPU Only**: 5-10 seconds per query (normal)
- **GPU**: 1-3 seconds per query
- Enable GPU support in docker-compose.yml (see comments)

## 📈 Performance Benchmarks

| Hardware | Embeddings | LLM Query | Contract Extraction |
|----------|------------|-----------|---------------------|
| CPU 8-core | 100ms | 5-10s | 10-15s |
| GPU GTX 1660+ | 50ms | 1-3s | 3-5s |

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional financial analysis modules
- More ML models for forecasting
- Enhanced pattern detection
- Additional data source integrations

## 📄 License

MIT License - See LICENSE file

## 🎓 Learn More

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed system architecture
- [LOCAL_LLM_GUIDE.md](LOCAL_LLM_GUIDE.md) - Guide to using local LLMs
- [API_DOCS.md](API_DOCS.md) - Complete API documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide

## 💡 Why 100% FREE?

**No Vendor Lock-in**: All components are open-source
**Privacy First**: Your financial data never leaves your infrastructure
**Cost Effective**: Zero API costs, perfect for startups and SMBs
**Scalable**: Can scale to enterprise with same free components

## 🌟 Acknowledgments

Built with these amazing FREE tools:
- [Ollama](https://ollama.ai/) - Local LLM inference
- [sentence-transformers](https://www.sbert.net/) - Embeddings
- [Neo4j Community](https://neo4j.com/) - Graph database
- [Qdrant](https://qdrant.tech/) - Vector database
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Streamlit](https://streamlit.io/) - Dashboard framework

---

**Made with ❤️ by the FINCENTER team**

**Total Cost: $0.00** | **100% Free & Open Source** | **No API Keys Required**
