# F360 Financial Synthesis Engine — Week 2: Decision Fusion

**PFE 2026 — Talan**

---

## 1. What Is This Project?

This project belongs to **Week 2** of the PFE (Projet de Fin d'Études) internship at **Talan**. The overall PFE goal is to build a **self-adaptive financial model (F360)** that can autonomously monitor enterprise financial health, detect threats early, and recommend tactical actions.

**Week 2 focuses on one critical piece of this model: Decision Fusion.**

The engine takes financial signals coming from multiple heterogeneous sources — ERP systems, knowledge graphs, IoT production data, and scenario simulations — and **fuses them into a single, prioritized, explainable decision**. The key question it answers is:

> *Given conflicting or complementary signals from different data sources, which tactical financial action should the enterprise take — and why?*

---

## 2. What Is Decision Fusion?

**Decision Fusion** (also called information fusion or evidence combination) is the process of combining decisions, predictions, or evidence from **multiple independent sources** to produce a final decision that is **more accurate and robust** than any single source alone.

### Why Is It Needed in Finance?

In enterprise finance, decisions rely on data from many places:

| Source | What It Provides | Example |
|--------|-----------------|---------|
| **ERP / SAP** | Invoices, budgets, cash flow | "Client X has a 15% spike in unpaid invoices" |
| **Knowledge Graph** | Client relationships, historical patterns | "Client X's parent company is restructuring" |
| **IoT / Production** | Factory output, supply chain metrics | "Production dropped 12% this quarter" |
| **Scenario Simulations** | What-if projections | "If we do nothing, cash flow drops 20%" |

Each source tells part of the story. **No single source is sufficient.** Decision fusion combines them:

```
  ERP data ─────────┐
  Knowledge Graph ───┤──→ [ DECISION FUSION ] ──→ Tactical Action + Explanation
  IoT Production ────┤
  Simulations ───────┘
```

---

## 3. Decision Fusion Strategies Implemented

This project implements **three** mathematically distinct fusion strategies plus a **meta-fusion** layer that combines all three:

### 3.1 Weighted Averaging Fusion

The simplest and most interpretable approach. Each scenario is scored along two axes:

- **Risk Mitigation Score** — How much does this scenario reduce financial risk?
- **Profitability Score** — How much does this scenario protect or improve margin?

These are combined using configurable weights:

$$\text{FusionScore}(S_i) = w_{\text{risk}} \times \text{RiskScore}(S_i) + w_{\text{profit}} \times \text{ProfitScore}(S_i)$$

Default weights: Risk = 60%, Profitability = 40%. When critical weak signals are detected, the engine **automatically shifts** toward risk-averse weighting (+20%).

**Strengths**: Simple, explainable, fast  
**Weakness**: Assumes linear combination, no uncertainty modeling

### 3.2 Dempster-Shafer Theory (DST)

An evidence-based framework from **mathematical theory of evidence** (Shafer, 1976). Unlike probability, DST can represent **ignorance** — the state of "I don't know" — separately from "it's 50/50".

**Core concepts:**
- **Mass function** $m(A)$: Degree of belief committed exactly to hypothesis $A$
- **Belief** $Bel(A)$: Total evidence supporting $A$ (lower bound of probability)
- **Plausibility** $Pl(A)$: Maximum possible probability for $A$ (upper bound)
- **Dempster's Rule**: Combines two independent mass functions:

$$m_{1,2}(A) = \frac{1}{1-K} \sum_{B \cap C = A} m_1(B) \cdot m_2(C)$$

where $K$ is the **conflict** between sources (higher = sources disagree more).

**Insight produced**: The gap between $Bel(A)$ and $Pl(A)$ tells you **how much uncertainty remains** even after fusing all evidence. A narrow gap = confident decision. A wide gap = more data needed.

**Strengths**: Models uncertainty and ignorance, quantifies source conflict  
**Weakness**: Computationally heavier, can be counter-intuitive with high conflict

### 3.3 Bayesian Inference Fusion

A probabilistic approach using **Bayes' theorem** to sequentially update beliefs as new evidence arrives:

$$P(H|E) = \frac{P(E|H) \cdot P(H)}{P(E)}$$

Each data source is treated as an observation. Starting from a **uniform prior** (equal belief in all scenarios), the engine updates step by step:

```
Prior → [Invoice Evidence] → Posterior₁ → [Production Evidence] → Posterior₂ → ... → Final
```

**Key diagnostics:**
- **Shannon Entropy**: Measures remaining uncertainty. $H = -\sum p_i \log p_i$. Lower = more certain.
- **KL Divergence**: Distance between prior and posterior — how much the evidence changed your mind.
- **Bayes Factor**: Strength of evidence for the winning hypothesis. Values > 100 = decisive evidence.

**Strengths**: Rigorous probabilistic foundation, sequential updating  
**Weakness**: Requires likelihood calibration, assumes prior independence

### 3.4 Meta-Fusion (Consensus Layer)

When three strategies may disagree, meta-fusion determines the **final recommendation** using weighted consensus voting:

| Strategy | Weight |
|----------|--------|
| Weighted Average | 30% |
| Dempster-Shafer | 40% |
| Bayesian Inference | 30% |

DST gets the highest meta-weight because it explicitly models uncertainty and inter-source conflict.

The **agreement level** (0–100%) measures how many strategies converge on the same answer. When all three agree, confidence is high. When they diverge, the output flags the disagreement for human review.

---

## 4. The Insight Layer: Weak Signal Correlation

Beyond decision fusion, the engine performs **weak signal correlation** — detecting patterns that only become meaningful when cross-referenced across sources:

| Weak Signal Type | Sources Combined | What It Detects |
|-----------------|-----------------|-----------------|
| **Production-Client Systemic Risk** | IoT + Knowledge Graph + ERP | Production slowdown + client restructuring + invoice spikes = systemic threat |
| **Budget Liquidity Squeeze** | ERP Budget + ERP Invoices | Low budget remaining + rising unpaid invoices = liquidity crisis |
| **Historical Pattern Recurrence** | Knowledge Graph Memory | Current situation matches a past incident that led to cash flow delays |

Each weak signal has a **correlation strength** (0.0–1.0) and a **risk level** (Low / Medium / High / Critical). Critical signals trigger automatic weight adjustment in the fusion layer.

This is the engine's **early warning system** — it detects threats before they fully materialize.

---

## 5. How the Pipeline Works (End-to-End)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           INPUT SOURCES                                  │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  ERP Data   │  │ Knowledge Graph  │  │   IoT    │  │ Simulations │  │
│  │  (invoices, │  │ (client context, │  │(production│  │ (what-if    │  │
│  │   budgets)  │  │  history, links) │  │  output)  │  │  scenarios) │  │
│  └──────┬──────┘  └────────┬─────────┘  └─────┬────┘  └──────┬──────┘  │
└─────────┼──────────────────┼──────────────────┼──────────────┼──────────┘
          └──────────────────┴──────────────────┴──────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │  Stage 1: Data Aggregation      │
                    │  • Financial stress scoring     │
                    │  • Scenario risk analysis       │
                    │  • Source normalization          │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │  Stage 2: Weak Signal Detection │
                    │  • Cross-source correlation     │
                    │  • Pattern matching (episodic)  │
                    │  • Risk level classification    │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │  Stage 3: Decision Fusion       │
                    │  ┌─────────┐ ┌─────┐ ┌──────┐ │
                    │  │Weighted │ │ DST │ │Bayes │ │
                    │  │Average  │ │     │ │      │ │
                    │  └────┬────┘ └──┬──┘ └──┬───┘ │
                    │       └─────────┼───────┘     │
                    │            Meta-Fusion         │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │  Stage 4: Prioritization        │
                    │  • Priority: High/Medium/Low    │
                    │  • Explainable recommendation   │
                    │  • Confidence scoring            │
                    │  • Alternative actions ranking   │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │         OUTPUT (JSON)           │
                    │  Tactical Decision + Insights   │
                    │  → Feedback Loop Validation     │
                    └────────────────────────────────┘
```

---

## 6. Example: What the Engine Actually Produces

**Input situation**: Client X has a 15% invoice spike, production is down 12%, budget is at 5%, and the knowledge graph says the client's parent company is restructuring. Two scenarios are simulated: (A) do nothing or (B) offer early payment discount.

**Output:**

```json
{
  "tactical_priority": "High",
  "recommended_action": "Trigger early payment incentive for Client CLIENT_X",
  "explanation": "Prioritize SCENARIO_B (Early payment discount) based on weighted 
    decision fusion. Risk mitigation weighted at 80% due to CRITICAL weak signal 
    detection. SCENARIO_B eliminates 20% cash flow risk at cost of 5% margin...",
  "weak_signal_alert": [
    {
      "signal_type": "Production-Client_Systemic_Risk",
      "correlation_strength": 0.6,
      "source_indices": ["IoT_Production", "KG_Client_Parent", "ERP_Invoices"],
      "risk_level": "High"
    }
  ],
  "predicted_financial_outcome": {
    "cash_flow_impact_pct": 0.0,
    "margin_impact_pct": -5.0,
    "time_to_impact_days": 30,
    "probability": 0.9
  },
  "confidence_score": 0.82,
  "meta_fusion": {
    "recommended_scenario": "SCENARIO_A",
    "confidence": 0.754,
    "agreement_level": 0.67,
    "strategy_breakdown": {
      "Weighted Average": "SCENARIO_B (82.3%)",
      "Dempster-Shafer": "SCENARIO_A (55.2%, conflict=34.1%)",
      "Bayesian": "SCENARIO_A (95.2%, Bayes Factor=255x)"
    }
  }
}
```

**Key insight**: The three strategies can **disagree**. Weighted averaging picks Scenario B (early payment) because it optimizes the risk/profit tradeoff linearly. But DST and Bayesian both identify Scenario A as having the highest evidence weight. Meta-fusion resolves the conflict with a 67% agreement level, flagging the disagreement for human review.

---

## 7. Project Structure

```
week_2-decision_fusion/
│
├── f360_synthesis_engine.py     # Core engine (weighted averaging fusion)
├── dempster_shafer.py           # Dempster-Shafer Theory implementation
├── bayesian_fusion.py           # Bayesian inference fusion
├── multi_strategy_engine.py     # Unified multi-strategy + meta-fusion
├── config.py                    # Configuration presets (conservative/balanced/aggressive/crisis)
│
├── keyword_search.py            # Keyword search engine (Personne 2)
├── graph_peers.py               # Knowledge graph peers enrichment (Personne 3)
├── simulation_bridge.py         # Simulation bridge (Personne 4)
├── assistant.py                 # Rule-based assistant with ask() function
│
├── api.py                       # FastAPI REST API (for Docker / inter-service)
├── Dockerfile                   # Container image definition
├── docker-compose.yml           # Full pipeline orchestration
├── .dockerignore                # Docker build exclusions
│
├── example_usage.py             # Basic usage demo (high-risk & low-risk scenarios)
├── advanced_integration.py      # Enterprise integration patterns
├── comparison_demo.py           # Side-by-side strategy comparison
│
├── test_f360_engine.py          # Unit tests — core engine (15 tests)
├── test_advanced_fusion.py      # Unit tests — DST, Bayesian, meta-fusion (33 tests)
├── test_assistant.py            # Unit tests — assistant + search + graph (38 tests)
│
├── README.md                    # ← This file
├── ARCHITECTURE.md              # Detailed architecture diagrams
├── QUICKSTART.md                # Quick start guide
├── requirements.txt             # Dependencies (fastapi, uvicorn, pydantic)
└── .gitignore
```

---

## 8. How to Run

### Local (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests (86 total)
python test_f360_engine.py          # 15 tests
python test_advanced_fusion.py      # 33 tests
python test_assistant.py            # 38 tests

# Run demos
python assistant.py                 # Interactive assistant demo (5 queries)
python example_usage.py             # Basic high-risk / low-risk comparison
python comparison_demo.py           # Side-by-side strategy comparison
python advanced_integration.py      # Enterprise patterns (crisis mode, feedback loop)

# Start the API server locally
python api.py                       # → http://localhost:8000/docs
```

### Docker (containerised)

```bash
# Build & start the decision-fusion service
docker-compose up --build

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness / readiness probe |
| `POST` | `/api/v1/fuse` | **Main** — Run multi-strategy decision fusion |
| `POST` | `/api/v1/fuse/simple` | Lightweight raw JSON output |
| `POST` | `/api/v1/feedback` | Submit actual outcomes (feedback loop) |
| `POST` | `/api/v1/ask` | Natural-language assistant |
| `GET` | `/api/v1/strategies` | List available fusion strategies |
| `GET` | `/api/v1/config` | Current engine configuration |

---

## 9. Configuration Presets

The engine supports four operational modes:

| Preset | Risk Weight | Profitability Weight | Use Case |
|--------|:-----------:|:--------------------:|----------|
| **Conservative** | 80% | 20% | High-uncertainty environments |
| **Balanced** | 60% | 40% | Normal operations (default) |
| **Aggressive** | 30% | 70% | Growth-focused decisions |
| **Crisis** | 90% | 10% | Emergency financial response |

When **CRITICAL** weak signals fire, the engine automatically shifts toward conservative weighting regardless of the configured preset.

---

## 10. Integration Into the PFE Workflow

This module is a **standalone microservice**. It does not embed Neo4j, Kafka, or any other infrastructure. Instead, upstream services send it data over HTTP and it returns fused decisions.

### Where it sits in the pipeline

```
  Other PFE modules (upstream)                This module                   Downstream
  ─────────────────────────────               ───────────                   ──────────
  Contexte Financier (Personne 1)  ──┐
  Knowledge Graph    (Personne 3)  ──┼──→  POST /api/v1/fuse  ──→  JSON response  ──→  UI / Dashboard
  Scenario Simulator (Personne 4)  ──┘                                                  Real-time module
  Real-time Feedback               ──────→  POST /api/v1/feedback
```

### How another service calls decision fusion

1. **Build the container** (or run locally with `python api.py`):

```bash
docker-compose up --build          # → http://localhost:8000
```

2. **POST real data** from your service to `/api/v1/fuse`:

```python
import requests

result = requests.post("http://localhost:8000/api/v1/fuse", json={
    "financial_data": {
        "unpaid_invoices_spike": 15.0,
        "client_id": "CLIENT_X",
        "production_output_change": -12.0,
        "budget_remaining_q3": 5.0
    },
    "kg_context": {
        "client_parent_status": "Undergoing restructuring",
        "similar_historical_pattern": {"years_ago": 2, "cash_flow_delay_days": 30},
        "external_data_signals": [],
        "risk_indicators": []
    },
    "scenarios": [
        {"scenario_id": "A", "description": "Do nothing",
         "cash_flow_impact": -20.0, "margin_impact": 0.0,
         "probability": 0.85, "time_horizon_days": 60},
        {"scenario_id": "B", "description": "Early payment discount",
         "cash_flow_impact": 0.0, "margin_impact": -5.0,
         "probability": 0.90, "time_horizon_days": 30}
    ]
}).json()

print(result["recommended_action"])   # tactical action
print(result["consensus_confidence"]) # 0-1 confidence score
```

3. **Use the response** in your UI or downstream logic. The JSON contains:
   - `recommended_action` — what to do
   - `consensus_confidence` — how sure the engine is (0-1)
   - `strategy_results` — per-strategy breakdown (Weighted / DST / Bayesian)
   - `weak_signals` — early warnings from cross-source correlation
   - `meta_fusion` — agreement level across strategies

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Listen port |
| `RISK_WEIGHT` | `0.6` | Risk vs. profitability balance (0-1) |
| `PROFITABILITY_WEIGHT` | `0.4` | Profitability weight (1 - RISK_WEIGHT) |

Override in `docker-compose.yml` or pass via `-e` when running the container.

### Inside the container

The Dockerfile is minimal: Python 3.11-slim, pip install, expose port 8000, and run `api.py`. No database, no message broker — those live in their own containers managed by the teams responsible for them.

```
Dockerfile
  └─ python:3.11-slim
       └─ pip install fastapi uvicorn pydantic
            └─ COPY . /app
                 └─ CMD python api.py   (port 8000)
```

---

## 11. Key Takeaways

1. **Decision fusion is not just averaging** — Three mathematically distinct strategies (Weighted, DST, Bayesian) can reach different conclusions. Meta-fusion resolves disagreements and flags low-confidence splits for human review.

2. **Uncertainty is explicit** — DST's belief/plausibility intervals and Bayesian entropy quantify "how sure are we?" separately from the decision itself.

3. **Weak signals are the early warning system** — A single invoice spike is noise. A spike + production drop + parent restructuring is a correlated threat.

4. **Every decision is explainable** — Full trace: which sources contributed, which signals fired, why this action was chosen, what outcome is predicted, and what alternatives were considered.

5. **Integration is HTTP** — Other PFE modules don't import Python files. They `POST` JSON to the API and get a decision back. The container is self-contained.

---

**Talan — PFE 2026**  
Week 2: Decision Fusion & Insight Generation
