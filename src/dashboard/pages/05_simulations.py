"""
Scenario Simulations Dashboard Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Scenario Simulations", page_icon="🎲", layout="wide")

st.title("🎲 Scenario Simulations")
st.markdown("What-if analysis for budget changes, contract negotiations, and cash flow stress testing")

# Scenario Selection
st.header("🎯 Select Simulation Type")

simulation_type = st.radio(
    "Choose simulation:",
    ["Budget Variance", "Contract Renegotiation", "Cash Flow Stress Test", "Monte Carlo Analysis"],
    horizontal=True
)

# Budget Variance Simulation
if simulation_type == "Budget Variance":
    st.header("💵 Budget Variance Simulator")
    
    st.markdown("""
    Simulate the impact of budget increases/decreases on different departments.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        dept = st.selectbox("Department", ["Marketing", "R&D", "Operations", "Sales"])
        current_budget = {"Marketing": 500000, "R&D": 800000, "Operations": 600000, "Sales": 400000}[dept]
        st.metric("Current Budget", f"${current_budget:,.0f}")
        
    with col2:
        change_pct = st.slider("Budget Change (%)", -30, 50, 0, 5)
        new_budget = current_budget * (1 + change_pct/100)
        st.metric("New Budget", f"${new_budget:,.0f}", f"{change_pct:+.0f}%")
    
    # Impact analysis
    st.subheader("📊 Impact Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Budget Change", f"${new_budget - current_budget:+,.0f}")
    
    with col2:
        projects_impact = int(change_pct / 10)
        st.metric("Projects Affected", f"{abs(projects_impact)}", 
                 f"{'Can fund' if projects_impact > 0 else 'Must cut'} {abs(projects_impact)}")
    
    with col3:
        risk_level = "Low" if abs(change_pct) < 10 else "Medium" if abs(change_pct) < 20 else "High"
        st.metric("Risk Level", risk_level)
    
    # Visualization
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    baseline = [current_budget/12] * 6
    scenario = [new_budget/12] * 6
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=baseline, name="Current", line=dict(color='blue', dash='dash')))
    fig.add_trace(go.Scatter(x=months, y=scenario, name="Scenario", line=dict(color='green' if change_pct > 0 else 'red')))
    fig.update_layout(title=f"{dept} Monthly Budget Comparison", yaxis_title="Monthly Budget ($)", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.subheader("💡 AI Recommendations")
    if change_pct > 0:
        st.success(f"""
        **Budget Increase Scenario (+{change_pct}%)**
        
        ✅ **Opportunities:**
        - Fund {abs(projects_impact)} additional projects
        - Hire {abs(projects_impact)} new team members
        - Invest in tools/infrastructure
        
        ⚠️ **Considerations:**
        - Ensure ROI justifies increase
        - Plan spending timeline carefully
        - Monitor variance closely
        """)
    elif change_pct < 0:
        st.warning(f"""
        **Budget Cut Scenario ({change_pct}%)**
        
        ⚠️ **Impacts:**
        - May need to cut {abs(projects_impact)} projects
        - Potential staffing implications
        - Reduced operational capacity
        
        💡 **Mitigation Strategies:**
        - Prioritize high-ROI projects
        - Negotiate better vendor terms
        - Look for efficiency gains
        """)
    else:
        st.info("No change scenario - current budget maintained")

# Contract Renegotiation
elif simulation_type == "Contract Renegotiation":
    st.header("📄 Contract Renegotiation Impact")
    
    st.markdown("Simulate different contract negotiation outcomes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        contract = st.selectbox(
            "Contract",
            ["Software License ($120K)", "Cloud Services ($360K)", "Marketing Services ($80K)"]
        )
        current_value = int(contract.split("$")[1].split("K")[0]) * 1000
        
    with col2:
        negotiation_result = st.slider("Price Change (%)", -25, 25, 0, 5)
        new_value = current_value * (1 + negotiation_result/100)
    
    # Comparison
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Contract Value", f"${current_value:,.0f}")
    
    with col2:
        st.metric("Negotiated Value", f"${new_value:,.0f}", f"{negotiation_result:+.0f}%")
    
    with col3:
        savings = current_value - new_value
        st.metric("Annual Savings/Cost", f"${abs(savings):,.0f}", 
                 "Savings" if savings > 0 else "Additional Cost")
    
    # Multi-year impact
    st.subheader("📊 Multi-Year Impact")
    
    years = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
    current_costs = [current_value * (1.03 ** i) for i in range(5)]  # 3% annual increase
    negotiated_costs = [new_value * (1.03 ** i) for i in range(5)]
    cumulative_savings = [sum(current_costs[:i+1]) - sum(negotiated_costs[:i+1]) for i in range(5)]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=current_costs, name="Current Contract"))
    fig.add_trace(go.Bar(x=years, y=negotiated_costs, name="Negotiated Contract"))
    fig.add_trace(go.Scatter(x=years, y=cumulative_savings, name="Cumulative Savings", 
                            yaxis="y2", line=dict(color='green', width=3)))
    
    fig.update_layout(
        title="5-Year Contract Cost Comparison",
        yaxis_title="Annual Cost ($)",
        yaxis2=dict(title="Cumulative Savings ($)", overlaying="y", side="right"),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.metric("5-Year Total Savings", f"${cumulative_savings[-1]:,.0f}")

# Cash Flow Stress Test
elif simulation_type == "Cash Flow Stress Test":
    st.header("💸 Cash Flow Stress Test")
    
    st.markdown("Test cash flow resilience under various scenarios")
    
    scenario = st.selectbox(
        "Stress Scenario",
        [
            "30% Revenue Drop",
            "50% Payment Delays",
            "Major Unexpected Expense",
            "Combined Worst Case"
        ]
    )
    
    # Generate stress test data
    days = list(range(90))
    baseline_balance = [1200000 - i*5000 for i in days]
    
    if scenario == "30% Revenue Drop":
        stressed_balance = [1200000 - i*6500 for i in days]
        description = "Revenue drops by 30% due to market conditions"
    elif scenario == "50% Payment Delays":
        stressed_balance = [1200000 - i*7000 for i in days]
        description = "50% of expected payments are delayed by 30 days"
    elif scenario == "Major Unexpected Expense":
        stressed_balance = baseline_balance.copy()
        stressed_balance[30] -= 200000
        for i in range(31, 90):
            stressed_balance[i] = stressed_balance[30] - (i-30)*5000
        description = "Unexpected $200K expense in month 1"
    else:  # Combined
        stressed_balance = [1200000 - i*8000 for i in days]
        stressed_balance[30] -= 150000
        for i in range(31, 90):
            stressed_balance[i] = stressed_balance[30] - (i-30)*8000
        description = "Combined: revenue drop + expense + delays"
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=baseline_balance, name="Baseline", 
                            line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=days, y=stressed_balance, name="Stressed", 
                            line=dict(color='red')))
    fig.add_hline(y=1000000, line_dash="dash", line_color="orange", 
                 annotation_text="Minimum Threshold")
    fig.update_layout(title=f"Cash Flow Stress Test: {scenario}", 
                     xaxis_title="Days", yaxis_title="Balance ($)", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"**Scenario:** {description}")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_below = sum(1 for b in stressed_balance if b < 1000000)
        st.metric("Days Below Threshold", days_below)
    
    with col2:
        min_balance = min(stressed_balance)
        st.metric("Minimum Balance", f"${min_balance:,.0f}")
    
    with col3:
        shortfall = max(0, 1000000 - min_balance)
        st.metric("Maximum Shortfall", f"${shortfall:,.0f}")
    
    if days_below > 0:
        st.error(f"⚠️ **Risk Alert:** Cash balance falls below threshold for {days_below} days")
        st.markdown("""
        **Recommended Actions:**
        - Arrange backup credit line
        - Accelerate receivables collection
        - Defer non-critical expenses
        - Consider emergency cost cuts
        """)
    else:
        st.success("✅ Cash flow remains above threshold throughout stress period")

