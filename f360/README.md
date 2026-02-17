# F360 – Financial Command Center

> AI-native financial intelligence platform built on a **7-layer cognitive pipeline** — from multimodal data ingestion through real-time feedback loops to tactical decision fusion and weak-signal correlation.

---

## Architecture – 7-Layer Cognitive Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      F360 – Financial Command Center                    │
├─────────────────────────────────────────────────────────────────────────┤
│  FRONTEND (Next.js 14 + TailwindCSS + Recharts)                         │
│  Dashboard Tactique │ KPIs │ Alerts │ Simulations │ Weak Signals        │
├──────────────────────────────┬──────────────────────────────────────────┤
│  Layer 7 – Recommendation    │  API de Recommandation                   │
│  Dashboard Tactique          │  Corrélation d'Indices Faibles           │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Layer 6 – Decision Fusion   │  Décisions Tactiques (prioritised)       │
│                              │  Agrégation Multi-sources (weighted)     │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Layer 5 – Simulation        │  Moteur Physique Simulation Parallèle    │
│                              │  Génération de Scénarios IA              │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Layer 4 – Real-Time Feedback│  Calcul Écart Prévu / Réel              │
│                              │  Récompense / Échec → Ré-indexation     │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Layer 3 – RAGraph           │  Mémoire Épisodique                     │
│                              │  RAG Orchestrator + LLM Raisonnement    │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Layer 2 – Cognitive Ingestion│ Extraction & Vectorisation             │
│                              │  Indexation Vector + Metadata            │
├──────────────────────────────┼──────────────────────────────────────────┤
│  Layer 1 – Sources           │  S3 / Kafka / API / SharePoint           │
│  Multimodales                │  PDF / Images / Audio / Video            │
│                              │  IoT / Logs                              │
├──────────────────────────────┴──────────────────────────────────────────┤
│  DATA LAYER                                                             │
│  PostgreSQL 16 + pgvector │ Neo4j 5 │ OpenAI API (GPT-4o)              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, async/await |
| Database | PostgreSQL 16 + pgvector (IVFFlat) |
| Vector Search | pgvector (cosine similarity, 1 536 dims) |
| Knowledge Graph | Neo4j 5 (Community + APOC) |
| LLM | OpenAI API (GPT-4o + text-embedding-3-small + Whisper) |
| Document Parsing | pdfplumber, openpyxl, pandas, pytesseract (OCR), ffmpeg |
| Connectors | S3 (aiobotocore), Kafka (aiokafka), SharePoint (MS Graph), REST APIs |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Frontend | Next.js 14, React 18, TailwindCSS, Recharts |
| Deployment | Docker Compose |

## Project Structure

