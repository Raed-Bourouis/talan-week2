"""
FINCENTER - Financial Intelligence Hub Dashboard
100% FREE - No API keys required!
"""

import streamlit as st
import requests
import os
from typing import Dict, Any
import logging

# Configure page
st.set_page_config(
    page_title="FINCENTER - Financial Intelligence Hub",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health() -> Dict[str, Any]:
    """Check if backend is accessible."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}


def query_backend(question: str) -> Dict[str, Any]:
    """Send query to backend."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": question},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# Main app
def main():
    # Header
    st.title("💰 FINCENTER - Financial Intelligence Hub")
    st.markdown("""
    ### GraphRAG-based Financial Analysis using **100% FREE** Local LLMs
    
    ✅ **No API Keys Required** | 💻 Runs Completely Locally | 🔒 Your Data Stays Private
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Navigation")
        st.page_link("app.py", label="🏠 Home", icon="🏠")
        
        if os.path.exists("dashboard/pages"):
            st.markdown("### 📊 Financial Intelligence")
            st.page_link("pages/01_budget.py", label="💵 Budget Analysis", icon="💵")
            st.page_link("pages/02_contracts.py", label="📄 Contracts", icon="📄")
            st.page_link("pages/03_cashflow.py", label="💸 Cash Flow", icon="💸")
            st.page_link("pages/04_alerts.py", label="🚨 Alerts", icon="🚨")
            st.page_link("pages/05_simulations.py", label="🎲 Simulations", icon="🎲")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("""
        **Tech Stack (All FREE):**
        - 🤖 Ollama (Llama 3.1)
        - 🔢 sentence-transformers
        - 🕸️ Neo4j Community
        - 🔍 Qdrant
        - 🗄️ PostgreSQL
        
        **Total Cost: $0.00** ✨
        """)
    
    # System Status
    st.header("📡 System Status")
    
    health = check_backend_health()
    
    if health.get("status") == "healthy":
        st.success("✅ All systems operational")
        
        cols = st.columns(4)
        services = health.get("services", {})
        
        with cols[0]:
            status = "✅" if services.get("ollama") else "❌"
            st.metric("Ollama LLM", status)
        with cols[1]:
            status = "✅" if services.get("neo4j") else "❌"
            st.metric("Neo4j Graph", status)
        with cols[2]:
            status = "✅" if services.get("qdrant") else "❌"
            st.metric("Qdrant Vector", status)
        with cols[3]:
            status = "✅" if services.get("api") else "❌"
            st.metric("API", status)
    elif health.get("status") == "degraded":
        st.warning("⚠️ Some services are degraded")
        st.json(health.get("services", {}))
    else:
        st.error("❌ Backend is unreachable. Please start the backend service:")
        st.code("docker-compose up -d backend")
        st.stop()
    
    # Quick Query Interface
    st.header("🔍 Ask Financial Questions")
    st.markdown("Ask any financial question in natural language!")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            "Which departments are over budget?",
            "Show me contracts expiring in the next 90 days",
            "What suppliers consistently pay late?",
            "What's the current cash flow situation?",
            "Show me all overdue invoices",
            "What financial patterns have been detected?",
            "Which projects have the highest spending?"
        ]
        for ex in examples:
            if st.button(f"📌 {ex}", key=ex):
                st.session_state.query = ex
    
    # Query input
    query = st.text_input(
        "Your Question:",
        value=st.session_state.get("query", ""),
        placeholder="e.g., Which departments are over budget?",
        key="query_input"
    )
    
    if st.button("🚀 Ask", type="primary"):
        if query:
            with st.spinner("🤔 Analyzing with local LLM..."):
                result = query_backend(query)
                
                if result.get("success"):
                    st.success("✅ Analysis Complete")
                    
                    # Display answer
                    st.markdown("### 📊 Answer:")
                    st.markdown(result.get("answer", "No answer provided"))
                    
                    # Display metadata
                    with st.expander("📋 Query Details"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Query Type", result.get("query_type", "N/A"))
                        with col2:
                            st.metric("Timestamp", result.get("timestamp", "N/A"))
                        
                        if result.get("sources"):
                            st.markdown("**Sources:**")
                            st.json(result["sources"])
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a question")
    
    # Quick Stats
    st.header("📊 Quick Overview")
    
    try:
        # Get quick stats from backend
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Active Contracts",
                value="Loading...",
                delta="View all →"
            )
        
        with col2:
            st.metric(
                label="Overdue Invoices",
                value="Loading...",
                delta="Check details →"
            )
        
        with col3:
            st.metric(
                label="Budget Variance",
                value="Loading...",
                delta="Analyze →"
            )
        
        with col4:
            st.metric(
                label="Detected Patterns",
                value="Loading...",
                delta="View insights →"
            )
        
        st.info("💡 Navigate to specific pages in the sidebar for detailed analysis")
        
    except Exception as e:
        st.error(f"Could not load overview: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p><strong>FINCENTER v1.0.0</strong> | 100% FREE & Open Source | No API Keys Required</p>
        <p>Built with ❤️ using Ollama, Streamlit, Neo4j, Qdrant & PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
