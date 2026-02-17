"""
GraphRAG Graph Store
====================
Abstract graph database interface with Neo4j implementation.
Provides CRUD operations and graph traversal capabilities.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from .config import GraphRAGConfig, get_config
from .exceptions import (
    GraphConnectionError,
    GraphStoreError,
    EntityNotFoundError,
    DuplicateEntityError,
)
from .models import (
    FinancialEntity,
    Relationship,
    EntityType,
    RelationshipType,
    GraphQuery,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ABSTRACT GRAPH STORE
# ═══════════════════════════════════════════════════════════════

class GraphStore(ABC):
    """Abstract base class for graph database operations."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the graph database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the graph database."""
        pass
    
    @abstractmethod
    async def create_entity(self, entity: FinancialEntity) -> str:
        """Create a new entity in the graph."""
        pass
    
    @abstractmethod
    async def get_entity(self, entity_id: UUID) -> Optional[dict[str, Any]]:
        """Retrieve an entity by ID."""
        pass
    
    @abstractmethod
    async def update_entity(self, entity_id: UUID, updates: dict[str, Any]) -> bool:
        """Update an entity's properties."""
        pass
    
    @abstractmethod
    async def delete_entity(self, entity_id: UUID) -> bool:
        """Delete an entity and its relationships."""
        pass
    
    @abstractmethod
    async def create_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: RelationshipType,
        properties: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a relationship between two entities."""
        pass
    
    @abstractmethod
    async def get_relationships(
        self,
        entity_id: UUID,
        direction: str = "both",
        relationship_types: Optional[list[RelationshipType]] = None,
    ) -> list[dict[str, Any]]:
        """Get all relationships for an entity."""
        pass
    
    @abstractmethod
    async def traverse(self, query: GraphQuery) -> list[dict[str, Any]]:
        """Traverse the graph starting from an entity."""
        pass
    
    @abstractmethod
    async def execute_cypher(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Execute a raw Cypher query."""
        pass


# ═══════════════════════════════════════════════════════════════
# NEO4J IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════

