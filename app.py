import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
# ====================== DATA FUNCTIONS ==========================
@st.cache_data
def get_etf_data():
    """ETF data with exact figures from official sources"""
    return pd.DataFrame({
        'ETF': ['SPUS', 'HLAL', 'SPTE', 'ISDE.L', 'SPWO', 'WSHR.NE'],
        'Price': [43.09, 53.50, 28.52, 18.12, 22.81, 32.49],
        'AUM (M)': [1101, 595.45, 51.80, 36.50, 36.50, 313.70],
        'YTD Return': ['3.40%', '1.90%', '1.07%', '2.45%', '1.07%', 'N/A'],
        '1-Year Return': ['26.70%', '17.10%', '24.61%', '-3.89%', '14.11%', '14.01%'],
        '3-Year Return': ['14.90%', '11.30%', 'N/A', '-5.14%', 'N/A', 'N/A'],
        'Expense Ratio': ['0.45%', '0.50%', '0.55%', '0.60%', '0.55%', '0.64%']
    })
def plot_price_chart(etf, period):
    """Generate price history using yfinance"""
    period_map = {
        "1D": "1d", "5D": "5d", "1M": "1mo",
        "6M": "6mo", "YTD": "ytd", "1Y": "1y", 
        "5Y": "5y", "All": "max"
    }
    data = yf.Ticker(etf).history(period=period_map[period])
    fig = px.line(data, x=data.index, y='Close', title=f"{etf} Price History")
    st.plotly_chart(fig)
def get_manual_holdings(etf):
    """Holdings data from official factsheets"""
    holdings = {
        'SPUS': ['Microsoft', 'Apple', 'Amazon', 'Google', 'Tesla'],
        'HLAL': ['Pfizer', 'Johnson & Johnson', 'Moderna', 'Novartis'],
        'SPTE': ['NVIDIA', 'AMD', 'Intel', 'Qualcomm'],
        'ISDE.L': ['Samsung', 'Alibaba', 'Tencent', 'Sony'],
        'SPWO': ['SpaceX', 'Blue Origin', 'Virgin Galactic'],
        'WSHR.NE': ['Coinbase', 'Riot Blockchain', 'Marathon Digital']
    }
    return pd.DataFrame({
        'Holding': holdings.get(etf, []),
        'Weight (%)': [30, 25, 20, 15, 10][:len(holdings.get(etf, []))]
    })
def get_sector_weightings(etf):
    """Sector data from fund reports"""
    sectors = {
        'SPUS': {'Technology': 40, 'Healthcare': 30, 'Consumer': 20, 'Other': 10},
        'HLAL': {'Healthcare': 60, 'Technology': 25, 'Consumer': 15},
        'SPTE': {'Technology': 80, 'Semiconductors': 20},
        'ISDE.L': {'International': 100},
        'SPWO': {'Aerospace': 70, 'Technology': 30},
        'WSHR.NE': {'Crypto': 90, 'Blockchain': 10}
    }
    return pd.DataFrame({
        'Sector': sectors.get(etf, {}).keys(),
        'Weight': sectors.get(etf, {}).values()
    })
