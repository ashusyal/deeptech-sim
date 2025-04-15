import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

st.set_page_config(page_title="Deep Tech Financial Simulator", layout="wide")
st.title("🚀 Deep Tech Startup Financial Simulator")

# --- Sidebar: Intake Form ---
st.sidebar.header("Input Your Assumptions")

with st.sidebar.expander("💵 Revenue Model Assumptions", expanded=True):
    rev_type = st.radio("What are you selling?", ["Product", "Service (SaaS)", "Both"])
    st.text_input("Estimated Customer Lifetime Value (LTV) — in years", value="3", help="This is a descriptive estimate only. It helps you understand the impact of recurring vs one-time revenue models.")
    cumulative_view = st.toggle("Enable Recurring Revenue Accumulation", value=False, help="When ON, customers from previous years continue generating revenue (if not churned). Most relevant for SaaS/Service models. Turn OFF for one-time product purchases.")
    price_per_unit = st.number_input("Product Price per Unit ($)", 1, 100_000, 1000)
    saas_monthly_price = 0
    if rev_type in ["Service (SaaS)", "Both"]:
        saas_monthly_price = st.number_input("Monthly SaaS Price per Customer ($)", 1, 100_000, 100)

with st.sidebar.expander("🔬 R&D and Operating Costs"):
    monthly_rnd = st.number_input("Monthly R&D Spend ($)", 0, 1_000_000, 25000, step=5000)
    rnd_years = st.slider("R&D Phase Duration (Years)", 1, 5, 2, help="This represents the development time for your current product or tech stack. Expenses entered above will apply for this duration.")
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

# --- Customer Logic ---
customer_counts = [initial_customers]
for year in range(1, years):
    prev = customer_counts[-1]
    growth = prev * (customer_growth / 100) * mod
    churn = prev * (customer_churn / 100)
    customer_counts.append(prev + growth - churn)

expanded_customers = np.repeat(customer_counts, 12)[:60]
data['Customers'] = expanded_customers

# --- Revenue Calculation ---
diffs = np.diff(customer_counts)
diffs = np.insert(diffs, 0, initial_customers)
diffs = np.repeat(diffs, 12)[:60]
data['New Customers'] = diffs
data['New Revenue'] = data['New Customers'] * price_per_unit / 12 if rev_type in ["Product", "Both"] else 0
data['Recurring Revenue'] = data['Customers'] * saas_monthly_price if rev_type in ["Service (SaaS)", "Both"] else 0
data['Revenue'] = data['New Revenue'] + data['Recurring Revenue']

# --- Cost Logic ---
data['R&D'] = np.where(np.arange(60) < rnd_years * 12, monthly_rnd * mod, 0)
data['Capitalized R&D'] = data['R&D'] if capitalize_rnd else 0

data['Operating Costs'] = (fte * salary_per_fte / 12 + monthly_ops * mod)
data['CapEx'] = np.where(np.arange(60) == 0, capex, 0)
data['Depreciation'] = capex / depr_years / 12

# --- Financials ---
data['EBITDA'] = data['Revenue'] - (data['R&D'] - data['Capitalized R&D']) - data['Operating Costs']
data['Net Income'] = data['EBITDA'] - data['Depreciation']
data['Cash Flow'] = data['Net Income'] - data['CapEx']
data['Cash Balance'] = initial_capital + data['Cash Flow'].cumsum()

monthly_burn = data['Operating Costs'] + data['R&D']
data['Runway Months'] = (data['Cash Balance'] / monthly_burn.replace(0, np.nan)).fillna(0).astype(int)
data['Runway Warning'] = data['Runway Months'] < months_of_runway

# --- Display Section ---
st.subheader("🚦 Runway Status")
if data['Runway Warning'].any():
    breach_month = data[data['Runway Warning']].index[0].strftime('%b %Y')
    st.warning(f"🟡 Your projected cash dips below {months_of_runway} months of runway in {breach_month}.")
else:
    st.success("🟢 Cash runway remains above threshold for the entire forecast period.")

st.subheader("📊 Key Financial Projections")
plot_df = data.reset_index()
plot_df['Quarter Label'] = plot_df['Date'].dt.to_period('Q').astype(str)
melted = plot_df.melt(id_vars=['Quarter Label', 'Date'], value_vars=['Revenue', 'Net Income', 'Cash Balance'], var_name='Metric', value_name='Value')
line_chart = alt.Chart(melted).mark_line().encode(
    x=alt.X('Quarter Label:N', title='Quarter'),
    y=alt.Y('Value:Q', title='USD'),
    color='Metric:N'
).properties(
    width=800,
    height=400
)
st.altair_chart(line_chart, use_container_width=True)

st.subheader("🧮 Financial Table")
styled_data = data.copy()
styled_data['Customers'] = styled_data['Customers'].astype(int)
styled_data_formatted = styled_data.style.format({
    "Price": "${:,.0f}",
    "Revenue": "${:,.0f}",
    "New Revenue": "${:,.0f}",
    "Recurring Revenue": "${:,.0f}",
    "R&D": "${:,.0f}",
    "Capitalized R&D": "${:,.0f}",
    "Operating Costs": "${:,.0f}",
    "CapEx": "${:,.0f}",
    "Depreciation": "${:,.0f}",
    "EBITDA": "${:,.0f}",
    "Net Income": "${:,.0f}",
    "Cash Flow": "${:,.0f}",
    "Cash Balance": "${:,.0f}"
})
st.dataframe(styled_data_formatted)

st.subheader("📤 Export Your Data")
@st.cache_data
def convert_df(df):
    return df.to_csv(index=True).encode('utf-8')

csv = convert_df(data)
st.download_button(
    label="Download financial projection as CSV",
    data=csv,
    file_name='financial_projection.csv',
    mime='text/csv'
) 
