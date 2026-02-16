"""
Episodic Memory
Pattern detection and historical learning
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from collections import defaultdict

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """Detect and store patterns from historical financial data"""
    
    def __init__(self, neo4j_driver, qdrant_client, embedding_function):
        self.neo4j_driver = neo4j_driver
        self.qdrant_client = qdrant_client
        self.embedding_function = embedding_function
    
    def detect_patterns(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """
        Detect patterns for a specific entity
        
        Args:
            entity_type: Type of entity (Supplier, Department, etc.)
            entity_id: Entity identifier
            
        Returns:
            List of detected patterns
        """
        logger.info(f"Detecting patterns for {entity_type}: {entity_id}")
        
        patterns = []
        
        if entity_type == 'Supplier':
            patterns.extend(self._detect_supplier_patterns(entity_id))
        elif entity_type == 'Department':
            patterns.extend(self._detect_department_patterns(entity_id))
        
        return patterns
    
    def _detect_supplier_patterns(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Detect supplier-specific patterns"""
        with self.neo4j_driver.session() as session:
            # Check for late delivery patterns
            query = """
            MATCH (s:Supplier {id: $supplier_id})-[:HAS_CONTRACT]->(c:Contract)
                  -[:GENERATED_INVOICE]->(i:Invoice)
            WHERE i.days_late > 0
            RETURN count(i) as late_count, avg(i.days_late) as avg_late_days,
                   collect(i.issue_date) as late_dates
            """
            
            result = session.run(query, supplier_id=supplier_id)
            record = result.single()
            
            patterns = []
            
            if record and record['late_count'] > 2:
                # Pattern detected
                patterns.append({
                    'type': 'late_payment',
                    'entity_type': 'Supplier',
                    'entity_id': supplier_id,
                    'description': f"Supplier consistently pays late (avg {record['avg_late_days']:.1f} days)",
                    'confidence': min(0.5 + (record['late_count'] * 0.1), 0.95),
                    'occurrences': record['late_count'],
                    'recommendation': 'Consider adjusting payment terms or penalties'
                })
            
            return patterns
    
    def _detect_department_patterns(self, department_id: str) -> List[Dict[str, Any]]:
        """Detect department-specific patterns"""
        with self.neo4j_driver.session() as session:
            # Check for budget overrun patterns
            query = """
            MATCH (d:Department {id: $department_id})-[:HAS_BUDGET]->(b:Budget)
            WHERE b.variance_percent < 0
            RETURN count(b) as overrun_count, avg(b.variance_percent) as avg_variance
            """
            
            result = session.run(query, department_id=department_id)
            record = result.single()
            
            patterns = []
            
            if record and record['overrun_count'] > 0:
                patterns.append({
                    'type': 'budget_overrun',
                    'entity_type': 'Department',
                    'entity_id': department_id,
                    'description': f"Department frequently exceeds budget (avg {record['avg_variance']*100:.1f}%)",
                    'confidence': min(0.5 + (record['overrun_count'] * 0.15), 0.9),
                    'occurrences': record['overrun_count'],
                    'recommendation': 'Review budget allocation or spending controls'
                })
            
            return patterns
    
    def store_pattern(self, pattern: Dict[str, Any]) -> bool:
        """Store detected pattern in episodic memory"""
        try:
            # Store in Neo4j graph
            with self.neo4j_driver.session() as session:
                query = """
                MERGE (p:Pattern {id: $id})
                SET p.type = $type,
                    p.description = $description,
                    p.confidence = $confidence,
                    p.occurrences = $occurrences,
                    p.last_observed = datetime()
                RETURN p
                """
                
                pattern_id = f"PATTERN_{pattern['entity_type']}_{pattern['entity_id']}_{pattern['type']}"
                
                session.run(query,
                          id=pattern_id,
                          type=pattern['type'],
                          description=pattern['description'],
                          confidence=pattern['confidence'],
                          occurrences=pattern['occurrences'])
                
                # Link to entity
                link_query = f"""
                MATCH (p:Pattern {{id: $pattern_id}})
                MATCH (e:{pattern['entity_type']} {{id: $entity_id}})
                MERGE (e)-[:HAS_PATTERN]->(p)
                """
                
                session.run(link_query,
                          pattern_id=pattern_id,
                          entity_id=pattern['entity_id'])
            
            # Store embedding in Qdrant for semantic search
            self._store_pattern_embedding(pattern)
            
            logger.info(f"Stored pattern: {pattern['type']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing pattern: {e}")
            return False
    
    def _store_pattern_embedding(self, pattern: Dict[str, Any]):
        """Store pattern embedding in Qdrant"""
        try:
            embedding = self.embedding_function(pattern['description'])
            
            from qdrant_client.models import PointStruct
            import hashlib
            
            point_id = int(hashlib.md5(pattern['description'].encode()).hexdigest()[:8], 16)
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    'pattern_type': pattern['type'],
                    'entity_type': pattern['entity_type'],
                    'entity_id': pattern['entity_id'],
                    'description': pattern['description'],
                    'confidence': pattern['confidence']
                }
            )
            
            self.qdrant_client.upsert(
                collection_name='episodic_memory',
                points=[point]
            )
        except Exception as e:
            logger.error(f"Error storing pattern embedding: {e}")
    
    def retrieve_relevant_patterns(self, context: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant patterns based on current context
        
        Args:
            context: Current context or query
            top_k: Number of patterns to retrieve
            
        Returns:
            List of relevant patterns
        """
        try:
            # Search for similar patterns
            query_vector = self.embedding_function(context)
            
            results = self.qdrant_client.search(
                collection_name='episodic_memory',
                query_vector=query_vector,
                limit=top_k
            )
            
            patterns = []
            for hit in results:
                patterns.append({
                    'score': hit.score,
                    **hit.payload
                })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error retrieving patterns: {e}")
            return []
