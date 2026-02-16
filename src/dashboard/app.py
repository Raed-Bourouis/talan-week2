"""
Financial Intelligence Hub - Streamlit Dashboard
Main Application
"""

import streamlit as st
import requests
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Financial Intelligence Hub",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-critical {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
    }
    .alert-warning {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff9800;
    }
    .alert-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1f77b4/ffffff?text=FinCenter", use_column_width=True)
    st.markdown("---")
    
    st.markdown("### 🎯 Quick Navigation")
    st.markdown("""
    - 📊 **Budget** - Budget analysis and variance
    - 📄 **Contracts** - Contract monitoring
    - 💰 **Cash Flow** - Treasury forecasting
    - 🚨 **Alerts** - Active alerts and recommendations
    - 🎲 **Simulations** - Scenario analysis
    """)
    
    st.markdown("---")
    
    # System status
    st.markdown("### 🔧 System Status")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            health = response.json()
            if health['status'] == 'healthy':
                st.success("✅ All services operational")
            else:
                st.warning("⚠️ Some services degraded")
        else:
            st.error("❌ API unreachable")
    except:
        st.error("❌ Cannot connect to API")
    
    st.markdown("---")
    st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Main content
st.markdown('<p class="main-header">💰 Financial Intelligence Hub</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">GraphRAG-powered Financial Analysis & Decision Support</p>', unsafe_allow_html=True)

# Overview metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📊 Total Budget",
        value="$1.9M",
        delta="-$58K vs target"
    )

with col2:
    st.metric(
        label="📄 Active Contracts",
        value="24",
        delta="3 expiring soon"
    )

with col3:
    st.metric(
        label="💰 Cash Position",
        value="$1.05M",
        delta="+$120K this month"
    )

with col4:
    st.metric(
        label="🚨 Active Alerts",
        value="19",
        delta="+4 today"
    )

st.markdown("---")

# Quick insights section
st.markdown("### 📈 Quick Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🎯 Top Priorities")
    st.markdown("""
    <div class="alert-critical">
        <strong>🔴 CRITICAL:</strong> Marketing budget exceeded by 15% - Immediate action required
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert-warning">
        <strong>🟡 WARNING:</strong> Office Supplies contract expires in 45 days
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert-info">
        <strong>🔵 INFO:</strong> Cash flow forecast shows healthy position for next 90 days
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("#### 💡 AI Recommendations")
    st.markdown("""
    - **Budget Reallocation**: Consider shifting $50K from under-utilized R&D budget to Marketing
    - **Contract Negotiation**: Renew Office Supplies contract with 10% volume discount
    - **Cash Optimization**: 3 invoices eligible for early payment discount ($2.5K savings)
    - **Risk Mitigation**: Supplier "TechVendor Inc" shows increasing late payment pattern
    """)

st.markdown("---")

# Natural language query section
st.markdown("### 🤖 Ask a Financial Question")

query = st.text_input(
    "Enter your question in natural language:",
    placeholder="e.g., Which departments are over budget? or Show me contracts expiring in Q2"
)

if st.button("🔍 Search", type="primary"):
    if query:
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json={"question": query},
                    timeout=10
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ Analysis complete!")
                    st.markdown(f"**Answer:** {result.get('answer', 'No answer available')}")
                    
                    if result.get('patterns'):
                        with st.expander("📊 Historical Patterns"):
                            for pattern in result['patterns']:
                                st.markdown(f"- {pattern.get('description', 'N/A')}")
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error connecting to API: {e}")
    else:
        st.warning("Please enter a question")

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Financial Intelligence Hub v1.0 | Powered by GraphRAG</p>
    <p>📖 <a href='/docs'>API Documentation</a> | 🔧 <a href='/health'>System Health</a></p>
</div>
""", unsafe_allow_html=True)
