"""FastAPI application main module."""
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile
from pathlib import Path

from .config import settings
from ..parsers.pdf_parser import PDFParser
from ..parsers.excel_parser import ExcelParser
from ..parsers.word_parser import WordParser
from ..entities.extractor import EntityExtractor
from ..graphrag.manager import GraphRAGManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Processing API",
    description="API for document parsing, entity extraction, and GraphRAG queries",
    version="1.0.0"
)

# Initialize services
pdf_parser = PDFParser()
excel_parser = ExcelParser()
word_parser = WordParser()
entity_extractor = EntityExtractor(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model
)
graphrag_manager = GraphRAGManager(
    storage_path=settings.graphrag_storage_path,
    model=settings.graphrag_embedding_model
)


def get_parser(filename: str):
    """Get appropriate parser based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".pdf":
        return pdf_parser
    elif ext in [".xlsx", ".xls"]:
        return excel_parser
    elif ext in [".docx", ".doc"]:
        return word_parser
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Document Processing API",
        "version": "1.0.0",
        "endpoints": {
            "parse": "/api/v1/parse",
            "extract_entities": "/api/v1/extract-entities",
            "index": "/api/v1/graphrag/index",
            "query": "/api/v1/graphrag/query",
            "documents": "/api/v1/graphrag/documents"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/v1/parse")
async def parse_document(file: UploadFile = File(...)):
    """Parse a document and extract its content.
    
    Supports PDF, Excel, and Word documents.
    """
    try:
        # Validate file size
        contents = await file.read()
        if len(contents) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Get parser
        parser = get_parser(file.filename)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Parse document
            result = parser.parse(tmp_path)
            result["filename"] = file.filename
            return result
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/extract-entities")
async def extract_entities(file: UploadFile = File(...), entity_types: Optional[str] = None):
    """Extract entities from a document.
    
    Args:
        file: Document file
        entity_types: Comma-separated list of entity types (optional)
    """
    try:
        # Validate file size
        contents = await file.read()
        if len(contents) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Get parser and extract text
        parser = get_parser(file.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            text = parser.extract_text(tmp_path)
            
            # Extract entities
            if entity_types:
                entity_type_list = [et.strip() for et in entity_types.split(",")]
                entities = entity_extractor.extract_entities(text, entity_type_list)
            else:
                entities = entity_extractor.extract_financial_entities(text)
            
            return {
                "filename": file.filename,
                "entities": entities,
                "entity_count": len(entities)
            }
        finally:
            os.unlink(tmp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/graphrag/index")
async def index_document(file: UploadFile = File(...), doc_id: Optional[str] = None):
    """Index a document for GraphRAG queries.
    
    Args:
        file: Document file
        doc_id: Optional document ID (defaults to filename)
    """
    try:
        # Validate file size
        contents = await file.read()
        if len(contents) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Get parser and extract text
        parser = get_parser(file.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            parsed_data = parser.parse(tmp_path)
            text = parsed_data.get("text", "")
            
            # Use filename as doc_id if not provided
            if not doc_id:
                doc_id = file.filename
            
            # Index document
            success = graphrag_manager.index_document(
                doc_id=doc_id,
                text=text,
                metadata={
                    "filename": file.filename,
                    "file_type": parsed_data.get("file_type", "unknown")
                }
            )
            
            if success:
                return {
                    "status": "success",
                    "doc_id": doc_id,
                    "message": "Document indexed successfully"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to index document")
                
        finally:
            os.unlink(tmp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/graphrag/query")
async def query_graphrag(query: str, n_results: int = 5):
    """Query the GraphRAG system.
    
    Args:
        query: Query text
        n_results: Number of results to return (default: 5)
    """
    try:
        result = graphrag_manager.query(query, n_results=n_results)
        return result
    except Exception as e:
        logger.error(f"Error querying GraphRAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/graphrag/documents")
async def list_documents():
    """List all indexed documents."""
    try:
        documents = graphrag_manager.list_documents()
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/graphrag/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the GraphRAG index.
    
    Args:
        doc_id: Document ID to delete
    """
    try:
        success = graphrag_manager.delete_document(doc_id)
        if success:
            return {
                "status": "success",
                "message": f"Document {doc_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
