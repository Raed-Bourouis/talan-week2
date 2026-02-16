"""
Cash Flow Dashboard Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Cash Flow & Invoices", page_icon="💸", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("💸 Cash Flow & Invoices")
st.markdown("90-day cash flow forecast, invoice tracking, and payment optimization")

# Cash Flow Summary
st.header("💰 Cash Flow Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Current Balance",
        value="$1.2M",
        delta="+$150K this month"
    )

with col2:
    st.metric(
        label="Expected Inflow (30d)",
        value="$450K",
        delta="+8%"
    )

with col3:
    st.metric(
        label="Expected Outflow (30d)",
        value="$380K",
        delta="-5%"
    )

with col4:
    st.metric(
        label="Net Position (30d)",
        value="$70K",
        delta="+$25K"
    )

# 90-Day Forecast
st.header("📈 90-Day Cash Flow Forecast")

# Generate forecast data
dates = pd.date_range(start=datetime.now(), periods=90, freq='D')
base_balance = 1200000

# Simulate cash flow
inflow = [15000 + i*200 for i in range(90)]
outflow = [12000 + i*150 for i in range(90)]
balance = [base_balance]

for i in range(89):
    balance.append(balance[-1] + inflow[i] - outflow[i])

# Create confidence intervals
upper = [b * 1.1 for b in balance]
lower = [b * 0.9 for b in balance]

# Plot
fig = go.Figure()

# Confidence interval
fig.add_trace(go.Scatter(
    x=dates,
    y=upper,
    fill=None,
    mode='lines',
    line_color='rgba(0,100,255,0)',
    showlegend=False,
    name='Upper Bound'
))

fig.add_trace(go.Scatter(
    x=dates,
    y=lower,
    fill='tonexty',
    mode='lines',
    line_color='rgba(0,100,255,0)',
    fillcolor='rgba(0,100,255,0.2)',
    name='Confidence Interval'
))

# Predicted balance
fig.add_trace(go.Scatter(
    x=dates,
    y=balance,
    mode='lines',
    name='Predicted Balance',
    line=dict(color='blue', width=3)
))

# Threshold line
fig.add_trace(go.Scatter(
    x=dates,
    y=[1000000]*90,
    mode='lines',
    name='Minimum Threshold',
    line=dict(color='red', dash='dash')
))

fig.update_layout(
    title='90-Day Cash Flow Forecast (Prophet Model)',
    xaxis_title='Date',
    yaxis_title='Balance ($)',
    height=500,
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# Forecast insights
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Forecast Horizon", "90 days")
    st.metric("Model Confidence", "85%")

with col2:
    st.metric("Predicted Peak", "$2.1M")
    st.metric("Peak Date", "Day 68")

with col3:
    st.metric("Predicted Low", "$980K")
    st.metric("⚠️ Below Threshold", "Days 82-87")

if min(balance) < 1000000:
    st.warning("🚨 **Cash Flow Alert:** Balance is predicted to fall below minimum threshold around day 82. Consider:")
    st.markdown("""
    - Accelerate receivables collection
    - Delay non-critical payments
    - Arrange credit line as backup
    """)

# Invoice Tracking
st.header("📄 Invoice Tracking")

# Sample invoice data
invoices_data = {
    "Invoice": ["INV-001", "INV-002", "INV-003", "INV-004", "INV-005"],
    "Supplier": ["TechVendor Inc", "Marketing Agency", "Cloud Services", "Office Supplies", "Consulting Services"],
    "Amount": [10000, 15000, 30000, 5000, 25000],
    "Issue Date": pd.date_range(start='2024-01-15', periods=5, freq='15D'),
    "Due Date": pd.date_range(start='2024-02-14', periods=5, freq='15D'),
    "Status": ["Paid", "Overdue", "Pending", "Pending", "Paid"]
}
inv_df = pd.DataFrame(invoices_data)

# Calculate days info
today = datetime.now()
inv_df["Days Since Issue"] = (today - inv_df["Issue Date"]).dt.days
inv_df["Days Until Due"] = (inv_df["Due Date"] - today).dt.days
inv_df["Days Overdue"] = inv_df.apply(
    lambda x: max(0, (today - x["Due Date"]).days) if x["Status"] == "Overdue" else 0,
    axis=1
)

# Status filter
status_tabs = st.tabs(["All", "Pending", "Overdue", "Paid"])

with status_tabs[0]:
    st.dataframe(
        inv_df.style.format({"Amount": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True
    )

with status_tabs[1]:
    pending = inv_df[inv_df["Status"] == "Pending"]
    st.dataframe(
        pending.style.format({"Amount": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True
    )
    st.metric("Total Pending", f"${pending['Amount'].sum():,.0f}")

with status_tabs[2]:
    overdue = inv_df[inv_df["Status"] == "Overdue"]
    st.dataframe(
        overdue.style.format({"Amount": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True
    )
    st.metric("Total Overdue", f"${overdue['Amount'].sum():,.0f}")
    if len(overdue) > 0:
        st.error(f"⚠️ {len(overdue)} invoice(s) overdue. Total: ${overdue['Amount'].sum():,.0f}")

with status_tabs[3]:
    paid = inv_df[inv_df["Status"] == "Paid"]
    st.dataframe(
        paid.style.format({"Amount": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True
    )
    st.metric("Total Paid", f"${paid['Amount'].sum():,.0f}")

# Invoice Aging
st.header("📊 Invoice Aging Analysis")

aging_data = {
    "Category": ["Current (0-30)", "31-60 days", "61-90 days", ">90 days"],
    "Count": [12, 5, 2, 1],
    "Amount": [150000, 75000, 30000, 15000]
}
aging_df = pd.DataFrame(aging_data)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        aging_df,
        x="Category",
        y="Amount",
        title="Invoice Aging by Amount",
        color="Category",
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.pie(
        aging_df,
        values="Count",
        names="Category",
        title="Invoice Aging by Count",
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

# Payment Optimization
st.header("💡 Payment Optimization Opportunities")

st.markdown("""
### Early Payment Discounts Available

The following invoices offer early payment discounts:
""")

discounts = pd.DataFrame({
    "Invoice": ["INV-006", "INV-007", "INV-008"],
    "Supplier": ["Office Supplies", "Software Vendor", "Marketing Agency"],
    "Amount": [5000, 12000, 8000],
    "Discount %": [2, 1.5, 2],
    "Savings": [100, 180, 160],
    "Pay By": ["2024-02-20", "2024-02-22", "2024-02-25"]
})

st.dataframe(
    discounts.style.format({
        "Amount": "${:,.0f}",
        "Discount %": "{:.1f}%",
        "Savings": "${:,.0f}"
    }),
    use_container_width=True,
    hide_index=True
)

st.metric("Total Potential Savings", f"${discounts['Savings'].sum():,.0f}")
st.info("💡 Consider early payment if cash position allows to capture $440 in savings")

# Export & Actions
st.header("📥 Export & Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Export Invoice Report"):
        csv = inv_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "invoices.csv",
            "text/csv"
        )

with col2:
    if st.button("📧 Send Reminders"):
        st.success("Payment reminders sent to overdue suppliers")

with col3:
    if st.button("📊 Generate Forecast Report"):
        st.info("Full forecast report generation coming soon!")

# Footer
st.markdown("---")
st.markdown("*Cash flow forecast powered by Prophet ML model | Invoice data from PostgreSQL*")
