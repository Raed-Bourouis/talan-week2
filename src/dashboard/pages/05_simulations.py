"""Scenario Simulations Dashboard Page"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Simulations", page_icon="🎲", layout="wide")
st.title("🎲 Scenario Simulations")

# Simulation type selection
sim_type = st.selectbox(
    "Simulation Type",
    ["Budget Adjustment", "Contract Renegotiation", "Cash Flow Monte Carlo"]
)

st.markdown("---")

if sim_type == "Budget Adjustment":
    st.markdown("### 📊 Budget Adjustment Simulation")
    
    col1, col2 = st.columns(2)
    with col1:
        dept = st.selectbox("Department", ["Marketing", "R&D", "Operations"])
    with col2:
        change = st.slider("Budget Change %", -30, 30, 0)
    
    if st.button("Run Simulation", type="primary"):
        baseline = 500000
        new_budget = baseline * (1 + change/100)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Budget", f"${baseline:,.0f}")
        with col2:
            st.metric("Adjusted Budget", f"${new_budget:,.0f}", f"{change}%")
        with col3:
            st.metric("Change", f"${new_budget-baseline:,.0f}")
        
        st.success("✅ Simulation complete!")
        st.markdown("#### 💡 Impact Analysis")
        if change > 10:
            st.info("- Enables expansion of marketing campaigns\n- Consider hiring 2 additional staff\n- Review ROI projections")
        elif change < -10:
            st.warning("- Reduce non-critical spending\n- Defer 2 planned initiatives\n- Review resource allocation")
        else:
            st.info("- Minor adjustment - maintain current trajectory\n- Monitor variance closely")

elif sim_type == "Contract Renegotiation":
    st.markdown("### 📄 Contract Renegotiation Simulation")
    
    col1, col2 = st.columns(2)
    with col1:
        contract = st.selectbox("Contract", ["Software License", "Office Supplies", "Cloud Services"])
    with col2:
        price_change = st.slider("Price Change %", -20, 20, 0)
    
    if st.button("Run Simulation", type="primary"):
        baseline_value = 120000
        new_value = baseline_value * (1 + price_change/100)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Value", f"${baseline_value:,.0f}")
        with col2:
            st.metric("Proposed Value", f"${new_value:,.0f}", f"{price_change}%")
        with col3:
            st.metric("Annual Impact", f"${new_value-baseline_value:,.0f}")
        
        st.success("✅ Simulation complete!")
        st.markdown("#### 💡 Recommendations")
        if price_change > 5:
            st.warning("- Significant price increase\n- Negotiate multi-year lock-in\n- Request additional services")
        else:
            st.info("- Reasonable adjustment\n- Consider extended commitment\n- Review alternatives")

else:  # Monte Carlo
    st.markdown("### 🎲 Monte Carlo Cash Flow Simulation")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        days = st.slider("Forecast Days", 30, 180, 90)
    with col2:
        sims = st.selectbox("Simulations", [100, 500, 1000], index=2)
    with col3:
        volatility = st.slider("Volatility", 0.1, 0.5, 0.2)
    
    if st.button("Run Simulation", type="primary"):
        # Mock simulation results
        import numpy as np
        
        final_balances = np.random.normal(1050000, 150000, sims)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Final", f"${np.mean(final_balances):,.0f}")
        with col2:
            st.metric("10th Percentile", f"${np.percentile(final_balances, 10):,.0f}")
        with col3:
            st.metric("90th Percentile", f"${np.percentile(final_balances, 90):,.0f}")
        with col4:
            prob_neg = (final_balances < 0).sum() / len(final_balances) * 100
            st.metric("Risk of Negative", f"{prob_neg:.1f}%")
        
        # Distribution chart
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=final_balances, nbinsx=50, name='Distribution'))
        fig.update_layout(title='Final Balance Distribution', xaxis_title='Balance ($)', yaxis_title='Frequency')
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ Simulation complete!")
        st.info("💡 Low probability of cash shortage detected. Cash position appears healthy.")
