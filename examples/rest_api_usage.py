"""
Example: REST API client usage.

This example demonstrates how to use the GraphRAG system via REST API.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def check_health():
    """Check system health."""
    print("Checking system health...")
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"Status: {data['status']}")
    print("Services:")
    for service, status in data['services'].items():
        emoji = "✓" if status else "✗"
        print(f"  {emoji} {service}: {'healthy' if status else 'unhealthy'}")
    print()


def add_documents():
    """Add documents to the vector store."""
    print("Adding documents...")
    
    documents = {
        "texts": [
            "GraphRAG is a hybrid retrieval system combining vector and graph search.",
            "Vector databases enable semantic similarity search over embeddings.",
            "Knowledge graphs represent structured information as nodes and relationships.",
            "Llama 3.1 is a powerful open-source language model by Meta.",
            "Sentence transformers convert text into dense vector embeddings."
        ],
        "metadata": [
            {"category": "system", "importance": "high"},
            {"category": "vector", "importance": "high"},
            {"category": "graph", "importance": "high"},
            {"category": "llm", "importance": "high"},
            {"category": "embeddings", "importance": "high"}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/documents",
        json=documents
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Added {len(data['ids'])} documents")
        return data['ids']
    else:
        print(f"✗ Failed to add documents: {response.text}")
        return []


def create_knowledge_graph():
    """Create a knowledge graph."""
    print("\nCreating knowledge graph...")
    
    # Create nodes
    nodes = [
        {"label": "System", "properties": {"name": "GraphRAG", "type": "Software"}},
        {"label": "Component", "properties": {"name": "Vector Store", "technology": "Qdrant"}},
        {"label": "Component", "properties": {"name": "Graph Store", "technology": "Neo4j"}},
        {"label": "Component", "properties": {"name": "LLM", "technology": "Ollama"}},
    ]
    
    node_ids = []
    for node in nodes:
        response = requests.post(
            f"{BASE_URL}/nodes",
            json=node
        )
        if response.status_code == 200:
            node_id = response.json()['id']
            node_ids.append(node_id)
            print(f"✓ Created node: {node['properties']['name']}")
    
    # Create relationships
    if len(node_ids) >= 4:
        relationships = [
            {"source_id": node_ids[0], "target_id": node_ids[1], "rel_type": "HAS_COMPONENT"},
            {"source_id": node_ids[0], "target_id": node_ids[2], "rel_type": "HAS_COMPONENT"},
            {"source_id": node_ids[0], "target_id": node_ids[3], "rel_type": "HAS_COMPONENT"},
        ]
        
        for rel in relationships:
            response = requests.post(
                f"{BASE_URL}/relationships",
                json=rel
            )
            if response.status_code == 201:
                print(f"✓ Created relationship")
    
    return node_ids


def query_system(query, session_id):
    """Query the system."""
    print(f"\nQuery: {query}")
    
    payload = {
        "query": query,
        "session_id": session_id
    }
    
    response = requests.post(
        f"{BASE_URL}/query",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data['answer']}\n")
        return data['answer']
    else:
        print(f"✗ Query failed: {response.text}")
        return None


def retrieve_information(query):
    """Retrieve information without generating an answer."""
    print(f"\nRetrieving information for: {query}")
    
    payload = {"query": query}
    
    response = requests.post(
        f"{BASE_URL}/retrieve",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\nVector Results:")
        for i, result in enumerate(data['vector_results'][:3], 1):
            print(f"  {i}. [{result['score']:.3f}] {result['text'][:60]}...")
        
        print("\nGraph Results:")
        for i, result in enumerate(data['graph_results'][:3], 1):
            print(f"  {i}. {result['labels']}: {result['properties']}")
        
        return data
    else:
        print(f"✗ Retrieval failed: {response.text}")
        return None


def get_conversation_history(session_id):
    """Get conversation history."""
    print(f"\nRetrieving conversation history for session: {session_id}")
    
    response = requests.get(f"{BASE_URL}/conversations/{session_id}")
    
    if response.status_code == 200:
        data = response.json()
        history = data['history']
        
        print(f"Found {len(history)} interactions:")
        for i, interaction in enumerate(history, 1):
            print(f"\n  Interaction {i}:")
            print(f"    Query: {interaction['query']}")
            print(f"    Response: {interaction['response'][:60]}...")
            print(f"    Time: {interaction['timestamp']}")
        
        return history
    else:
        print(f"✗ Failed to get history: {response.text}")
        return []


def clear_conversation(session_id):
    """Clear conversation history."""
    print(f"\nClearing conversation: {session_id}")
    
    response = requests.delete(f"{BASE_URL}/conversations/{session_id}")
    
    if response.status_code == 200:
        print(f"✓ Conversation cleared")
    else:
        print(f"✗ Failed to clear conversation: {response.text}")


def main():
    print("=" * 70)
    print("GraphRAG REST API Example")
    print("=" * 70)
    print()
    
    # Check health
    check_health()
    
    # Add documents
    doc_ids = add_documents()
    
    # Create knowledge graph
    node_ids = create_knowledge_graph()
    
    # Create a session
    session_id = f"rest-api-demo-{int(time.time())}"
    
    # Query the system
    print("\n" + "=" * 70)
    print("Querying the System")
    print("=" * 70)
    
    queries = [
        "What is GraphRAG?",
        "What components does it have?",
        "Tell me about the vector store"
    ]
    
    for query in queries:
        query_system(query, session_id)
        time.sleep(1)
    
    # Retrieve without generating
    print("\n" + "=" * 70)
    print("Testing Retrieval Mode")
    print("=" * 70)
    
    retrieve_information("knowledge graph and embeddings")
    
    # Get conversation history
    print("\n" + "=" * 70)
    print("Conversation History")
    print("=" * 70)
    
    get_conversation_history(session_id)
    
    # Clear conversation
    clear_conversation(session_id)
    
    print("\n" + "=" * 70)
    print("REST API example completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
