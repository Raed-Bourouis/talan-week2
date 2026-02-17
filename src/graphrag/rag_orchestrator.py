"""
GraphRAG RAG Orchestrator
==========================
Central orchestration layer that combines vector search, knowledge graph traversal,
episodic memory, and LLM reasoning for comprehensive financial question answering.
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from .config import GraphRAGConfig, get_config
from .episodic_memory import EpisodicMemory
from .exceptions import RAGOrchestrationError, VectorSearchError
from .knowledge_graph import KnowledgeGraphBuilder
from .llm_reasoning import ReasoningEngine
from .models import (
    RAGQuery,
    RAGResponse,
    FinancialEpisode,
    EntityType,
    RelationshipType,
)

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Multi-source RAG orchestrator for financial intelligence.
    
    Orchestrates:
    1. Vector similarity search for semantic retrieval
    2. Knowledge graph traversal for structural relationships
    3. Episodic memory recall for historical patterns
    4. LLM reasoning for answer generation and insights
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraphBuilder] = None,
        episodic_memory: Optional[EpisodicMemory] = None,
        reasoning_engine: Optional[ReasoningEngine] = None,
        config: Optional[GraphRAGConfig] = None,
    ):
        self.config = config or get_config()
        self.knowledge_graph = knowledge_graph or KnowledgeGraphBuilder(config=self.config)
        self.episodic_memory = episodic_memory or EpisodicMemory(config=self.config)
        self.reasoning_engine = reasoning_engine or ReasoningEngine(config=self.config)
        
        self._initialized = False
        logger.info("RAG Orchestrator created")
    
    async def initialize(self) -> None:
        """Initialize all components."""
        if not self._initialized:
            await self.knowledge_graph.initialize()
            self._initialized = True
            logger.info("RAG Orchestrator initialized")
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
        await self.knowledge_graph.shutdown()
        self._initialized = False
        logger.info("RAG Orchestrator shutdown")
    
    async def query(self, query: RAGQuery) -> RAGResponse:
        """
        Execute a comprehensive RAG query.
        
        Pipeline:
        1. Vector search for semantic retrieval (if enabled)
        2. Recall episodic memory (if enabled)
        3. Traverse knowledge graph (if enabled)
        4. Merge all context sources
        5. Generate answer via LLM reasoning
        6. Store interaction as new episode
        
        Args:
            query: RAGQuery containing the question and configuration
        
        Returns:
            RAGResponse with answer, sources, and confidence
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Processing RAG query: {query.question[:100]}...")
            
            sources = []
            context_parts = []
            retrieved_entities = []
            episodic_context = []
            
            # ── Step 1: Vector Search ──
            if query.use_vector_search:
                vector_results = await self._vector_search(
                    query.question,
                    query.company_id,
                    query.top_k,
                )
                
                for result in vector_results:
                    sources.append({
                        "type": "vector",
                        "filename": result.get("filename", "unknown"),
                        "similarity": result.get("similarity", 0.0),
                        "excerpt": result.get("content", "")[:300],
                    })
                    context_parts.append(
                        f"[Document: {result.get('filename', 'unknown')}]\n"
                        f"{result.get('content', '')}"
                    )
            
            # ── Step 2: Episodic Memory Recall ──
            if query.use_episodic_memory:
                recalled_episodes = self.episodic_memory.recall_similar(
                    query.question,
                    top_k=self.config.episodic_memory_recall_top_k,
                )
                
                if recalled_episodes:
                    episodic_context = recalled_episodes
                    memory_text = self.episodic_memory.get_context_for_rag(recalled_episodes)
                    context_parts.append(memory_text)
                    sources.append({
                        "type": "episodic_memory",
                        "count": len(recalled_episodes),
                        "excerpt": f"{len(recalled_episodes)} relevant past events recalled",
                    })
            
            # ── Step 3: Knowledge Graph Traversal ──
            if query.use_graph_traversal:
                graph_results = await self._query_knowledge_graph(
                    query.question,
                    query.company_id,
                )
                
                if graph_results:
                    context_parts.append(f"[Knowledge Graph]\n{graph_results['text']}")
                    sources.append({
                        "type": "knowledge_graph",
                        "entity_count": graph_results.get("entity_count", 0),
                        "excerpt": graph_results['text'][:300],
                    })
                    retrieved_entities.extend(graph_results.get("entity_ids", []))
            
            # ── Step 4: Merge Context ──
            if not context_parts:
                context = "No relevant information found in the knowledge base."
            else:
                context = "\n\n---\n\n".join(context_parts)
            
            # ── Step 5: LLM Reasoning ──
            answer = await self.reasoning_engine.generate_answer(
                query.question,
                context,
            )
            
            # Calculate confidence based on sources
            confidence = self._calculate_confidence(sources)
            
            # ── Step 6: Store as Episode ──
            episode = FinancialEpisode(
                title=f"Q: {query.question[:100]}",
                description=f"A: {answer[:200]}...",
                event_date=__import__('datetime').datetime.utcnow(),
                entities_involved=retrieved_entities,
                event_type="rag_query",
                context={
                    "question": query.question,
                    "answer": answer,
                    "sources_count": len(sources),
                },
                tags=["rag", "query"],
            )
            self.episodic_memory.store_episode(episode)
            
            # ── Step 7: Build Response ──
            response = RAGResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                retrieved_entities=retrieved_entities,
                episodic_context=episodic_context,
            )
            
            logger.info(f"RAG query completed: {len(sources)} sources, confidence={confidence}")
            return response
        
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise RAGOrchestrationError(f"Failed to process query: {e}")
    
    async def reason_with_chain_of_thought(
        self,
        question: str,
        context: Optional[str] = None,
        steps: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Perform chain-of-thought reasoning on a financial question.
        
        Args:
            question: The financial question to analyze
            context: Optional additional context
            steps: Optional custom reasoning steps
        
        Returns:
            Dictionary with reasoning steps, conclusion, and recommendations
        """
        if not self._initialized:
            await self.initialize()
        
        # If no context provided, try to gather it
        if not context:
            query = RAGQuery(
                question=question,
                use_vector_search=True,
                use_graph_traversal=True,
                use_episodic_memory=True,
                top_k=5,
            )
            rag_result = await self.query(query)
            
            # Build context from RAG results
            context_parts = []
            for source in rag_result.sources:
                if source.get("excerpt"):
                    context_parts.append(source["excerpt"])
            context = "\n\n".join(context_parts)
        
        # Perform chain-of-thought reasoning
        result = await self.reasoning_engine.chain_of_thought(
            question, context, steps
        )
        
        return result
    
    async def _vector_search(
        self,
        query: str,
        company_id: Optional[UUID],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Note: This is a placeholder. In production, integrate with:
        - pgvector (PostgreSQL extension)
        - ChromaDB
        - Qdrant
        - Or other vector databases
        """
        try:
            # TODO: Integrate with actual vector store
            # For now, return empty results
            logger.debug(f"Vector search for: {query[:50]}... (placeholder)")
            return []
        
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
    
    async def _query_knowledge_graph(
        self,
        question: str,
        company_id: Optional[UUID],
    ) -> Optional[dict[str, Any]]:
        """
        Query the knowledge graph based on the question.
        Determines relevant queries based on keywords.
        """
        try:
            q_lower = question.lower()
            results_parts = []
            entity_ids = []
            
            # Detect question intent and query accordingly
            
            # Contract-related queries
            if any(kw in q_lower for kw in ["contract", "contrat", "accord", "agreement"]):
                if any(kw in q_lower for kw in ["penalty", "pénalité", "sanction"]):
                    contracts = await self.knowledge_graph.find_contracts_with_penalty_clauses(company_id)
                    if contracts:
                        results_parts.append(
                            "Contracts with penalty clauses: " +
                            ", ".join(f"{c.get('reference', '?')} ({c.get('penalty_text', '')})" 
                                     for c in contracts[:3])
                        )
                
                if any(kw in q_lower for kw in ["expir", "renew", "renouvellement"]):
                    contracts = await self.knowledge_graph.find_contracts_expiring_soon(90)
                    if contracts:
                        results_parts.append(
                            "Contracts expiring soon: " +
                            ", ".join(f"{c.get('reference', '?')} (ends {c.get('end_date', '?')})" 
                                     for c in contracts[:3])
                        )
            
            # Invoice-related queries
            if any(kw in q_lower for kw in ["invoice", "facture", "payment", "paiement"]):
                if any(kw in q_lower for kw in ["late", "overdue", "retard", "impayé"]):
                    invoices = await self.knowledge_graph.find_overdue_invoices()
                    if invoices:
                        results_parts.append(
                            f"Overdue invoices: {len(invoices)} found, " +
                            f"total delay: {sum(i.get('delay_days', 0) for i in invoices)} days"
                        )
            
            # Budget-related queries
            if any(kw in q_lower for kw in ["budget", "spending", "dépense"]):
                # This would require department/company context
                # Placeholder for now
                pass
            
            # Client/Supplier queries
            if any(kw in q_lower for kw in ["client", "customer"]):
                # Would need entity ID from question
                pass
            
            if any(kw in q_lower for kw in ["supplier", "fournisseur", "vendor"]):
                # Would need entity ID from question
                pass
            
            if results_parts:
                return {
                    "text": "\n".join(results_parts),
                    "entity_count": len(entity_ids),
                    "entity_ids": entity_ids,
                }
            
            return None
        
        except Exception as e:
            logger.warning(f"Knowledge graph query failed: {e}")
            return None
    
    def _calculate_confidence(self, sources: list[dict[str, Any]]) -> Optional[float]:
        """Calculate confidence score based on sources."""
        if not sources:
            return 0.0
        
        # Weight different source types
        weights = {
            "vector": 0.4,
            "knowledge_graph": 0.3,
            "episodic_memory": 0.3,
        }
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for source in sources:
            source_type = source.get("type")
            if source_type in weights:
                weight = weights[source_type]
                total_weight += weight
                
                # Use similarity score if available
                if "similarity" in source:
                    weighted_score += weight * source["similarity"]
                else:
                    # Default score for non-vector sources
                    weighted_score += weight * 0.8
        
        if total_weight > 0:
            confidence = weighted_score / total_weight
            return round(confidence, 3)
        
        return 0.5  # Default medium confidence
    
    async def analyze_entity_context(
        self,
        entity_id: UUID,
        depth: int = 2,
    ) -> dict[str, Any]:
        """
        Gather comprehensive context about an entity from all sources.
        
        Returns:
            Dictionary with entity data, relationships, episodes, and insights
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get entity from knowledge graph
            entity = await self.knowledge_graph.get_entity(entity_id)
            if not entity:
                return {"error": "Entity not found"}
            
            # Traverse related entities
            related = await self.knowledge_graph.traverse_from_entity(
                entity_id,
                max_depth=depth,
            )
            
            # Recall episodes involving this entity
            episodes = self.episodic_memory.recall_by_entity(entity_id, top_k=10)
            
            # Detect patterns
            patterns = []
            late_payment_pattern = self.episodic_memory.detect_late_payment_pattern(entity_id)
            if late_payment_pattern:
                patterns.append(late_payment_pattern)
            
            return {
                "entity": entity,
                "related_entities": related,
                "episodes": [ep.model_dump(mode='json') for ep in episodes],
                "patterns": [p.model_dump(mode='json') for p in patterns],
                "statistics": {
                    "related_count": len(related),
                    "episodes_count": len(episodes),
                    "patterns_count": len(patterns),
                },
            }
        
        except Exception as e:
            logger.error(f"Failed to analyze entity context: {e}")
            return {"error": str(e)}
