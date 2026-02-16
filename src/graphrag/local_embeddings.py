"""
Local Embeddings using sentence-transformers
100% FREE - No API keys required!
"""

from typing import List
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class LocalEmbeddings:
    """
    Free local embeddings using sentence-transformers.
    Downloads model once, then cached locally.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embeddings model.
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2, 384 dimensions)
                       Alternatives: sentence-transformers/all-mpnet-base-v2 (768 dimensions)
        """
        logger.info(f"Loading embeddings model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        logger.debug(f"Embedding {len(texts)} documents")
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        logger.debug(f"Embedding query: {text[:50]}...")
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed texts in batches for better performance.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        embeddings = self.model.encode(
            texts, 
            batch_size=batch_size,
            show_progress_bar=True
        )
        return embeddings.tolist()


# Singleton instance
_embeddings_instance = None


def get_embeddings(model_name: str = "all-MiniLM-L6-v2") -> LocalEmbeddings:
    """
    Get or create singleton embeddings instance.
    
    Args:
        model_name: Model name to use
        
    Returns:
        LocalEmbeddings instance
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = LocalEmbeddings(model_name)
    return _embeddings_instance
