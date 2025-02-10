import streamlit as st
import pandas as pd
import plotly.express as px
from etf_data import get_etf_data, format_currency, format_percentage, format_volume

# Page Configuration
st.set_page_config(
    page_title="Myrizq Halal ETF Tool",
    page_icon="🌿",
    layout="wide"
)

# Load Custom Logo
st.image("logo.png", width=120)

# Title and Description
st.title("🌿 Myrizq Halal ETF Comparison Tool")
st.markdown("""
**Compare all Shariah-compliant ETFs in real-time with interactive analysis.**  
This tool helps investors find the best Halal investment opportunities based on price, returns, and market performance.
""")

# Load ETF Data
try:
    df = get_etf_data()

    if df.empty:
        st.error("No ETF data available. Try again later.")
    else:
        # Filters Section
        with st.sidebar:
            st.header("🔍 Filters")
            min_price = st.number_input("Minimum Price ($)", 0.0, 1000.0, 0.0)
            max_expense = st.number_input("Max Expense Ratio (%)", 0.0, 2.0, 1.0)

        # Apply Filters
        filtered_df = df[
            (df['Price'] >= min_price) &
            (df['Expense Ratio (%)'] <= max_expense)
        ]

        # Display Data Table
        st.subheader("📊 **ETF Data Table**")
        st.dataframe(filtered_df, use_container_width=True)

        # Performance Charts
        st.subheader("📈 **ETF Performance Charts**")
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(filtered_df, x='Ticker', y='YTD Return (%)', color='Company', title='YTD Return by ETF')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(filtered_df, x='Ticker', y='All-Time Return (%)', color='Company', title='All-Time Return Since Inception')
            st.plotly_chart(fig2, use_container_width=True)

        # Last Updated Time
        st.markdown(f"📅 **Last Updated:** {df['Last Updated'].iloc[0]}")

except Exception as e:
    st.error(f"Error loading ETF data: {str(e)}")
    st.warning("Please refresh the page and try again.")
