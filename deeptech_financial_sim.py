import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

st.set_page_config(page_title="Deep Tech Financial Simulator", layout="wide")
st.title("🚀 Deep Tech Startup Financial Simulator")

with st.sidebar.expander("💵 Revenue Model Assumptions"):
    rev_type = st.radio("What are you selling?", ["Product", "Service (SaaS)", "Both"], help="This determines your revenue model – one-time, subscription, or a mix.")
    price_per_unit = st.number_input("Product Price per Unit ($)", 0, 100_000, 1000)
    saas_monthly_price = st.number_input("Monthly SaaS Revenue per Customer ($)", 0, 100_000, 100)

with st.sidebar.expander("🔬 R&D and Operating Costs"):
    scale_mode = st.radio("Cost Scaling Model", ["Lean", "Steady", "Aggressive"], help="Controls how team size and spending scale over time.")
    scale_factors = {"Lean": 1.05, "Steady": 1.2, "Aggressive": 1.4}
    scale_rate = scale_factors[scale_mode]
    eng_fte = st.number_input("FTEs (Engineering)", 0, 500, 5)
    eng_salary = st.number_input("Average Salary per Engineering FTE ($)", 10000, 300000, 90000)
    st.caption("These are engineering roles, contributing primarily to R&D costs.")
    monthly_rnd = st.number_input("Monthly R&D Prototype Costs ($)", 0, 1_000_000, 25000)
    fte = st.number_input("FTEs (Non-R&D)", 0, 500, 5)
    salary_per_fte = st.number_input("Average Salary per FTE ($)", 10000, 300000, 80000)
    st.caption("This is the average annual salary for non-engineering FTEs. It contributes to operating costs.")
    monthly_ops = st.number_input("Monthly Non-R&D Operating Costs ($)", 0, 1_000_000, 15000)
    capitalize_rnd = st.checkbox("Capitalize R&D Expenses?", value=True, help="Toggling this ON means R&D costs are treated as assets that provide future benefit, rather than expenses. This affects EBITDA and Net Income.")

with st.sidebar.expander("📋 Base Assumptions"):
    scenario = st.selectbox("Select Scenario", ["Base Case", "Optimistic", "Pessimistic"])
    start_date = st.date_input("Forecast Start Date", datetime.today())
    years = 5
    initial_capital = st.number_input("Initial Capital ($)", 0, 10_000_000, 500_000, step=50000)
    months_of_runway = st.number_input("Runway Alert Threshold (Months)", 1, 24, 6, help="You’ll receive a warning when projected cash is less than this many months of burn.")
    price_growth = st.slider("Annual Price Growth (%)", 0, 50, 5, help="A good rule of thumb is keeping up with inflation as a baseline")
    initial_customers = st.number_input("Initial Customers (Year 1)", 0, 10_000, 100)
    customer_growth = st.slider("Annual Customer Growth (%)", 0, 200, 50)
    customer_churn = st.slider("Annual Customer Churn (%)", 0, 100, 10)

with st.sidebar.expander("💸 Fundraising Rounds"):
    num_rounds = st.number_input("How many rounds?", 0, 10, 3)
    rounds = []
    for i in range(num_rounds):
        col1, col2 = st.columns([2, 1])
        with col1:
            label = st.text_input(f"Round {i+1} Type", value=f"Round {i+1}", key=f"round_label_{i}")
        with col2:
            amount = st.number_input(f"Amount for {label} ($)", 0, 10_000_000, 0, step=50000, key=f"round_amt_{i}")
        date = st.date_input(f"Date for {label}", value=datetime.today(), key=f"round_date_{i}")
        rounds.append((label, amount, date))

# Scenario modifier
scenario_mods = {"Base Case": 1.0, "Optimistic": 1.2, "Pessimistic": 0.8}
mod = scenario_mods[scenario]

# Initial capital with fundraising applied
for label, amount, date in rounds:
    if date <= start_date:
        initial_capital += amount

# --- Financial Model ---
months = pd.date_range(start=start_date, periods=60, freq='MS')
data = pd.DataFrame(index=months)
data.index.name = "Date"
data['Quarter'] = data.index.to_period("Q").astype(str)

customer_counts = [initial_customers]
for year in range(1, years):
    prev = customer_counts[-1]
    growth = prev * (customer_growth / 100) * mod
    churn = prev * (customer_churn / 100)
    customer_counts.append(prev + growth - churn)

expanded_customers = np.repeat(customer_counts, 12)[:60]
data['Customers'] = expanded_customers

diffs = np.diff(customer_counts)
diffs = np.insert(diffs, 0, initial_customers)
diffs = np.repeat(diffs, 12)[:60]
data['New Customers'] = diffs

