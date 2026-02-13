import yfinance as yf

def get_market_data():
    data = {}
    try:
        sp500 = yf.Ticker("^GSPC").history(period="1d")['Close'].iloc[-1]
        nasdaq = yf.Ticker("^IXIC").history(period="1d")['Close'].iloc[-1]
        return f"S&P 500 is at {int(sp500)}, NASDAQ is at {int(nasdaq)}."
    except Exception:
        return "Market data unavailable."
