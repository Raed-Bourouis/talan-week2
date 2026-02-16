"""Alerts & Recommendations Dashboard Page"""
import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_alerts, resolve_alert

st.set_page_config(page_title="Alerts", page_icon="🚨", layout="wide")
st.title("🚨 Alerts & Recommendations")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    status_filter = st.selectbox("Status", ["all", "active", "resolved"], index=1)
with col2:
    severity_filter = st.selectbox("Severity", ["all", "critical", "high", "medium", "low"], index=0)
with col3:
    type_filter = st.selectbox("Type", ["all", "budget", "contract", "payment", "risk"], index=0)

# Get alerts
alerts_data = get_alerts(status=status_filter if status_filter != "all" else None)

if 'error' not in alerts_data:
    alerts = alerts_data.get('alerts', [])
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Alerts", alerts_data.get('total_count', 0))
    with col2:
        st.metric("Active", alerts_data.get('active_count', 0))
    with col3:
        critical = sum(1 for a in alerts if a.get('severity') == 'critical')
        st.metric("Critical", critical)
    with col4:
        high = sum(1 for a in alerts if a.get('severity') == 'high')
        st.metric("High", high)
    
    st.markdown("---")
    
    # Display alerts
    for alert in alerts:
        severity_color = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(alert.get('severity'), '⚪')
        
        with st.expander(f"{severity_color} {alert.get('title')} [{alert.get('type').upper()}]"):
            st.markdown(f"**Severity:** {alert.get('severity').upper()}")
            st.markdown(f"**Description:** {alert.get('description')}")
            st.markdown(f"**Status:** {alert.get('status')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if alert.get('status') == 'active':
                    if st.button(f"✅ Resolve", key=f"resolve_{alert.get('id')}"):
                        result = resolve_alert(alert.get('id'))
                        if 'error' not in result:
                            st.success("Alert resolved!")
                            st.rerun()
            with col2:
                if st.button(f"📊 View Details", key=f"details_{alert.get('id')}"):
                    st.info(f"Entity: {alert.get('entity_type')} - {alert.get('entity_id')}")
    
    if not alerts:
        st.success("✅ No alerts match the selected filters")
else:
    st.error(f"Error loading alerts: {alerts_data['error']}")
