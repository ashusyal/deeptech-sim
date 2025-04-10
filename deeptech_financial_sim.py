import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Deep Tech Financial Simulator", layout="wide")
st.title("🚀 Deep Tech Startup Financial Simulator")

# --- Sidebar: Intake Form ---
st.sidebar.header("Input Your Assumptions")

scenario = st.sidebar.selectbox("Select Scenario", ["Base Case", "Optimistic", "Pessimistic"])

start_date = st.sidebar.date_input("Forecast Start Date", datetime.today())
years = st.sidebar.slider("Forecast Period (Years)", 3, 7, 5)
initial_capital = st.sidebar.number_input("Initial Capital ($)", 0, 10_000_000, 500_000, step=50000)
min_cash = st.sidebar.number_input("Minimum Cash Buffer ($)", 0, 1_000_000, 100_000, step=10000)

st.sidebar.markdown("---")

price = st.sidebar.number_input("Initial Product Price ($)", 1, 100_000, 1000)
price_growth = st.sidebar.slider("Annual Price Growth (%)", 0, 50, 5)
initial_customers = st.sidebar.number_input("Initial Customers (Year 1)", 0, 10_000, 100)
customer_growth = st.sidebar.slider("Annual Customer Growth (%)", 0, 200, 50)

st.sidebar.markdown("---")

monthly_rnd = st.sidebar.number_input("Monthly R&D Spend ($)", 0, 1_000_000, 25000, step=5000)
rnd_years = st.sidebar.slider("R&D Phase Duration (Years)", 1, 5, 2)
capitalize_rnd = st.sidebar.checkbox("Capitalize R&D Expenses?", value=True)

fte = st.sidebar.number_input("FTEs (Non-R&D)", 0, 500, 5)
salary_per_fte = st.sidebar.number_input("Average Salary per FTE ($)", 10000, 300000, 80000)
monthly_ops = st.sidebar.number_input("Monthly Non-R&D Operating Costs ($)", 0, 1_000_000, 15000)

capex = st.sidebar.number_input("Total Equipment Spend ($)", 0, 5_000_000, 100_000)
depr_years = st.sidebar.slider("Equipment Depreciation (Years)", 1, 10, 5)

# --- Scenario Modifiers ---
scenario_mods = {
    "Base Case": 1.0,
    "Optimistic": 1.2,
    "Pessimistic": 0.8
}
mod = scenario_mods[scenario]

# --- Model Calculations ---
dates = pd.date_range(start=start_date, periods=years, freq='Y')
data = pd.DataFrame(index=dates)

data['Customers'] = initial_customers * ((1 + (customer_growth / 100 * mod)) ** np.arange(years))
data['Price'] = price * ((1 + (price_growth / 100 * mod)) ** np.arange(years))
data['Revenue'] = data['Customers'] * data['Price']

data['R&D'] = np.where(np.arange(years) < rnd_years, monthly_rnd * 12 * mod, 0)
data['Capitalized R&D'] = data['R&D'] if capitalize_rnd else 0

data['Operating Costs'] = (fte * salary_per_fte + monthly_ops * 12 * mod)
data['CapEx'] = np.where(np.arange(years) == 0, capex, 0)
data['Depreciation'] = capex / depr_years

data['EBITDA'] = data['Revenue'] - data['R&D'] - data['Operating Costs']
data['Net Income'] = data['EBITDA'] - data['Depreciation']

data['Cumulative CapEx'] = data['CapEx'].cumsum()
data['Cash Flow'] = data['Net Income'] - data['CapEx']
data['Cash Balance'] = initial_capital + data['Cash Flow'].cumsum()
data['Runway Breach'] = data['Cash Balance'] < min_cash

# --- Dashboard Display ---
st.subheader("📊 Key Financial Projections")
st.line_chart(data[['Revenue', 'Net Income', 'Cash Balance']])

st.subheader("🧮 Financial Table")
st.dataframe(data.style.format("${:,.0f}"))

st.subheader("⚠️ Runway Alert")
if data['Runway Breach'].any():
    breach_year = data[data['Runway Breach']].index[0].year
    st.error(f"⚠️ Your cash balance drops below the minimum buffer in {breach_year}. Consider raising funds.")
else:
    st.success("✅ Cash buffer is maintained throughout the forecast period.")

# --- Export Section ---
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
