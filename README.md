# Document Processing & RAG System

A comprehensive document processing system with entity extraction and Microsoft GraphRAG integration, powered by local LLMs through Ollama.

## Features

- **Document Parsing**: Support for PDF, Excel (.xlsx), and Word (.docx) documents
- **Entity Extraction**: Extract financial entities using local LLMs via Ollama
- **GraphRAG Integration**: Index documents and perform RAG-based queries using Microsoft GraphRAG concepts
- **REST API**: Full-featured FastAPI-based REST API
- **Docker Support**: Complete Docker setup with Ollama integration
- **Sample Data**: Pre-built financial documents for testing

## Architecture

```
├── src/
│   ├── parsers/          # Document parsers (PDF, Excel, Word)
│   ├── entities/         # Entity extraction with LLM
│   ├── graphrag/         # GraphRAG implementation
│   └── api/              # FastAPI REST API
├── data/
│   ├── sample_docs/      # Sample financial documents
│   ├── processed/        # Processed document storage
│   └── graphrag/         # GraphRAG index storage
├── tests/                # Test suite
└── config/               # Configuration files
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- At least 8GB RAM (for Ollama models)

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd talan-week2
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Pull the Ollama model** (first time only)
   ```bash
   docker exec -it ollama ollama pull llama2
   ```

4. **Access the API**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Ollama: http://localhost:11434

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Ollama separately**
   ```bash
   ollama serve
   ollama pull llama2
   ```

4. **Run the API**
   ```bash
   uvicorn src.api.main:app --reload
   ```

## API Endpoints

### Document Parsing

**Parse a document**
```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_docs/annual_report_2023.pdf"
```

### Entity Extraction

**Extract entities from a document**
```bash
curl -X POST "http://localhost:8000/api/v1/extract-entities" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_docs/financial_report_q4.docx"
```

**Extract specific entity types**
```bash
curl -X POST "http://localhost:8000/api/v1/extract-entities?entity_types=company_name,monetary_amount" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_docs/financial_data_2023.xlsx"
```

### GraphRAG

**Index a document**
```bash
curl -X POST "http://localhost:8000/api/v1/graphrag/index" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_docs/annual_report_2023.pdf" \
  -F "doc_id=annual_2023"
```

**Query the indexed documents**
```bash
curl -X GET "http://localhost:8000/api/v1/graphrag/query?query=What%20was%20the%20total%20revenue%20in%202023?"
```

**List indexed documents**
```bash
curl -X GET "http://localhost:8000/api/v1/graphrag/documents"
```

**Delete a document**
```bash
curl -X DELETE "http://localhost:8000/api/v1/graphrag/documents/annual_2023"
```

## Sample Documents

The repository includes three sample financial documents in `data/sample_docs/`:

1. **annual_report_2023.pdf** - Annual financial report with comprehensive financial data
2. **financial_report_q4.docx** - Q4 quarterly report with tables and metrics
3. **financial_data_2023.xlsx** - Multi-sheet Excel with revenue, expenses, and key metrics

## Configuration

Environment variables (see `.env.example`):

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2

# GraphRAG Configuration
GRAPHRAG_STORAGE_PATH=./data/graphrag
GRAPHRAG_EMBEDDING_MODEL=llama2

# Document Processing
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=.pdf,.docx,.xlsx

# Logging
LOG_LEVEL=INFO
```

## Usage Examples

### Python Client Example

```python
import requests

# Parse a document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/parse',
        files={'file': f}
    )
    data = response.json()
    print(f"Extracted text: {data['text'][:200]}...")

# Extract entities
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/extract-entities',
        files={'file': f}
    )
    entities = response.json()['entities']
    print(f"Found {len(entities)} entities")

# Index and query
with open('document.pdf', 'rb') as f:
    requests.post(
        'http://localhost:8000/api/v1/graphrag/index',
        files={'file': f},
        data={'doc_id': 'my_doc'}
    )

response = requests.get(
    'http://localhost:8000/api/v1/graphrag/query',
    params={'query': 'What is the revenue?'}
)
print(response.json()['response'])
```

### Testing with Sample Documents

```bash
# Parse PDF
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@data/sample_docs/annual_report_2023.pdf"

# Extract entities from Word document
curl -X POST "http://localhost:8000/api/v1/extract-entities" \
  -F "file=@data/sample_docs/financial_report_q4.docx"

# Index all sample documents
for file in data/sample_docs/*; do
  curl -X POST "http://localhost:8000/api/v1/graphrag/index" \
    -F "file=@$file" \
    -F "doc_id=$(basename $file)"
done

# Query the indexed documents
curl -X GET "http://localhost:8000/api/v1/graphrag/query?query=What%20is%20the%20profit%20margin?"
```

## Entity Types

The system can extract the following financial entity types:

- `company_name` - Company names
- `stock_symbol` - Stock ticker symbols
- `monetary_amount` - Dollar amounts and currencies
- `revenue` - Revenue figures
- `profit` - Profit amounts
- `loss` - Loss amounts
- `financial_ratio` - Financial ratios and percentages
- `date` - Dates and time periods
- `fiscal_year` - Fiscal years
- `quarter` - Quarterly periods
- `person_name` - Names of people
- `location` - Locations and addresses

## Technology Stack

- **FastAPI** - Modern web framework for building APIs
- **Ollama** - Local LLM inference
- **ChromaDB** - Vector database for embeddings
- **LangChain** - LLM application framework
- **PyPDF2 & pdfplumber** - PDF parsing
- **python-docx** - Word document parsing
- **openpyxl** - Excel document parsing

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

- `src/parsers/` - Document parsing modules for different file types
- `src/entities/` - Entity extraction using Ollama LLM
- `src/graphrag/` - GraphRAG implementation with ChromaDB
- `src/api/` - FastAPI application and endpoints

### Adding New Features

1. **New document parser**: Extend `BaseParser` in `src/parsers/`
2. **New entity types**: Update entity types in `src/entities/extractor.py`
3. **New endpoints**: Add routes in `src/api/main.py`

## Troubleshooting

### Ollama Connection Issues

If you get connection errors to Ollama:

```bash
# Check if Ollama is running
docker ps | grep ollama

# Check Ollama logs
docker logs ollama

# Restart Ollama
docker-compose restart ollama
```

### Model Not Found

```bash
# Pull the model manually
docker exec -it ollama ollama pull llama2

# List available models
docker exec -it ollama ollama list
```

### Memory Issues

If you encounter out-of-memory errors:
- Reduce the number of concurrent requests
- Use a smaller model (e.g., `llama2:7b`)
- Increase Docker memory allocation

## Performance Optimization

- **Chunk size**: Adjust `chunk_size` in GraphRAG for better performance
- **Model selection**: Use smaller models for faster inference
- **Batch processing**: Process multiple documents in batches
- **Caching**: Enable caching for repeated queries

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
