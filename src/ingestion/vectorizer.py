"""
Vectorizer
Create embeddings for semantic search
"""

from typing import Dict, Any, List, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

logger = logging.getLogger(__name__)


class Vectorizer:
    """Create and store document embeddings"""
    
    def __init__(self, qdrant_client: QdrantClient, embedding_function: Any):
        self.qdrant_client = qdrant_client
        self.embedding_function = embedding_function
        self.dimension = 1536  # Default for OpenAI embeddings
    
    def vectorize_document(self, document: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """
        Create embeddings for document and store in Qdrant
        
        Args:
            document: Parsed document
            entities: Extracted entities
            
        Returns:
            Document ID
        """
        text_content = document.get('text_content', str(document.get('data', '')))
        
        # Generate embedding
        embedding = self._create_embedding(text_content)
        
        # Generate unique ID
        doc_id = self._generate_id(document['file_name'])
        
        # Prepare payload
        payload = {
            'document_id': doc_id,
            'document_type': document.get('file_type', 'unknown'),
            'file_name': document['file_name'],
            'text_content': text_content[:1000],  # Store snippet
            'num_amounts': len(entities.get('amounts', [])),
            'num_dates': len(entities.get('dates', [])),
        }
        
        # Store in Qdrant
        self._store_vector(doc_id, embedding, payload, 'financial_documents')
        
        logger.info(f"Vectorized document: {document['file_name']}")
        return doc_id
    
    def vectorize_clauses(self, contract_id: str, clauses: List[str]) -> List[str]:
        """Vectorize contract clauses"""
        clause_ids = []
        
        for idx, clause in enumerate(clauses):
            embedding = self._create_embedding(clause)
            clause_id = f"{contract_id}_clause_{idx}"
            
            payload = {
                'contract_id': contract_id,
                'clause_type': 'extracted',
                'clause_text': clause,
            }
            
            self._store_vector(clause_id, embedding, payload, 'contract_clauses')
            clause_ids.append(clause_id)
        
        return clause_ids
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding vector"""
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimension
        
        try:
            # Use the embedding function
            embedding = self.embedding_function(text)
            return embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return [0.0] * self.dimension
    
    def _store_vector(self, point_id: str, vector: List[float], payload: Dict[str, Any], collection_name: str):
        """Store vector in Qdrant"""
        try:
            point = PointStruct(
                id=self._hash_id(point_id),
                vector=vector,
                payload=payload
            )
            
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[point]
            )
        except Exception as e:
            logger.error(f"Error storing vector: {e}")
    
    def _generate_id(self, file_name: str) -> str:
        """Generate document ID"""
        return f"doc_{file_name}_{hashlib.md5(file_name.encode()).hexdigest()[:8]}"
    
    def _hash_id(self, id_str: str) -> int:
        """Convert string ID to integer hash for Qdrant"""
        return int(hashlib.md5(id_str.encode()).hexdigest()[:8], 16)


def create_embedding_function(api_key: str, model: str = "text-embedding-3-small"):
    """Create embedding function using OpenAI"""
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key)
    
    def embed(text: str) -> List[float]:
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    
    return embed
