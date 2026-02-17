"""
Basic usage example for GraphRAG system.

This example demonstrates:
1. Adding documents to vector store
2. Creating knowledge nodes in graph
3. Creating relationships
4. Querying the system
"""

from graphrag import GraphRAG
import time

def main():
    print("=" * 60)
    print("GraphRAG Basic Usage Example")
    print("=" * 60)
    
    # Initialize the GraphRAG client
    print("\n1. Initializing GraphRAG client...")
    client = GraphRAG()
    print("✓ Client initialized")
    
    # Add documents to vector store
    print("\n2. Adding documents to vector store...")
    documents = [
        "Python is a high-level, interpreted programming language known for its simplicity.",
        "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
        "Neural networks are computing systems inspired by biological neural networks in animal brains.",
        "Natural language processing (NLP) is a field of AI that helps computers understand human language.",
        "GraphRAG combines vector search and knowledge graphs for enhanced information retrieval."
    ]
    
    doc_ids = client.add_documents(documents)
    print(f"✓ Added {len(doc_ids)} documents")
    
    # Create knowledge nodes
    print("\n3. Creating knowledge nodes in graph...")
    
    # Create nodes for programming languages
    python_id = client.add_knowledge_node(
        label="ProgrammingLanguage",
        properties={
            "name": "Python",
            "paradigm": "Multi-paradigm",
            "typing": "Dynamic"
        }
    )
    print(f"✓ Created Python node: {python_id}")
    
    # Create nodes for AI concepts
    ml_id = client.add_knowledge_node(
        label="Concept",
        properties={
            "name": "Machine Learning",
            "field": "Artificial Intelligence",
            "description": "Learning from data"
        }
    )
    print(f"✓ Created ML node: {ml_id}")
    
    nlp_id = client.add_knowledge_node(
        label="Concept",
        properties={
            "name": "Natural Language Processing",
            "field": "Artificial Intelligence",
            "description": "Understanding human language"
        }
    )
    print(f"✓ Created NLP node: {nlp_id}")
    
    # Create relationships
    print("\n4. Creating relationships...")
    
    client.add_relationship(
        source_id=python_id,
        target_id=ml_id,
        rel_type="USED_FOR",
        properties={"common": True}
    )
    print("✓ Created relationship: Python -> USED_FOR -> Machine Learning")
    
    client.add_relationship(
        source_id=nlp_id,
        target_id=ml_id,
        rel_type="PART_OF",
        properties={"field": "AI"}
    )
    print("✓ Created relationship: NLP -> PART_OF -> Machine Learning")
    
    # Query the system
    print("\n5. Querying the system...")
    print("-" * 60)
    
    # Session ID for conversation tracking
    session_id = f"demo-session-{int(time.time())}"
    
    # Query 1
    query1 = "What is Python?"
    print(f"\nQuery: {query1}")
    answer1 = client.query(query1, session_id=session_id)
    print(f"Answer: {answer1}")
    
    # Query 2 (with context from previous query)
    query2 = "What can it be used for in AI?"
    print(f"\nQuery: {query2}")
    answer2 = client.query(query2, session_id=session_id)
    print(f"Answer: {answer2}")
    
    # Retrieve without generating answer
    print("\n6. Retrieving information (without answer generation)...")
    query3 = "Tell me about neural networks"
    results = client.retrieve(query3, session_id=session_id)
    
    print(f"\nVector Search Results ({len(results['vector_results'])} results):")
    for i, result in enumerate(results['vector_results'], 1):
        print(f"  {i}. Score: {result['score']:.3f}")
        print(f"     Text: {result['text'][:80]}...")
    
    print(f"\nGraph Search Results ({len(results['graph_results'])} results):")
    for i, result in enumerate(results['graph_results'], 1):
        print(f"  {i}. Labels: {result['labels']}")
        print(f"     Properties: {result['properties']}")
    
    # Get conversation history
    print("\n7. Retrieving conversation history...")
    history = client.get_conversation_history(session_id)
    print(f"✓ Found {len(history)} interactions in conversation")
    
    for i, interaction in enumerate(history, 1):
        print(f"\nInteraction {i}:")
        print(f"  Query: {interaction['query']}")
        print(f"  Response: {interaction['response'][:100]}...")
        print(f"  Timestamp: {interaction['timestamp']}")
    
    # Clean up
    print("\n8. Cleaning up...")
    client.clear_conversation(session_id)
    print(f"✓ Cleared conversation {session_id}")
    
    client.close()
    print("✓ Closed client connection")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
