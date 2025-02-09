import streamlit as st
import pandas as pd
from etf_data import get_etf_data, format_currency, format_percentage, format_volume  # Ensure etf_data.py is in the same folder
import plotly.express as px

# Page configuration
st.set_page_config(page_title="Halal ETF Comparison Tool", page_icon="📊", layout="wide")

# Header
st.title("🕌 Halal ETF Comparison Tool")
st.markdown("Compare Shariah-compliant ETFs in real time.")

# Load ETF data
try:
    df = get_etf_data()

    if df.empty:
        st.error("No ETF data available. Try again later.")
    else:
        # Display dataframe
        st.dataframe(df)

        # Chart: ETF Performance Comparison
        st.subheader("ETF Performance Comparison")
        fig = px.bar(df, x='Ticker', y='YTD Return (%)', title="Year-to-Date (YTD) Return by ETF")
        st.plotly_chart(fig)

except Exception as e:
    st.error(f"Error loading ETF data: {e}")
