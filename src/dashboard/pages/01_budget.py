"""
Budget Augmenté Dashboard Page
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    get_departments, get_budget_analysis,
    format_currency, format_percent, get_status_color
)

st.set_page_config(page_title="Budget Analysis", page_icon="📊", layout="wide")

st.title("📊 Budget Augmenté")
st.markdown("Comprehensive budget analysis with variance tracking and AI recommendations")

# Get departments data
departments_data = get_departments()

if 'error' in departments_data:
    st.error(f"Error loading data: {departments_data['error']}")
else:
    departments = departments_data.get('departments', [])
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Allocated",
            format_currency(departments_data.get('total_allocated', 0)),
            delta=None
        )
    
    with col2:
        st.metric(
            "Total Spent",
            format_currency(departments_data.get('total_spent', 0)),
            delta=None
        )
    
    with col3:
        variance = departments_data.get('overall_variance', 0)
        st.metric(
            "Overall Variance",
            format_currency(variance),
            delta=format_currency(variance)
        )
    
    with col4:
        over_budget_count = sum(1 for d in departments if d['budget_status'] == 'over_budget')
        st.metric(
            "Departments Over Budget",
            over_budget_count,
            delta=None
        )
    
    st.markdown("---")
    
    # Department selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_dept = st.selectbox(
            "Select Department",
            options=[d['name'] for d in departments],
            index=0
        )
    
    with col2:
        selected_year = st.selectbox(
            "Select Year",
            options=[2024, 2023, 2022],
            index=0
        )
    
    # Get selected department details
    dept = next((d for d in departments if d['name'] == selected_dept), None)
    
    if dept:
        # Department analysis
        st.markdown(f"### {selected_dept} - Budget Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Allocated", format_currency(dept['allocated']))
        
        with col2:
            st.metric("Spent", format_currency(dept['spent']))
        
        with col3:
            variance = dept['spent'] - dept['allocated']
            st.metric("Variance", format_currency(variance), delta=format_currency(variance))
        
        with col4:
            st.metric("Variance %", format_percent(dept['variance_percent']), 
                     delta=format_percent(dept['variance_percent']))
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Budget vs Actual bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Allocated',
                x=[selected_dept],
                y=[dept['allocated']],
                marker_color='#2196f3'
            ))
            fig.add_trace(go.Bar(
                name='Spent',
                x=[selected_dept],
                y=[dept['spent']],
                marker_color='#f44336' if dept['variance_percent'] < 0 else '#4caf50'
            ))
            fig.update_layout(
                title='Budget vs Actual',
                barmode='group',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Department comparison
            df = pd.DataFrame(departments)
            fig = px.bar(
                df,
                x='name',
                y='variance_percent',
                color='variance_percent',
                color_continuous_scale=['red', 'yellow', 'green'],
                title='Budget Variance by Department',
                labels={'variance_percent': 'Variance %', 'name': 'Department'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed analysis
        st.markdown("### 📈 Detailed Analysis")
        
        # Get detailed analysis
        analysis = get_budget_analysis(dept['id'], selected_year)
        
        if 'error' not in analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Top Expenses")
                for expense in analysis.get('top_expenses', []):
                    st.markdown(f"""
                    **{expense['category']}**: {format_currency(expense['amount'])} 
                    ({format_percent(expense['percent'])})
                    """)
            
            with col2:
                st.markdown("#### 💡 Recommendations")
                for rec in analysis.get('recommendations', []):
                    st.markdown(f"- {rec}")
        
        # Historical trend (mock data)
        st.markdown("### 📊 Historical Trend")
        
        trend_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Allocated': [83333, 83333, 83333, 83333, 83333, 83333],
            'Spent': [75000, 82000, 95000, 88000, 96000, 89000]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['Month'],
            y=trend_data['Allocated'],
            mode='lines+markers',
            name='Allocated',
            line=dict(color='#2196f3', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=trend_data['Month'],
            y=trend_data['Spent'],
            mode='lines+markers',
            name='Spent',
            line=dict(color='#f44336', width=2)
        ))
        fig.update_layout(
            title='Monthly Budget Trend',
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
