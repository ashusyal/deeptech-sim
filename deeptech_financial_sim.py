
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

st.set_page_config(page_title="Deep Tech Financial Simulator", layout="wide")
st.title("🚀 Deep Tech Startup Financial Simulator")

# --- Sidebar: Intake Form ---
st.sidebar.header("Input Your Assumptions")

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

# Display fundraising summary table
if rounds:
    st.subheader("📈 Fundraising Summary")
    round_df = pd.DataFrame(rounds, columns=["Round", "Amount ($)", "Date"])
    st.dataframe(round_df)

# --- Continue Sidebar: R&D and Operating Costs ---
with st.sidebar.expander("🔬 R&D and Operating Costs"):
    monthly_rnd = st.number_input("Monthly R&D Spend ($)", 0, 1_000_000, 25000, step=5000)
    rnd_years = st.slider("R&D Phase Duration (Years)", 1, 5, 2, help="This represents the development time for your current product or tech stack. Expenses entered above will apply for this duration.")
    capitalize_rnd = st.checkbox("Capitalize R&D Expenses?", value=True, help="Toggling this ON means R&D costs are treated as assets that provide future benefit, rather than expenses. This affects EBITDA and Net Income.")

    fte = st.number_input("FTEs (Non-R&D)", 0, 500, 5)
    salary_per_fte = st.number_input("Average Salary per FTE ($)", 10000, 300000, 80000)
    st.caption("This is the average annual salary for non-engineering FTEs. It contributes to operating costs.")
    monthly_ops = st.number_input("Monthly Non-R&D Operating Costs ($)", 0, 1_000_000, 15000)
