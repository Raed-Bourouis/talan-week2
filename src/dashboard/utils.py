"""Dashboard utilities and helper functions."""

import requests
import streamlit as st
from typing import Dict, Any, Optional
import os


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health() -> Dict[str, Any]:
    """
    Check if backend API is healthy and accessible.
    
    Returns:
        Health status dictionary
    """
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "status": "unreachable",
            "error": str(e),
            "services": {}
        }


def query_backend(question: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Send a natural language query to the backend.
    
    Args:
        question: User's question
        timeout: Request timeout in seconds
        
    Returns:
        Query response dictionary
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": question},
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "query": question
        }


def fetch_budgets() -> Dict[str, Any]:
    """Fetch budget information from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/budgets", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_contracts(status: Optional[str] = None, expiring_days: Optional[int] = None) -> Dict[str, Any]:
    """Fetch contract information from backend."""
    try:
        params = {}
        if status:
            params["status"] = status
        if expiring_days:
            params["expiring_days"] = expiring_days
        
        response = requests.get(f"{BACKEND_URL}/contracts", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_suppliers() -> Dict[str, Any]:
    """Fetch supplier information from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/suppliers", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_invoices(status: Optional[str] = None) -> Dict[str, Any]:
    """Fetch invoice information from backend."""
    try:
        params = {}
        if status:
            params["status"] = status
        
        response = requests.get(f"{BACKEND_URL}/invoices", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_patterns() -> Dict[str, Any]:
    """Fetch detected financial patterns from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/patterns", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_alerts() -> Dict[str, Any]:
    """Fetch active alerts from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/alerts", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_cashflow_forecast(days: int = 90) -> Dict[str, Any]:
    """Fetch cash flow forecast from backend."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/cashflow/forecast",
            params={"days": days},
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def show_backend_error():
    """Display backend connection error message."""
    st.error("❌ Backend API is unreachable")
    st.info("""
    **To start the backend:**
    ```bash
    docker-compose up -d backend
    ```
    
    **Check logs:**
    ```bash
    docker logs fincenter-backend
    ```
    """)


def format_currency(amount: float) -> str:
    """Format number as currency."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage."""
    return f"{value:.1f}%"


def get_status_color(status: str) -> str:
    """Get color for status."""
    colors = {
        "active": "green",
        "inactive": "gray",
        "pending": "yellow",
        "overdue": "red",
        "paid": "green",
        "completed": "green",
        "expired": "red",
        "critical": "red",
        "high": "orange",
        "medium": "yellow",
        "low": "green"
    }
    return colors.get(status.lower(), "gray")


def get_status_emoji(status: str) -> str:
    """Get emoji for status."""
    emojis = {
        "active": "✅",
        "inactive": "⭕",
        "pending": "⏳",
        "overdue": "🔴",
        "paid": "✅",
        "completed": "✅",
        "expired": "❌",
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }
    return emojis.get(status.lower(), "⚪")


def show_query_interface():
    """Display reusable query interface."""
    st.markdown("### 🔍 Ask a Question")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            "Which departments are over budget?",
            "Show me contracts expiring in the next 90 days",
            "What suppliers consistently pay late?",
            "What's the current cash flow situation?",
            "Show me all overdue invoices"
        ]
        for ex in examples:
            if st.button(f"📌 {ex}", key=f"ex_{ex}"):
                st.session_state.query = ex
                st.rerun()
    
    query = st.text_input(
        "Your Question:",
        value=st.session_state.get("query", ""),
        placeholder="e.g., Which departments are over budget?",
        key="query_input"
    )
    
    if st.button("🚀 Ask", type="primary"):
        if query:
            with st.spinner("🤔 Analyzing..."):
                result = query_backend(query)
                
                if result.get("success"):
                    st.success("✅ Analysis Complete")
                    st.markdown(result.get("answer", "No answer provided"))
                    
                    with st.expander("📋 Details"):
                        st.json(result)
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a question")


def init_session_state():
    """Initialize session state variables."""
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "page" not in st.session_state:
        st.session_state.page = "home"
