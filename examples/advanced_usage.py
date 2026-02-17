"""
Advanced usage example for GraphRAG system.

This example demonstrates:
1. Building a knowledge graph for a specific domain
2. Complex graph relationships
3. Advanced retrieval patterns
4. Multi-turn conversations
"""

from graphrag import GraphRAG
import time

def build_knowledge_graph(client):
    """Build a knowledge graph about software development."""
    print("Building knowledge graph...")
    
    # Create language nodes
    languages = [
        {"name": "Python", "type": "Interpreted", "year": 1991},
        {"name": "JavaScript", "type": "Interpreted", "year": 1995},
        {"name": "Java", "type": "Compiled", "year": 1995},
        {"name": "Go", "type": "Compiled", "year": 2009},
    ]
    
    language_ids = {}
    for lang in languages:
        node_id = client.add_knowledge_node("Language", lang)
        language_ids[lang["name"]] = node_id
        print(f"  ✓ Created {lang['name']} node")
    
    # Create framework nodes
    frameworks = [
        {"name": "Django", "language": "Python", "type": "Web"},
        {"name": "FastAPI", "language": "Python", "type": "API"},
        {"name": "React", "language": "JavaScript", "type": "Frontend"},
        {"name": "Spring", "language": "Java", "type": "Web"},
    ]
    
    framework_ids = {}
    for fw in frameworks:
        node_id = client.add_knowledge_node("Framework", {
            "name": fw["name"],
            "type": fw["type"]
        })
        framework_ids[fw["name"]] = node_id
        print(f"  ✓ Created {fw['name']} framework node")
        
        # Create relationship to language
        if fw["language"] in language_ids:
            client.add_relationship(
                framework_ids[fw["name"]],
                language_ids[fw["language"]],
                "WRITTEN_IN"
            )
    
    # Create use case nodes
    use_cases = [
        {"name": "Web Development", "description": "Building web applications"},
        {"name": "Data Science", "description": "Analyzing and visualizing data"},
        {"name": "Machine Learning", "description": "Building AI models"},
    ]
    
    use_case_ids = {}
    for uc in use_cases:
        node_id = client.add_knowledge_node("UseCase", uc)
        use_case_ids[uc["name"]] = node_id
        print(f"  ✓ Created {uc['name']} use case node")
    
    # Create relationships between languages and use cases
    relationships = [
        (language_ids["Python"], use_case_ids["Web Development"], "USED_FOR"),
        (language_ids["Python"], use_case_ids["Data Science"], "USED_FOR"),
        (language_ids["Python"], use_case_ids["Machine Learning"], "USED_FOR"),
        (language_ids["JavaScript"], use_case_ids["Web Development"], "USED_FOR"),
        (language_ids["Java"], use_case_ids["Web Development"], "USED_FOR"),
    ]
    
    for source, target, rel_type in relationships:
        client.add_relationship(source, target, rel_type)
    
    print("✓ Knowledge graph built successfully\n")
    
    return language_ids, framework_ids, use_case_ids


def add_documentation(client):
    """Add documentation as vector documents."""
    print("Adding documentation to vector store...")
    
    docs = [
        "Python is excellent for web development with frameworks like Django and FastAPI.",
        "JavaScript is the primary language for frontend web development with React, Vue, and Angular.",
        "Django is a high-level Python web framework that encourages rapid development.",
        "FastAPI is a modern, fast Python web framework for building APIs with automatic documentation.",
        "React is a JavaScript library for building user interfaces with component-based architecture.",
        "Machine learning in Python is facilitated by libraries like scikit-learn, TensorFlow, and PyTorch.",
        "Data science with Python involves libraries like pandas, numpy, and matplotlib.",
        "Java Spring framework is widely used for enterprise applications.",
        "Go is known for its simplicity and excellent performance in concurrent programming.",
        "TypeScript adds static typing to JavaScript for better developer experience.",
    ]
    
    metadata = [{"source": "docs", "index": i} for i in range(len(docs))]
    
    doc_ids = client.add_documents(docs, metadata)
    print(f"✓ Added {len(doc_ids)} documents\n")
    
    return doc_ids


def interactive_conversation(client, session_id):
    """Simulate an interactive multi-turn conversation."""
    print("Starting interactive conversation...")
    print("-" * 60)
    
    questions = [
        "What is Python used for?",
        "Which frameworks are available for it?",
        "How does FastAPI compare to Django?",
        "Can you suggest a framework for building REST APIs?",
        "What about frontend development?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n[Turn {i}] User: {question}")
        answer = client.query(question, session_id=session_id)
        print(f"Assistant: {answer}")
        time.sleep(1)  # Simulate thinking time
    
    print("\n" + "-" * 60)


def analyze_conversation(client, session_id):
    """Analyze the conversation history."""
    print("\nAnalyzing conversation...")
    
    history = client.get_conversation_history(session_id)
    
    print(f"Total interactions: {len(history)}")
    
    # Count metadata
    total_vector_results = sum(
        h['metadata'].get('vector_results_count', 0) 
        for h in history
    )
    total_graph_results = sum(
        h['metadata'].get('graph_results_count', 0) 
        for h in history
    )
    
    print(f"Total vector results used: {total_vector_results}")
    print(f"Total graph results used: {total_graph_results}")
    
    # Show query patterns
    print("\nQuery sequence:")
    for i, interaction in enumerate(history, 1):
        print(f"  {i}. {interaction['query']}")


def main():
    print("=" * 60)
    print("GraphRAG Advanced Usage Example")
    print("=" * 60)
    print()
    
    # Initialize client
    client = GraphRAG()
    session_id = f"advanced-demo-{int(time.time())}"
    
    try:
        # Build knowledge graph
        lang_ids, fw_ids, uc_ids = build_knowledge_graph(client)
        
        # Add documentation
        doc_ids = add_documentation(client)
        
        # Run interactive conversation
        interactive_conversation(client, session_id)
        
        # Analyze conversation
        analyze_conversation(client, session_id)
        
        # Test retrieval-only mode
        print("\n" + "=" * 60)
        print("Testing retrieval-only mode...")
        print("=" * 60)
        
        query = "best Python framework for APIs"
        results = client.retrieve(query)
        
        print(f"\nQuery: {query}")
        print(f"\nTop vector results:")
        for i, result in enumerate(results['vector_results'][:3], 1):
            print(f"  {i}. [{result['score']:.3f}] {result['text']}")
        
        print(f"\nGraph results:")
        for i, result in enumerate(results['graph_results'][:3], 1):
            props = result['properties']
            print(f"  {i}. {result['labels']}: {props}")
        
        print("\n" + "=" * 60)
        print("Advanced example completed successfully!")
        print("=" * 60)
        
    finally:
        # Cleanup
        print("\nCleaning up...")
        client.clear_conversation(session_id)
        client.close()
        print("✓ Done")


if __name__ == "__main__":
    main()
