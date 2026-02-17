"""Integration tests for GraphRAG SDK."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from graphrag.sdk import GraphRAG


class TestGraphRAGSDK:
    """Integration tests for GraphRAG SDK."""
    
    @patch('graphrag.sdk.client.EmbeddingService')
    @patch('graphrag.sdk.client.VectorStore')
    @patch('graphrag.sdk.client.GraphStore')
    @patch('graphrag.sdk.client.LLMService')
    @patch('graphrag.sdk.client.EpisodicMemory')
    def test_initialization(self, mock_memory, mock_llm, mock_graph, 
                           mock_vector, mock_embedding):
        """Test SDK initialization."""
        # Setup mocks
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_dimension.return_value = 384
        mock_embedding.return_value = mock_embedding_instance
        
        mock_vector_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        
        # Initialize SDK
        client = GraphRAG()
        
        # Verify services were created
        mock_embedding.assert_called_once()
        mock_vector.assert_called_once()
        mock_graph.assert_called_once()
        mock_llm.assert_called_once()
        mock_memory.assert_called_once()
        
        # Verify collection creation
        mock_vector_instance.create_collection.assert_called_once_with(384)
    
    @patch('graphrag.sdk.client.EmbeddingService')
    @patch('graphrag.sdk.client.VectorStore')
    @patch('graphrag.sdk.client.GraphStore')
    @patch('graphrag.sdk.client.LLMService')
    @patch('graphrag.sdk.client.EpisodicMemory')
    def test_add_documents(self, mock_memory, mock_llm, mock_graph, 
                          mock_vector, mock_embedding):
        """Test adding documents."""
        # Setup mocks
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_dimension.return_value = 384
        mock_embedding_instance.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_embedding.return_value = mock_embedding_instance
        
        mock_vector_instance = Mock()
        mock_vector_instance.add_vectors.return_value = ["id1", "id2"]
        mock_vector.return_value = mock_vector_instance
        
        # Test
        client = GraphRAG()
        ids = client.add_documents(["text1", "text2"])
        
        assert ids == ["id1", "id2"]
        mock_embedding_instance.embed_batch.assert_called_once_with(["text1", "text2"])
        mock_vector_instance.add_vectors.assert_called_once()
    
    @patch('graphrag.sdk.client.EmbeddingService')
    @patch('graphrag.sdk.client.VectorStore')
    @patch('graphrag.sdk.client.GraphStore')
    @patch('graphrag.sdk.client.LLMService')
    @patch('graphrag.sdk.client.EpisodicMemory')
    def test_add_knowledge_node(self, mock_memory, mock_llm, mock_graph, 
                               mock_vector, mock_embedding):
        """Test adding knowledge node."""
        # Setup mocks
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_dimension.return_value = 384
        mock_embedding.return_value = mock_embedding_instance
        
        mock_graph_instance = Mock()
        mock_graph_instance.add_node.return_value = "node-123"
        mock_graph.return_value = mock_graph_instance
        
        # Test
        client = GraphRAG()
        node_id = client.add_knowledge_node("Label", {"name": "test"})
        
        assert node_id == "node-123"
        mock_graph_instance.add_node.assert_called_once_with("Label", {"name": "test"})
    
    @patch('graphrag.sdk.client.EmbeddingService')
    @patch('graphrag.sdk.client.VectorStore')
    @patch('graphrag.sdk.client.GraphStore')
    @patch('graphrag.sdk.client.LLMService')
    @patch('graphrag.sdk.client.EpisodicMemory')
    @patch('graphrag.sdk.client.HybridRetriever')
    def test_query(self, mock_retriever, mock_memory, mock_llm, mock_graph, 
                   mock_vector, mock_embedding):
        """Test querying the system."""
        # Setup mocks
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_dimension.return_value = 384
        mock_embedding.return_value = mock_embedding_instance
        
        mock_retriever_instance = Mock()
        mock_retriever_instance.query.return_value = "Test answer"
        mock_retriever.return_value = mock_retriever_instance
        
        # Test
        client = GraphRAG()
        answer = client.query("Test query", session_id="session-1")
        
        assert answer == "Test answer"
        mock_retriever_instance.query.assert_called_once_with("Test query", "session-1")
    
    @patch('graphrag.sdk.client.EmbeddingService')
    @patch('graphrag.sdk.client.VectorStore')
    @patch('graphrag.sdk.client.GraphStore')
    @patch('graphrag.sdk.client.LLMService')
    @patch('graphrag.sdk.client.EpisodicMemory')
    def test_conversation_management(self, mock_memory, mock_llm, mock_graph, 
                                    mock_vector, mock_embedding):
        """Test conversation management."""
        # Setup mocks
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_dimension.return_value = 384
        mock_embedding.return_value = mock_embedding_instance
        
        mock_memory_instance = Mock()
        mock_memory_instance.get_session_history.return_value = [
            {"query": "q1", "response": "r1"}
        ]
        mock_memory.return_value = mock_memory_instance
        
        # Test
        client = GraphRAG()
        
        # Get history
        history = client.get_conversation_history("session-1")
        assert len(history) == 1
        mock_memory_instance.get_session_history.assert_called_once_with("session-1", None)
        
        # Clear conversation
        client.clear_conversation("session-1")
        mock_memory_instance.clear_session.assert_called_once_with("session-1")
