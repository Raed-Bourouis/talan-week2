# ── Stage 1: Build ──────────────────────────────────────────────
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# ── Runtime ─────────────────────────────────────────────────────
# Default config — override via docker-compose / env vars
ENV HOST=0.0.0.0 \
    PORT=8000 \
    RISK_WEIGHT=0.6 \
    PROFITABILITY_WEIGHT=0.4

EXPOSE 8000

# Health-check: hit the /health endpoint every 30s
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the API server
CMD ["python", "api.py"]
