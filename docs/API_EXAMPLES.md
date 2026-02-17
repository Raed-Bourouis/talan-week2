# API Examples

This document provides examples of how to use the Document Processing API.

## Quick Start Examples

### Parse a PDF Document

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf"
```

### Extract Entities

```bash
curl -X POST "http://localhost:8000/api/v1/extract-entities" \
  -F "file=@financial_report.pdf"
```

### Index and Query

```bash
# Index a document
curl -X POST "http://localhost:8000/api/v1/graphrag/index" \
  -F "file=@document.pdf" \
  -F "doc_id=my_doc"

# Query indexed documents
curl -X GET "http://localhost:8000/api/v1/graphrag/query?query=What%20is%20the%20revenue?"
```

## Python Client Example

```python
import requests

class DocumentProcessingClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def parse_document(self, file_path):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/v1/parse",
                files={'file': f}
            )
        return response.json()
    
    def extract_entities(self, file_path):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/v1/extract-entities",
                files={'file': f}
            )
        return response.json()
    
    def index_document(self, file_path, doc_id=None):
        data = {'doc_id': doc_id} if doc_id else {}
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/v1/graphrag/index",
                files={'file': f},
                data=data
            )
        return response.json()
    
    def query(self, query_text, n_results=5):
        response = requests.get(
            f"{self.base_url}/api/v1/graphrag/query",
            params={'query': query_text, 'n_results': n_results}
        )
        return response.json()

# Usage
client = DocumentProcessingClient()
result = client.parse_document("document.pdf")
print(f"Extracted {len(result['text'])} characters")
```

For more examples, see the API documentation at http://localhost:8000/docs
