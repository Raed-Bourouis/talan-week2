"""Unit tests for GraphRAG components."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from graphrag.core.embeddings import EmbeddingService
from graphrag.core.vector_store import VectorStore
from graphrag.core.graph_store import GraphStore
from graphrag.core.llm import LLMService
from graphrag.core.episodic_memory import EpisodicMemory


class TestEmbeddingService:
    """Tests for EmbeddingService."""
    
    @patch('graphrag.core.embeddings.SentenceTransformer')
    def test_initialization(self, mock_transformer):
        """Test service initialization."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService("test-model")
        
        assert service.dimension == 384
        mock_transformer.assert_called_once_with("test-model")
    
    @patch('graphrag.core.embeddings.SentenceTransformer')
    def test_embed_text(self, mock_transformer):
        """Test single text embedding."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = Mock(tolist=lambda: [0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        result = service.embed_text("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once()
    
    @patch('graphrag.core.embeddings.SentenceTransformer')
    def test_embed_batch(self, mock_transformer):
        """Test batch text embedding."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = Mock(
            tolist=lambda: [[0.1, 0.2], [0.3, 0.4]]
        )
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        results = service.embed_batch(["text1", "text2"])
        
        assert len(results) == 2
        assert results == [[0.1, 0.2], [0.3, 0.4]]


class TestVectorStore:
    """Tests for VectorStore."""
    
    @patch('graphrag.core.vector_store.QdrantClient')
    def test_initialization(self, mock_client):
        """Test vector store initialization."""
        store = VectorStore(host="test-host", port=1234)
        
        mock_client.assert_called_once_with(host="test-host", port=1234)
    
    @patch('graphrag.core.vector_store.QdrantClient')
    def test_create_collection(self, mock_client):
        """Test collection creation."""
        mock_instance = Mock()
        mock_instance.get_collections.return_value = Mock(collections=[])
        mock_client.return_value = mock_instance
        
        store = VectorStore()
        store.create_collection(dimension=384)
        
        mock_instance.create_collection.assert_called_once()
    
    @patch('graphrag.core.vector_store.QdrantClient')
    def test_search(self, mock_client):
        """Test vector search."""
        mock_result = Mock()
        mock_result.id = "test-id"
        mock_result.score = 0.95
        mock_result.payload = {"text": "test text", "meta": "data"}
        
        mock_instance = Mock()
        mock_instance.search.return_value = [mock_result]
        mock_client.return_value = mock_instance
        
        store = VectorStore()
        results = store.search([0.1, 0.2, 0.3], top_k=5)
        
        assert len(results) == 1
        assert results[0]["id"] == "test-id"
        assert results[0]["score"] == 0.95
        assert results[0]["text"] == "test text"


class TestGraphStore:
    """Tests for GraphStore."""
    
    @patch('graphrag.core.graph_store.GraphDatabase')
    def test_initialization(self, mock_db):
        """Test graph store initialization."""
        store = GraphStore("test-uri", "user", "pass")
        
        mock_db.driver.assert_called_once_with("test-uri", auth=("user", "pass"))
    
    @patch('graphrag.core.graph_store.GraphDatabase')
    def test_add_node(self, mock_db):
        """Test node addition."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.single.return_value = {"id": "node-123"}
        mock_session.run.return_value = mock_result
        
        mock_driver = Mock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        mock_db.driver.return_value = mock_driver
        
        store = GraphStore("uri", "user", "pass")
        node_id = store.add_node("Label", {"name": "test"})
        
        assert node_id == "node-123"


class TestLLMService:
    """Tests for LLMService."""
    
    @patch('graphrag.core.llm.ollama.Client')
    def test_initialization(self, mock_client):
        """Test LLM service initialization."""
        service = LLMService(host="test-host", model="test-model")
        
        assert service.model == "test-model"
        mock_client.assert_called_once_with(host="test-host")
    
    @patch('graphrag.core.llm.ollama.Client')
    def test_generate(self, mock_client):
        """Test text generation."""
        mock_instance = Mock()
        mock_instance.chat.return_value = {
            "message": {"content": "Generated response"}
        }
        mock_client.return_value = mock_instance
        
        service = LLMService()
        response = service.generate("Test prompt")
        
        assert response == "Generated response"
        mock_instance.chat.assert_called_once()


class TestEpisodicMemory:
    """Tests for EpisodicMemory."""
    
    @patch('graphrag.core.episodic_memory.redis.Redis')
    def test_initialization(self, mock_redis):
        """Test episodic memory initialization."""
        memory = EpisodicMemory(host="test-host", port=1234)
        
        mock_redis.assert_called_once()
    
    @patch('graphrag.core.episodic_memory.redis.Redis')
    def test_add_interaction(self, mock_redis):
        """Test adding interaction."""
        mock_instance = Mock()
        mock_redis.return_value = mock_instance
        
        memory = EpisodicMemory()
        memory.add_interaction("session-1", "query", "response", {"key": "value"})
        
        mock_instance.rpush.assert_called_once()
    
    @patch('graphrag.core.episodic_memory.redis.Redis')
    def test_get_session_history(self, mock_redis):
        """Test getting session history."""
        mock_instance = Mock()
        mock_instance.lrange.return_value = [
            '{"query": "q1", "response": "r1", "timestamp": "2024-01-01", "metadata": {}}'
        ]
        mock_redis.return_value = mock_instance
        
        memory = EpisodicMemory()
        history = memory.get_session_history("session-1")
        
        assert len(history) == 1
        assert history[0]["query"] == "q1"
