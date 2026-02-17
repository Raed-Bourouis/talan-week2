"""
F360 – RAG Orchestrator
Central orchestration layer combining:
- Vector search (pgvector)
- Knowledge graph traversal (Neo4j)
- Episodic memory recall
- LLM-augmented answer generation
"""
from __future__ import annotations

import uuid
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.schemas.schemas import RAGResponse
from app.services.cognitive_ingestion.vectorizer import get_embedding
from app.services.cognitive_ingestion.indexer import search_index
from app.services.ragraph.episodic_memory import EpisodicMemory, Episode
from app.services.ragraph.reasoning import ReasoningEngine

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGOrchestrator:
    """
    Multi-source RAG orchestrator.
    Combines vector search, graph traversal, and episodic memory
    for comprehensive financial question answering.
    """

    def __init__(self):
        self.memory = EpisodicMemory(max_episodes=500)
        self.reasoning = ReasoningEngine()

    async def query(
        self,
        question: str,
        company_id: uuid.UUID | None,
        top_k: int = 5,
        use_memory: bool = True,
        use_graph: bool = True,
        db: AsyncSession = None,
    ) -> RAGResponse:
        """
        Full RAG orchestration pipeline:
        1. Embed the user query
        2. Vector search in pgvector
        3. Recall relevant episodes from memory
        4. Traverse knowledge graph for related entities
        5. Merge all context sources
        6. Generate answer via LLM with reasoning
        7. Store the interaction as a new episode
        """
        # ── 1. Embed query ──
        query_embedding = await get_embedding(question)

        # ── 2. Vector search ──
        vector_results = await search_index(
            query_embedding=query_embedding,
            company_id=company_id,
            top_k=top_k,
            db=db,
        )

        # ── 3. Episodic memory recall ──
        memory_context = ""
        if use_memory:
            past_episodes = await self.memory.recall(
                query=question,
                company_id=str(company_id) if company_id else None,
                top_k=3,
                db=db,
            )
            memory_context = self.memory.get_context_for_query(past_episodes)

        # ── 4. Knowledge graph traversal ──
        graph_context = ""
        if use_graph:
            graph_context = await self._query_knowledge_graph(question, company_id)

        # ── 5. Merge context ──
        sources: list[dict[str, Any]] = []
        context_parts: list[str] = []

        for result in vector_results:
            sources.append({
                "chunk_id": result["chunk_id"],
                "filename": result["filename"],
                "similarity": result["similarity"],
                "excerpt": result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"],
                "source_type": "vector",
            })
            context_parts.append(f"[Document: {result['filename']}]\n{result['content']}")

        if graph_context:
            context_parts.append(f"[Knowledge Graph]\n{graph_context}")
            sources.append({"source_type": "graph", "excerpt": graph_context[:300]})

        if memory_context:
            context_parts.append(memory_context)
            sources.append({"source_type": "episodic_memory", "excerpt": memory_context[:300]})

        context = "\n\n---\n\n".join(context_parts)

        # ── 6. LLM reasoning ──
        answer = await self.reasoning.generate_answer(question, context)

        # ── 7. Store as episode ──
        episode = Episode(
            query=question,
            answer=answer,
            context_sources=[{"filename": s.get("filename", s.get("source_type", ""))} for s in sources],
            user_id=None,
            company_id=str(company_id) if company_id else None,
        )
        await self.memory.store(episode, db=db)

        confidence = float(vector_results[0]["similarity"]) if vector_results else None

        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
        )

    async def _query_knowledge_graph(
        self, question: str, company_id: uuid.UUID | None,
    ) -> str:
        """
        Query Neo4j knowledge graph for related entities.
        Determines relevant graph queries based on the question.
        """
        try:
            from app.services.graph.knowledge_graph import run_graph_query

            results_parts: list[str] = []
            q_lower = question.lower()

            # Determine relevant queries based on question keywords
            if company_id:
                cid = str(company_id)

                if any(kw in q_lower for kw in ["contrat", "contract", "fournisseur", "supplier"]):
                    records = await run_graph_query(
                        "all_contracts_for_company", {"company_id": cid}
                    )
                    if records:
                        results_parts.append(
                            "Related contracts: " +
                            ", ".join(f"{r.get('reference', '?')} (€{r.get('amount', '?')})" for r in records[:5])
                        )

                if any(kw in q_lower for kw in ["budget", "dépassement", "overrun", "dépense"]):
                    records = await run_graph_query("budget_overruns")
                    if records:
                        results_parts.append(
                            "Budget overruns: " +
                            ", ".join(f"{r.get('budget_category', '?')}" for r in records[:5])
                        )

                if any(kw in q_lower for kw in ["département", "department", "service"]):
                    records = await run_graph_query("departments_over_budget")
                    if records:
                        results_parts.append(
                            "Departments over budget: " +
                            ", ".join(f"{r.get('department', '?')} ({r.get('deviation_pct', 0)}%)" for r in records[:5])
                        )

            return "\n".join(results_parts)

        except Exception as e:
            logger.debug(f"Graph query failed (expected if Neo4j not running): {e}")
            return ""
