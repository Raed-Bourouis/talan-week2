#!/bin/bash
# Quick start script for GraphRAG system

set -e

echo "==============================================="
echo "GraphRAG System - Quick Start"
echo "==============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"
echo ""

# Start services
echo "Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."
echo "(This may take 30-60 seconds)"

# Wait for services
max_attempts=30
attempt=0
all_healthy=false

while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    
    # Check if all services are healthy
    unhealthy=$(docker-compose ps --format json 2>/dev/null | grep -c '"Health":"unhealthy"' || true)
    starting=$(docker-compose ps --format json 2>/dev/null | grep -c '"Health":"starting"' || true)
    
    if [ "$unhealthy" -eq 0 ] && [ "$starting" -eq 0 ]; then
        all_healthy=true
        break
    fi
    
    echo -ne "  Attempt $attempt/$max_attempts\r"
    sleep 2
done

echo ""
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✓ All services are healthy${NC}"
else
    echo -e "${YELLOW}⚠ Some services may still be starting${NC}"
fi
echo ""

# Pull LLM model
echo "Checking Ollama model..."
ollama_container=$(docker-compose ps -q ollama)

if [ -n "$ollama_container" ]; then
    # Check if model is already pulled
    model_exists=$(docker exec "$ollama_container" ollama list 2>/dev/null | grep -c "llama3.1" || true)
    
    if [ "$model_exists" -eq 0 ]; then
        echo "Pulling Llama 3.1 model (this may take several minutes)..."
        docker exec "$ollama_container" ollama pull llama3.1
        echo -e "${GREEN}✓ Model pulled successfully${NC}"
    else
        echo -e "${GREEN}✓ Llama 3.1 model already available${NC}"
    fi
else
    echo -e "${RED}✗ Ollama container not found${NC}"
fi

echo ""
echo "==============================================="
echo -e "${GREEN}GraphRAG System is ready!${NC}"
echo "==============================================="
echo ""
echo "Access the API:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"
echo ""
echo "Access individual services:"
echo "  - Qdrant UI: http://localhost:6333/dashboard"
echo "  - Neo4j Browser: http://localhost:7474 (user: neo4j, password: password)"
echo ""
echo "Run examples:"
echo "  python examples/basic_usage.py"
echo "  python examples/rest_api_usage.py"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
