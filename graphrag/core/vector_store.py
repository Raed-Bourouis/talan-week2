"""Vector store service using Qdrant."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import uuid


class VectorStore:
    """Vector store using Qdrant for semantic search."""
    
    def __init__(self, host: str = "localhost", port: int = 6333, 
                 collection_name: str = "graphrag_vectors"):
        """Initialize the vector store.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of the collection to use
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
    
    def create_collection(self, dimension: int):
        """Create a collection if it doesn't exist.
        
        Args:
            dimension: Dimension of the vectors
        """
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )
    
    def add_vectors(self, vectors: List[List[float]], 
                   texts: List[str], 
                   metadata: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add vectors to the store.
        
        Args:
            vectors: List of embedding vectors
            texts: List of original texts
            metadata: Optional metadata for each vector
            
        Returns:
            List of IDs for the added vectors
        """
        if metadata is None:
            metadata = [{} for _ in vectors]
        
        points = []
        ids = []
        for i, (vector, text, meta) in enumerate(zip(vectors, texts, metadata)):
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            payload = {"text": text, **meta}
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        
        self.client.upsert(collection_name=self.collection_name, points=points)
        return ids
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of search results with scores and payloads
        """
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
            }
            for result in results
        ]
    
    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(collection_name=self.collection_name)
