import streamlit as st
import pandas as pd
import plotly.express as px
from etf_data import get_etf_data, format_currency, format_percentage, format_volume
import time

# 📌 Page Configuration with Custom Logo
st.set_page_config(page_title="Myrizq Halal ETF Tool", page_icon="🌱", layout="wide")

# 📌 Display Logo & Title
col1, col2 = st.columns([0.2, 0.8])
with col1:
    st.image("logo.png", width=100)  # Make sure 'logo.png' is in the same directory as 'app.py'
with col2:
    st.title("🌱 Myrizq Halal ETF Tool")
st.markdown("Compare all Halal-compliant ETFs in real-time with interactive analysis.")

# Sidebar Controls
st.sidebar.header("Filters & Premium Features")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (minutes)", 1, 10, 5) if auto_refresh else None

# Load ETF Data
try:
    df = get_etf_data()
    if df.empty:
        st.error("No ETF data is available. Please try again later.")
    else:
        # Display Data Table
        st.subheader("📊 ETF Data Table")
        st.dataframe(df, use_container_width=True)

        # Interactive Charts
        st.subheader("📈 ETF Performance Charts")
        fig1 = px.bar(df, x="Ticker", y="YTD Return (%)", title="📊 Year-to-Date (YTD) Returns")
        st.plotly_chart(fig1, use_container_width=True)

        # Last Updated Timestamp
        st.markdown(f"*Last updated: {df['Last Updated'].iloc[0]}*")

        # Auto-Refresh
        if auto_refresh:
            time.sleep(refresh_interval * 60)
            st.experimental_rerun()
except Exception as e:
    st.error(f"Error fetching ETF data: {e}")
