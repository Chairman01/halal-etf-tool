import yfinance as yf
import pandas as pd

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
            'Change (%)': round(percent_change, 2)
        })

    return pd.DataFrame(data)

def format_currency(value):
    return f"${value:,.2f}"

def format_percentage(value):
    return f"{value:.2f}%"

def format_volume(value):
    if value >= 1e6:
        return f"{value/1e6:.1f}M"
    elif value >= 1e3:
        return f"{value/1e3:.1f}K"
    return f"{value:.0f}"
