"""Cash Flow & Invoices Dashboard Page"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_cash_flow_forecast, get_pending_invoices, format_currency

st.set_page_config(page_title="Cash Flow", page_icon="💰", layout="wide")
st.title("💰 Cash Flow & Invoices")

# Controls
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### 90-Day Cash Flow Forecast")
with col2:
    forecast_days = st.selectbox("Forecast Period", [30, 60, 90], index=2)

# Get forecast data
forecast_data = get_cash_flow_forecast(forecast_days)

if 'error' not in forecast_data:
    forecast = forecast_data.get('forecast', [])
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Balance", format_currency(forecast[0]['balance'] if forecast else 0))
    with col2:
        st.metric("Projected (30d)", format_currency(forecast[min(30, len(forecast)-1)]['balance'] if len(forecast) > 30 else 0))
    with col3:
        tensions = forecast_data.get('tensions', [])
        st.metric("Tensions Detected", len(tensions))
    with col4:
        avg_inflow = sum(f['predicted_inflow'] for f in forecast[:10]) / 10 if forecast else 0
        st.metric("Avg Daily Inflow", format_currency(avg_inflow))
    
    # Forecast chart
    if forecast:
        df = pd.DataFrame(forecast)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['date'], y=df['balance'], name='Balance', line=dict(color='#2196f3', width=3)))
        fig.add_trace(go.Scatter(x=df['date'], y=df['confidence_high'], name='High Confidence', line=dict(dash='dash', color='green')))
        fig.add_trace(go.Scatter(x=df['date'], y=df['confidence_low'], name='Low Confidence', line=dict(dash='dash', color='red')))
        fig.update_layout(title='Cash Flow Forecast', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Tensions
    if tensions:
        st.markdown("### ⚠️ Cash Flow Tensions")
        for t in tensions[:3]:
            st.warning(f"**{t['date']}**: {t['description']} (Severity: {t['severity']})")
    
    # Recommendations
    st.markdown("### 💡 Recommendations")
    for rec in forecast_data.get('recommendations', []):
        st.markdown(f"- {rec}")

# Pending invoices
st.markdown("---")
st.markdown("### 📄 Pending Invoices")

invoices_data = get_pending_invoices()
if 'error' not in invoices_data:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Receivables")
        for inv in invoices_data.get('receivables', []):
            st.markdown(f"**{inv['client']}**: {format_currency(inv['amount'])} - Due: {inv['due_date']}")
    
    with col2:
        st.markdown("#### 📤 Payables")
        for inv in invoices_data.get('payables', []):
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(inv['priority'], '⚪')
            st.markdown(f"{priority_emoji} **{inv['supplier']}**: {format_currency(inv['amount'])} - Due: {inv['due_date']}")
    
    # Net position
    st.metric("Net Position", format_currency(invoices_data.get('net_position', 0)))
