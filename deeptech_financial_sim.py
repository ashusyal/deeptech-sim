import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Deep Tech Financial Simulator", layout="wide")
st.title("🚀 Deep Tech Startup Financial Simulator")

# --- Sidebar: Intake Form ---
st.sidebar.header("Input Your Assumptions")

with st.sidebar.expander("💵 Revenue Model Assumptions", expanded=True):
    rev_type = st.radio("What are you selling?", ["Product", "Service (SaaS)", "Both"])
    avg_lifetime = st.slider("Expected Customer Lifetime (Years)", 1, 10, 3, help="Defines your Customer Lifetime Value (LTV). This is how long you expect a customer to stick around and generate revenue.")
    annual_revenue_per_customer = st.number_input("Annual Revenue per Customer ($)", 1, 100_000, 1000)

with st.sidebar.expander("🔬 R&D and Operating Costs"):
    monthly_rnd = st.number_input("Monthly R&D Spend ($)", 0, 1_000_000, 25000, step=5000)
    rnd_years = st.slider("R&D Phase Duration (Years)", 1, 5, 2)
    capitalize_rnd = st.checkbox("Capitalize R&D Expenses?", value=True, help="Toggling this ON means R&D costs are treated as assets that provide future benefit, rather than expenses. This affects EBITDA and Net Income.")

    fte = st.number_input("FTEs (Non-R&D)", 0, 500, 5)
    salary_per_fte = st.number_input("Average Salary per FTE ($)", 10000, 300000, 80000)
    monthly_ops = st.number_input("Monthly Non-R&D Operating Costs ($)", 0, 1_000_000, 15000)

    capex = st.number_input("Total Equipment Spend ($)", 0, 5_000_000, 100_000)
    depr_years = st.slider("Equipment Depreciation (Years)", 1, 10, 5)

with st.sidebar.expander("📋 Base Assumptions"):
    scenario = st.selectbox("Select Scenario", ["Base Case", "Optimistic", "Pessimistic"])
    start_date = st.date_input("Forecast Start Date", datetime.today())
    years = 5
    initial_capital = st.number_input("Initial Capital ($)", 0, 10_000_000, 500_000, step=50000)
    months_of_runway = st.number_input("Runway Alert Threshold (Months)", 1, 24, 6, help="You’ll receive a warning when projected cash is less than this many months of burn.")

    st.markdown("---")

    price_growth = st.slider("Annual Price Growth (%)", 0, 50, 5, help="A good rule of thumb is keeping up with inflation as a baseline")
    initial_customers = st.number_input("Initial Customers (Year 1)", 0, 10_000, 100)
    customer_growth = st.slider("Annual Customer Growth (%)", 0, 200, 50)
    customer_churn = st.slider("Annual Customer Churn (%)", 0, 100, 10)
    cumulative_view = st.toggle("Show Cumulative Values", value=False, help="When ON, customers from previous years continue generating revenue unless churned.")

# --- Scenario Modifiers ---
scenario_mods = {
    "Base Case": 1.0,
    "Optimistic": 1.2,
    "Pessimistic": 0.8
}
mod = scenario_mods[scenario]

# --- Time Model ---
months = pd.date_range(start=start_date, periods=60, freq='MS')
data = pd.DataFrame(index=months)
data.index.name = "Date"
data['Quarter'] = data.index.to_period("Q").astype(str)

# --- Customer & Revenue Logic ---
customer_counts = [initial_customers]
for year in range(1, years):
    prev = customer_counts[-1]
    growth = prev * (customer_growth / 100) * mod
    churn = prev * (customer_churn / 100)
    customer_counts.append(prev + growth - churn)

expanded_customers = np.repeat(customer_counts, 12)[:60]
data['Customers'] = expanded_customers

data['Price'] = annual_revenue_per_customer * ((1 + (price_growth / 100 * mod)) ** (np.arange(60)/12))
data['Revenue'] = data['Customers'] * data['Price'] / 12

# --- Cost Logic ---
data['R&D'] = np.where(np.arange(60) < rnd_years * 12, monthly_rnd * mod, 0)
data['Capitalized R&D'] = data['R&D'] if capitalize_rnd else 0

data['Operating Costs'] = (fte * salary_per_fte / 12 + monthly_ops * mod)
data['CapEx'] = np.where(np.arange(60) == 0, capex, 0)
data['Depreciation'] = capex / depr_years / 12

# --- Financials ---
data['EBITDA'] = data['Revenue'] - data['R&D'] - data['Operating Costs']
data['Net Income'] = data['EBITDA'] - data['Depreciation']
data['Cash Flow'] = data['Net Income'] - data['CapEx']
data['Cash Balance'] = initial_capital + data['Cash Flow'].cumsum()

monthly_burn = data['Operating Costs'] + data['R&D']
data['Runway Months'] = data['Cash Balance'] / monthly_burn.replace(0, np.nan)
data['Runway Warning'] = data['Runway Months'] < months_of_runway

# --- Display Section ---
# --- Display Section ---
st.subheader("⚠️ Runway Status")
if data['Runway Warning'].any():
    breach_month = data[data['Runway Warning']].index[0].strftime('%b %Y')
    st.error(f"⚠️ Your projected cash dips below {months_of_runway} months of runway in {breach_month}.")
else:
    st.success("✅ Cash runway remains above threshold for the entire forecast period.")

st.subheader("📊 Key Financial Projections")
fig, ax = plt.subplots()
data[['Revenue', 'Net Income', 'Cash Balance']].plot(ax=ax)

# Add vertical dotted lines and bold year labels
for yr in range(1, years + 1):
    x = pd.to_datetime(start_date) + pd.DateOffset(years=yr)
    ax.axvline(x, color='gray', linestyle='--', linewidth=0.8)
    ax.text(x, ax.get_ylim()[1], f"Year {yr}", rotation=90, verticalalignment='bottom', horizontalalignment='center', fontsize=9, fontweight='bold')

ax.set_ylabel("USD")
ax.set_title("Revenue, Net Income, and Cash Balance Over Time")
st.pyplot(fig)
