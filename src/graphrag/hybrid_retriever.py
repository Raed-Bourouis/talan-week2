"""
Hybrid Retriever combining Vector Search (Qdrant) + Graph Search (Neo4j)
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue
from neo4j import GraphDatabase
import logging
import os
from .local_embeddings import get_embeddings

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines vector search and graph traversal for comprehensive retrieval.
    """
    
    def __init__(
        self,
        qdrant_host: Optional[str] = None,
        qdrant_port: Optional[int] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ):
        """Initialize hybrid retriever with Qdrant and Neo4j connections."""
        # Qdrant connection
        self.qdrant_host = qdrant_host or os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = qdrant_port or int(os.getenv("QDRANT_PORT", "6333"))
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        
        # Neo4j connection
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "fincenter123")
        self.neo4j_driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Embeddings model
        self.embeddings = get_embeddings()
        
        logger.info("HybridRetriever initialized")
    
    def vector_search(
        self,
        query: str,
        collection_name: str = "financial_documents",
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            query: Search query
            collection_name: Qdrant collection to search
            limit: Max number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores
        """
        try:
            # Embed query
            query_vector = self.embeddings.embed_query(query)
            
            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def graph_search(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Perform graph traversal to find related entities.
        
        Args:
            entity_type: Type of starting entity (Department, Contract, Supplier, etc.)
            entity_id: Specific entity ID to start from
            relationship_types: Types of relationships to follow
            depth: Max traversal depth
            
        Returns:
            List of related entities and relationships
        """
        try:
            with self.neo4j_driver.session() as session:
                # Build Cypher query
                if entity_id:
                    query = f"""
                    MATCH (start:{entity_type} {{id: $entity_id}})
                    CALL apoc.path.subgraphAll(start, {{
                        maxLevel: $depth,
                        relationshipFilter: $rel_filter
                    }})
                    YIELD nodes, relationships
                    RETURN nodes, relationships
                    """
                    params = {
                        "entity_id": entity_id,
                        "depth": depth,
                        "rel_filter": "|".join(relationship_types) if relationship_types else None
                    }
                else:
                    # Search for all entities of type
                    query = f"""
                    MATCH (n:{entity_type})
                    RETURN n
                    LIMIT 50
                    """
                    params = {}
                
                result = session.run(query, params)
                
                results = []
                for record in result:
                    if "nodes" in record:
                        for node in record["nodes"]:
                            results.append({
                                "type": "node",
                                "labels": list(node.labels),
                                "properties": dict(node)
                            })
                        for rel in record["relationships"]:
                            results.append({
                                "type": "relationship",
                                "rel_type": rel.type,
                                "properties": dict(rel)
                            })
                    elif "n" in record:
                        node = record["n"]
                        results.append({
                            "type": "node",
                            "labels": list(node.labels),
                            "properties": dict(node)
                        })
                
                logger.info(f"Graph search returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Graph search error: {e}")
            return []
    
    def find_payment_chain(
        self,
        contract_id: Optional[str] = None,
        supplier_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find complete payment chain: Contract -> Invoice -> Payment.
        
        Args:
            contract_id: Contract ID to trace
            supplier_id: Supplier ID to trace
            
        Returns:
            List of chain elements
        """
        try:
            with self.neo4j_driver.session() as session:
                if contract_id:
                    query = """
                    MATCH path = (c:Contract {id: $contract_id})<-[:FOR_CONTRACT]-(i:Invoice)
                    OPTIONAL MATCH (i)<-[:FOR_INVOICE]-(p:Payment)
                    RETURN c, i, p
                    """
                    params = {"contract_id": contract_id}
                elif supplier_id:
                    query = """
                    MATCH path = (s:Supplier {id: $supplier_id})<-[:WITH_SUPPLIER]-(c:Contract)
                    OPTIONAL MATCH (c)<-[:FOR_CONTRACT]-(i:Invoice)
                    OPTIONAL MATCH (i)<-[:FOR_INVOICE]-(p:Payment)
                    RETURN s, c, i, p
                    """
                    params = {"supplier_id": supplier_id}
                else:
                    return []
                
                result = session.run(query, params)
                
                chains = []
                for record in result:
                    chain = {}
                    for key in record.keys():
                        if record[key]:
                            chain[key] = dict(record[key])
                    chains.append(chain)
                
                logger.info(f"Found {len(chains)} payment chains")
                return chains
                
        except Exception as e:
            logger.error(f"Payment chain search error: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Combine vector and graph search for comprehensive results.
        
        Args:
            query: Search query
            entity_type: Optional entity type to focus on
            limit: Max results
            
        Returns:
            Combined results from both search methods
        """
        # Vector search for relevant documents
        vector_results = self.vector_search(query, limit=limit)
        
        # If entity type specified, also do graph search
        graph_results = []
        if entity_type:
            graph_results = self.graph_search(entity_type, depth=2)
        
        # Combine and deduplicate
        combined = {
            "query": query,
            "vector_results": vector_results,
            "graph_results": graph_results,
            "total_results": len(vector_results) + len(graph_results)
        }
        
        logger.info(f"Hybrid search complete: {combined['total_results']} total results")
        return combined
    
    def close(self):
        """Close all connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        logger.info("HybridRetriever connections closed")
