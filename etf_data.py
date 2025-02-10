import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ✅ List of Halal ETFs (Updated)
HALAL_ETFS = {
    'SPUS': "S&P 500 Sharia Industry Exclusions ETF",
    'SPSK': "SP Funds Dow Jones Global Sukuk ETF",
    'SPRE': "S&P Global REIT Sharia ETF",
    'HLAL': "Wahed FTSE USA Shariah ETF",
    'UMMA': "Wahed Dow Jones Islamic World ETF",
    'WSHR': "Wealthsimple Shariah World Equity ETF",
    'ISDU': "iShares MSCI USA Islamic UCITS ETF",
    'ISDE': "iShares MSCI World Islamic UCITS ETF",
    'SPTE': "SP Funds S&P 500 Sharia Industry Exclusions ETF",
    'SPWO': "SP Funds MSCI World Sharia ETF"
}

def get_etf_data():
    """Fetches ETF data from Yahoo Finance and calculates additional metrics."""
    data = []

    for ticker, name in HALAL_ETFS.items():
        try:
            etf = yf.Ticker(ticker)
            info = etf.info
            hist = etf.history(period="max")  # Fetch full history for all-time return

            if hist.empty:
                continue

            last_close = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else last_close
            percent_change = ((last_close - prev_close) / prev_close) * 100 
