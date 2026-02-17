"""
F360 – Mémoire Épisodique (Episodic Memory)
Stores and retrieves past queries, decisions and feedback
to provide contextual memory for the RAG system.
Enables the system to learn from past interactions.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# EPISODE MODEL (in-memory + DB backed)
# ═══════════════════════════════════════════════════════════════

class Episode:
    """A single episode in the episodic memory."""

    def __init__(
        self,
        query: str,
        answer: str,
        context_sources: list[dict[str, Any]],
        feedback_score: float | None = None,
        user_id: str | None = None,
        company_id: str | None = None,
        tags: list[str] | None = None,
        timestamp: datetime | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.query = query
        self.answer = answer
        self.context_sources = context_sources
        self.feedback_score = feedback_score  # 0.0 to 1.0
        self.user_id = user_id
        self.company_id = company_id
        self.tags = tags or []
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "answer": self.answer,
            "context_sources": self.context_sources,
            "feedback_score": self.feedback_score,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_context_text(self) -> str:
        """Convert episode to text for RAG context injection."""
        return (
            f"[Previous Q&A – {self.timestamp.strftime('%Y-%m-%d')}]\n"
            f"Q: {self.query}\n"
            f"A: {self.answer}\n"
            f"Confidence: {self.feedback_score or 'N/A'}"
        )


# ═══════════════════════════════════════════════════════════════
# EPISODIC MEMORY STORE
# ═══════════════════════════════════════════════════════════════

class EpisodicMemory:
    """
    Manages episodic memory for the RAG system.
    Stores past Q&A interactions with feedback scores.
    Enables contextual recall of similar past queries.
    """

    def __init__(self, max_episodes: int = 1000):
        self.max_episodes = max_episodes
        self._episodes: list[Episode] = []

    async def store(self, episode: Episode, db: AsyncSession | None = None) -> None:
        """Store an episode in memory and optionally persist to DB."""
        self._episodes.append(episode)

        # Evict oldest if over capacity
        if len(self._episodes) > self.max_episodes:
            self._episodes = self._episodes[-self.max_episodes:]

        # Persist to DB if available
        if db:
            await self._persist_episode(episode, db)

        logger.debug(f"Stored episode: {episode.id} (total: {len(self._episodes)})")

    async def recall(
        self,
        query: str,
        company_id: str | None = None,
        top_k: int = 3,
        min_score: float = 0.5,
        db: AsyncSession | None = None,
    ) -> list[Episode]:
        """
        Recall relevant past episodes based on query similarity.
        Uses simple keyword matching in-memory, or vector search if DB is available.
        """
        if db:
            return await self._recall_from_db(query, company_id, top_k, db)

        # In-memory keyword-based recall
        query_words = set(query.lower().split())
        scored: list[tuple[float, Episode]] = []

        for ep in self._episodes:
            if company_id and ep.company_id != company_id:
                continue

            ep_words = set(ep.query.lower().split())
            overlap = len(query_words & ep_words)
            score = overlap / max(len(query_words), 1)

            if score >= min_score or (ep.feedback_score and ep.feedback_score > 0.8):
                scored.append((score, ep))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]

    async def record_feedback(
        self,
        episode_id: str,
        score: float,
        db: AsyncSession | None = None,
    ) -> bool:
        """Record user feedback for an episode (reinforcement signal)."""
        for ep in self._episodes:
            if ep.id == episode_id:
                ep.feedback_score = score
                if db:
                    await self._update_feedback_in_db(episode_id, score, db)
                return True
        return False

    def get_context_for_query(self, episodes: list[Episode]) -> str:
        """Build context string from past episodes for RAG injection."""
        if not episodes:
            return ""

        parts = ["=== Relevant Past Interactions ==="]
        for ep in episodes:
            parts.append(ep.to_context_text())
            parts.append("---")

        return "\n".join(parts)

    # ── Persistence helpers ──

    async def _persist_episode(self, episode: Episode, db: AsyncSession) -> None:
        """Store episode in PostgreSQL (JSONB)."""
        try:
            await db.execute(
                text("""
                    INSERT INTO episodic_memory (id, query, answer, context_sources,
                        feedback_score, user_id, company_id, tags, created_at)
                    VALUES (:id, :query, :answer, :context::jsonb,
                        :score, :user_id, :company_id, :tags::jsonb, :created_at)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": episode.id,
                    "query": episode.query,
                    "answer": episode.answer,
                    "context": str(episode.context_sources).replace("'", '"'),
                    "score": episode.feedback_score,
                    "user_id": episode.user_id,
                    "company_id": episode.company_id,
                    "tags": str(episode.tags).replace("'", '"'),
                    "created_at": episode.timestamp,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to persist episode {episode.id}: {e}")

    async def _recall_from_db(
        self, query: str, company_id: str | None, top_k: int, db: AsyncSession,
    ) -> list[Episode]:
        """Recall episodes from DB using full-text search."""
        try:
            filter_clause = ""
            params: dict[str, Any] = {"query": query, "top_k": top_k}
            if company_id:
                filter_clause = "AND company_id = :company_id"
                params["company_id"] = company_id

            result = await db.execute(
                text(f"""
                    SELECT id, query, answer, context_sources, feedback_score,
                           user_id, company_id, tags, created_at
                    FROM episodic_memory
                    WHERE to_tsvector('french', query || ' ' || answer)
                          @@ plainto_tsquery('french', :query)
                    {filter_clause}
                    ORDER BY feedback_score DESC NULLS LAST, created_at DESC
                    LIMIT :top_k
                """),
                params,
            )
            rows = result.fetchall()
            return [
                Episode(
                    query=row[1], answer=row[2], context_sources=row[3] or [],
                    feedback_score=row[4], user_id=row[5], company_id=row[6],
                    tags=row[7] or [], timestamp=row[8],
                )
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"DB recall failed, using in-memory: {e}")
            return await self.recall(query, company_id, top_k, db=None)

    async def _update_feedback_in_db(
        self, episode_id: str, score: float, db: AsyncSession,
    ) -> None:
        try:
            await db.execute(
                text("UPDATE episodic_memory SET feedback_score = :score WHERE id = :id"),
                {"score": score, "id": episode_id},
            )
        except Exception as e:
            logger.warning(f"Failed to update feedback in DB: {e}")
