# 📡 FINCENTER API Documentation

## Base URL
```
http://localhost:8000
```

## API Features
- ✅ **100% FREE** - No API keys required
- ✅ **Auto-generated docs** at `/docs` (Swagger UI)
- ✅ **Alternative docs** at `/redoc` (ReDoc)
- ✅ **OpenAPI spec** at `/openapi.json`

## Authentication
Currently no authentication required. In production, implement your preferred method (JWT, API keys, OAuth2, etc.)

## Core Endpoints

### System

#### GET `/`
Get API information and features.

**Response:**
```json
{
  "name": "FINCENTER API",
  "version": "1.0.0",
  "description": "Financial Intelligence Hub using FREE local LLMs",
  "features": ["..."],
  "docs": "/docs",
  "health": "/health"
}
```

#### GET `/health`
Check system health and service status.

**Response:**
```json
{
  "status": "healthy|degraded|unreachable",
  "timestamp": "2024-02-16T10:30:00Z",
  "services": {
    "api": true,
    "ollama": true,
    "neo4j": true,
    "qdrant": true
  }
}
```

### Natural Language Queries

#### POST `/query`
Process natural language financial queries using local LLM.

**Request:**
```json
{
  "question": "Which departments are over budget?",
  "query_type": "budget",  // optional
  "max_results": 10  // optional
}
```

**Response:**
```json
{
  "success": true,
  "query": "Which departments are over budget?",
  "answer": "Based on current data, Marketing department is 15% over budget...",
  "query_type": "budget",
  "timestamp": "2024-02-16T10:30:00Z",
  "sources": {...}
}
```

**Example Queries:**
```bash
# Budget analysis
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which departments are over budget?"}'

# Contract monitoring
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me contracts expiring in 90 days"}'

# Supplier analysis
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which suppliers have late payment patterns?"}'

# Cash flow
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the cash flow forecast?"}'
```

### Budget

#### GET `/budgets`
Get budget information for all departments.

**Response:**
```json
{
  "success": true,
  "total_allocated": 2300000,
  "total_spent": 1975000,
  "total_remaining": 325000,
  "departments": [
    {
      "department_id": "DEPT-001",
      "department_name": "Marketing",
      "allocated": 500000,
      "spent": 425000,
      "remaining": 75000,
      "variance_pct": -15.0,
      "status": "over"
    }
  ],
  "timestamp": "2024-02-16T10:30:00Z"
}
```

### Contracts

#### GET `/contracts`
Get contract information with optional filters.

**Query Parameters:**
- `status` (optional): Filter by status (active, expired, pending)
- `expiring_days` (optional): Show contracts expiring in N days

**Examples:**
```bash
# All contracts
curl http://localhost:8000/contracts

# Active contracts only
curl http://localhost:8000/contracts?status=active

# Contracts expiring in 90 days
curl http://localhost:8000/contracts?expiring_days=90
```

**Response:**
```json
{
  "success": true,
  "contracts": [
    {
      "contract_id": "CONT-001",
      "title": "Software License Agreement",
      "supplier_name": "TechVendor Inc",
      "value": 120000,
      "start_date": "2024-01-01",
      "expiration_date": "2024-12-31",
      "status": "active",
      "auto_renewal": true,
      "days_until_expiration": 319
    }
  ],
  "total_value": 560000,
  "expiring_soon_count": 3,
  "timestamp": "2024-02-16T10:30:00Z"
}
```

### Suppliers

#### GET `/suppliers`
Get supplier information and performance metrics.

**Response:**
```json
{
  "success": true,
  "suppliers": [
    {
      "supplier_id": "SUP-001",
      "name": "TechVendor Inc",
      "payment_terms": "NET30",
      "reliability_score": 0.85,
      "avg_delay_days": 5,
      "total_contracts": 3,
      "total_paid": 150000
    }
  ],
  "timestamp": "2024-02-16T10:30:00Z"
}
```

### Invoices

#### GET `/invoices`
Get invoice information with optional status filter.

**Query Parameters:**
- `status` (optional): Filter by status (paid, pending, overdue)

**Examples:**
```bash
# All invoices
curl http://localhost:8000/invoices

# Overdue invoices only
curl http://localhost:8000/invoices?status=overdue
```

**Response:**
```json
{
  "success": true,
  "invoices": [
    {
      "invoice_id": "INV-001",
      "invoice_number": "INV-2024-001",
      "supplier_name": "TechVendor Inc",
      "amount": 10000,
      "issue_date": "2024-01-15",
      "due_date": "2024-02-14",
      "payment_date": "2024-02-12",
      "status": "paid",
      "days_overdue": 0
    }
  ],
  "total_amount": 85000,
  "overdue_count": 2,
  "overdue_amount": 30000,
  "timestamp": "2024-02-16T10:30:00Z"
}
```

### Patterns

#### GET `/patterns`
Get detected financial patterns and insights.

**Response:**
```json
{
  "success": true,
  "patterns": [
    {
      "pattern_id": "PATTERN-001",
      "pattern_type": "late_payment",
      "description": "Supplier SUP-003 consistently pays late in Q4",
      "confidence": 0.85,
      "occurrences": 3,
      "recommendation": "Negotiate better terms or find alternative supplier",
      "entities": ["SUP-003"]
    }
  ],
  "total_patterns": 5,
  "timestamp": "2024-02-16T10:30:00Z"
}
```

### Alerts

#### GET `/alerts`
Get active alerts and recommendations.

