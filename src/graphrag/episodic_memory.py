"""
Episodic Memory - Pattern Detection and Historical Learning
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from neo4j import GraphDatabase
import os

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Detects and learns from recurring financial patterns.
    Examples: "Supplier X always delivers late in Q4", "Marketing always overspends by 15%"
    """
    
    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ):
        """Initialize episodic memory with Neo4j connection."""
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "fincenter123")
        self.neo4j_driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        logger.info("EpisodicMemory initialized")
    
    def detect_late_payment_patterns(
        self,
        lookback_days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Detect suppliers with consistent late payment patterns.
        
        Args:
            lookback_days: Days to look back for pattern detection
            
        Returns:
            List of detected patterns
        """
        try:
            with self.neo4j_driver.session() as session:
                query = """
                MATCH (s:Supplier)<-[:FROM_SUPPLIER]-(i:Invoice)
                WHERE i.status = 'overdue' OR i.payment_date > i.due_date
                WITH s, count(i) as late_count, collect(i) as invoices
                WHERE late_count >= 2
                RETURN s.id as supplier_id, 
                       s.name as supplier_name,
                       late_count,
                       s.avg_delay_days as avg_delay
                ORDER BY late_count DESC
                """
                
                result = session.run(query)
                
                patterns = []
                for record in result:
                    pattern = {
                        "pattern_type": "late_payment",
                        "supplier_id": record["supplier_id"],
                        "supplier_name": record["supplier_name"],
                        "occurrences": record["late_count"],
                        "avg_delay_days": record["avg_delay"],
                        "confidence": min(record["late_count"] / 10.0, 1.0),  # Max confidence at 10 occurrences
                        "recommendation": f"Consider renegotiating terms or finding alternative supplier. Average delay: {record['avg_delay']} days.",
                        "detected_at": datetime.now().isoformat()
                    }
                    patterns.append(pattern)
                
                logger.info(f"Detected {len(patterns)} late payment patterns")
                return patterns
                
        except Exception as e:
            logger.error(f"Error detecting late payment patterns: {e}")
            return []
    
    def detect_budget_overrun_patterns(
        self,
        threshold_pct: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Detect departments with consistent budget overruns.
        
        Args:
            threshold_pct: Minimum overrun percentage to consider
            
        Returns:
            List of detected patterns
        """
        try:
            with self.neo4j_driver.session() as session:
                query = """
                MATCH (d:Department)<-[:ALLOCATED_TO]-(b:Budget)
                WHERE b.variance_pct > $threshold
                WITH d, count(b) as overrun_count, avg(b.variance_pct) as avg_variance
                WHERE overrun_count >= 2
                RETURN d.id as dept_id,
                       d.name as dept_name,
                       overrun_count,
                       avg_variance,
                       d.budget_allocated as allocated,
                       d.budget_spent as spent
                ORDER BY avg_variance DESC
                """
                
                result = session.run(query, {"threshold": threshold_pct})
                
                patterns = []
                for record in result:
                    pattern = {
                        "pattern_type": "budget_overrun",
                        "department_id": record["dept_id"],
                        "department_name": record["dept_name"],
                        "occurrences": record["overrun_count"],
                        "avg_variance_pct": record["avg_variance"],
                        "budget_allocated": record["allocated"],
                        "budget_spent": record["spent"],
                        "confidence": min(record["overrun_count"] / 5.0, 1.0),
                        "recommendation": f"Increase budget allocation by {record['avg_variance']:.1f}% or implement stricter controls.",
                        "detected_at": datetime.now().isoformat()
                    }
                    patterns.append(pattern)
                
                logger.info(f"Detected {len(patterns)} budget overrun patterns")
                return patterns
                
        except Exception as e:
            logger.error(f"Error detecting budget overrun patterns: {e}")
            return []
    
    def detect_seasonal_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect seasonal spending or payment patterns.
        
        Returns:
            List of seasonal patterns
        """
        try:
            with self.neo4j_driver.session() as session:
                # Detect Q4 patterns
                query = """
                MATCH (i:Invoice)
                WHERE i.issue_date >= date('2023-10-01') AND i.issue_date <= date('2023-12-31')
                   OR i.issue_date >= date('2024-10-01') AND i.issue_date <= date('2024-12-31')
                WITH count(i) as q4_count
                MATCH (i2:Invoice)
                WITH q4_count, count(i2) as total_count
                RETURN q4_count, total_count, 
                       toFloat(q4_count) / total_count * 100 as q4_pct
                """
                
                result = session.run(query)
                record = result.single()
                
                patterns = []
                if record and record["q4_pct"] > 30:  # Q4 accounts for >30% of invoices
                    pattern = {
                        "pattern_type": "seasonal",
                        "season": "Q4",
                        "description": f"Q4 accounts for {record['q4_pct']:.1f}% of annual invoices",
                        "confidence": 0.75,
                        "recommendation": "Prepare for increased Q4 spending. Consider early negotiations.",
                        "detected_at": datetime.now().isoformat()
                    }
                    patterns.append(pattern)
                
                logger.info(f"Detected {len(patterns)} seasonal patterns")
                return patterns
                
        except Exception as e:
            logger.error(f"Error detecting seasonal patterns: {e}")
            return []
    
    def store_pattern(
        self,
        pattern_type: str,
        description: str,
        entity_type: str,
        entity_id: str,
        confidence: float,
        recommendation: str
    ) -> bool:
        """
        Store a detected pattern in the graph.
        
        Args:
            pattern_type: Type of pattern
            description: Pattern description
            entity_type: Type of related entity
            entity_id: ID of related entity
            confidence: Confidence score (0-1)
            recommendation: Recommendation text
            
        Returns:
            True if stored successfully
        """
        try:
            with self.neo4j_driver.session() as session:
                query = """
                MERGE (p:Pattern {
                    id: $pattern_id,
                    type: $pattern_type,
                    description: $description,
                    confidence: $confidence,
                    recommendation: $recommendation,
                    detected_at: datetime()
                })
                WITH p
                MATCH (e {id: $entity_id})
                MERGE (p)-[:OBSERVED_IN]->(e)
                RETURN p
                """
                
                pattern_id = f"PATTERN-{pattern_type}-{entity_id}-{datetime.now().timestamp()}"
                
                session.run(query, {
                    "pattern_id": pattern_id,
                    "pattern_type": pattern_type,
                    "description": description,
                    "confidence": confidence,
                    "recommendation": recommendation,
                    "entity_id": entity_id
                })
                
                logger.info(f"Stored pattern: {pattern_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing pattern: {e}")
            return False
    
    def get_patterns_for_entity(
        self,
        entity_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all patterns associated with an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            List of patterns
        """
        try:
            with self.neo4j_driver.session() as session:
                query = """
                MATCH (p:Pattern)-[:OBSERVED_IN]->(e {id: $entity_id})
                RETURN p.id as pattern_id,
                       p.type as pattern_type,
                       p.description as description,
                       p.confidence as confidence,
                       p.recommendation as recommendation,
                       p.detected_at as detected_at
                ORDER BY p.confidence DESC
                """
                
                result = session.run(query, {"entity_id": entity_id})
                
                patterns = []
                for record in result:
                    patterns.append(dict(record))
                
                logger.info(f"Found {len(patterns)} patterns for entity {entity_id}")
                return patterns
                
        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            return []
    
    def detect_all_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run all pattern detection algorithms.
        
        Returns:
            Dict of pattern types and their detections
        """
        all_patterns = {
            "late_payment": self.detect_late_payment_patterns(),
            "budget_overrun": self.detect_budget_overrun_patterns(),
            "seasonal": self.detect_seasonal_patterns()
        }
        
        total = sum(len(patterns) for patterns in all_patterns.values())
        logger.info(f"Detected {total} total patterns across all types")
        
        return all_patterns
    
    def close(self):
        """Close Neo4j connection."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        logger.info("EpisodicMemory connection closed")
