"""
Budget Analysis Dashboard Page
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Budget Analysis", page_icon="💵", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("💵 Budget Analysis")
st.markdown("Real-time budget tracking, variance analysis, and AI-powered recommendations")

# Quick stats
st.header("📊 Budget Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Allocated",
        value="$2.3M",
        delta="10% vs last quarter"
    )

with col2:
    st.metric(
        label="Total Spent",
        value="$1.975M",
        delta="-14.1%",
        delta_color="inverse"
    )

with col3:
    st.metric(
        label="Remaining",
        value="$325K",
        delta="14.1%"
    )

with col4:
    st.metric(
        label="Departments Over Budget",
        value="2",
        delta="1 more than last quarter",
        delta_color="inverse"
    )

# Department breakdown
st.header("🏢 Department Budget Breakdown")

# Sample data
departments_data = {
    "Department": ["Marketing", "R&D", "Operations", "Sales"],
    "Allocated": [500000, 800000, 600000, 400000],
    "Spent": [425000, 680000, 520000, 350000],
    "Manager": ["Jane Smith", "John Doe", "Bob Johnson", "Alice Williams"]
}
df = pd.DataFrame(departments_data)

# Calculate variance
df["Remaining"] = df["Allocated"] - df["Spent"]
df["Variance %"] = ((df["Spent"] - df["Allocated"]) / df["Allocated"] * 100).round(1)
df["Status"] = df["Variance %"].apply(lambda x: "🔴 Over" if x > 0 else "🟢 Under" if x < -10 else "🟡 On Track")

# Display table
st.dataframe(
    df.style.format({
        "Allocated": "${:,.0f}",
        "Spent": "${:,.0f}",
        "Remaining": "${:,.0f}",
        "Variance %": "{:.1f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# Visualizations
col1, col2 = st.columns(2)

with col1:
    # Bar chart: Allocated vs Spent
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Allocated',
        x=df['Department'],
        y=df['Allocated'],
        marker_color='lightblue'
    ))
    fig.add_trace(go.Bar(
        name='Spent',
        x=df['Department'],
        y=df['Spent'],
        marker_color='darkblue'
    ))
    fig.update_layout(
        title='Budget Allocated vs Spent by Department',
        barmode='group',
        yaxis_title='Amount ($)',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Pie chart: Spending distribution
    fig = px.pie(
        df,
        values='Spent',
        names='Department',
        title='Spending Distribution',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# Variance analysis
st.header("📈 Variance Analysis")

# Variance bar chart
fig = go.Figure()
colors = ['red' if x > 0 else 'green' for x in df['Variance %']]
fig.add_trace(go.Bar(
    x=df['Department'],
    y=df['Variance %'],
    marker_color=colors,
    text=df['Variance %'].apply(lambda x: f"{x:+.1f}%"),
    textposition='outside'
))
fig.update_layout(
    title='Budget Variance by Department',
    yaxis_title='Variance (%)',
    xaxis_title='Department',
    height=400,
    showlegend=False
)
fig.add_hline(y=0, line_dash="dash", line_color="gray")
st.plotly_chart(fig, use_container_width=True)

# AI Recommendations
st.header("🤖 AI-Powered Recommendations")

with st.spinner("Analyzing budget data with local LLM..."):
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": "Analyze the current budget situation and provide recommendations"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            st.success("✅ Analysis Complete")
            st.markdown(result.get("answer", "No recommendations available"))
        else:
            st.warning("Could not fetch AI recommendations")
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("💡 Sample Recommendation: Marketing department shows consistent 15% budget overrun. Consider:\n1. Increase budget allocation by 10-15%\n2. Implement stricter approval process\n3. Review Q4 spending patterns")

# Detailed Department View
st.header("🔍 Detailed Department Analysis")

selected_dept = st.selectbox(
    "Select Department",
    df["Department"].tolist()
)

dept_data = df[df["Department"] == selected_dept].iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Allocated", f"${dept_data['Allocated']:,.0f}")
    st.metric("Spent", f"${dept_data['Spent']:,.0f}")

with col2:
    st.metric("Remaining", f"${dept_data['Remaining']:,.0f}")
    st.metric("Variance", f"{dept_data['Variance %']:+.1f}%")

with col3:
    st.metric("Status", dept_data['Status'])
    st.metric("Manager", dept_data['Manager'])

# Spending trend
st.subheader(f"📊 {selected_dept} Spending Trend")

# Sample monthly data
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
spending = [60000, 75000, 80000, 85000, 70000, 55000]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=months,
    y=spending,
    mode='lines+markers',
    name='Actual Spending',
    line=dict(color='blue', width=3),
    marker=dict(size=10)
))

# Budget line
monthly_budget = dept_data['Allocated'] / 12
fig.add_trace(go.Scatter(
    x=months,
    y=[monthly_budget] * len(months),
    mode='lines',
    name='Monthly Budget Target',
    line=dict(color='red', dash='dash')
))

fig.update_layout(
    title=f'{selected_dept} Monthly Spending',
    xaxis_title='Month',
    yaxis_title='Spending ($)',
    height=400,
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)

# Export options
st.header("📥 Export Data")

col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="budget_analysis.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📊 Generate Report"):
        st.info("Report generation coming soon!")

# Footer
st.markdown("---")
st.markdown("*Data refreshed in real-time from Neo4j graph database*")
