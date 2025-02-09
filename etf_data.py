import yfinance as yf
import pandas as pd
from datetime import datetime

def get_etf_data():
    """Fetch Halal ETF data from Yahoo Finance."""
    tickers = ["SPUS", "SPSK", "SPRE", "HLAL", "UMMA"]
    data = []

    for ticker in tickers:
        etf = yf.Ticker(ticker)
        hist = etf.history(period="1y")
        if hist.empty:
            continue

        last_close = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        percent_change = ((last_close - prev_close) / prev_close) * 100

        data.append({
            'Ticker': ticker,
            'Price': last_close,
            'Change (%)': round(percent_change, 2),
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    return pd.DataFrame(data)

def format_currency(value):
    return f"${value:,.2f}"

def format_percentage(value):
    return f"{value:.2f}%"