class Neo4jGraphStore(GraphStore):
    """Neo4j implementation of the graph store."""
    
    def __init__(self, config: Optional[GraphRAGConfig] = None):
        self.config = config or get_config()
        self.driver: Optional[AsyncDriver] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            neo4j_config = self.config.get_neo4j_config()
            self.driver = AsyncGraphDatabase.driver(
                neo4j_config["uri"],
                auth=neo4j_config["auth"],
                max_connection_lifetime=neo4j_config["max_connection_lifetime"],
                max_connection_pool_size=neo4j_config["max_connection_pool_size"],
                connection_timeout=neo4j_config["connection_timeout"],
            )
            # Verify connectivity
            await self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Connected to Neo4j at {neo4j_config['uri']}")
        except ServiceUnavailable as e:
            raise GraphConnectionError(
                f"Could not connect to Neo4j: {e}",
                {"uri": self.config.neo4j_uri}
            )
        except Exception as e:
            raise GraphStoreError(f"Failed to connect to Neo4j: {e}")
    
    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self._connected = False
            logger.info("Disconnected from Neo4j")
    
    async def create_entity(self, entity: FinancialEntity) -> str:
        """Create a new entity in Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            # Convert entity to dict, handling special types
            entity_dict = entity.model_dump(mode='json')
            entity_id = str(entity.id)
            entity_type = entity.entity_type.value
            
            # Create Cypher query
            cypher = f"""
            CREATE (n:{entity_type} {{id: $id}})
            SET n += $properties
            RETURN n.id as id
            """
            
            # Remove id from properties to avoid duplication
            properties = {k: v for k, v in entity_dict.items() if k != 'id'}
            
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(
                    cypher,
                    {"id": entity_id, "properties": properties}
                )
                record = await result.single()
                if record:
                    logger.debug(f"Created entity {entity_id} of type {entity_type}")
                    return record["id"]
                else:
                    raise GraphStoreError(f"Failed to create entity {entity_id}")
        
        except Neo4jError as e:
            if "ConstraintValidationFailed" in str(e):
                raise DuplicateEntityError(str(entity.id), entity.entity_type.value)
            raise GraphStoreError(f"Failed to create entity: {e}")
    
    async def get_entity(self, entity_id: UUID) -> Optional[dict[str, Any]]:
        """Retrieve an entity by ID from Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            cypher = """
            MATCH (n {id: $id})
            RETURN n, labels(n) as labels
            """
            
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(cypher, {"id": str(entity_id)})
                record = await result.single()
                
                if record:
                    node = dict(record["n"])
                    node["entity_type"] = record["labels"][0] if record["labels"] else None
                    return node
                return None
        
        except Neo4jError as e:
            raise GraphStoreError(f"Failed to get entity {entity_id}: {e}")
    
    async def update_entity(
        self,
        entity_id: UUID,
        updates: dict[str, Any]
    ) -> bool:
        """Update an entity's properties in Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            cypher = """
            MATCH (n {id: $id})
            SET n += $updates
            RETURN n.id as id
            """
            
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(
                    cypher,
                    {"id": str(entity_id), "updates": updates}
                )
                record = await result.single()
                
                if record:
                    logger.debug(f"Updated entity {entity_id}")
                    return True
                else:
                    raise EntityNotFoundError(str(entity_id))
        
        except Neo4jError as e:
            raise GraphStoreError(f"Failed to update entity {entity_id}: {e}")
    
    async def delete_entity(self, entity_id: UUID) -> bool:
        """Delete an entity and its relationships from Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            cypher = """
            MATCH (n {id: $id})
            DETACH DELETE n
            RETURN count(n) as deleted
            """
            
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(cypher, {"id": str(entity_id)})
                record = await result.single()
                
                if record and record["deleted"] > 0:
                    logger.debug(f"Deleted entity {entity_id}")
                    return True
                else:
                    raise EntityNotFoundError(str(entity_id))
        
        except Neo4jError as e:
            raise GraphStoreError(f"Failed to delete entity {entity_id}: {e}")
    
    async def create_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: RelationshipType,
        properties: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a relationship between two entities in Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            props = properties or {}
            rel_type = relationship_type.value.upper()
            
            cypher = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:{rel_type}]->(b)
            SET r += $properties
            RETURN id(r) as rel_id
            """
            
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(
                    cypher,
                    {
                        "source_id": str(source_id),
                        "target_id": str(target_id),
                        "properties": props,
                    }
                )
                record = await result.single()
                
                if record:
                    rel_id = str(record["rel_id"])
                    logger.debug(f"Created relationship {rel_id}: {source_id} -> {target_id}")
                    return rel_id
                else:
                    raise GraphStoreError("Failed to create relationship")
        
        except Neo4jError as e:
            raise GraphStoreError(f"Failed to create relationship: {e}")
    
    async def get_relationships(
        self,
        entity_id: UUID,
        direction: str = "both",
        relationship_types: Optional[list[RelationshipType]] = None,
    ) -> list[dict[str, Any]]:
        """Get all relationships for an entity in Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join([rt.value.upper() for rt in relationship_types])
                rel_filter = f":{rel_types}"
            
            # Build direction pattern
            if direction == "outgoing":
                pattern = f"(n)-[r{rel_filter}]->(m)"
            elif direction == "incoming":
                pattern = f"(n)<-[r{rel_filter}]-(m)"
            else:  # both
                pattern = f"(n)-[r{rel_filter}]-(m)"
            
            cypher = f"""
            MATCH {pattern}
            WHERE n.id = $id
            RETURN type(r) as rel_type, properties(r) as rel_props,
                   m.id as target_id, labels(m) as target_labels
            """
            
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(cypher, {"id": str(entity_id)})
                records = await result.values()
                
                relationships = []
                for record in records:
                    relationships.append({
                        "type": record[0],
                        "properties": record[1],
                        "target_id": record[2],
                        "target_type": record[3][0] if record[3] else None,
                    })
                
                return relationships
        
        except Neo4jError as e:
            raise GraphStoreError(f"Failed to get relationships for {entity_id}: {e}")
    
    async def traverse(self, query: GraphQuery) -> list[dict[str, Any]]:
        """Traverse the graph starting from an entity in Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            # Build relationship type filter
            rel_filter = "*1.." + str(query.max_depth)
            if query.relationship_types:
                rel_types = "|".join([rt.value.upper() for rt in query.relationship_types])
                rel_filter = f":{rel_types}{rel_filter}"
            
            # Build target entity type filter
            target_filter = ""
            if query.target_entity_types:
                target_types = "|".join([et.value for et in query.target_entity_types])
                target_filter = f":{target_types}"
            
            cypher = f"""
            MATCH path = (start {{id: $start_id}})-[r{rel_filter}]->(end{target_filter})
            RETURN end.id as entity_id, labels(end) as labels,
                   properties(end) as properties, length(path) as depth
            LIMIT 100
            """
            
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(
                    cypher,
                    {"start_id": str(query.start_entity_id)}
                )
                records = await result.values()
                
                entities = []
                for record in records:
                    entity_data = record[2] or {}
                    entity_data["id"] = record[0]
                    entity_data["entity_type"] = record[1][0] if record[1] else None
                    entity_data["depth"] = record[3]
                    entities.append(entity_data)
                
                return entities
        
        except Neo4jError as e:
            raise GraphStoreError(f"Failed to traverse graph: {e}")
    
    async def execute_cypher(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Execute a raw Cypher query in Neo4j."""
        if not self._connected:
            await self.connect()
        
        try:
            async with self.driver.session(database=self.config.neo4j_database) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
        
        except Neo4jError as e:
            raise GraphStoreError(f"Failed to execute Cypher query: {e}")
    
    async def create_indexes(self) -> None:
        """Create indexes for better query performance."""
        if not self._connected:
            await self.connect()
        
        indexes = [
            "CREATE INDEX entity_id IF NOT EXISTS FOR (n) ON (n.id)",
            "CREATE INDEX client_name IF NOT EXISTS FOR (n:client) ON (n.company_name)",
            "CREATE INDEX supplier_name IF NOT EXISTS FOR (n:supplier) ON (n.company_name)",
            "CREATE INDEX contract_ref IF NOT EXISTS FOR (n:contract) ON (n.reference)",
            "CREATE INDEX invoice_number IF NOT EXISTS FOR (n:invoice) ON (n.invoice_number)",
        ]
        
        try:
            async with self.driver.session(database=self.config.neo4j_database) as session:
                for index_query in indexes:
                    await session.run(index_query)
            logger.info("Created Neo4j indexes")
        except Neo4jError as e:
            logger.warning(f"Failed to create some indexes: {e}")


# ═══════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════

def create_graph_store(
    store_type: str = "neo4j",
    config: Optional[GraphRAGConfig] = None,
) -> GraphStore:
    """Factory function to create a graph store instance.
    
    Args:
        store_type: Type of graph store (currently only "neo4j" supported)
        config: Optional configuration object
    
    Returns:
        GraphStore instance
    """
    if store_type == "neo4j":
        return Neo4jGraphStore(config)
    else:
        raise ValueError(f"Unsupported graph store type: {store_type}")
