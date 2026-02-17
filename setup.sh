#!/bin/bash
set -e

echo "🚀 Setting up Document Processing & RAG System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{sample_docs,processed,graphrag}

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update if needed."
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
sleep 10

# Check if Ollama is healthy
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec ollama ollama list &> /dev/null; then
        echo "✅ Ollama is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for Ollama... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Ollama failed to start. Please check logs: docker logs ollama"
    exit 1
fi

# Pull the Llama2 model
echo "📥 Pulling Llama2 model (this may take a few minutes)..."
docker exec ollama ollama pull llama2

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Services are running:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Ollama: http://localhost:11434"
echo ""
echo "📖 Next steps:"
echo "   1. Check API health: curl http://localhost:8000/health"
echo "   2. View API docs: open http://localhost:8000/docs"
echo "   3. Test with sample documents in data/sample_docs/"
echo ""
echo "📊 To test the system:"
echo "   curl -X POST http://localhost:8000/api/v1/parse -F 'file=@data/sample_docs/annual_report_2023.pdf'"
echo ""
