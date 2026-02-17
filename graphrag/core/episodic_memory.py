"""Episodic memory service using Redis."""
import redis
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class EpisodicMemory:
    """Episodic memory store using Redis for conversation history and context."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize the episodic memory.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
        """
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    
    def add_interaction(self, session_id: str, query: str, response: str, 
                       metadata: Optional[Dict[str, Any]] = None):
        """Add an interaction to episodic memory.
        
        Args:
            session_id: Session identifier
            query: User query
            response: System response
            metadata: Optional metadata
        """
        interaction = {
            "query": query,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        key = f"session:{session_id}:interactions"
        self.client.rpush(key, json.dumps(interaction))
    
    def get_session_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get interaction history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of interactions to return (most recent)
            
        Returns:
            List of interactions
        """
        key = f"session:{session_id}:interactions"
        
        if limit:
            interactions = self.client.lrange(key, -limit, -1)
        else:
            interactions = self.client.lrange(key, 0, -1)
        
        return [json.loads(i) for i in interactions]
    
    def get_recent_context(self, session_id: str, n: int = 5) -> str:
        """Get recent context as a formatted string.
        
        Args:
            session_id: Session identifier
            n: Number of recent interactions to include
            
        Returns:
            Formatted context string
        """
        history = self.get_session_history(session_id, limit=n)
        
        context_parts = []
        for interaction in history:
            context_parts.append(f"User: {interaction['query']}")
            context_parts.append(f"Assistant: {interaction['response']}")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str):
        """Clear all interactions for a session.
        
        Args:
            session_id: Session identifier
        """
        key = f"session:{session_id}:interactions"
        self.client.delete(key)
    
    def set_context(self, session_id: str, key: str, value: Any, ttl: Optional[int] = None):
        """Set a context value for a session.
        
        Args:
            session_id: Session identifier
            key: Context key
            value: Context value (will be JSON serialized)
            ttl: Optional time-to-live in seconds
        """
        redis_key = f"session:{session_id}:context:{key}"
        self.client.set(redis_key, json.dumps(value))
        
        if ttl:
            self.client.expire(redis_key, ttl)
    
    def get_context(self, session_id: str, key: str) -> Optional[Any]:
        """Get a context value for a session.
        
        Args:
            session_id: Session identifier
            key: Context key
            
        Returns:
            Context value or None if not found
        """
        redis_key = f"session:{session_id}:context:{key}"
        value = self.client.get(redis_key)
        
        if value:
            return json.loads(value)
        return None