```
f360/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── sql/
│   │   └── init.sql                        # DB schema (PostgreSQL + pgvector)
│   ├── app/
│   │   ├── main.py                         # FastAPI entry point
│   │   ├── core/
│   │   │   ├── config.py                   # Settings (env vars)
│   │   │   ├── database.py                 # Async SQLAlchemy session
│   │   │   ├── neo4j_client.py             # Neo4j connection manager
│   │   │   └── security.py                 # JWT + password hashing
│   │   ├── api/v1/
│   │   │   ├── __init__.py                 # Router aggregation (7 layers)
│   │   │   ├── auth.py                     # /auth
│   │   │   ├── sources.py                  # /sources (L1 – upload, connectors, IoT)
│   │   │   ├── budget.py                   # /budget
│   │   │   ├── contracts.py                # /contracts
│   │   │   ├── cashflow.py                 # /cashflow
│   │   │   ├── ragraph.py                  # /ragraph (L3 – query, reason, memory)
│   │   │   ├── feedback.py                 # /feedback (L4 – gaps, cycle, history)
│   │   │   ├── simulate.py                 # /simulate (L5 – parallel engine)
│   │   │   ├── fusion.py                   # /fusion (L6/L7 – decisions, weak-signals, dashboard, scenarios)
│   │   │   └── recommend.py                # /recommendations
│   │   ├── models/
│   │   │   ├── user.py                     # User ORM
│   │   │   └── financial.py                # Financial ORM models
│   │   ├── schemas/
│   │   │   └── schemas.py                  # Pydantic schemas (all layers)
│   │   └── services/
│   │       ├── sources/                    # ── Layer 1 ──
│   │       │   ├── connectors.py           #   S3, Kafka, API, SharePoint
│   │       │   ├── parsers.py              #   PDF, Excel, Image (OCR), Audio, Video
│   │       │   └── iot_logger.py           #   IoT events, logs, anomaly detection
│   │       ├── cognitive_ingestion/        # ── Layer 2 ──
│   │       │   ├── extractor.py            #   Financial entity extraction (regex + LLM)
│   │       │   ├── vectorizer.py           #   Chunking + OpenAI embedding
│   │       │   └── indexer.py              #   Full ingest / reindex / search pipeline
│   │       ├── ragraph/                    # ── Layer 3 ──
│   │       │   ├── episodic_memory.py      #   Episode store + DB persistence
│   │       │   ├── orchestrator.py         #   RAG orchestrator (vector + memory + graph + LLM)
│   │       │   └── reasoning.py            #   Chain-of-thought, comparative analysis
│   │       ├── realtime_feedback/          # ── Layer 4 ──
│   │       │   ├── gap_calculator.py        #   Predicted vs actual gap computation
│   │       │   └── reindexer.py            #   Reward / penalty classification, re-indexation
│   │       ├── simulation/                 # ── Layer 5 ──
│   │       │   ├── parallel_engine.py      #   Parallel simulation engine (ThreadPool)
│   │       │   └── scenario_generator.py   #   AI scenario generation, sensitivity, strategy comparison
│   │       ├── decision_fusion/            # ── Layer 6 ──
│   │       │   ├── aggregator.py           #   Multi-source signal aggregation (weighted, time-decay)
│   │       │   └── tactical.py             #   Tactical decision engine (rules + LLM enrichment)
│   │       ├── recommendation/             # ── Layer 7 ──
│   │       │   ├── engine.py               #   Rule-based + LLM recommendations
│   │       │   ├── dashboard.py            #   Tactical dashboard data provider
│   │       │   └── weak_signals.py         #   Weak signal correlation engine
│   │       ├── graph/
│   │       │   └── knowledge_graph.py      #   Neo4j schema + Cypher queries
│   │       ├── ingestion/                  #   (legacy – superseded by L1 + L2)
│   │       │   ├── pipeline.py
│   │       │   ├── parsers.py
│   │       │   └── entity_extractor.py
│   │       └── rag/                        #   (legacy – superseded by L3)
│   │           ├── embedder.py
│   │           └── retriever.py
│   └── tests/
│       ├── test_simulation.py
│       ├── test_entity_extractor.py
│       └── test_chunker.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── tailwind.config.js
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx                    # Main dashboard
        │   └── globals.css
        ├── components/
        │   ├── Sidebar.tsx
        │   ├── KPICard.tsx
        │   ├── BudgetChart.tsx
        │   ├── CashflowChart.tsx
        │   └── AlertsPanel.tsx
        └── lib/
            └── api.ts                      # API client
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An OpenAI API key (optional for development)

### 1. Clone & Configure

```bash
cd f360
cp .env.example .env
# Edit .env with your settings (especially OPENAI_API_KEY)
```

### 2. Start All Services

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL + pgvector** on port `5432`
- **Neo4j** on ports `7474` (browser) and `7687` (bolt)
- **Backend API** on port `8000`
- **Frontend** on port `3000`

### 3. Access the Application

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| API Documentation (Swagger) | http://localhost:8000/docs |
| API Documentation (ReDoc) | http://localhost:8000/redoc |
| Neo4j Browser | http://localhost:7474 |
| Health Check | http://localhost:8000/health |

### 4. Development Without Docker

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 5. Run Tests

```bash
cd backend
pytest tests/ -v
```

## API Endpoints (25 routes)

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login → JWT token |
| GET | `/api/v1/auth/me` | Current user profile |

### Layer 1 – Sources Multimodales
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sources/upload` | Upload multimodal file (PDF, Excel, Image, Audio, Video) |
| POST | `/api/v1/sources/connector/test` | Test S3 / Kafka / API / SharePoint connector |
| POST | `/api/v1/sources/iot/ingest` | Ingest IoT events with anomaly detection |

### Financial CRUD
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/budget/` | Create budget line |
| GET | `/api/v1/budget/overview` | Budget overview with deviations |
| GET | `/api/v1/contracts/` | List contracts |
| GET | `/api/v1/contracts/alerts` | Contract alerts (expiring, overbudget) |
| GET | `/api/v1/cashflow/forecast` | Cashflow projection J+N |

### Layer 3 – RAGraph
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ragraph/query` | RAG orchestrated query (vector + episodic memory + graph + LLM) |
| POST | `/api/v1/ragraph/reason` | Chain-of-thought reasoning on a financial question |
| GET | `/api/v1/ragraph/memory/recall` | Recall past episodes from episodic memory |

