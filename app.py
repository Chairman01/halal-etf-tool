import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
from database import (
    create_user, 
    verify_user, 
    init_db, 
    test_connection, 
    get_db_connection, 
    update_subscription_status
)
import os
from streamlit.components.v1 import html
import streamlit.components.v1 as components
import stripe
import time
from dotenv import load_dotenv
from webhook_handler import handle_webhook_event
from flask import Flask, request
import threading

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PRICE_ID = os.getenv('STRIPE_PRICE_ID')

# Initialize Flask app
app = Flask(__name__)

# Add this function to run Streamlit and Flask together
def run_flask():
    app.run(port=5000)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# ====================== DATA FUNCTIONS ==========================
@st.cache_data
def get_etf_data():
    """ETF data with exact figures from official sources"""
    return pd.DataFrame({
        'ETF': ['SPUS', 'SPWO', 'UMMA', 'HLAL', 'ISDU', 'ISDE', 'WSHR'],
        'Full Name': [
            'SP Funds S&P 500 Sharia Industry Exclusions ETF',
            'SP Funds Dow Jones World ETF',
            'UMMA Islamic Values ETF',
            'Wahed FTSE USA Shariah ETF',
            'iShares MSCI USA Islamic UCITS ETF',
            'iShares MSCI World Islamic UCITS ETF',
            'Wealthsimple Shariah World Equity Index ETF'
        ],
        'Focus': [
            'US Large Cap',
            'Global Equity',
            'Global Islamic',
            'US All Cap',
            'US Islamic',
            'Global Islamic',
            'Global Islamic'
        ],
        'AUM (M)': [1101, 36.50, 245.86, 595.45, 325.50, 36.50, 313.70],
        'Expense Ratio': ['0.45%', '0.55%', '0.50%', '0.50%', '0.60%', '0.60%', '0.64%'],
        'Shariah Advisory': [
            'Ratings Intelligence',
            'Ratings Intelligence',
            'Yasaar Limited',
            'Yasaar Limited',
            'Amanie Advisors',
            'Amanie Advisors',
            'Ratings Intelligence'
        ],
        'YTD Return': ['3.40%', '1.07%', '2.80%', '1.90%', '2.45%', '2.10%', '2.30%'],
        '1-Year Return': ['26.70%', '14.11%', '20.50%', '17.10%', '22.45%', '18.89%', '14.01%'],
        '3-Year Return': ['14.90%', 'N/A', 'N/A', '11.30%', '14.14%', '10.50%', 'N/A']
    })
def plot_price_chart(etf, period, key=None):
    """Generate price history using yfinance"""
    period_map = {
        "1mo": "1mo",
        "3mo": "3mo",
        "6mo": "6mo",
        "1y": "1y",
        "max": "max"
    }
    try:
        data = yf.Ticker(etf).history(period=period_map[period])
        fig = px.line(data, x=data.index, y='Close', title=f"{etf} Price History")
        st.plotly_chart(fig, key=key)
    except KeyError:
        data = yf.Ticker(etf).history(period="1y")
        fig = px.line(data, x=data.index, y='Close', title=f"{etf} Price History")
        st.plotly_chart(fig, key=key)
def get_manual_holdings(etf):
    """Holdings data from official factsheets"""
    holdings = {
        'SPUS': ['Microsoft', 'Apple', 'Amazon', 'Google', 'Tesla'],
        'SPTE': ['NVIDIA', 'AMD', 'Intel', 'Qualcomm'],
        'SPWO': ['SpaceX', 'Blue Origin', 'Virgin Galactic'],
        'UMMA': ['Microsoft', 'Apple', 'NVIDIA', 'Tesla', 'Meta'],
        'HLAL': ['Pfizer', 'Johnson & Johnson', 'Moderna', 'Novartis'],
        'ISDU': ['Microsoft', 'Apple', 'NVIDIA', 'Tesla', 'Meta'],
        'ISDE': ['Samsung', 'Alibaba', 'Tencent', 'Sony'],
        'WSHR': ['Microsoft', 'Apple', 'NVIDIA', 'Tesla', 'Meta']
    }
    return pd.DataFrame({
        'Holding': holdings.get(etf, []),
        'Weight (%)': [30, 25, 20, 15, 10][:len(holdings.get(etf, []))]
    })
def get_sector_weightings(etf):
    """Sector data from fund reports"""
    sectors = {
        'SPUS': {'Technology': 40, 'Healthcare': 30, 'Consumer': 20, 'Other': 10},
        'SPTE': {'Technology': 80, 'Semiconductors': 20},
        'SPWO': {'Aerospace': 70, 'Technology': 30},
        'UMMA': {'Technology': 45, 'Healthcare': 25, 'Consumer': 20, 'Other': 10},
        'HLAL': {'Healthcare': 60, 'Technology': 25, 'Consumer': 15},
        'ISDU': {'Technology': 42, 'Healthcare': 28, 'Consumer': 20, 'Other': 10},
        'ISDE': {'Technology': 35, 'Consumer': 30, 'Healthcare': 25, 'Other': 10},
        'WSHR': {'Technology': 40, 'Healthcare': 30, 'Consumer': 20, 'Other': 10}
    }
    return pd.DataFrame({
        'Sector': sectors.get(etf, {}).keys(),
        'Weight': sectors.get(etf, {}).values()
    })
