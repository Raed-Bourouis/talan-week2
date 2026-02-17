"""GraphRAG integration for document indexing and querying."""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import ollama
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class GraphRAGManager:
    """Manage GraphRAG indexing and querying."""
    
    def __init__(
        self,
        storage_path: str = "./data/graphrag",
        collection_name: str = "documents",
        model: str = "llama2"
    ):
        """Initialize GraphRAG manager.
        
        Args:
            storage_path: Path to store GraphRAG data
            collection_name: Name of the collection
            model: Model name for embeddings
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.model = model
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.storage_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Document embeddings for RAG"}
        )
        
        logger.info(f"Initialized GraphRAG with storage at {self.storage_path}")
    
    def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Index a document for RAG.
        
        Args:
            doc_id: Unique document identifier
            text: Document text
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            # Split text into chunks
            chunks = self._chunk_text(text)
            
            # Prepare data for indexing
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            documents = chunks
            metadatas = [
                {
                    "doc_id": doc_id,
                    "chunk_index": i,
                    **(metadata or {})
                }
                for i in range(len(chunks))
            ]
            
            # Generate embeddings using Ollama
            embeddings = self._generate_embeddings(chunks)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Indexed document {doc_id} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return False
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the RAG system.
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            Query results with context and generated response
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embeddings([query_text])[0]
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Prepare context from results
            context = self._prepare_context(results)
            
            # Generate response using LLM with context
            response = self._generate_response(query_text, context)
            
            return {
                "query": query_text,
                "response": response,
                "context": context,
                "sources": results.get("metadatas", [[]])[0]
            }
            
        except Exception as e:
            logger.error(f"Error querying RAG: {e}")
            return {
                "query": query_text,
                "response": f"Error: {str(e)}",
                "context": [],
                "sources": []
            }
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to end at a sentence boundary
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                boundary = max(last_period, last_newline)
                
                if boundary > chunk_size // 2:
                    chunk = chunk[:boundary + 1]
                    end = start + len(chunk)
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using Ollama.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            try:
                response = ollama.embeddings(
                    model=self.model,
                    prompt=text
                )
                embeddings.append(response['embedding'])
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                # Fallback: create a dummy embedding
                embeddings.append([0.0] * 4096)
        
        return embeddings
    
    def _prepare_context(self, results: Dict[str, Any]) -> List[str]:
        """Prepare context from search results.
        
        Args:
            results: Search results from ChromaDB
            
        Returns:
            List of context strings
        """
        if not results or not results.get("documents"):
            return []
        
        return results["documents"][0]
    
    def _generate_response(self, query: str, context: List[str]) -> str:
        """Generate response using LLM with context.
        
        Args:
            query: User query
            context: Context from RAG
            
        Returns:
            Generated response
        """
        if not context:
            return "No relevant information found in the documents."
        
        context_text = "\n\n".join([f"Context {i+1}: {c}" for i, c in enumerate(context)])
        
        prompt = f"""You are a helpful assistant answering questions based on provided documents.

Context from documents:
{context_text}

Question: {query}

Based on the context above, provide a clear and concise answer. If the context doesn't contain enough information, say so.

Answer:"""
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            return response['response']
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def list_documents(self) -> List[str]:
        """List all indexed document IDs.
        
        Returns:
            List of document IDs
        """
        try:
            all_items = self.collection.get()
            doc_ids = set()
            
            if all_items and all_items.get("metadatas"):
                for metadata in all_items["metadatas"]:
                    if "doc_id" in metadata:
                        doc_ids.add(metadata["doc_id"])
            
            return sorted(list(doc_ids))
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful
        """
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if results and results.get("ids"):
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted document {doc_id}")
                return True
            else:
                logger.warning(f"Document {doc_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
