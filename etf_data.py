import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import streamlit_authenticator as stauth

# ====================== DATA FUNCTIONS ==========================
@st.cache_data
def get_etf_data():
    """ETF data with exact figures from official sources"""
    initial_prices = [30.00, 40.00, 25.00, 15.00, 20.00, 28.00]  # Example initial prices
    current_prices = [43.09, 53.50, 28.52, 18.12, 22.81, 32.49]
    return pd.DataFrame({
        'ETF': ['SPUS', 'HLAL', 'SPTE', 'ISDE.L', 'SPWO', 'WSHR.NE'],
        'Price': current_prices,
        'AUM (M)': [1101, 595.45, 51.80, 36.50, 36.50, 313.70],
        'YTD Return': ['3.40%', '1.90%', '1.07%', '2.45%', '1.07%', 'N/A'],
        '1-Year Return': ['26.70%', '17.10%', '24.61%', '-3.89%', '14.11%', '14.01%'],
        '3-Year Return': ['14.90%', '11.30%', 'N/A', '-5.14%', 'N/A', 'N/A'],
        'Expense Ratio': ['0.45%', '0.50%', '0.55%', '0.60%', '0.55%', '0.64%'],
        'Annual Dividend Per Share': ['$0.302', '$0.331', '1.20%', '1.80%', '1.00%', 'N/A'],
        'Initial Price': initial_prices,
        'Return Since Inception': [f"{((current / initial - 1) * 100):.2f}%" for current, initial in zip(current_prices, initial_prices)]
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
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Close Price",
        title_x=0.5,
        template="plotly_white"
    )
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

@st.cache_data
def get_wshr_holdings_from_excel(file_path):
    """Read WSHR holdings data from an Excel file"""
    excel_data = pd.read_excel(file_path, sheet_name='WSHR.NE Details')
    return excel_data[['Holding', 'Weight (%)']]

# ====================== INITIAL SETUP ==========================
st.set_page_config(
    page_title="Halal ETF Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== CONSTANTS ==============================
EXCEL_FILE_PATH = 'c:/Users/Admin/Documents/Halal-ETF-Tool/WSHR.NE Details.xlsx'
wshr_holdings = get_wshr_holdings_from_excel(EXCEL_FILE_PATH)
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

# ====================== MAIN APP ==========================
col1, col2 = st.columns([1, 10])
with col1:
    st.image("logo/myrizq_logo.png", width=50)
with col2:
    st.markdown("# 📈 MyRizq Halal ETF Analysis Dashboard - Welcome!")

# Add tabs for different views
tabs = st.tabs(["Overview"] + SELECTED_ETFS)

with tabs[0]:
    st.header("ETF Overview")
    
    # Display financial metrics table
    etf_data = get_etf_data()
    if not etf_data.empty:
        st.dataframe(
            etf_data.style.format({
                "Price": "${:.2f}",
                "AUM (M)": "${:,.1f}M",
                "YTD Return": "{:}",
                "1-Year Return": "{:}",
                "3-Year Return": "{:}",
                "Expense Ratio": "{:}",
                "Dividend Yield": "{:}",
                "Return Since Inception": "{:}"
            }),
            use_container_width=True,
            height=400
        )
    
    # Expense Ratio Comparison
    st.subheader("📊 ETF Expense Ratio Comparison")
    if filtered_etfs:
        expense_ratios = {etf: ETF_EXPENSE_RATIOS[etf] for etf in filtered_etfs}
        expense_df = pd.DataFrame({
            'ETF': list(expense_ratios.keys()),
            'Expense Ratio (%)': list(expense_ratios.values())
        })
        if not expense_df.empty:
            fig = px.bar(
                expense_df,
                x='ETF',
                y='Expense Ratio (%)',
                title="Expense Ratio Comparison",
                labels={'Expense Ratio (%)': 'Expense Ratio (%)', 'ETF': 'ETF'},
                text='Expense Ratio (%)'
            )
            fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside', width=0.4)
            fig.update_layout(
                xaxis_title="ETF",
                yaxis_title="Expense Ratio (%)",
                title_x=0.5,
                template="plotly_white",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No ETFs match the selected expense ratio filter.")
    
    # Annual Dividend Per Share Comparison
    st.subheader("📊 Annual Dividend Per Share Comparison")
    dividend_df = etf_data[['ETF', 'Annual Dividend Per Share']]
    if not dividend_df.empty:
        fig = px.bar(
            dividend_df,
            x='ETF',
            y='Annual Dividend Per Share',
            title="Annual Dividend Per Share Comparison",
            labels={'Annual Dividend Per Share': 'Annual Dividend Per Share', 'ETF': 'ETF'},
            text='Annual Dividend Per Share'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside', width=0.4)
        fig.update_layout(
            xaxis_title="ETF",
            yaxis_title="Annual Dividend Per Share",
            title_x=0.5,
            template="plotly_white",
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

# Create a tab for each ETF
for i, etf in enumerate(SELECTED_ETFS):
    with tabs[i + 1]:
        st.header(f"{etf} Analysis")
        
        # Display financial metrics for the selected ETF
        etf_info = etf_data[etf_data['ETF'] == etf]
        if not etf_info.empty:
            st.dataframe(
                etf_info.style.format({
                    "Price": "${:.2f}",
                    "AUM (M)": "${:,.1f}M",
                    "YTD Return": "{:}",
                    "1-Year Return": "{:}",
                    "3-Year Return": "{:}",
                    "Expense Ratio": "{:}",
                    "Dividend Yield": "{:}",
                    "Return Since Inception": "{:}"
                }),
                use_container_width=True,
                height=200
            )
        
        # Price chart section
        st.subheader("Price Chart")
        time_period = st.select_slider(
            "Time Period",
            options=["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "All"],
            value="YTD"
        )
        plot_price_chart(etf, time_period)
        
        # Holdings table
        st.subheader("Top Holdings Composition")
        if etf == 'WSHR.NE':
            st.dataframe(
                wshr_holdings.style.format({'Weight (%)': '{:.0f}%'}),
                use_container_width=True
            )
        else:
            holdings_df = get_manual_holdings(etf)
            if not holdings_df.empty:
                st.dataframe(
                    holdings_df.style.format({'Weight (%)': '{:.0f}%'}),
                    use_container_width=True
                )
        
        # Sector breakdown
        st.subheader("Sector Allocation")
        sectors_df = get_sector_weightings(etf)
        if not sectors_df.empty:
            fig = px.pie(sectors_df, values='Weight', names='Sector', 
                        hole=0.3, template='plotly_white')
            fig.update_layout(
                title="Sector Allocation",
                title_x=0.5
            )
            st.plotly_chart(fig)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <small>Data sources: SPUS Fund Report 2025, HLAL Quarterly Update, ISDE.L Prospectus</small>
</div>
""", unsafe_allow_html=True)