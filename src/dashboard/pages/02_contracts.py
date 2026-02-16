"""
Contracts Monitoring Dashboard Page
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    get_expiring_contracts, get_contract_clauses,
    format_currency, get_status_color
)

st.set_page_config(page_title="Contract Monitoring", page_icon="📄", layout="wide")

st.title("📄 Contract Monitoring")
st.markdown("Track contracts, clauses, and supplier performance")

# Time horizon selection
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### Expiring Contracts")

with col2:
    days_ahead = st.selectbox(
        "Look ahead (days)",
        options=[30, 60, 90, 180],
        index=2
    )

# Get expiring contracts
contracts_data = get_expiring_contracts(days_ahead)

if 'error' in contracts_data:
    st.error(f"Error loading data: {contracts_data['error']}")
else:
    contracts = contracts_data.get('contracts', [])
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Contracts Expiring", len(contracts))
    
    with col2:
        st.metric("Total Value", format_currency(contracts_data.get('total_value', 0)))
    
    with col3:
        high_urgency = sum(1 for c in contracts if c.get('urgency') == 'high')
        st.metric("High Urgency", high_urgency)
    
    with col4:
        auto_renew = sum(1 for c in contracts if c.get('auto_renew', False))
        st.metric("Auto-Renew", auto_renew)
    
    st.markdown("---")
    
    # Contracts table
    if contracts:
        df = pd.DataFrame(contracts)
        
        # Format for display
        display_df = df[['name', 'supplier', 'days_until_expiry', 'value', 'urgency', 'auto_renew']].copy()
        display_df['value'] = display_df['value'].apply(lambda x: format_currency(x))
        display_df.columns = ['Contract', 'Supplier', 'Days Until Expiry', 'Value', 'Urgency', 'Auto-Renew']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Contract expiration timeline
        st.markdown("### 📅 Expiration Timeline")
        
        fig = px.timeline(
            df,
            x_start='end_date',
            x_end='end_date',
            y='name',
            color='urgency',
            color_discrete_map={
                'critical': '#f44336',
                'high': '#ff9800',
                'medium': '#ffc107',
                'low': '#4caf50'
            },
            title='Contract Expiration Schedule'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No contracts expiring in the selected period")
    
    # Contract details
    st.markdown("---")
    st.markdown("### 🔍 Contract Details")
    
    if contracts:
        selected_contract = st.selectbox(
            "Select contract to analyze",
            options=[c['name'] for c in contracts],
            index=0
        )
        
        contract = next((c for c in contracts if c['name'] == selected_contract), None)
        
        if contract:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Contract ID:** {contract['contract_id']}")
                st.markdown(f"**Supplier:** {contract['supplier']}")
                st.markdown(f"**Value:** {format_currency(contract['value'])}")
                st.markdown(f"**End Date:** {contract['end_date']}")
                st.markdown(f"**Days Until Expiry:** {contract['days_until_expiry']}")
                
                urgency_color = {
                    'critical': '🔴',
                    'high': '🟡',
                    'medium': '🟢',
                    'low': '⚪'
                }.get(contract['urgency'], '⚪')
                
                st.markdown(f"**Urgency:** {urgency_color} {contract['urgency'].upper()}")
                st.markdown(f"**Auto-Renew:** {'✅ Yes' if contract['auto_renew'] else '❌ No'}")
            
            with col2:
                st.markdown("#### Quick Actions")
                if st.button("📧 Send Renewal Reminder"):
                    st.success("Reminder sent to procurement team")
                if st.button("📝 Request Renegotiation"):
                    st.success("Renegotiation request created")
                if st.button("📊 View Performance History"):
                    st.info("Performance history will be displayed")
            
            # Clause extraction
            st.markdown("### 📋 Extracted Clauses")
            
            clauses_data = get_contract_clauses(contract['contract_id'])
            
            if 'error' not in clauses_data:
                clauses = clauses_data.get('clauses', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    for category, items in list(clauses.items())[:3]:
                        if items:
                            st.markdown(f"**{category.replace('_', ' ').title()}:**")
                            for item in items:
                                st.markdown(f"- {item}")
                
                with col2:
                    for category, items in list(clauses.items())[3:]:
                        if items:
                            st.markdown(f"**{category.replace('_', ' ').title()}:**")
                            for item in items:
                                st.markdown(f"- {item}")
                
                # Risk assessment
                st.markdown("### ⚠️ Risk Assessment")
                
                risks = clauses_data.get('risks', [])
                if risks:
                    for risk in risks:
                        severity_emoji = {
                            'high': '🔴',
                            'medium': '🟡',
                            'low': '🟢'
                        }.get(risk['severity'], '⚪')
                        
                        st.markdown(f"""
                        {severity_emoji} **{risk['type'].replace('_', ' ').title()}** 
                        ({risk['severity'].upper()})
                        
                        {risk['description']}
                        
                        💡 *Recommendation:* {risk['recommendation']}
                        """)
                else:
                    st.success("No significant risks identified")