def add_back_to_top_button():
    # Create a fixed container for the button
    st.markdown(
        """
        <style>
            .stButton.fixed-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 999;
            }
            
            /* Hide default streamlit button margins */
            .stButton>button {
                margin: 0;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Create a container for the button
    with st.container():
        col1, col2 = st.columns([9, 1])
        with col2:
            if st.button("⬆️", key="back_to_top", help="Back to top"):
                js = """
                    <script>
                        window.scrollTo({top: 0, behavior: 'smooth'});
                    </script>
                """
                components.html(js, height=0)

@st.cache_data
def read_excel_data(file_path):
    """Read ISDU data from Excel file"""
    try:
        if not os.path.exists(file_path):
            st.error(f"Excel file not found at: {file_path}")
            return None
            
        excel_data = pd.ExcelFile(file_path)
        data = {}
        for sheet in excel_data.sheet_names:
            data[sheet] = pd.read_excel(file_path, sheet_name=sheet)
        return data
    except pd.errors.EmptyDataError:
        st.error("The Excel file is empty")
        return None
    except pd.errors.ParserError:
        st.error("Error parsing the Excel file. Please check the file format.")
        return None
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

@st.cache_data
def get_isdu_holdings():
    """Get ISDU holdings from Excel"""
    file_path = '7- ISDU Details.xlsx'
    data = read_excel_data(file_path)
    
    if data is None or 'ISDE Holdings' not in data:
        return pd.DataFrame()
    
    holdings_df = data['ISDE Holdings']
    # Ensure column names match exactly
    if 'Security Name' in holdings_df.columns and 'Weightings' in holdings_df.columns:
        return holdings_df.sort_values('Weightings', ascending=False)
    return pd.DataFrame()

@st.cache_data
def get_isdu_sectors():
    """Get ISDU sectors from Excel"""
    file_path = '7- ISDU Details.xlsx'
    data = read_excel_data(file_path)
    
    if data is None or 'ISDE Sector' not in data:
        return pd.DataFrame()
    
    sectors_df = data['ISDE Sector']
    # Ensure column names match exactly
    if 'Sector' in sectors_df.columns and 'Weightings' in sectors_df.columns:
        return sectors_df.sort_values('Weightings', ascending=False)
    return pd.DataFrame()

@st.cache_data
def get_isdu_countries():
    """Get ISDU countries from Excel"""
    file_path = '7- ISDU Details.xlsx'
    data = read_excel_data(file_path)
    
    if data is None or 'ISDE Country' not in data:
        return pd.DataFrame()
    
    countries_df = data['ISDE Country']
    # Note the space after "Country" in the column name
    if 'Country ' in countries_df.columns and 'Weightings' in countries_df.columns:
        return countries_df.sort_values('Weightings', ascending=False)
    return pd.DataFrame()

@st.cache_data
def get_isdu_returns():
    """Get ISDU returns data from Excel"""
    file_path = '7- ISDU Details.xlsx'
    data = read_excel_data(file_path)
    
    if data is None or 'ISDE Returns' not in data:
        return pd.DataFrame()
    
    returns_df = data['ISDE Returns']
    if 'Period' in returns_df.columns and 'ISDU.L Return (%)' in returns_df.columns and 'S&P 500 Return (%)' in returns_df.columns:
        return returns_df
    return pd.DataFrame()

@st.cache_data
def get_isdu_price():
    """Get current ISDU price from Excel"""
    file_path = '7- ISDU Details.xlsx'
    data = read_excel_data(file_path)
    
    if data is None or 'ISDE Price' not in data:
        return None
    
    price_df = data['ISDE Price']
    if 'Current Price' in price_df.columns and not price_df.empty:
        return price_df['Current Price'].iloc[0]
    return None

@st.cache_data
def get_current_price(ticker):
    """Get current price from yfinance"""
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.info.get('regularMarketPrice')
        return current_price if current_price else None
    except Exception as e:
        st.error(f"Error fetching price: {e}")
        return None

@st.cache_data
def get_etf_summary(ticker):
    """Get ETF summary from yfinance"""
    try:
        etf = yf.Ticker(ticker)
        return etf.info
    except Exception as e:
        st.error(f"Error fetching ETF summary: {e}")
        return None

@st.cache_data
def calculate_returns(history, periods):
    """Calculate returns for different time periods"""
    returns = {}
    for period_name, period_info in periods.items():
        years = period_info['years']
        if not history.empty:
            current_price = history['Close'].iloc[-1]
            # Calculate the number of trading days to look back
            lookback_days = years * 252  # Approximate trading days in a year
            
            # Get the start date index
            if len(history) >= lookback_days:
                start_price = history['Close'].iloc[-lookback_days]
            else:
                # If we don't have enough history, use the earliest available price
                start_price = history['Close'].iloc[0]
            
            # Calculate return
            returns[period_name] = {
                "start_price": start_price,
                "current_price": current_price,
                "return": ((current_price - start_price) / start_price) * 100
            }
    return returns

# ====================== SUBSCRIPTION FUNCTIONS ==========================
def check_subscription(username):
    """Check if user has active subscription"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        print(f"\n=== Checking subscription for {username} ===")
        cur.execute('''
            SELECT stripe_customer_id, subscription_status, subscription_end_date 
            FROM users 
            WHERE username = %s
        ''', (username,))
        user_data = cur.fetchone()
        
        print(f"User data: {user_data}")
        
        if not user_data or not user_data['stripe_customer_id']:
            print("❌ No subscription data found")
            return False
            
        # Check if subscription is active and not expired
        is_active = (user_data['subscription_status'] == 'active' and 
                    user_data['subscription_end_date'] and 
                    user_data['subscription_end_date'] > datetime.now())
                    
        print(f"Subscription active: {is_active}")
        return is_active
        
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ====================== INITIAL SETUP ==========================
st.set_page_config(
    page_title="Halal ETF Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for authentication if not already set
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'show_full_holdings' not in st.session_state:
    st.session_state['show_full_holdings'] = False
if 'history_period' not in st.session_state:
    st.session_state['history_period'] = "1y"

# ====================== CONSTANTS ==============================
SELECTED_ETFS = ['SPUS', 'SPWO', 'UMMA', 'HLAL', 'ISDU', 'ISDE', 'WSHR']
ETF_EXPENSE_RATIOS = {row['ETF']: float(row['Expense Ratio'].strip('%')) 
                     for _, row in get_etf_data().iterrows()}
ADMIN_USERS = ['abdul']  # List of usernames with admin access
# ====================== USER AUTHENTICATION ==========================
# Main content
if not st.session_state['authentication_status']:
    # Show login/register/claim tabs
    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["Login", "Register", "Claim Subscription"])
    
    with auth_tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if username and password:
                user = verify_user(username, password)
                if user:
                    st.session_state['authentication_status'] = True
                    st.session_state['name'] = user['name']
                    st.session_state['username'] = user['username']
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
    
    with auth_tab2:
        st.subheader("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_email = st.text_input("Email", key="reg_email")
        reg_name = st.text_input("Full Name", key="reg_name")
        
        if st.button("Register"):
            if reg_username and reg_password and reg_email and reg_name:
                success, message = create_user(reg_email, reg_username, reg_password, reg_name)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields")
        
    with auth_tab3:
        st.subheader("Claim Your Subscription")
        st.write("""
        If you made a payment but haven't registered yet:
        1. First, register an account in the 'Register' tab
        2. Then login to your account
        3. Go to the 'ISDU Deep Dive' tab
        4. Look for the 'Already Paid?' section
        5. Enter the email you used for payment
        6. Click 'Claim Subscription'
        """)
        
        st.info("""
        💡 Important: Make sure to register with the same email you used for payment, 
        or you'll need to claim your subscription manually after registering.
        """)

else:
    # Show logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state['authentication_status'] = None
        st.session_state['name'] = None
        st.session_state['username'] = None
        st.rerun()

    # Create main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "ETF Overview", 
        "Holdings Analysis", 
        "Performance Comparison",
        "ISDU Deep Dive"
    ])

    # Tab 1: ETF Overview - Always accessible
    with tab1:
        st.header("Halal ETF Overview")
        
        # Summary Statistics
        st.subheader("Quick Statistics")
        col1, col2, col3 = st.columns(3)
        
        etf_data = get_etf_data()
        with col1:
            st.metric("Total ETFs", len(SELECTED_ETFS))
            st.metric("Average Expense Ratio", f"{etf_data['Expense Ratio'].str.rstrip('%').astype(float).mean():.2f}%")
        with col2:
            st.metric("Lowest Cost ETF", f"{etf_data['ETF'][etf_data['Expense Ratio'].str.rstrip('%').astype(float).idxmin()]}")
            st.metric("Highest YTD Return", f"{etf_data['YTD Return'].max()}")
        with col3:
            total_aum = etf_data['AUM (M)'].sum()
            st.metric("Total AUM", f"${total_aum:,.2f}M")
            st.metric("Average 1Y Return", f"{etf_data['1-Year Return'].str.rstrip('%').astype(float).mean():.2f}%")

        # Detailed ETF Comparison
        st.subheader("ETF Comparison")
        
        # Create tabs for different comparison views
        compare_tab1, compare_tab2, compare_tab3 = st.tabs([
            "Basic Info", 
            "Visual Analysis",
            "Risk Metrics"
        ])
        
        with compare_tab1:
            st.subheader("ETF Information")
            # Basic Information Table
            st.dataframe(
                etf_data,
                column_config={
                    "ETF": st.column_config.TextColumn("ETF Symbol"),
                    "Full Name": st.column_config.TextColumn("Full Name"),
                    "Focus": st.column_config.TextColumn("Investment Focus"),
                    "AUM (M)": st.column_config.NumberColumn("AUM (M USD)", format="$%.2f M"),
                    "Expense Ratio": st.column_config.TextColumn("Expense Ratio"),
                    "Shariah Advisory": st.column_config.TextColumn("Shariah Advisory")
                },
                hide_index=True,
                use_container_width=True
            )

            # Investment Approach section
            st.subheader("Investment Approach")
            approach_data = pd.DataFrame({
                'ETF': etf_data['ETF'],
                'Investment Style': [
                    'Large Cap Value',
                    'Global Equity',
                    'Global Islamic',
                    'US All Cap',
                    'US Islamic',
                    'Global Islamic',
                    'Global Islamic'
                ],
                'Screening Method': [
                    'AAOIFI Standards',
                    'AAOIFI Standards',
                    'Custom Islamic',
                    'FTSE Shariah',
                    'MSCI Islamic',
                    'MSCI Islamic',
                    'Custom Islamic'
                ],
                'Rebalancing': [
                    'Quarterly',
                    'Quarterly',
                    'Semi-Annual',
                    'Quarterly',
                    'Quarterly',
                    'Quarterly',
                    'Semi-Annual'
                ],
                'Key Features': [
                    'Low cost, S&P 500 based',
                    'Global diversification',
                    'ESG integration',
                    'US market focus',
                    'MSCI methodology',
                    'Global exposure',
                    'ESG focused'
                ]
            })

            # Display the approach comparison table
            st.dataframe(
                approach_data,
                column_config={
                    "ETF": st.column_config.TextColumn("ETF Symbol"),
                    "Investment Style": st.column_config.TextColumn(
                        "Investment Style",
                        help="The primary investment approach"
                    ),
                    "Screening Method": st.column_config.TextColumn(
                        "Screening Method",
                        help="Islamic screening methodology used"
                    ),
                    "Rebalancing": st.column_config.TextColumn(
                        "Rebalancing",
                        help="How often the ETF is rebalanced"
                    ),
                    "Key Features": st.column_config.TextColumn(
                        "Key Features",
                        help="Distinctive characteristics"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

            # Key Features and Common Features section
            st.markdown("""
            ### Key Features
            #### Common Features
            ✅ Shariah-compliant investment options  
            ✅ Regular screening and monitoring  
            ✅ Transparent methodology  
            ✅ Competitive expense ratios  
            ✅ Diversified exposure  

            #### Benefits
            🌟 Access to global markets  
            🌟 Professional management  
            🌟 Easy to trade  
            🌟 Tax efficiency  
            🌟 Lower transaction costs  

            **Disclaimer**: Past performance does not guarantee future results. The information provided is for educational purposes only and should not be considered as investment advice. Please consult with a financial advisor before making any investment decisions.
            """)

        with compare_tab2:
            st.subheader("ETF Performance Analysis")
            
            # Create bar charts for expense ratios and AUM
            col1, col2 = st.columns(2)
            
            with col1:
                # Expense Ratio Bar Chart
                expense_ratios = [float(x.strip('%')) for x in etf_data['Expense Ratio']]
                fig_expense = px.bar(
                    etf_data,
                    x='ETF',
                    y=expense_ratios,
                    title="Expense Ratios Comparison",
                    labels={'y': 'Expense Ratio (%)'}
                )
                fig_expense.update_traces(
                    texttemplate='%{y:.2f}%',
                    textposition='outside',
                    marker_color='#1f77b4'
                )
                st.plotly_chart(fig_expense, use_container_width=True)
            
            with col2:
                # AUM Bar Chart
                fig_aum = px.bar(
                    etf_data,
                    x='ETF',
                    y='AUM (M)',
                    title="Assets Under Management",
                    labels={'y': 'AUM (Million USD)'}
                )
                fig_aum.update_traces(
                    texttemplate='$%{y:.1f}M',
                    textposition='outside',
                    marker_color='#2ca02c'
                )
                st.plotly_chart(fig_aum, use_container_width=True)
            
            # Returns Comparison
            st.subheader("Returns Comparison")
            returns_data = pd.DataFrame({
                'ETF': etf_data['ETF'],
                'YTD Return': [float(x.strip('%')) for x in etf_data['YTD Return']],
                '1-Year Return': [float(x.strip('%')) if x != 'N/A' else 0 for x in etf_data['1-Year Return']],
                '3-Year Return': [float(x.strip('%')) if x != 'N/A' else 0 for x in etf_data['3-Year Return']]
            })
            
            fig_returns = px.bar(
                returns_data,
                x='ETF',
                y=['YTD Return', '1-Year Return', '3-Year Return'],
                title="Performance Comparison",
                barmode='group'
            )
            fig_returns.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
            st.plotly_chart(fig_returns, use_container_width=True)
            st.info("Note: Some ETFs may show 0% returns for certain periods if data is not available (N/A).")

        with compare_tab3:
            st.subheader("Risk Metrics")
            
            # Risk metrics data
            risk_metrics = pd.DataFrame({
                'ETF': SELECTED_ETFS,
                'Beta': ['1.0', '0.85', '0.95', '0.98', '1.02', '0.96', '0.92'],
                'Volatility': ['12.5%', '8.5%', '11.5%', '12.0%', '13.2%', '12.8%', '11.8%']
            })
            
            # Display risk metrics table
            st.dataframe(
                risk_metrics,
                column_config={
                    "ETF": st.column_config.TextColumn("ETF Symbol"),
                    "Beta": st.column_config.TextColumn("Beta", help="Measure of volatility compared to the market"),
                    "Volatility": st.column_config.TextColumn("Volatility", help="Standard deviation of returns")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Risk metrics visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                fig_beta = px.bar(
                    risk_metrics,
                    x='ETF',
                    y=[float(x) for x in risk_metrics['Beta']],
                    title="Beta Comparison"
                )
                fig_beta.add_hline(y=1, line_dash="dash", line_color="red")
                fig_beta.update_traces(texttemplate='%{y:.2f}', textposition='outside')
                st.plotly_chart(fig_beta, use_container_width=True)
            
            with col2:
                fig_vol = px.bar(
                    risk_metrics,
                    x='ETF',
                    y=[float(x.strip('%')) for x in risk_metrics['Volatility']],
                    title="Volatility Comparison"
                )
                fig_vol.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
                st.plotly_chart(fig_vol, use_container_width=True)
            
            # Add explanation of metrics
            st.markdown("""
            ### Understanding Risk Metrics
            
            **Beta**
            - A beta of 1 indicates the ETF moves in line with the market
            - Beta > 1 means more volatile than the market
            - Beta < 1 means less volatile than the market
            
            **Volatility**
            - Measures the degree of variation in returns
            - Higher volatility indicates greater risk and potential return
            - Lower volatility suggests more stable returns
            """)

        # Add Newsletter Signup
        st.markdown("---")  # Add a divider
        st.markdown("## 📬 Stay Updated with Halal Finance")
        st.markdown("""
        Interested in learning more about Halal Finance? Join our newsletter to receive:
        - Monthly ETF performance updates
        - New Halal investment opportunities
        - Expert insights on Islamic finance
        - Educational content on Shariah-compliant investing
        """)

        col1, col2 = st.columns([2, 1])
        with col1:
            newsletter_name = st.text_input("Name", key="newsletter_name")
            newsletter_email = st.text_input("Email", key="newsletter_email")
            
        with col2:
            st.write("")  # Add some spacing
            st.write("")  # Add some spacing
            if st.button("Subscribe to Newsletter"):
                if newsletter_email and newsletter_name:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    try:
                        cur.execute('''
                            INSERT INTO newsletter_subscribers (email, name)
                            VALUES (%s, %s)
                            ON DUPLICATE KEY UPDATE 
                            name = VALUES(name),
                            status = 'active'
                        ''', (newsletter_email, newsletter_name))
                        conn.commit()
                        st.success("✅ Thanks for subscribing! You'll receive our next newsletter soon.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                    finally:
                        cur.close()
                        conn.close()
                else:
                    st.warning("Please fill in both name and email.")

    # Check subscription for premium tabs
    has_subscription = check_subscription(st.session_state['username'])
    
    # Tab 2: Holdings Analysis - Premium feature
    with tab2:
        if not has_subscription:
            st.warning("⭐ This feature requires a premium subscription")
            
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin: 20px 0;'>
                <h2>Subscribe to Access Premium Features</h2>
                <p style='font-size: 18px;'>Only $1.00/month for full access</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Direct link to Stripe checkout
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <a href="https://buy.stripe.com/test_14k5lSgzd7p5eGY000" target="_blank">
                            <button style="
                                background-color: #FF4B4B;
                                color: white;
                                padding: 12px 24px;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                font-size: 16px;
                                font-weight: bold;
                                width: 100%;
                                ">
                                🔓 Click Here to Subscribe
                            </button>
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("""
            ### Premium Features Include:
            - ✨ Detailed ETF Comparisons
            - 📊 Advanced Holdings Analysis
            - 📈 Performance Tracking
            - 🔍 Deep Dive Analysis
            """)
        else:
            # Show existing Holdings Analysis content
            st.header("Holdings Analysis")
            
            # Filter ETFs
            filtered_etfs = [etf for etf in SELECTED_ETFS if ETF_EXPENSE_RATIOS[etf] <= 0.65]
            
            # ETF selector with filtered ETFs
            selected_etf = st.selectbox(
                "Select ETF to analyze",
                filtered_etfs
            )
            
            # Add period selector
            period = st.selectbox(
                "Select Time Period",
                ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "All"],
                index=5
            )
            
            # Show price chart
            plot_price_chart(selected_etf, period, key=f"holdings_{selected_etf}")
            
            # Show holdings
            st.subheader(f"{selected_etf} Holdings")
            holdings_df = get_manual_holdings(selected_etf)
            st.dataframe(holdings_df)
            
            # Show sector weights with pie chart
            st.subheader("Sector Weightings")
            sectors_df = get_sector_weightings(selected_etf)
            fig = px.pie(sectors_df, values='Weight', names='Sector',
                        title=f'{selected_etf} Sector Distribution')
            st.plotly_chart(fig)

    # Tab 3: Performance Comparison - Premium feature
    with tab3:
        if not has_subscription:
            st.warning("⭐ This feature requires a premium subscription")
            
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin: 20px 0;'>
                <h2>Subscribe to Access Premium Features</h2>
                <p style='font-size: 18px;'>Only $1.00/month for full access</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Direct link to Stripe checkout
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <a href="https://buy.stripe.com/test_14k5lSgzd7p5eGY000" target="_blank">
                            <button style="
                                background-color: #FF4B4B;
                                color: white;
                                padding: 12px 24px;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                font-size: 16px;
                                font-weight: bold;
                                width: 100%;
                                ">
                                🔓 Click Here to Subscribe
                            </button>
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("""
            ### Premium Features Include:
            - ✨ Detailed ETF Comparisons
            - 📊 Advanced Holdings Analysis
            - 📈 Performance Tracking
            - 🔍 Deep Dive Analysis
            """)
        else:
            # Show existing Performance Comparison content
            st.header("Performance Comparison")
            
            selected_etfs_compare = st.multiselect(
                "Compare ETFs",
                SELECTED_ETFS,
                default=SELECTED_ETFS[:2]
            )
            
            if selected_etfs_compare:
                st.subheader("Historical Performance")
                for i, etf in enumerate(selected_etfs_compare):
                    plot_price_chart(etf, "1Y", key=f"compare_{etf}_{i}")
            else:
                st.warning("Select at least 2 ETFs for comparison")

    # Tab 4: ISDU Deep Dive - Premium feature
    with tab4:
        if not has_subscription:
            st.warning("This is a premium feature.")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                stripe_html = f"""
                <stripe-pricing-table 
                    pricing-table-id="{os.getenv('STRIPE_PRICING_TABLE_ID')}"
                    publishable-key="{os.getenv('STRIPE_PUBLISHABLE_KEY')}"
                ></stripe-pricing-table>
                <script async src="https://js.stripe.com/v3/pricing-table.js"></script>
                """
                components.html(stripe_html, height=400)
            
            with col2:
                st.markdown("### Already Paid?")
                st.write("If you made a payment with a different email, claim your subscription here:")
                payment_email = st.text_input("Email used for payment:", key="claim_email")
                if st.button("Claim Subscription"):
                    conn = get_db_connection()
                    cur = conn.cursor(dictionary=True)
                    try:
                        # Check for pending subscription
                        cur.execute('''
                            SELECT * FROM pending_subscriptions 
                            WHERE email = %s AND claimed_by_user_id IS NULL
                        ''', (payment_email,))
                        pending = cur.fetchone()
                        
                        if pending:
                            # Update user's subscription
                            success = update_subscription_status(
                                email=st.session_state['username'],  # Current user's username
                                stripe_customer_id=pending['stripe_customer_id']
                            )
                            
                            if success:
                                # Mark pending subscription as claimed
                                cur.execute('''
                                    UPDATE pending_subscriptions 
                                    SET claimed_by_user_id = 
                                        (SELECT id FROM users WHERE username = %s),
                                    claimed_date = NOW() 
                                    WHERE id = %s
                                ''', (st.session_state['username'], pending['id']))
                                conn.commit()
                                st.success("✅ Subscription claimed successfully! Please refresh the page.")
                            else:
                                st.error("❌ Failed to update subscription")
                        else:
                            st.error("❌ No pending subscription found for this email")
                    finally:
                        cur.close()
                        conn.close()
        else:
            # Show existing ISDU Deep Dive content
            st.header("ISDU Analysis")
            
            # Add refresh button at the top
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("🔄 Refresh Data", key="refresh_isdu"):
                    with st.spinner("Refreshing data..."):
                        st.cache_data.clear()
                        get_isdu_holdings.clear()
                        get_isdu_sectors.clear()
                        get_isdu_countries.clear()
                        get_isdu_returns.clear()
                        get_current_price.clear()
                        get_etf_summary.clear()
                        calculate_returns.clear()
                        get_etf_data.clear()
                        st.success("Cache cleared! Data refreshed.")
                        st.rerun()
            
            # Add an image at the top
            st.image("logo.png", width=200)
            
            # Center the title
            st.markdown("<h1 style='text-align: center;'>iShares MSCI USA Islamic UCITS ETF (ISDU.L) ETF Analysis</h1>", unsafe_allow_html=True)

            # ETF Description and Summary
            etf_summary = get_etf_summary("ISDU.L")
            if etf_summary:
                st.markdown("## ISDU.L Summary")
                
                # Create two columns
                col1, col2 = st.columns([1, 1])
                
                # Description in left column
                with col1:
                    st.write("""
                    The iShares MSCI USA Islamic UCITS ETF (ISDU.L) provides exposure to U.S. companies that comply with Shariah principles. 
                    It is similar to other Shariah-compliant ETFs but has a U.S. focus.
                    
                    A Value-Conscious Sharia-Compliant ETF ISDU.L is an exchange-traded fund (ETF) designed to provide investors with 
                    value-focused exposure to a diversified portfolio of Sharia-compliant stocks. Adhering to the guidelines set by the 
                    Accounting and Auditing Organization for Islamic Financial Institutions (AAOIFI), ISDU.L ensures all investments align 
                    with Islamic ethical principles.
                    
                    Tracking the MSCI USA Islamic Index ISDU.L tracks the performance of U.S. stocks that meet stringent Sharia-compliance criteria. 
                    This index includes companies with robust financial health, characterized by low leverage and debt to market capitalization 
                    ratios below 30%.
                    """)
                
                # Summary table in right column
                with col2:
                    st.subheader("ETF Summary from Yahoo Finance")
                    summary_items = {
                        "Name": etf_summary.get('longName', 'N/A'),
                        "Previous Close": f"${etf_summary.get('regularMarketPreviousClose', 'N/A'):.2f}",
                        "Open": f"${etf_summary.get('regularMarketOpen', 'N/A'):.2f}",
                        "Bid": f"${etf_summary.get('bid', 'N/A'):.2f}",
                        "Ask": f"${etf_summary.get('ask', 'N/A'):.2f}",
                        "Day's Range": f"${etf_summary.get('dayLow', 'N/A'):.2f} - ${etf_summary.get('dayHigh', 'N/A'):.2f}",
                        "52 Week Range": f"${etf_summary.get('fiftyTwoWeekLow', 'N/A'):.2f} - ${etf_summary.get('fiftyTwoWeekHigh', 'N/A'):.2f}",
                        "Volume": f"{etf_summary.get('volume', 'N/A'):,}",
                        "Avg. Volume": f"{etf_summary.get('averageVolume', 'N/A'):,}",
                        "Net Assets": f"${etf_summary.get('totalAssets', 'N/A'):,.0f}",
                        "NAV": f"${etf_summary.get('navPrice', 'N/A'):.4f}",
                        "PE Ratio (TTM)": f"{etf_summary.get('trailingPE', 'N/A'):.2f}",
                        "Yield": f"{float(etf_summary.get('yield', 0)) * 100:.2f}%",
                        "YTD Daily Total Return": f"{etf_summary.get('ytdReturn', 'N/A'):.2f}%"
                    }
                    
                    # Create and display the summary table
                    summary_df = pd.DataFrame(
                        [(k, v) for k, v in summary_items.items() if 'N/A' not in str(v)],
                        columns=['Metric', 'Value']
                    )
                    st.dataframe(
                        summary_df,
                        column_config={
                            "Metric": st.column_config.TextColumn("Metric", width="medium"),
                            "Value": st.column_config.TextColumn("Value", width="medium")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
            else:
                st.warning("Unable to fetch ETF summary from Yahoo Finance")

            # Historical Price Data
            st.subheader("Historical Price Data")
            current_price = get_current_price("ISDU.L")
            if current_price is not None:
                st.write(f"**Current Price:** ${current_price:.2f}")
            else:
                st.warning("Unable to fetch current price from Yahoo Finance")
            
            # Add period selector buttons
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button("1 Month", key="1m_isdu"):
                    st.session_state['history_period'] = "1mo"
            with col2:
                if st.button("3 Months", key="3m_isdu"):
                    st.session_state['history_period'] = "3mo"
            with col3:
                if st.button("6 Months", key="6m_isdu"):
                    st.session_state['history_period'] = "6mo"
            with col4:
                if st.button("1 Year", key="1y_isdu"):
                    st.session_state['history_period'] = "1y"
            with col5:
                if st.button("All", key="all_isdu"):
                    st.session_state['history_period'] = "max"
            
            # Show price chart
            plot_price_chart("ISDU.L", st.session_state['history_period'], key="isdu_main_chart")
            
            # Holdings Analysis
            st.subheader("ISDE Holdings")
            holdings_df = get_isdu_holdings()
            
            if not holdings_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Top 10 Holdings")
                    st.dataframe(holdings_df.head(10))
                    
                    # Show/Hide full holdings
                    if st.button("Toggle Full Holdings"):
                        st.session_state['show_full_holdings'] = not st.session_state.get('show_full_holdings', False)
                    
                    if st.session_state.get('show_full_holdings', False):
                        st.write("Complete Holdings List")
                        st.dataframe(holdings_df)
                
                with col2:
                    fig = px.pie(
                        holdings_df.head(10),
                        values='Weightings',
                        names='Security Name',
                        title="Top 10 Holdings Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No holdings data available")

            # Sector and Country Breakdown
            st.subheader("Sector and Country Breakdown")
            col1, col2 = st.columns(2)
            
            with col1:
                sectors_df = get_isdu_sectors()
                if not sectors_df.empty:
                    # Group by sector and sum the weightings
                    grouped_sectors = sectors_df.groupby('Sector')['Weightings'].sum().reset_index()
                    
                    # Convert to percentages (multiply by 100 if not already in percentage)
                    if grouped_sectors['Weightings'].max() <= 1:
                        grouped_sectors['Weightings'] = grouped_sectors['Weightings'] * 100
                        
                    # Sort by weightings from highest to lowest
                    grouped_sectors = grouped_sectors.sort_values('Weightings', ascending=False)
                    
                    fig = px.bar(
                        grouped_sectors,
                        x='Weightings',
                        y='Sector',
                        title="Sector Breakdown",
                        orientation='h'
                    )
                    
                    # Update the traces to show percentage
                    fig.update_traces(
                        texttemplate='%{x:.0f}%',  # Remove decimal places
                        textposition='outside',
                        hovertemplate='Sector: %{y}<br>Weight: %{x:.0f}%'
                    )
                    
                    # Update layout with fixed scale
                    fig.update_layout(
                        xaxis_title="Weightings (%)",
                        yaxis_title="",
                        showlegend=False,
                        margin=dict(l=0, r=0, t=30, b=0),
                        xaxis=dict(
                            range=[0, 100],  # Fix scale from 0 to 100%
                            tickformat='d',  # Show whole numbers
                            ticksuffix='%',  # Add % to tick labels
                            dtick=10  # Show ticks every 10%
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No sector data available")
            
            with col2:
                countries_df = get_isdu_countries()
                if not countries_df.empty:
                    fig = px.pie(
                        countries_df,
                        values='Weightings',
                        names='Country ',  # Note the space after Country
                        title="Country Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No country data available")
            
            # Return Analysis
            st.subheader("Return Analysis")

            # Get historical data for both ETFs
            etf_history = yf.download("ISDU.L", period="5y")
            sp500_history = yf.download("^GSPC", period="5y")

            if not etf_history.empty and not sp500_history.empty:
                # Define periods for return calculation
                periods = {
                    "1 Year": {"years": 1},
                    "3 Years": {"years": 3},
                    "5 Years": {"years": 5}
                }
                
                # Create a clean DataFrame for display
                clean_data = []
                for period_name, period_info in periods.items():
                    years = period_info['years']
                    # Calculate lookback days
                    lookback_days = years * 252
                    
                    # Get ISDU.L prices
                    isdu_current = float(etf_history['Close'].iloc[-1])  # Convert to float
                    if len(etf_history) >= lookback_days:
                        isdu_start = float(etf_history['Close'].iloc[-lookback_days])  # Convert to float
                    else:
                        isdu_start = float(etf_history['Close'].iloc[0])  # Convert to float
                    isdu_return = ((isdu_current - isdu_start) / isdu_start) * 100
                    
                    # Get S&P 500 prices
                    sp_current = float(sp500_history['Close'].iloc[-1])  # Convert to float
                    if len(sp500_history) >= lookback_days:
                        sp_start = float(sp500_history['Close'].iloc[-lookback_days])  # Convert to float
                    else:
                        sp_start = float(sp500_history['Close'].iloc[0])  # Convert to float
                    sp_return = ((sp_current - sp_start) / sp_start) * 100
                    
                    clean_data.append({
                        'Period': period_name,
                        'ISDU.L Start Price': f'${isdu_start:.2f}',
                        'ISDU.L Current Price': f'${isdu_current:.2f}',
                        'ISDU.L Return (%)': f'{isdu_return:.2f}%',
                        'S&P 500 Start Price': f'${sp_start:.2f}',
                        'S&P 500 Current Price': f'${sp_current:.2f}',
                        'S&P 500 Return (%)': f'{sp_return:.2f}%'
                    })
                
                # Create DataFrame
                returns_df = pd.DataFrame(clean_data)
                
                # Display the table
                st.write("Returns Data:")
                st.dataframe(
                    returns_df,
                    column_config={
                        "Period": st.column_config.TextColumn("Period"),
                        "ISDU.L Start Price": st.column_config.TextColumn("ISDU.L Start Price"),
                        "ISDU.L Current Price": st.column_config.TextColumn("ISDU.L Current Price"),
                        "ISDU.L Return (%)": st.column_config.TextColumn("ISDU.L Return (%)"),
                        "S&P 500 Start Price": st.column_config.TextColumn("S&P 500 Start Price"),
                        "S&P 500 Current Price": st.column_config.TextColumn("S&P 500 Current Price"),
                        "S&P 500 Return (%)": st.column_config.TextColumn("S&P 500 Return (%)")
                    },
                    hide_index=True
                )
                
                # Plot the bar chart comparing returns
                plot_data = pd.DataFrame({
                    'Period': returns_df['Period'],
                    'ISDU.L Return (%)': [float(x.strip('%')) for x in returns_df['ISDU.L Return (%)']],
                    'S&P 500 Return (%)': [float(x.strip('%')) for x in returns_df['S&P 500 Return (%)']]
                })
                
                fig = px.bar(
                    plot_data, 
                    x='Period', 
                    y=['ISDU.L Return (%)', 'S&P 500 Return (%)'],
                    barmode='group',
                    title='Return Analysis',
                    template='plotly_white',
                    text_auto=True
                )
                fig.update_traces(width=0.2, texttemplate='%{y:.2f}%')
                fig.update_layout(yaxis_title='Return (%)', width=600, height=400)
                st.plotly_chart(fig)
            else:
                st.warning("No historical data available for ISDU.L or S&P 500.")

            # Halal Screening Methodology
            st.markdown("## Halal Screening Methodology")
            st.markdown("""
            - **Shariah Compliance**: The iShares MSCI USA Islamic UCITS ETF (ISDU.L) adheres to Shariah investment principles by tracking the MSCI USA Islamic Index. This index excludes companies involved in non-compliant activities such as alcohol, tobacco, pork-related products, conventional financial services, gambling, and entertainment.
            - **Shariah Advisory**: BlackRock collaborates with [Amanie Advisors Ltd](https://amanieadvisors.com/), a reputable Shariah advisory firm. Amanie Advisors provides a dedicated Shariah Panel comprising esteemed Islamic scholars who oversee and guide the fund's adherence to Shariah principles. This panel is responsible for issuing Fatwas (Islamic legal opinions) and ensuring that the fund's operations align with Islamic law.
            """)
            
            # Overall Thoughts
            st.markdown("## Overall Thoughts on iShares MSCI USA Islamic UCITS ETF (ISDU.L)")

            if etf_summary:
                expense_ratio = float(etf_summary.get('annualReportExpenseRatio', 0)) * 100
                nav = etf_summary.get('navPrice', 'N/A')
                ytd_return = etf_summary.get('ytdReturn', 'N/A')
                
                st.markdown(f"""
                - **Competitive Expense Ratio**: ISDU.L offers a total expense ratio (TER) of {expense_ratio:.2f}%, which is relatively low compared to other Shariah-compliant ETFs.
                - **U.S. Market Exposure**: The fund provides Shariah-compliant exposure to U.S. equities, focusing on companies that adhere to Islamic investment principles.
                - **Performance Snapshot**: As of {datetime.now().strftime('%B %d, %Y')}, ISDU.L has a net asset value (NAV) of ${nav:.2f}, reflecting a year-to-date (YTD) return of {ytd_return:.2f}%.
                """)
            else:
                st.warning("Unable to fetch current ETF metrics from Yahoo Finance")
            
            # Comparison to Other Halal ETFs
            st.markdown("## Comparison to Other Halal ETFs")
            st.markdown("""
            **SP Funds S&P 500 Sharia Industry Exclusions ETF (SPUS)**
            - **Focus**: U.S. equities
            - **Expense Ratio**: 0.45% (higher than ISDU.L)
            - **Risk**: Lower volatility due to investment in large-cap U.S. companies, but with less sector diversification compared to ISDU.L.
            - **Performance**: As of February 22, 2025, SPUS is trading at $43.19, reflecting recent market movements.
            
            **Wahed FTSE USA Shariah ETF (HLAL)**
            - **Focus**: U.S. equities with a Shariah-compliant approach
            - **Expense Ratio**: 0.50% (higher than ISDU.L)
            - **Risk**: Moderate volatility with a focus on U.S. growth stocks, particularly in technology and healthcare sectors.
            - **Performance**: Trading at $53.29, HLAL has shown consistent growth, benefiting from U.S. market stability but lacks international exposure.
            
            **Wealthsimple Shariah World Equity Index ETF (WSHR)**
            - **Focus**: Global equities, including U.S. and international developed markets
            - **Expense Ratio**: 0.56% (highest among the compared ETFs)
            - **Risk**: More diversified geographically, reducing region-specific risks but potentially offering lower returns compared to U.S.-focused ETFs.
            - **Performance**: Includes companies like Barry Callebaut AG, The Coca-Cola Company, Nestlé S.A., and Novartis AG, providing balanced growth with exposure to consumer staples, healthcare, and technology.
            """)
            
            # Key Takeaway
            st.markdown("## Key Takeaway")
            st.markdown("""
            ISDU.L is a cost-effective option for those seeking Shariah-compliant investments in the U.S. market, offering exposure to a broad range of sectors with a relatively low expense ratio. Compared to U.S.-focused ETFs like SPUS and HLAL, ISDU.L provides similar market exposure with a lower TER. However, for investors seeking broader geographic diversification, WSHR offers global exposure but at a higher expense ratio.
            
            **Disclaimer**: Please note that past performance does not guarantee future results. It's advisable to consult with a financial advisor to ensure alignment with your individual investment objectives and risk profile.
            """)

    # Add back to top button and footer
    st.markdown("---")
    add_back_to_top_button()
    
    # Footer
    st.markdown("""
    <div style='text-align: center'>
        <small>Data sources: SPUS Fund Report 2025, HLAL Quarterly Update, ISDE.L Prospectus</small>
    </div>
    """, unsafe_allow_html=True)

    # In the sidebar section, restore these features:
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

        # Add a divider
        st.markdown("---")
        
        # Newsletter Signup in Sidebar
        st.markdown("## 📬 Newsletter")
        st.markdown("""
        Stay updated with Halal Finance:
        - Monthly ETF updates
        - New investment opportunities
        - Expert insights
        - Educational content
        """)
        
        newsletter_name = st.text_input("Name", key="newsletter_name_sidebar")
        newsletter_email = st.text_input("Email", key="newsletter_email_sidebar")
        
        if st.button("Subscribe", key="subscribe_sidebar"):
            if newsletter_email and newsletter_name:
                conn = get_db_connection()
                cur = conn.cursor()
                try:
                    cur.execute('''
                        INSERT INTO newsletter_subscribers (email, name)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE 
                        name = VALUES(name),
                        status = 'active'
                    ''', (newsletter_email, newsletter_name))
                    conn.commit()
                    st.success("✅ Thanks for subscribing!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    cur.close()
                    conn.close()
            else:
                st.warning("Please fill in both fields")

    def claim_subscription():
        st.subheader("Claim Your Subscription")
        st.write("If you made a payment with a different email, you can claim it here.")
        
        payment_email = st.text_input("Enter the email used for payment:")
        
        if st.button("Claim Subscription"):
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            
            try:
                # Check for pending subscription
                cur.execute('''
                    SELECT * FROM pending_subscriptions 
                    WHERE email = %s AND claimed_by_user_id IS NULL
                ''', (payment_email,))
                pending = cur.fetchone()
                
                if pending:
                    # Update user's subscription
                    success = update_subscription_status(
                        email=st.session_state['email'],  # Current user's email
                        stripe_customer_id=pending['stripe_customer_id']
                    )
                    
                    if success:
                        # Mark pending subscription as claimed
                        cur.execute('''
                            UPDATE pending_subscriptions 
                            SET claimed_by_user_id = %s, 
                                claimed_date = NOW() 
                            WHERE id = %s
                        ''', (st.session_state['user_id'], pending['id']))
                        conn.commit()
                        st.success("Subscription claimed successfully!")
                    else:
                        st.error("Failed to update subscription")
                else:
                    st.error("No pending subscription found for this email")
                
            finally:
                cur.close()
                conn.close()

# Add this route after your other routes
@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the event
    handle_webhook_event(event)
    return 'Success', 200
