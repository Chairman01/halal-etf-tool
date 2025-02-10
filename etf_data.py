import yfinance as yf
import pandas as pd

# 📌 Fetch ETF Data
def get_etf_data():
    tickers = ["SPUS", "SPSK", "SPRE", "HLAL", "UMMA"]
    data = []

    for ticker in tickers:
        etf = yf.Ticker(ticker)
        info = etf.info
        hist = etf.history(period="1y")

        if hist.empty:
            continue

        last_close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        percent_change = ((last_close - prev_close) / prev_close) * 100

        data.append({
            "Ticker": ticker,
            "Company": info.get("shortName", "N/A"),
            "Name": info.get("longName", "N/A"),
            "Price": last_close,
            "Change (%)": round(percent_change, 2),
            "52-Week High": info.get("fiftyTwoWeekHigh", 0),
            "52-Week Low": info.get("fiftyTwoWeekLow", 0),
            "Market Cap": info.get("marketCap", 0),
            "Volume": info.get("volume", 0),
            "Last Updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return pd.DataFrame(data)

# 📌 Format Functions
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
