import yfinance as yf

def fetch_price_data(ticker_symbol, days=5):
    """Fetches recent closing prices using yfinance."""
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period=f"{days}d", interval="1d") 
    
    price_records = []
    for index, row in hist.iterrows():
        price_records.append({
            "date": index.strftime('%Y-%m-%d'),
            "close_price": round(row['Close'], 2)
        })
    
    return price_records