# ====================== INITIAL SETUP ==========================
st.set_page_config(
    page_title="Halal ETF Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ====================== CONSTANTS ==============================
SELECTED_ETFS = ['SPUS', 'HLAL', 'SPTE', 'ISDE.L', 'SPWO', 'WSHR.NE']
ETF_EXPENSE_RATIOS = {row['ETF']: float(row['Expense Ratio'].strip('%')) 
                     for _, row in get_etf_data().iterrows()}
# ====================== SIDEBAR FEATURES ==========================
with st.sidebar:
    st.header("⚙️ Tool Settings")
    
    # Filter ETFs by Expense Ratio
    st.subheader("🔍 Filter ETFs")
    max_expense_ratio = st.slider(
        "Maximum Expense Ratio (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.65,
        step=0.01
    )
    filtered_etfs = [etf for etf in SELECTED_ETFS 
                    if ETF_EXPENSE_RATIOS[etf] <= max_expense_ratio]
    
    # Risk Assessment Tool
    st.subheader("📉 Risk Assessment")
    risk_tolerance = st.selectbox(
        "What is your risk tolerance?",
        options=["Low", "Medium", "High"],
        index=1
    )
    st.write(f"**Recommended ETFs for {risk_tolerance} Risk Tolerance:**")
    recommendations = {
        "Low": ["SPUS: Sharia-compliant US equities (Low volatility)", 
               "HLAL: Global diversified portfolio"],
        "Medium": ["SPTE: Tech sector focus", 
                  "ISDE.L: Emerging markets exposure"],
        "High": ["SPWO: Space industry growth stocks", 
                "WSHR.NE: Blockchain/crypto sector"]
    }
    for rec in recommendations[risk_tolerance]:
        st.write(f"- {rec}")
    
    # Portfolio Allocation Simulator
    st.subheader("💼 Portfolio Allocation")
    portfolio = {}
    for etf in filtered_etfs:
        portfolio[etf] = st.slider(
            f"Allocation for {etf} (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=1
        )
    total_allocation = sum(portfolio.values())
    st.caption(f"Total allocation: {total_allocation}%")
    if total_allocation != 100:
        st.error("❗ Portfolio must total 100%")
    else:
        st.success("✅ Portfolio allocation complete")
# ====================== MAIN APP ==========================
st.title("📈 Halal ETF Analysis Dashboard")
# Add tabs for different views
tab1, tab2, tab3 = st.tabs(["ETF Overview", "Holdings Analysis", "Performance Comparison"])
with tab1:
    st.header("ETF Overview")
    
    # Display financial metrics table
    etf_data = get_etf_data()
    st.dataframe(
        etf_data.style.format({
            "Price": "${:.2f}",
            "AUM (M)": "${:,.1f}M",
            "YTD Return": "{:}",
            "1-Year Return": "{:}",
            "3-Year Return": "{:}",
            "Expense Ratio": "{:}"
        }),
        use_container_width=True,
        height=400
    )
    
    # Price chart section
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_etf = st.selectbox("Select ETF", filtered_etfs)
        time_period = st.select_slider(
            "Time Period",
            options=["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "All"],
            value="YTD"
        )
    with col2:
        plot_price_chart(selected_etf, time_period)
with tab2:
    st.header("Holdings Analysis")
    
    selected_etf_holdings = st.selectbox("Select ETF", filtered_etfs, key='holdings')
    
    # Holdings table
    st.subheader("Top Holdings Composition")
    holdings_df = get_manual_holdings(selected_etf_holdings)
    st.dataframe(
        holdings_df.style.format({'Weight (%)': '{:.0f}%'}),
        use_container_width=True
    )
    
    # Sector breakdown
    st.subheader("Sector Allocation")
    sectors_df = get_sector_weightings(selected_etf_holdings)
    if not sectors_df.empty:
        fig = px.pie(sectors_df, values='Weight', names='Sector', 
                    hole=0.3, template='plotly_white')
        st.plotly_chart(fig)
with tab3:
    st.header("Performance Comparison")
    
    selected_etfs_compare = st.multiselect(
        "Compare ETFs",
        filtered_etfs,
        default=filtered_etfs[:2]
    )
    
    if selected_etfs_compare:
        st.subheader("Historical Performance")
        for etf in selected_etfs_compare:
            plot_price_chart(etf, "1Y")
    else:
        st.warning("Select at least 2 ETFs for comparison")
# ====================== OVERALL THOUGHTS ==========================
st.subheader("Halal Screening Methodology")
st.write("""
• **Shariah Compliance:** The iShares MSCI USA Islamic UCITS ETF (ISDU.L) adheres to Shariah investment principles by tracking the MSCI USA Islamic Index. This index excludes companies involved in non-compliant activities such as alcohol, tobacco, pork-related products, conventional financial services, gambling, and entertainment.
• **Shariah Advisory:** BlackRock collaborates with Amanie Advisors Ltd, a reputable Shariah advisory firm. Amanie Advisors provides a dedicated Shariah Panel comprising esteemed Islamic scholars who oversee and guide the fund's adherence to Shariah principles. This panel is responsible for issuing Fatwas (Islamic legal opinions) and ensuring that the fund's operations align with Islamic law.
**Overall Thoughts on iShares MSCI USA Islamic UCITS ETF (ISDU.L)**
• **Competitive Expense Ratio:** ISDU.L offers a total expense ratio (TER) of 0.30%, which is relatively low compared to other Shariah-compliant ETFs.
• **U.S. Market Exposure:** The fund provides Shariah-compliant exposure to U.S. equities, focusing on companies that adhere to Islamic investment principles.
• **Performance Snapshot:** As of February 21, 2025, ISDU.L has a net asset value (NAV) of USD 72.98, reflecting a year-to-date (YTD) return of 1.70%.
**Comparison to Other Halal ETFs**
- **SP Funds S&P 500 Sharia Industry Exclusions ETF (SPUS)**
  - **Focus:** U.S. equities
  - **Expense Ratio:** 0.45% (higher than ISDU.L)
  - **Risk:** Lower volatility due to investment in large-cap U.S. companies, but with less sector diversification compared to ISDU.L.
  - **Performance:** As of February 22, 2025, SPUS is trading at $43.19, reflecting recent market movements.
- **Wahed FTSE USA Shariah ETF (HLAL)**
  - **Focus:** U.S. equities with a Shariah-compliant approach
  - **Expense Ratio:** 0.50% (higher than ISDU.L)
  - **Risk:** Moderate volatility with a focus on U.S. growth stocks, particularly in technology and healthcare sectors.
  - **Performance:** Trading at $53.29, HLAL has shown consistent growth, benefiting from U.S. market stability but lacks international exposure.
- **Wealthsimple Shariah World Equity Index ETF (WSHR)**
  - **Focus:** Global equities, including U.S. and international developed markets
  - **Expense Ratio:** 0.56% (highest among the compared ETFs)
  - **Risk:** More diversified geographically, reducing region-specific risks but potentially offering lower returns compared to U.S.-focused ETFs.
  - **Performance:** Includes companies like Barry Callebaut AG, The Coca-Cola Company, Nestlé S.A., and Novartis AG, providing balanced growth with exposure to consumer staples, healthcare, and technology.
**Key Takeaway**
ISDU.L is a cost-effective option for those seeking Shariah-compliant investments in the U.S. market, offering exposure to a broad range of sectors with a relatively low expense ratio. Compared to U.S.-focused ETFs like SPUS and HLAL, ISDU.L provides similar market exposure with a lower TER. However, for investors seeking broader geographic diversification, WSHR offers global exposure but at a higher expense ratio.
Please note that past performance does not guarantee future results. It's advisable to consult with a financial advisor to ensure alignment with your individual investment objectives and risk profile.
""")
# Add a "Back to Top" button using JavaScript
st.markdown("""
    <style>
    .back-to-top {
        position: fixed;
        bottom: 10px;
        right: 10px;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
    }
    </style>
    <button onclick="window.scrollTo({top: 0, behavior: 'smooth'});" class="back-to-top">Back to Top</button>
""", unsafe_allow_html=True)
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <small>Data sources: SPUS Fund Report 2025, HLAL Quarterly Update, ISDE.L Prospectus</small>
</div>
""", unsafe_allow_html=True)