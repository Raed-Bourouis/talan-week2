"""Tests for episodic memory."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from graphrag.episodic_memory import EpisodicMemory
from graphrag.models import FinancialEpisode
from graphrag.config import GraphRAGConfig


class TestEpisodicMemory:
    """Test episodic memory functionality."""
    
    @pytest.fixture
    def memory(self):
        """Create a fresh episodic memory instance."""
        config = GraphRAGConfig(episodic_memory_max_episodes=10)
        return EpisodicMemory(config=config)
    
    @pytest.fixture
    def sample_episode(self):
        """Create a sample episode."""
        return FinancialEpisode(
            title="Late Payment",
            description="Client ABC paid invoice late",
            event_date=datetime.utcnow(),
            entities_involved=[uuid4()],
            event_type="late_payment",
            context={"delay_days": 15},
            tags=["payment", "late"],
        )
    
    def test_store_episode(self, memory, sample_episode):
        """Test storing an episode."""
        episode_id = memory.store_episode(sample_episode)
        
        assert episode_id == str(sample_episode.id)
        assert len(memory._episodes) == 1
    
    def test_get_episode(self, memory, sample_episode):
        """Test retrieving an episode by ID."""
        memory.store_episode(sample_episode)
        
        retrieved = memory.get_episode(sample_episode.id)
        
        assert retrieved is not None
        assert retrieved.title == "Late Payment"
        assert retrieved.event_type == "late_payment"
    
    def test_recall_by_entity(self, memory):
        """Test recalling episodes by entity."""
        entity_id = uuid4()
        
        # Store multiple episodes with the same entity
        for i in range(3):
            episode = FinancialEpisode(
                title=f"Event {i}",
                description=f"Description {i}",
                event_date=datetime.utcnow(),
                entities_involved=[entity_id],
                event_type="test_event",
            )
            memory.store_episode(episode)
        
        # Recall episodes for this entity
        recalled = memory.recall_by_entity(entity_id, top_k=5)
        
        assert len(recalled) == 3
        for ep in recalled:
            assert entity_id in ep.entities_involved
    
    def test_recall_by_event_type(self, memory):
        """Test recalling episodes by event type."""
        # Store episodes of different types
        for event_type in ["late_payment", "budget_overrun", "late_payment"]:
            episode = FinancialEpisode(
                title=f"Event {event_type}",
                description="Test",
                event_date=datetime.utcnow(),
                entities_involved=[uuid4()],
                event_type=event_type,
            )
            memory.store_episode(episode)
        
        # Recall late_payment events
        recalled = memory.recall_by_event_type("late_payment", top_k=5)
        
        assert len(recalled) == 2
        for ep in recalled:
            assert ep.event_type == "late_payment"
    
    def test_recall_by_temporal_range(self, memory):
        """Test recalling episodes within a time range."""
        now = datetime.utcnow()
        
        # Store episodes at different times
        dates = [
            now - timedelta(days=10),
            now - timedelta(days=5),
            now - timedelta(days=1),
        ]
        
        for date in dates:
            episode = FinancialEpisode(
                title="Temporal Event",
                description="Test",
                event_date=date,
                entities_involved=[uuid4()],
                event_type="test",
            )
            memory.store_episode(episode)
        
        # Recall episodes from last 7 days
        start_date = now - timedelta(days=7)
        end_date = now
        
        recalled = memory.recall_by_temporal_range(start_date, end_date)
        
        assert len(recalled) == 2  # Only episodes from last 7 days
    
    def test_recall_similar(self, memory):
        """Test similarity-based recall."""
        # Store episodes with related content
        episodes_data = [
            ("Late payment from client", "Client paid 15 days late"),
            ("Budget overrun detected", "Department exceeded budget by 10%"),
            ("Payment delay issue", "Client payment delayed by 20 days"),
        ]
        
        for title, description in episodes_data:
            episode = FinancialEpisode(
                title=title,
                description=description,
                event_date=datetime.utcnow(),
                entities_involved=[uuid4()],
                event_type="test",
            )
            memory.store_episode(episode)
        
        # Search for payment-related episodes
        recalled = memory.recall_similar("client payment late", top_k=5, min_similarity=0.1)
        
        assert len(recalled) >= 2  # Should find payment-related episodes
        # Check that similarity scores were set
        for ep in recalled:
            assert ep.similarity_score is not None
            assert ep.similarity_score > 0
    
    def test_recall_recent(self, memory):
        """Test recalling recent episodes."""
        # Store episodes
        for i in range(5):
            episode = FinancialEpisode(
                title=f"Event {i}",
                description="Test",
                event_date=datetime.utcnow() - timedelta(days=i),
                entities_involved=[uuid4()],
                event_type="test",
            )
            memory.store_episode(episode)
        
        # Get 3 most recent
        recent = memory.recall_recent(top_k=3)
        
        assert len(recent) == 3
        # Check they're ordered by date (newest first)
        for i in range(len(recent) - 1):
            assert recent[i].event_date >= recent[i + 1].event_date
    
    def test_eviction_on_capacity(self, memory):
        """Test that oldest episodes are evicted when capacity is reached."""
        # Memory is configured with max 10 episodes
        
        # Store 12 episodes
        for i in range(12):
            episode = FinancialEpisode(
                title=f"Event {i}",
                description="Test",
                event_date=datetime.utcnow() + timedelta(seconds=i),
                entities_involved=[uuid4()],
                event_type="test",
            )
            memory.store_episode(episode)
        
        # Should only have 10 episodes (max capacity)
        assert len(memory._episodes) == 10
    
    def test_detect_pattern(self, memory):
        """Test pattern detection."""
        entity_id = uuid4()
        
        # Store multiple late payment episodes for the same entity
        for i in range(4):
            episode = FinancialEpisode(
                title=f"Late Payment {i}",
                description="Payment delay",
                event_date=datetime.utcnow() - timedelta(days=i*30),
                entities_involved=[entity_id],
                event_type="late_payment",
                context={"delay_days": 15 + i},
            )
            memory.store_episode(episode)
        
        # Detect pattern
        def is_late_payment(ep):
            return ep.event_type == "late_payment" and entity_id in ep.entities_involved
        
        pattern = memory.detect_pattern(
            "recurring_late_payment",
            is_late_payment,
            min_occurrences=3,
        )
        
        assert pattern is not None
        assert pattern.pattern_type == "recurring_late_payment"
        assert pattern.occurrences == 4
        assert entity_id in pattern.entities
    
    def test_detect_late_payment_pattern(self, memory):
        """Test built-in late payment pattern detection."""
        entity_id = uuid4()
        
        # Store late payment episodes
        for i in range(3):
            episode = FinancialEpisode(
                title=f"Late Payment {i}",
                description="Payment delay",
                event_date=datetime.utcnow() - timedelta(days=i*30),
                entities_involved=[entity_id],
                event_type="late_payment",
                context={"delay_days": 20},
            )
            memory.store_episode(episode)
        
        pattern = memory.detect_late_payment_pattern(entity_id, min_delay_days=15)
        
        assert pattern is not None
        assert pattern.occurrences == 3
    
    def test_get_context_for_rag(self, memory, sample_episode):
        """Test formatting episodes as RAG context."""
        memory.store_episode(sample_episode)
        
        episodes = [sample_episode]
        context = memory.get_context_for_rag(episodes)
        
        assert "Relevant Past Events" in context
        assert sample_episode.title in context
        assert sample_episode.event_type in context
    
    def test_clear(self, memory, sample_episode):
        """Test clearing all episodes."""
        memory.store_episode(sample_episode)
        assert len(memory._episodes) > 0
        
        memory.clear()
        
        assert len(memory._episodes) == 0
        assert len(memory._patterns) == 0
    
    def test_get_statistics(self, memory):
        """Test getting memory statistics."""
        # Store some episodes
        for i in range(3):
            episode = FinancialEpisode(
                title=f"Event {i}",
                description="Test",
                event_date=datetime.utcnow(),
                entities_involved=[uuid4()],
                event_type="test",
            )
            memory.store_episode(episode)
        
        stats = memory.get_statistics()
        
        assert stats["total_episodes"] == 3
        assert stats["max_episodes"] == 10
        assert "oldest_episode" in stats
        assert "newest_episode" in stats
