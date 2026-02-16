# API Documentation

Base URL: `http://localhost:8000`

## Authentication

Currently no authentication required. For production, implement JWT tokens.

## Core Endpoints

### Health Check
```
GET /health
```
Returns system health status and service availability.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-16T14:30:00",
  "services": {
    "neo4j": "healthy",
    "qdrant": "healthy",
    "postgres": "healthy",
    "redis": "healthy"
  }
}
```

### Natural Language Query
```
POST /query
```
Process natural language financial queries.

**Request:**
```json
{
  "question": "Which departments are over budget?",
  "context": {}
}
```

**Response:**
```json
{
  "query": "Which departments are over budget?",
  "query_type": "budget",
  "answer": "Marketing department is 15% over budget...",
  "results": {...},
  "patterns": [...]
}
```

## Budget Endpoints

### Analyze Budget
```
POST /api/budget/analyze
```

**Request:**
```json
{
  "department_id": "DEPT001",
  "year": 2024
}
```

### Forecast Budget
```
GET /api/budget/forecast/{department_id}/{year}
```

### List Departments
```
GET /api/budget/departments
```

## Contract Endpoints

### Get Expiring Contracts
```
POST /api/contracts/expiring
```

**Request:**
```json
{
  "days_ahead": 90
}
```

### Extract Clauses
```
GET /api/contracts/{contract_id}/clauses
```

### Supplier Performance
```
GET /api/contracts/supplier/{supplier_id}/performance
```

## Cash Flow Endpoints

### Forecast Cash Flow
```
POST /api/cashflow/forecast
```

**Request:**
```json
{
  "days": 90
}
```

### Pending Invoices
```
GET /api/cashflow/pending-invoices
```

### Invoice Aging
```
GET /api/cashflow/aging
```

### Monte Carlo Simulation
```
POST /api/cashflow/monte-carlo?days=90&simulations=1000
```

## Alert Endpoints

### List Alerts
```
GET /api/alerts/list?status=active&severity=high
```

### Get Alert
```
GET /api/alerts/{alert_id}
```

### Resolve Alert
```
POST /api/alerts/{alert_id}/resolve
```

### Detect Anomalies
```
POST /api/alerts/anomalies/detect
```

## Interactive Documentation

Full interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
