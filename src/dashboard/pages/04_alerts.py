"""
Alerts Dashboard Page
"""

import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="Alerts & Recommendations", page_icon="🚨", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("🚨 Alerts & Recommendations")
st.markdown("Prioritized financial alerts and AI-powered actionable recommendations")

# Alert Summary
st.header("📊 Alert Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Critical Alerts", "3", delta="+1")

with col2:
    st.metric("High Priority", "5", delta="+2")

with col3:
    st.metric("Medium Priority", "8", delta="-1")

with col4:
    st.metric("Low Priority", "12", delta="+3")

# Active Alerts
st.header("🔔 Active Alerts")

# Sample alerts data
alerts = [
    {
        "id": "ALERT-001",
        "severity": "critical",
        "type": "payment",
        "title": "Overdue Invoice - 30 Days",
        "description": "Invoice INV-2024-002 is 30 days overdue. Amount: $15,000",
        "recommendation": "Contact supplier immediately regarding payment. Consider payment plan.",
        "created": "2024-02-16",
        "status": "open"
    },
    {
        "id": "ALERT-002",
        "severity": "high",
        "type": "budget",
        "title": "Marketing Budget Overrun",
        "description": "Marketing department has exceeded budget by 15% ($75,000 over)",
        "recommendation": "Review marketing spend and implement stricter controls. Consider budget reallocation.",
        "created": "2024-02-15",
        "status": "open"
    },
    {
        "id": "ALERT-003",
        "severity": "high",
        "type": "contract",
        "title": "Contract Expiring Soon",
        "description": "Software License Agreement expires in 45 days. Value: $120,000",
        "recommendation": "Start renewal negotiations with supplier immediately.",
        "created": "2024-02-14",
        "status": "open"
    },
    {
        "id": "ALERT-004",
        "severity": "medium",
        "type": "risk",
        "title": "Supplier Payment Pattern",
        "description": "Cloud Services Ltd shows consistent late payments (avg 12 days)",
        "recommendation": "Negotiate better payment terms or consider alternative supplier.",
        "created": "2024-02-13",
        "status": "acknowledged"
    },
    {
        "id": "ALERT-005",
        "severity": "medium",
        "type": "optimization",
        "title": "Cash Flow Opportunity",
        "description": "Early payment discount available on 3 invoices. Potential savings: $2,400",
        "recommendation": "Review cash position and consider early payment to capture discount.",
        "created": "2024-02-12",
        "status": "open"
    }
]

# Filter controls
col1, col2, col3 = st.columns(3)

with col1:
    severity_filter = st.multiselect(
        "Severity",
        ["critical", "high", "medium", "low"],
        default=["critical", "high", "medium", "low"]
    )

with col2:
    type_filter = st.multiselect(
        "Type",
        ["budget", "contract", "payment", "risk", "optimization"],
        default=["budget", "contract", "payment", "risk", "optimization"]
    )

with col3:
    status_filter = st.multiselect(
        "Status",
        ["open", "acknowledged", "resolved"],
        default=["open", "acknowledged"]
    )

# Display alerts
filtered_alerts = [
    a for a in alerts
    if a["severity"] in severity_filter
    and a["type"] in type_filter
    and a["status"] in status_filter
]

