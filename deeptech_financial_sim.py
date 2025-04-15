import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

st.set_page_config(page_title="Deep Tech Financial Simulator", layout="wide")
st.title("🚀 Deep Tech Startup Financial Simulator")


with st.sidebar.expander("🔬 R&D and Operating Costs"):
    scale_mode = st.radio("Cost Scaling Model", ["Lean", "Steady", "Aggressive"], help="Controls how team size and spending scale over time.")
    scale_factors = {"Lean": 1.05, "Steady": 1.2, "Aggressive": 1.4}
    scale_rate = scale_factors[scale_mode]
    eng_fte = st.number_input("FTEs (Engineering)", 0, 500, 5)
    eng_salary = st.number_input("Average Salary per Engineering FTE ($)", 10000, 300000, 90000)
    st.caption("These are engineering roles, contributing primarily to R&D costs.")
    rd_share = st.slider("Target R&D % of Burn", 5, 60, 35, help="R&D typically accounts for 35–50% of spend in deep tech. This controls max scaling.")
        capitalize_rnd = st.checkbox("Capitalize R&D Expenses?", value=True, help="Toggling this ON means R&D costs are treated as assets that provide future benefit, rather than expenses. This affects EBITDA and Net Income.")
