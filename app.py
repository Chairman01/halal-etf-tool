import streamlit as st
import pandas as pd
from etf_data import get_etf_data, format_currency, format_percentage, format_volume
import plotly.express as px

# Page configuration
st.set_page_config(page_title="Halal ETF Comparison Tool", page_icon="📊", layout="wide")

# Header
st.title("🕌 Halal ETF Comparison Tool")
st.markdown("Compare Shariah-compliant ETFs in real time.")

# Load ETF data
df = get_etf_data()

if df.empty:
    st.error("No ETF data available. Try again later.")
else:
    st.dataframe(df)