### Layer 4 – Real-Time Feedback
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/feedback/gaps` | Compute predicted vs actual gaps (budget, cashflow, contracts) |
| POST | `/api/v1/feedback/cycle` | Full feedback cycle: gaps → classify → reindex → store |
| GET | `/api/v1/feedback/history` | Retrieve feedback event history |

### Layer 5 – Simulation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/simulate/` | Run parallel simulation (budget, cashflow, Monte Carlo, renegotiation) |

### Layer 6/7 – Fusion, Decisions & Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fusion/decisions` | Generate tactical decisions (multi-source aggregation) |
| POST | `/api/v1/fusion/weak-signals` | Detect and correlate weak signals |
| GET | `/api/v1/fusion/dashboard` | Tactical dashboard payload (KPIs, alerts, trends) |
| POST | `/api/v1/fusion/scenarios` | AI-powered scenario generation |

### Recommendations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/recommendations/` | List recommendations |
| POST | `/api/v1/recommendations/generate` | Generate AI recommendations |

## Simulation Types

### 1. Budget Variation
```json
{
  "simulation_type": "budget_variation",
  "parameters": {
    "base_budget": 2000000,
    "variation_pct": [-15, -10, -5, 0, 5, 10],
    "categories": ["OPEX", "CAPEX", "HR", "IT"]
  }
}
```

### 2. Cashflow Projection (J+90)
```json
{
  "simulation_type": "cashflow_projection",
  "parameters": {
    "initial_balance": 500000,
    "daily_avg_inflow": 15000,
    "daily_avg_outflow": 12000,
    "days": 90,
    "volatility": 0.15
  }
}
```

### 3. Monte Carlo Risk Analysis
```json
{
  "simulation_type": "monte_carlo",
  "parameters": {
    "base_revenue": 5000000,
    "base_costs": 4200000,
    "revenue_volatility": 0.15,
    "cost_volatility": 0.10,
    "num_simulations": 10000,
    "periods": 12
  }
}
```

### 4. Contract Renegotiation Impact
```json
{
  "simulation_type": "renegotiation",
  "parameters": {
    "current_annual_cost": 500000,
    "proposed_discount_pct": 10,
    "contract_duration_years": 3,
    "inflation_rate": 0.03,
    "has_indexation_clause": true,
    "penalty_exit_pct": 5
  }
}
```

## Knowledge Graph (Neo4j)

### Nodes
`Company`, `Contract`, `Invoice`, `Budget`, `Department`, `Supplier`, `Client`

### Edges
`GENERATES`, `PAYS`, `BELONGS_TO`, `EXCEEDS`, `LINKS_TO`

### Example Cypher Queries

```cypher
-- All contracts for a company
MATCH (c:Company {id: $company_id})-[:GENERATES]->(ct:Contract)
RETURN ct.reference, ct.title, ct.total_amount
ORDER BY ct.end_date;

-- Invoices exceeding budget
MATCH (i:Invoice)-[:EXCEEDS]->(b:Budget)
RETURN b.category, b.planned_amount, collect(i.invoice_number);

-- Full financial path
MATCH path = (c:Company)-[:GENERATES]->(ct:Contract)-[:LINKS_TO]->(i:Invoice)
RETURN ct.reference, i.invoice_number, i.amount_ttc;
```

## RAGraph – Cognitive Search (Layer 3)

Example query:
> "Quels contrats contiennent des clauses de pénalité indexées sur l'inflation ?"

The RAGraph pipeline:
1. Embeds the question using OpenAI `text-embedding-3-small`
2. Performs **vector similarity search** in pgvector
3. Recalls **past relevant episodes** from episodic memory
4. Traverses the **Neo4j knowledge graph** for related entities
5. Sends combined context to **GPT-4o** with chain-of-thought reasoning
6. Returns answer with source citations
7. **Stores the interaction** as a new episode for future recall

## Decision Fusion (Layer 6)

The tactical decision engine:
1. Collects **signals** from simulation results, gap analysis, RAG insights, and graph data
2. Applies **confidence-weighted**, **time-decayed** aggregation per topic
3. Detects **conflicts** between opposing sources
4. Maps aggregated scores to **prioritised tactical decisions** (P1–P4)
5. Enriches top decisions with **LLM-generated rationale and actions**

## Weak Signal Correlation (Layer 7)

Four detection strategies run in parallel:
- **Category clustering** – repeated signals in the same domain
- **Temporal clustering** – bursts of signals within a 72-hour window
- **Cross-source convergence** – independent sources flagging the same area
- **Trend detection** – escalating signal strength over time

## License

MIT
