"""Graph database service using Neo4j."""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional


class GraphStore:
    """Graph store using Neo4j for knowledge graph storage and traversal."""
    
    def __init__(self, uri: str, user: str, password: str):
        """Initialize the graph store.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        """Close the database connection."""
        self.driver.close()
    
    def add_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Add a node to the graph.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            Node ID
        """
        with self.driver.session() as session:
            result = session.run(
                f"CREATE (n:{label} $props) RETURN elementId(n) as id",
                props=properties
            )
            return result.single()["id"]
    
    def add_relationship(self, source_id: str, target_id: str, 
                        rel_type: str, properties: Optional[Dict[str, Any]] = None):
        """Add a relationship between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_type: Relationship type
            properties: Optional relationship properties
        """
        if properties is None:
            properties = {}
        
        with self.driver.session() as session:
            session.run(
                f"""
                MATCH (a), (b)
                WHERE elementId(a) = $source_id AND elementId(b) = $target_id
                CREATE (a)-[r:{rel_type} $props]->(b)
                """,
                source_id=source_id,
                target_id=target_id,
                props=properties
            )
    
    def find_nodes(self, label: str, properties: Optional[Dict[str, Any]] = None, 
                   limit: int = 10) -> List[Dict[str, Any]]:
        """Find nodes by label and properties.
        
        Args:
            label: Node label
            properties: Properties to match (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching nodes
        """
        with self.driver.session() as session:
            if properties:
                where_clause = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
                query = f"MATCH (n:{label}) WHERE {where_clause} RETURN n LIMIT $limit"
                params = {**properties, "limit": limit}
            else:
                query = f"MATCH (n:{label}) RETURN n LIMIT $limit"
                params = {"limit": limit}
            
            result = session.run(query, params)
            return [dict(record["n"]) for record in result]
    
    def get_neighbors(self, node_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Get neighboring nodes.
        
        Args:
            node_id: Node ID to start from
            depth: Traversal depth
            
        Returns:
            List of neighboring nodes with relationships
        """
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH path = (n)-[*1..{depth}]-(neighbor)
                WHERE elementId(n) = $node_id
                RETURN neighbor, relationships(path) as rels
                """,
                node_id=node_id
            )
            
            neighbors = []
            for record in result:
                neighbors.append({
                    "node": dict(record["neighbor"]),
                    "relationships": [dict(rel) for rel in record["rels"]]
                })
            
            return neighbors
    
    def search_by_text(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search nodes by text content.
        
        Args:
            text: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching nodes
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $text)
                RETURN n, labels(n) as labels
                LIMIT $limit
                """,
                text=text,
                limit=limit
            )
            
            return [
                {
                    "properties": dict(record["n"]),
                    "labels": record["labels"]
                }
                for record in result
            ]
    
    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