for alert in filtered_alerts:
    severity_icon = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }[alert["severity"]]
    
    severity_color = {
        "critical": "red",
        "high": "orange",
        "medium": "yellow",
        "low": "green"
    }[alert["severity"]]
    
    with st.expander(f"{severity_icon} **{alert['title']}** - {alert['type'].title()}", expanded=alert["severity"]=="critical"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Description:** {alert['description']}")
            st.markdown(f"**💡 Recommendation:** {alert['recommendation']}")
            st.caption(f"Created: {alert['created']} | Status: {alert['status'].title()}")
        
        with col2:
            st.markdown(f"**Severity:** :{severity_color}[{alert['severity'].title()}]")
            st.markdown(f"**ID:** {alert['id']}")
            
            # Action buttons
            if alert["status"] == "open":
                if st.button("✅ Acknowledge", key=f"ack_{alert['id']}"):
                    st.success("Alert acknowledged")
                if st.button("✓ Resolve", key=f"resolve_{alert['id']}"):
                    st.success("Alert resolved")
            elif alert["status"] == "acknowledged":
                if st.button("✓ Resolve", key=f"resolve2_{alert['id']}"):
                    st.success("Alert resolved")

# AI-Powered Insights
st.header("🤖 AI-Powered Insights")

with st.spinner("Analyzing alerts with local LLM..."):
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": "Analyze current alerts and provide strategic recommendations"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            st.success("✅ Analysis Complete")
            st.markdown(result.get("answer", "No insights available"))
        else:
            st.warning("Could not fetch AI insights")
    except Exception as e:
        st.info("""
        **Sample AI Insight:**
        
        Based on current alerts, I recommend:
        
        1. **Immediate Action Required**: The 30-day overdue invoice needs urgent attention. Contact the supplier and set up a payment plan.
        
        2. **Budget Reallocation**: Marketing's consistent 15% overrun suggests systematic underbudgeting. Recommend increasing Marketing budget by 10-12% next quarter.
        
        3. **Contract Management**: With software license expiring in 45 days, begin renewal negotiations now to avoid service disruption and leverage early renewal discounts.
        
        4. **Supplier Diversification**: Consider diversifying cloud services providers given the late payment pattern of current supplier.
        
        5. **Cash Flow Optimization**: Capture the $2,400 in early payment discounts if cash position allows.
        """)

# Alert Categories
st.header("📊 Alert Distribution")

col1, col2 = st.columns(2)

with col1:
    # By Severity
    import plotly.graph_objects as go
    
    severity_counts = {"critical": 3, "high": 5, "medium": 8, "low": 12}
    colors = ['#FF0000', '#FFA500', '#FFFF00', '#00FF00']
    
    fig = go.Figure(data=[go.Pie(
        labels=list(severity_counts.keys()),
        values=list(severity_counts.values()),
        hole=.4,
        marker_colors=colors
    )])
    fig.update_layout(title="Alerts by Severity", height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # By Type
    type_counts = {"budget": 6, "contract": 5, "payment": 7, "risk": 4, "optimization": 6}
    
    fig = go.Figure(data=[go.Bar(
        x=list(type_counts.keys()),
        y=list(type_counts.values()),
        marker_color='lightblue'
    )])
    fig.update_layout(
        title="Alerts by Type",
        xaxis_title="Type",
        yaxis_title="Count",
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

# Alert Trends
st.header("📈 Alert Trends")

import pandas as pd

dates = pd.date_range(start='2024-01-01', end='2024-02-16', freq='D')
alert_counts = [2, 3, 1, 2, 4, 3, 2, 5, 3, 4, 2, 3, 5, 4, 3, 2, 4, 5, 3, 2, 4, 3, 5, 4, 3, 2, 4, 5, 6, 4, 3, 5, 4, 6, 5, 4, 6, 5, 7, 6, 5, 7, 6, 8, 7, 6, 5]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=dates[:len(alert_counts)],
    y=alert_counts,
    mode='lines+markers',
    name='Daily Alerts',
    line=dict(color='red', width=2),
    fill='tozeroy',
    fillcolor='rgba(255,0,0,0.1)'
))

fig.update_layout(
    title="Alert Volume Over Time",
    xaxis_title="Date",
    yaxis_title="Number of Alerts",
    height=400,
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)

# Quick Actions
st.header("⚡ Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📧 Email All Open Alerts"):
        st.success("Alerts emailed to stakeholders")

with col2:
    if st.button("📊 Generate Alert Report"):
        st.info("Report generation coming soon!")

with col3:
    if st.button("🔄 Refresh Alerts"):
        st.rerun()

with col4:
    if st.button("✓ Mark All As Read"):
        st.success("All alerts marked as read")

# Footer
st.markdown("---")
st.markdown("*Alerts generated by episodic memory and pattern detection systems*")
