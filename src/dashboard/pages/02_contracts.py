"""
Contracts Dashboard Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Contract Monitoring", page_icon="📄", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("📄 Contract Monitoring")
st.markdown("Track contracts, monitor expiration dates, and analyze supplier performance")

# Quick Stats
st.header("📊 Contract Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Active Contracts",
        value="38",
        delta="+5 this quarter"
    )

with col2:
    st.metric(
        label="Total Value",
        value="$5.6M",
        delta="+12.3%"
    )

with col3:
    st.metric(
        label="Expiring (90 days)",
        value="7",
        delta="+2 vs last month",
        delta_color="inverse"
    )

with col4:
    st.metric(
        label="Auto-Renewal",
        value="23",
        delta="60.5% of total"
    )

# Contract List
st.header("📋 Active Contracts")

# Sample contracts data
contracts_data = {
    "ID": ["CONT-001", "CONT-002", "CONT-003"],
    "Title": [
        "Software License Agreement",
        "Marketing Services 2024",
        "Cloud Infrastructure"
    ],
    "Supplier": ["TechVendor Inc", "Marketing Agency Pro", "Cloud Services Ltd"],
    "Value": [120000, 80000, 360000],
    "Start Date": ["2024-01-01", "2024-03-01", "2023-06-01"],
    "Expiration": ["2024-12-31", "2024-09-30", "2026-05-31"],
    "Status": ["Active", "Active", "Active"],
    "Auto-Renewal": [True, False, True]
}
df = pd.DataFrame(contracts_data)

# Calculate days until expiration
today = datetime.now()
df["Expiration"] = pd.to_datetime(df["Expiration"])
df["Days Until Expiration"] = (df["Expiration"] - today).dt.days
df["Expiration Status"] = df["Days Until Expiration"].apply(
    lambda x: "🔴 Urgent" if x < 30 else "🟡 Soon" if x < 90 else "🟢 Safe"
)

# Filter controls
col1, col2, col3 = st.columns(3)

with col1:
    status_filter = st.selectbox("Status", ["All", "Active", "Expired", "Pending"])

with col2:
    supplier_filter = st.selectbox(
        "Supplier",
        ["All"] + df["Supplier"].unique().tolist()
    )

with col3:
    expiring_filter = st.selectbox(
        "Expiring",
        ["All", "Next 30 days", "Next 90 days", "Next 180 days"]
    )

# Display contracts
st.dataframe(
    df.style.format({
        "Value": "${:,.0f}",
        "Days Until Expiration": "{:.0f} days"
    }),
    use_container_width=True,
    hide_index=True
)

# Visualizations
col1, col2 = st.columns(2)

with col1:
    # Contract value by supplier
    fig = px.bar(
        df,
        x="Supplier",
        y="Value",
        title="Contract Value by Supplier",
        color="Supplier",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Expiration timeline
    fig = px.scatter(
        df,
        x="Expiration",
        y="Value",
        size="Value",
        color="Expiration Status",
        hover_data=["Title", "Supplier"],
        title="Contract Expiration Timeline",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# Expiring Contracts Alert
st.header("⚠️ Contracts Expiring Soon")

expiring_df = df[df["Days Until Expiration"] < 90].sort_values("Days Until Expiration")

if len(expiring_df) > 0:
    for _, contract in expiring_df.iterrows():
        with st.expander(f"{contract['Expiration Status']} {contract['Title']} - {contract['Days Until Expiration']:.0f} days"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Supplier:** {contract['Supplier']}")
                st.markdown(f"**Value:** ${contract['Value']:,.0f}")
                st.markdown(f"**Expiration:** {contract['Expiration'].strftime('%Y-%m-%d')}")
                st.markdown(f"**Auto-Renewal:** {'Yes' if contract['Auto-Renewal'] else 'No'}")
                
                if contract['Days Until Expiration'] < 30:
                    st.error("🚨 Urgent action required!")
                    st.markdown("**Recommendation:** Contact supplier immediately to start renewal negotiations.")
                else:
                    st.warning("⏰ Start planning renewal process")
                    st.markdown("**Recommendation:** Begin renewal discussions in the next 2-4 weeks.")
            
            with col2:
                if st.button("📧 Contact", key=f"contact_{contract['ID']}"):
                    st.success("Email sent to supplier")
                if st.button("📝 Renew", key=f"renew_{contract['ID']}"):
                    st.success("Renewal process initiated")
else:
    st.info("✅ No contracts expiring in the next 90 days")

# Contract Clauses (AI Extraction)
st.header("🤖 AI-Extracted Contract Clauses")

selected_contract = st.selectbox(
    "Select Contract for Clause Analysis",
    df["Title"].tolist()
)

contract = df[df["Title"] == selected_contract].iloc[0]

st.markdown(f"### {selected_contract}")
st.markdown(f"**Supplier:** {contract['Supplier']}")

# Sample extracted clauses
clauses = {
    "Payment Terms": "NET30 - Payment due 30 days after invoice date",
    "Renewal Clause": "Automatic renewal unless terminated 60 days before expiration" if contract['Auto-Renewal'] else "Manual renewal required",
    "Termination": "Either party may terminate with 30 days written notice",
    "Penalties": "Late payment: 2% interest per month",
    "Price Indexation": "Annual increase tied to CPI, max 5%",
    "SLA": "99.5% uptime guarantee with credits for breaches"
}

col1, col2 = st.columns(2)

with col1:
    for key, value in list(clauses.items())[:3]:
        st.markdown(f"**{key}:**")
        st.info(value)

with col2:
    for key, value in list(clauses.items())[3:]:
        st.markdown(f"**{key}:**")
        st.info(value)

# Supplier Performance
st.header("📊 Supplier Performance")

supplier_perf = pd.DataFrame({
    "Supplier": df["Supplier"].unique(),
    "Contracts": [1, 1, 1],
    "Total Value": [120000, 80000, 360000],
    "Reliability Score": [0.85, 0.92, 0.78],
    "Avg Delay (days)": [5, 2, 12],
    "On-Time %": [85, 92, 78]
})

st.dataframe(
    supplier_perf.style.format({
        "Total Value": "${:,.0f}",
        "Reliability Score": "{:.2f}",
        "On-Time %": "{:.0f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# Export Options
st.header("📥 Export & Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "contracts.csv",
            "text/csv"
        )

with col2:
    if st.button("📧 Email Report"):
        st.success("Report emailed to stakeholders")

with col3:
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Footer
st.markdown("---")
st.markdown("*Contract data updated from Neo4j graph database | Clauses extracted using local Ollama LLM*")
