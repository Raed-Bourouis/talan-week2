# 💰 Financial Intelligence Hub (FINCENTER)

A fully containerized GraphRAG-based Financial Intelligence System combining vector search, graph databases, and episodic memory to provide intelligent financial analysis and recommendations.

![Architecture](https://img.shields.io/badge/Architecture-GraphRAG-blue)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Overview

FINCENTER is a comprehensive financial intelligence platform that uses:
- **Vector Search** (Qdrant) for semantic document retrieval
- **Graph Database** (Neo4j) for relationship mapping and pattern detection  
- **Relational Database** (PostgreSQL with pgvector) for structured data
- **Redis** for caching and session management
- **FastAPI** for RESTful API services
- **Streamlit** for interactive dashboards
- **LLM Integration** (OpenAI/Azure OpenAI) for natural language queries

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (or Azure OpenAI credentials)
- 8GB+ RAM recommended
- 20GB+ disk space

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Raed-Bourouis/talan-week2.git
cd talan-week2
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
nano .env
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Wait for services to be ready** (2-3 minutes)
```bash
docker-compose logs -f
```

5. **Access the system**
- **Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, password: financehub123)

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Financial Intelligence Hub                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Streamlit   │  │   FastAPI    │  │   Ingestion  │      │
│  │  Dashboard   │──│   Backend    │──│   Pipeline   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                   │              │
│         └─────────────────┴───────────────────┘              │
│                          │                                   │
│         ┌────────────────┴────────────────┐                 │
│         │                                  │                 │
│  ┌──────▼───────┐  ┌───────────┐  ┌──────▼──────┐         │
│  │   Neo4j      │  │   Qdrant  │  │  PostgreSQL │         │
│  │   (Graph)    │  │  (Vector) │  │  (pgvector) │         │
│  └──────────────┘  └───────────┘  └─────────────┘         │
│         │                                  │                 │
│         └──────────────┬───────────────────┘                │
│                        │                                     │
│                   ┌────▼─────┐                              │
│                   │  Redis   │                              │
│                   │  (Cache) │                              │
│                   └──────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 Features

### 1. Multi-Modal Data Ingestion
- **Document Types**: PDF, Excel, CSV, Word, Text
- **Financial Entities**: Automatically extract amounts, dates, parties, clauses
- **Semantic Embeddings**: Create searchable vector representations
- **Graph Relationships**: Build contract → invoice → payment chains

### 2. Hybrid Search & Retrieval
- **Vector Search**: Semantic similarity using OpenAI embeddings
- **Graph Traversal**: Relationship-based queries (e.g., find all invoices for a supplier)
- **Combined Results**: Intelligent ranking and merging of results

### 3. Episodic Memory & Pattern Detection
- **Historical Patterns**: "Supplier X always delivers late in Q4"
- **Anomaly Detection**: Duplicate invoices, unusual amounts, suspicious patterns
- **Learning**: System improves recommendations based on feedback

### 4. Financial Intelligence Modules

#### Budget Analysis
- Variance tracking and alerting
- Year-end forecasting
- Department comparisons
- AI-powered recommendations

#### Contract Monitoring
- Expiration alerts (30/60/90 days)
- Clause extraction (payment terms, auto-renewal, SLA, penalties)
- Supplier performance scoring
- Risk assessment

#### Cash Flow Prediction
- 90-day rolling forecast
- Monte Carlo simulation with confidence intervals
- Treasury tension detection
- Payment optimization

#### Anomaly Detection
- Duplicate invoice detection
- Unusual amount flagging  
- Suspicious pattern identification
- Vendor risk analysis

### 5. Scenario Simulation
- Budget adjustment scenarios
- Contract renegotiation impact
- Monte Carlo cash flow modeling
- Side-by-side comparison

### 6. Interactive Dashboard

Five comprehensive pages:

1. **📊 Budget Augmenté** - Budget variance and forecasting
2. **📄 Contracts** - Contract monitoring and clause analysis  
3. **💰 Cash Flow** - Treasury forecasting and invoice aging
4. **🚨 Alerts** - Prioritized action center with recommendations
5. **🎲 Simulations** - What-if scenario analysis

### 7. REST API

Full-featured API with endpoints for:
- Natural language queries (`POST /query`)
- Budget analysis (`POST /api/budget/analyze`)
- Contract monitoring (`POST /api/contracts/expiring`)
- Cash flow forecasting (`POST /api/cashflow/forecast`)
- Alert management (`GET /api/alerts/list`)

Interactive API documentation at http://localhost:8000/docs

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-your-key-here

# Azure OpenAI (Optional Alternative)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Database Credentials
NEO4J_PASSWORD=financehub123
POSTGRES_PASSWORD=fincenter_secure_pass
REDIS_PASSWORD=redis_secure_pass

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Service Ports

- **Dashboard**: 8501
- **API**: 8000
- **Neo4j**: 7474 (HTTP), 7687 (Bolt)
- **Qdrant**: 6333 (HTTP), 6334 (gRPC)
- **PostgreSQL**: 5432
- **Redis**: 6379

## 📚 Usage Examples

### Natural Language Queries

```python
import requests

response = requests.post('http://localhost:8000/query', json={
    "question": "Which departments are over budget by more than 10%?"
})

print(response.json()['answer'])
# Output: "Marketing department is 15% over budget at $575,000 spent vs $500,000 allocated..."
```

### Budget Analysis

```python
response = requests.post('http://localhost:8000/api/budget/analyze', json={
    "department_id": "DEPT001",
    "year": 2024
})

budget = response.json()
print(f"Variance: {budget['variance_percent']}%")
print(f"Status: {budget['status']}")
```

### Cash Flow Forecast

```python
response = requests.post('http://localhost:8000/api/cashflow/forecast', json={
    "days": 90
})

forecast = response.json()
print(f"Tensions detected: {len(forecast['tensions'])}")
```

## 🧪 Testing

### Manual Testing

1. **Check services health**:
```bash
curl http://localhost:8000/health
```

2. **Test natural language query**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all active contracts"}'
```

3. **Access dashboard**:
Visit http://localhost:8501 and navigate through the pages

### Run Test Suite

```bash
# TODO: Add test commands once test suite is implemented
pytest tests/
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

### Database Connection Issues

```bash
# Verify Neo4j is accessible
docker-compose exec neo4j cypher-shell -u neo4j -p financehub123

# Check PostgreSQL
docker-compose exec postgres psql -U fincenter -d fincenter -c "SELECT 1;"
```

### API Errors

Check API logs:
```bash
docker-compose logs -f api
```

Common issues:
- **Missing OpenAI API key**: Set `OPENAI_API_KEY` in `.env`
- **Database not ready**: Wait 2-3 minutes for initial setup
- **Port conflicts**: Ensure ports 8000, 8501, 7474, 7687, 6333, 5432, 6379 are available

## 📖 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture
- **[API_DOCS.md](API_DOCS.md)** - Complete API reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

## 🔐 Security

- API keys stored in environment variables (never committed)
- Database credentials configurable
- CORS properly configured
- Input validation on all endpoints
- SQL injection protection via parameterized queries

**Production recommendations**:
- Use Docker secrets
- Enable HTTPS/TLS
- Implement JWT authentication
- Set up rate limiting
- Enable audit logging

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [Neo4j](https://neo4j.com/)
- [Qdrant](https://qdrant.tech/)
- [LangChain](https://langchain.com/)
- [OpenAI](https://openai.com/)

## 📞 Support

For issues and questions:
- Open a GitHub Issue
- Check existing documentation
- Review API docs at http://localhost:8000/docs

---

**Built with ❤️ for financial intelligence and decision support**
