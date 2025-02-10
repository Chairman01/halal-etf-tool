import yfinance as yf
import pandas as pd

def get_etf_data():
    tickers = [
        "SPUS", "SPSK", "SPRE", "HLAL", "UMMA", "SPIN", "SPEM", "SPTE", "SPWO",  
        "ISDE.L", "ISDU.L", "WSHR.NE"  # Updated tickers
    ]
    
    etf_data = []
    
    for ticker in tickers:
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period="1y")
            
            if hist.empty:
                print(f"Warning: No data for {ticker}")
                continue
            
            last_close = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[0]
            
            percent_change = ((last_close - prev_close) / prev_close) * 100 if prev_close else None
            ytd_return = (last_close / hist["Close"].iloc[0] - 1) * 100 if prev_close else None
            
            etf_data.append([
                ticker, etf.info.get("longName", "N/A"), etf.info.get("marketCap", "N/A"),
                last_close, percent_change, ytd_return
            ])
        except Exception as e:
            print(f"Error retrieving data for {ticker}: {e}")
    
    df = pd.DataFrame(etf_data, columns=["Ticker", "Name", "Market Cap", "Price", "All-Time Return (%)", "YTD Return (%)"])
    return df

if __name__ == "__main__":
    df = get_etf_data()
    print(df)