**Response:**
```json
{
  "success": true,
  "alerts": [
    {
      "alert_id": "ALERT-001",
      "alert_type": "payment",
      "severity": "critical",
      "title": "Overdue Invoice - 30 Days",
      "description": "Invoice INV-2024-002 is 30 days overdue",
      "entity_type": "invoice",
      "entity_id": "INV-002",
      "recommendation": "Contact supplier immediately",
      "status": "open",
      "created_at": "2024-02-16T10:00:00Z"
    }
  ],
  "critical_count": 3,
  "high_count": 5,
  "medium_count": 8,
  "low_count": 12,
  "timestamp": "2024-02-16T10:30:00Z"
}
```

### Cash Flow

#### GET `/cashflow/forecast`
Get cash flow forecast using Prophet ML model.

**Query Parameters:**
- `days` (optional): Forecast horizon in days (default: 90, max: 365)

**Example:**
```bash
# 90-day forecast
curl http://localhost:8000/cashflow/forecast?days=90
```

**Response:**
```json
{
  "success": true,
  "forecast_days": 90,
  "predictions": [
    {
      "prediction_date": "2024-02-17",
      "predicted_inflow": 45000,
      "predicted_outflow": 38000,
      "predicted_balance": 1207000,
      "confidence_lower": 1186300,
      "confidence_upper": 1227700
    }
  ],
  "current_balance": 1200000,
  "total_predicted_inflow": 4050000,
  "total_predicted_outflow": 3420000,
  "timestamp": "2024-02-16T10:30:00Z"
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message here",
  "detail": "Detailed error information",
  "timestamp": "2024-02-16T10:30:00Z"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (backend services down)

## Rate Limiting

Currently no rate limiting (unlimited queries - it's FREE!).

In production, consider implementing rate limiting based on your needs.

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Check health
health = requests.get(f"{BASE_URL}/health").json()
print(f"Status: {health['status']}")

# Ask a question
query = {
    "question": "Which departments are over budget?"
}
response = requests.post(f"{BASE_URL}/query", json=query).json()
print(f"Answer: {response['answer']}")

# Get contracts expiring soon
contracts = requests.get(
    f"{BASE_URL}/contracts",
    params={"expiring_days": 90}
).json()
print(f"Expiring contracts: {len(contracts['contracts'])}")

# Get overdue invoices
invoices = requests.get(
    f"{BASE_URL}/invoices",
    params={"status": "overdue"}
).json()
print(f"Overdue: ${invoices['overdue_amount']:,.0f}")

# Get cash flow forecast
forecast = requests.get(
    f"{BASE_URL}/cashflow/forecast",
    params={"days": 90}
).json()
print(f"90-day forecast: {len(forecast['predictions'])} predictions")
```

## JavaScript/TypeScript Client Example

```typescript
const BASE_URL = "http://localhost:8000";

// Check health
async function checkHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  const data = await response.json();
  console.log(`Status: ${data.status}`);
}

// Ask a question
async function askQuestion(question: string) {
  const response = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });
  const data = await response.json();
  console.log(`Answer: ${data.answer}`);
}

// Get budgets
async function getBudgets() {
  const response = await fetch(`${BASE_URL}/budgets`);
  const data = await response.json();
  return data.departments;
}

// Usage
await checkHealth();
await askQuestion("Which departments are over budget?");
const budgets = await getBudgets();
```

## Webhook Integration (Future)

Coming soon: Webhook support for real-time alerts.

```json
{
  "webhook_url": "https://your-app.com/webhook",
  "events": ["alert.created", "pattern.detected"],
  "secret": "your_webhook_secret"
}
```

## GraphQL Support (Future)

Coming soon: GraphQL API for more flexible querying.

## Best Practices

### 1. Use Specific Queries
```python
# ❌ Too general
"Tell me about finances"

# ✅ Specific
"Show me Marketing department budget variance for Q1 2024"
```

### 2. Cache Responses
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_budgets():
    return requests.get(f"{BASE_URL}/budgets").json()
```

### 3. Handle Errors Gracefully
```python
try:
    response = requests.post(f"{BASE_URL}/query", json=query, timeout=30)
    response.raise_for_status()
    return response.json()
except requests.exceptions.Timeout:
    print("Query timeout - try again")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
```

### 4. Use Appropriate Timeouts
```python
# Short timeout for health checks
requests.get(f"{BASE_URL}/health", timeout=5)

# Longer timeout for LLM queries
requests.post(f"{BASE_URL}/query", json=query, timeout=30)
```

## Performance

### Response Times (Typical)
- Health check: <100ms
- Budgets/Contracts/Invoices: 100-500ms
- Pattern detection: 1-3 seconds
- LLM queries: 5-10 seconds (CPU), 1-3 seconds (GPU)
- Cash flow forecast: 2-5 seconds

### Optimization Tips
1. Enable GPU for 3-5x faster LLM inference
2. Use smaller models (mistral:7b or phi3:3b) for faster responses
3. Cache frequent queries
4. Batch similar requests

## API Costs

**Total API Costs: $0.00** ✨

Unlike cloud-based LLM APIs:
- No per-token charges
- No per-query fees
- No rate limits (based on your hardware)
- Unlimited queries

**Estimated Savings:**
- vs. OpenAI GPT-4: ~$3000-5000/month
- vs. Anthropic Claude: ~$2000-4000/month
- vs. Google PaLM: ~$2500-4500/month

## Support & Feedback

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See README.md and other guides
- **Examples**: Check `/examples` directory for more code samples

## Changelog

### v1.0.0 (2024-02-16)
- Initial release
- Core endpoints: query, budgets, contracts, suppliers, invoices
- Pattern detection and alerts
- Cash flow forecasting
- 100% FREE with local LLMs (Ollama)

---

**Made with ❤️ by the FINCENTER team**

**Total Cost: $0.00** | **100% Free & Open Source** | **No API Keys Required**