# Revenue logic placeholders (replace with real pricing vars if needed)
price_per_unit = 1000
saas_monthly_price = 100
rev_type = "Both"
product_revenue = data['New Customers'] * price_per_unit if rev_type in ["Product", "Both"] else 0

saas_customers = np.zeros(60)
saas_customers[0] = data['New Customers'].iloc[0]
if customer_churn > 0:
    churn_rate = customer_churn / 100 / 12
    for i in range(1, 60):
        retained = saas_customers[i - 1] * (1 - churn_rate)
        new = data['New Customers'].iloc[i]
        saas_customers[i] = retained + new
else:
    saas_customers = data['Customers']

saas_revenue = saas_customers * saas_monthly_price if rev_type in ["Service (SaaS)", "Both"] else 0

data['New Revenue'] = product_revenue
data['Retained Customers'] = saas_customers.astype(int)
data['Recurring Revenue'] = saas_revenue
data['Revenue'] = data['New Revenue'] + data['Recurring Revenue']

months_arr = np.arange(60)
years_arr = months_arr // 12

eng_fte_scaled = eng_fte * (scale_rate ** years_arr)
ops_fte_scaled = fte * (scale_rate ** years_arr)

rnd_fte_cost = eng_fte_scaled * eng_salary / 12
rnd_ops_cost = ops_fte_scaled * salary_per_fte / 12

monthly_rnd_scaled = monthly_rnd * (scale_rate ** years_arr)


# R&D is engineering FTE + monthly R&D
rnd_total = (monthly_rnd_scaled + rnd_fte_cost) * mod
data['R&D'] = rnd_total

# Ops is non-engineering FTE only
ops_total = (rnd_ops_cost + monthly_ops) * mod
data['Operating Costs'] = ops_total

# Combined total burn
burn_total = rnd_total + ops_total

# Sanity check for implied breakdown
implied_rd_pct = rnd_total.mean() / burn_total.mean() * 100
implied_ops_pct = ops_total.mean() / burn_total.mean() * 100
st.caption(f"R&D = {implied_rd_pct:.1f}% of burn")
st.caption(f"Non-R&D Ops = {implied_ops_pct:.1f}% of burn")
if implied_rd_pct > 40:
    st.warning(f"⚠️ R&D costs are {implied_rd_pct:.0f}% of burn. Deep tech norms are usually 25–35%, with upper bound ~40%.")
if implied_ops_pct > 25:
    st.warning(f"⚠️ Non-R&D Ops costs are {implied_ops_pct:.0f}% of burn. Consider optimizing administrative costs.")
data['Capitalized R&D'] = data['R&D'] if capitalize_rnd else 0
data['CapEx'] = np.where(np.arange(60) == 0, 100_000, 0)
data['Depreciation'] = 100_000 / 5 / 12

data['EBITDA'] = data['Revenue'] - (data['R&D'] - data['Capitalized R&D']) - data['Operating Costs']
data['Net Income'] = data['EBITDA'] - data['Depreciation']
data['Cash Flow'] = data['Net Income'] - data['CapEx']
data['Cash Balance'] = initial_capital + data['Cash Flow'].cumsum()

monthly_burn = data['Operating Costs'] + data['R&D']
data['Runway Months'] = (data['Cash Balance'] / monthly_burn.replace(0, np.nan)).fillna(0).astype(int)
data['Runway Warning'] = data['Runway Months'] < months_of_runway

st.subheader("📊 Key Financial Projections")
plot_df = data.reset_index()
melted = plot_df.melt(id_vars=['Date'], value_vars=['Revenue', 'Net Income', 'Cash Balance', 'Retained Customers'], var_name='Metric', value_name='Value')
line_chart = alt.Chart(melted).mark_line(interpolate='monotone', tooltip=True).encode(
    x=alt.X('Date:T', title='Date'),
    y=alt.Y('Value:Q', title='USD'),
    color='Metric:N'
).properties(width=800, height=400)
st.altair_chart(line_chart, use_container_width=True)

st.subheader("🚦 Runway Status")
if data['Runway Warning'].any():
    breach_month = data[data['Runway Warning']].index[0].strftime('%b %Y')
    st.warning(f"🟡 Your projected cash dips below {months_of_runway} months of runway in {breach_month}.")
else:
    st.success("🟢 Cash runway remains above threshold for the entire forecast period.")

st.subheader("🧮 Financial Table")
styled_data = data.copy()
styled_data['Customers'] = styled_data['Customers'].astype(int)
styled_data_formatted = styled_data.style.format({
    "Retained Customers": "{:,}",
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

