import streamlit as st
import pandas as pd
import plotly.express as px
from etf_data import get_etf_data, format_currency, format_percentage, format_volume
import time

# 📌 Page Configuration (Full-Screen)
st.set_page_config(page_title="Halal ETF Comparison Tool", page_icon="📊", layout="wide")

# 📌 Custom CSS for Better Design
st.markdown("""
    <style>
        .stApp { padding: 2rem; }
        .stDataFrame { font-size: 16px; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# 📌 App Title
st.title("🕌 Halal ETF Comparison Tool")
st.markdown("Compare Shariah-compliant ETFs in real-time with live data and interactive charts.")

# 📌 Sidebar Controls
st.sidebar.header("Filters & Settings")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (minutes)", 1, 10, 5) if auto_refresh else None

# 📌 Load ETF Data
try:
    df = get_etf_data()

    if df.empty:
        st.error("No ETF data is available. Please try again later.")
    else:
        # 📌 Sidebar Filters
        st.sidebar.subheader("Filter ETFs")
        min_price = st.sidebar.slider("Minimum Price ($)", float(df["Price"].min()), float(df["Price"].max()), float(df["Price"].min()))
        max_price = st.sidebar.slider("Maximum Price ($)", float(df["Price"].min()), float(df["Price"].max()), float(df["Price"].max()))
        min_change = st.sidebar.slider("Minimum Change (%)", float(df["Change (%)"].min()), float(df["Change (%)"].max()), float(df["Change (%)"].min()))

        # Apply filters
        filtered_df = df[(df["Price"] >= min_price) & (df["Price"] <= max_price) & (df["Change (%)"] >= min_change)]

        # 📌 Display Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total ETFs", len(filtered_df))
        with col2:
            avg_price = filtered_df["Price"].mean()
            st.metric("Avg. Price", format_currency(avg_price))
        with col3:
            avg_change = filtered_df["Change (%)"].mean()
            st.metric("Avg. Daily Change", format_percentage(avg_change))
        with col4:
            total_volume = filtered_df["Volume"].sum()
            st.metric("Total Volume", format_volume(total_volume))

        # 📌 Enhanced Data Table
        st.subheader("📊 ETF Data Table (Filtered)")
        display_df = filtered_df.copy()
        columns_order = ["Company", "Ticker", "Name", "Price", "Change (%)", "52-Week High", "52-Week Low", "Market Cap"]
        display_df = display_df[columns_order]

        # Format Columns
        numeric_formatters = {
            "Price": format_currency,
            "Change (%)": format_percentage,
            "52-Week High": format_currency,
            "52-Week Low": format_currency,
            "Market Cap": format_currency,
        }
        for col, formatter in numeric_formatters.items():
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(formatter)

        st.dataframe(display_df, use_container_width=True)

        # 📌 Interactive Charts
        st.subheader("📈 ETF Performance Charts")

        # Price Trend Chart
        fig1 = px.line(filtered_df, x="Ticker", y="Price", title="📊 ETF Price Trends")
        st.plotly_chart(fig1, use_container_width=True)

        # Daily Change Chart
        fig2 = px.bar(filtered_df, x="Ticker", y="Change (%)", title="📉 Daily Price Change", color="Change (%)")
        st.plotly_chart(fig2, use_container_width=True)

        # 📌 Last Updated Timestamp
        st.markdown(f"*Last updated: {df['Last Updated'].iloc[0]}*")

        # 📌 Auto-Refresh Logic
        if auto_refresh:
            time.sleep(refresh_interval * 60)
            st.experimental_rerun()

except Exception as e:
    st.error(f"An error occurred while fetching ETF data: {e}")
    st.warning("Please try refreshing the page or check back later.")
