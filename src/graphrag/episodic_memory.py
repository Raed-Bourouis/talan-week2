"""
GraphRAG Episodic Memory
=========================
Financial episodic memory system for storing and retrieving past events and patterns.
Enables the system to recall historical financial patterns and learn from past interactions.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from .config import GraphRAGConfig, get_config
from .exceptions import EpisodicMemoryError
from .models import FinancialEpisode, FinancialPattern

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Financial episodic memory system.
    Stores past financial events, patterns, and interactions.
    Provides temporal and similarity-based retrieval.
    """
    
    def __init__(self, config: Optional[GraphRAGConfig] = None):
        self.config = config or get_config()
        self.max_episodes = self.config.episodic_memory_max_episodes
        
        # In-memory storage
        self._episodes: dict[str, FinancialEpisode] = {}
        self._patterns: dict[str, FinancialPattern] = {}
        
        # Indexes for faster retrieval
        self._entity_index: dict[str, list[str]] = {}  # entity_id -> episode_ids
        self._event_type_index: dict[str, list[str]] = {}  # event_type -> episode_ids
        self._date_index: list[tuple[datetime, str]] = []  # (date, episode_id)
        
        logger.info(f"Episodic memory initialized (max_episodes={self.max_episodes})")
    
    # ═══════════════════════════════════════════════════════════════
    # EPISODE STORAGE & RETRIEVAL
    # ═══════════════════════════════════════════════════════════════
    
    def store_episode(self, episode: FinancialEpisode) -> str:
        """Store a financial episode in memory."""
        episode_id = str(episode.id)
        
        # Store episode
        self._episodes[episode_id] = episode
        
        # Update indexes
        for entity_id in episode.entities_involved:
            entity_key = str(entity_id)
            if entity_key not in self._entity_index:
                self._entity_index[entity_key] = []
            self._entity_index[entity_key].append(episode_id)
        
        if episode.event_type not in self._event_type_index:
            self._event_type_index[episode.event_type] = []
        self._event_type_index[episode.event_type].append(episode_id)
        
        self._date_index.append((episode.event_date, episode_id))
        self._date_index.sort(key=lambda x: x[0], reverse=True)
        
        # Evict oldest episodes if over capacity
        if len(self._episodes) > self.max_episodes:
            self._evict_oldest_episode()
        
        logger.debug(f"Stored episode {episode_id}: {episode.title}")
        return episode_id
    
    def get_episode(self, episode_id: UUID) -> Optional[FinancialEpisode]:
        """Retrieve an episode by ID."""
        return self._episodes.get(str(episode_id))
    
    def recall_by_entity(
        self,
        entity_id: UUID,
        top_k: int = 5,
    ) -> list[FinancialEpisode]:
        """Recall episodes involving a specific entity."""
        entity_key = str(entity_id)
        episode_ids = self._entity_index.get(entity_key, [])
        
        episodes = [
            self._episodes[eid]
            for eid in episode_ids[:top_k]
            if eid in self._episodes
        ]
        
        return episodes
    
    def recall_by_event_type(
        self,
        event_type: str,
        top_k: int = 5,
    ) -> list[FinancialEpisode]:
        """Recall episodes of a specific event type."""
        episode_ids = self._event_type_index.get(event_type, [])
        
        episodes = [
            self._episodes[eid]
            for eid in episode_ids[:top_k]
            if eid in self._episodes
        ]
        
        return episodes
    
    def recall_by_temporal_range(
        self,
        start_date: datetime,
        end_date: datetime,
        top_k: Optional[int] = None,
    ) -> list[FinancialEpisode]:
        """Recall episodes within a specific time range."""
        matching_episodes = []
        
        for date, episode_id in self._date_index:
            if start_date <= date <= end_date:
                if episode_id in self._episodes:
                    matching_episodes.append(self._episodes[episode_id])
            elif date < start_date:
                break  # Index is sorted, so we can stop here
        
        if top_k:
            matching_episodes = matching_episodes[:top_k]
        
        return matching_episodes
    
    def recall_similar(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: Optional[float] = None,
    ) -> list[FinancialEpisode]:
        """
        Recall episodes similar to the query using simple keyword matching.
        For production use, integrate with a vector store for semantic similarity.
        """
        min_sim = min_similarity or self.config.episodic_memory_min_similarity
        query_words = set(query.lower().split())
        
        scored_episodes = []
        
        for episode in self._episodes.values():
            # Combine title and description for matching
            text = f"{episode.title} {episode.description}".lower()
            text_words = set(text.split())
            
            # Calculate simple Jaccard similarity
            intersection = len(query_words & text_words)
            union = len(query_words | text_words)
            similarity = intersection / union if union > 0 else 0.0
            
            if similarity >= min_sim:
                episode.similarity_score = similarity
                scored_episodes.append((similarity, episode))
        
        # Sort by similarity and return top_k
        scored_episodes.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored_episodes[:top_k]]
    
    def recall_recent(self, top_k: int = 10) -> list[FinancialEpisode]:
        """Recall the most recent episodes."""
        recent_ids = [eid for _, eid in self._date_index[:top_k]]
        return [self._episodes[eid] for eid in recent_ids if eid in self._episodes]
    
    # ═══════════════════════════════════════════════════════════════
    # PATTERN DETECTION & MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    def detect_pattern(
        self,
        pattern_type: str,
        condition_func: callable,
        min_occurrences: int = 3,
    ) -> Optional[FinancialPattern]:
        """
        Detect a recurring pattern in the stored episodes.
        
        Args:
            pattern_type: Type of pattern to detect
            condition_func: Function that takes an episode and returns True if it matches
            min_occurrences: Minimum number of occurrences to consider it a pattern
        
        Returns:
            FinancialPattern if detected, None otherwise
        """
        matching_episodes = [
            episode for episode in self._episodes.values()
            if condition_func(episode)
        ]
        
        if len(matching_episodes) >= min_occurrences:
            # Extract common entities
            all_entities = []
            for ep in matching_episodes:
                all_entities.extend(ep.entities_involved)
            
            # Find most common entities
            from collections import Counter
            entity_counts = Counter(all_entities)
            common_entities = [eid for eid, _ in entity_counts.most_common(5)]
            
            pattern = FinancialPattern(
                pattern_type=pattern_type,
                description=f"Pattern detected: {len(matching_episodes)} occurrences of {pattern_type}",
                confidence=min(1.0, len(matching_episodes) / 10.0),
                occurrences=len(matching_episodes),
                first_seen=min(ep.event_date for ep in matching_episodes),
                last_seen=max(ep.event_date for ep in matching_episodes),
                entities=common_entities,
                examples=[ep.id for ep in matching_episodes[:5]],
            )
            
            # Store pattern
            pattern_id = str(pattern.id)
            self._patterns[pattern_id] = pattern
            
            logger.info(f"Detected pattern: {pattern_type} ({len(matching_episodes)} occurrences)")
            return pattern
        
        return None
    
    def get_pattern(self, pattern_id: UUID) -> Optional[FinancialPattern]:
        """Retrieve a pattern by ID."""
        return self._patterns.get(str(pattern_id))
    
    def get_all_patterns(self) -> list[FinancialPattern]:
        """Get all detected patterns."""
        return list(self._patterns.values())
    
    def detect_late_payment_pattern(
        self,
        entity_id: UUID,
        min_delay_days: int = 15,
    ) -> Optional[FinancialPattern]:
        """Detect if an entity has a pattern of late payments."""
        
        def is_late_payment(episode: FinancialEpisode) -> bool:
            return (
                episode.event_type == "late_payment" and
                entity_id in episode.entities_involved and
                episode.context.get("delay_days", 0) >= min_delay_days
            )
        
        return self.detect_pattern(
            f"recurring_late_payment_{entity_id}",
            is_late_payment,
            min_occurrences=3,
        )
    
    def detect_budget_overrun_pattern(
        self,
        department_id: UUID,
    ) -> Optional[FinancialPattern]:
        """Detect if a department has a pattern of budget overruns."""
        
        def is_budget_overrun(episode: FinancialEpisode) -> bool:
            return (
                episode.event_type == "budget_overrun" and
                department_id in episode.entities_involved
            )
        
        return self.detect_pattern(
            f"recurring_budget_overrun_{department_id}",
            is_budget_overrun,
            min_occurrences=2,
        )
    
    def detect_seasonal_pattern(
        self,
        event_type: str,
        month: int,
    ) -> Optional[FinancialPattern]:
        """Detect seasonal patterns (e.g., higher spending in December)."""
        
        def is_seasonal(episode: FinancialEpisode) -> bool:
            return (
                episode.event_type == event_type and
                episode.event_date.month == month
            )
        
        return self.detect_pattern(
            f"seasonal_{event_type}_month_{month}",
            is_seasonal,
            min_occurrences=2,
        )
    
    # ═══════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def create_episode_from_event(
        self,
        title: str,
        description: str,
        event_type: str,
        entities_involved: list[UUID],
        context: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ) -> FinancialEpisode:
        """Helper to create an episode from event data."""
        
        # Generate pattern signature for similarity matching
        pattern_signature = self._generate_pattern_signature(
            event_type, entities_involved, context
        )
        
        episode = FinancialEpisode(
            title=title,
            description=description,
            event_date=datetime.utcnow(),
            entities_involved=entities_involved,
            event_type=event_type,
            context=context or {},
            pattern_signature=pattern_signature,
            tags=tags or [],
        )
        
        return episode
    
    def get_context_for_rag(
        self,
        episodes: list[FinancialEpisode],
    ) -> str:
        """Format episodes as context for RAG."""
        if not episodes:
            return ""
        
        context_parts = ["=== Relevant Past Events ===\n"]
        
        for episode in episodes:
            date_str = episode.event_date.strftime("%Y-%m-%d")
            context_parts.append(
                f"[{date_str}] {episode.title}\n"
                f"{episode.description}\n"
                f"Type: {episode.event_type}\n"
            )
            
            if episode.similarity_score:
                context_parts.append(f"Relevance: {episode.similarity_score:.2f}\n")
            
            context_parts.append("---\n")
        
        return "\n".join(context_parts)
    
    def _generate_pattern_signature(
        self,
        event_type: str,
        entities: list[UUID],
        context: Optional[dict[str, Any]],
    ) -> str:
        """Generate a signature for pattern matching."""
        # Sort entities for consistent hashing
        entity_str = ",".join(sorted([str(e) for e in entities]))
        context_str = str(sorted((context or {}).items()))
        
        signature_input = f"{event_type}:{entity_str}:{context_str}"
        return hashlib.md5(signature_input.encode()).hexdigest()
    
    def _evict_oldest_episode(self) -> None:
        """Remove the oldest episode to maintain capacity."""
        if not self._date_index:
            return
        
        # Get oldest episode
        _, oldest_id = self._date_index[-1]
        
        if oldest_id in self._episodes:
            episode = self._episodes[oldest_id]
            
            # Remove from episode storage
            del self._episodes[oldest_id]
            
            # Remove from indexes
            for entity_id in episode.entities_involved:
                entity_key = str(entity_id)
                if entity_key in self._entity_index:
                    self._entity_index[entity_key] = [
                        eid for eid in self._entity_index[entity_key]
                        if eid != oldest_id
                    ]
            
            if episode.event_type in self._event_type_index:
                self._event_type_index[episode.event_type] = [
                    eid for eid in self._event_type_index[episode.event_type]
                    if eid != oldest_id
                ]
            
            # Remove from date index
            self._date_index = [
                (date, eid) for date, eid in self._date_index
                if eid != oldest_id
            ]
            
            logger.debug(f"Evicted oldest episode: {oldest_id}")
    
    def clear(self) -> None:
        """Clear all episodes and patterns from memory."""
        self._episodes.clear()
        self._patterns.clear()
        self._entity_index.clear()
        self._event_type_index.clear()
        self._date_index.clear()
        logger.info("Cleared all episodes and patterns")
    
    def get_statistics(self) -> dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_episodes": len(self._episodes),
            "total_patterns": len(self._patterns),
            "max_episodes": self.max_episodes,
            "unique_event_types": len(self._event_type_index),
            "indexed_entities": len(self._entity_index),
            "oldest_episode": (
                self._date_index[-1][0].isoformat()
                if self._date_index else None
            ),
            "newest_episode": (
                self._date_index[0][0].isoformat()
                if self._date_index else None
            ),
        }