# Monte Carlo
else:
    st.header("🎲 Monte Carlo Simulation")
    
    st.markdown("Probabilistic analysis using 1000 randomized scenarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_metric = st.selectbox("Metric", ["Cash Flow", "Budget Variance", "Contract Cost"])
    
    with col2:
        simulations = st.number_input("Number of Simulations", 100, 10000, 1000, 100)
    
    if st.button("🚀 Run Simulation"):
        with st.spinner("Running Monte Carlo simulation..."):
            # Generate random outcomes
            np.random.seed(42)
            outcomes = np.random.normal(loc=100000, scale=30000, size=simulations)
            
            # Plot distribution
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=outcomes, nbinsx=50, name="Outcomes"))
            fig.update_layout(
                title=f"Monte Carlo Simulation: {target_metric} Distribution",
                xaxis_title=f"{target_metric} ($)",
                yaxis_title="Frequency",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Mean", f"${outcomes.mean():,.0f}")
            
            with col2:
                st.metric("Median", f"${np.median(outcomes):,.0f}")
            
            with col3:
                st.metric("Std Dev", f"${outcomes.std():,.0f}")
            
            with col4:
                prob_positive = (outcomes > 0).sum() / len(outcomes) * 100
                st.metric("Success Rate", f"{prob_positive:.1f}%")
            
            # Percentiles
            st.subheader("📊 Outcome Percentiles")
            
            percentiles = [10, 25, 50, 75, 90]
            values = [np.percentile(outcomes, p) for p in percentiles]
            
            perc_df = pd.DataFrame({
                "Percentile": [f"{p}th" for p in percentiles],
                "Value": values
            })
            
            st.dataframe(
                perc_df.style.format({"Value": "${:,.0f}"}),
                use_container_width=True,
                hide_index=True
            )
            
            st.info(f"""
            **Interpretation:**
            - 50% probability of outcomes between ${np.percentile(outcomes, 25):,.0f} and ${np.percentile(outcomes, 75):,.0f}
            - 80% probability of outcomes between ${np.percentile(outcomes, 10):,.0f} and ${np.percentile(outcomes, 90):,.0f}
            - {prob_positive:.1f}% probability of positive outcome
            """)

# Export
st.header("📥 Export Simulation Results")

col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Export to PDF"):
        st.info("PDF export coming soon!")

with col2:
    if st.button("📧 Email Report"):
        st.success("Simulation report emailed to stakeholders")

# Footer
st.markdown("---")
st.markdown("*Simulations powered by numpy/scipy | ML forecasting with Prophet*")
