# Makefile for GraphRAG system

.PHONY: help install dev-install test lint format docker-build docker-up docker-down clean

help:
	@echo "GraphRAG System - Available commands:"
	@echo ""
	@echo "  make install        - Install dependencies"
	@echo "  make dev-install    - Install in development mode"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start all services with Docker Compose"
	@echo "  make docker-down   - Stop all services"
	@echo "  make clean         - Clean temporary files"
	@echo "  make run-api       - Run API server locally"
	@echo "  make pull-model    - Pull Llama 3.1 model in Ollama"

install:
	pip install -r requirements.txt

dev-install:
	pip install -e .

test:
	pytest tests/ -v

lint:
	flake8 graphrag/ --max-line-length=100

format:
	black graphrag/ tests/ examples/

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Services started. Access API at http://localhost:8000"

docker-down:
	docker-compose down

pull-model:
	docker exec -it $$(docker ps -q -f name=ollama) ollama pull llama3.1

run-api:
	uvicorn graphrag.api.app:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf dist build
