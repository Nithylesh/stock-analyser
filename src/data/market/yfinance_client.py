import yfinance as yf

def get_comprehensive_stock_data(ticker_symbol, days=5):
    """
    Fetches recent closing prices, volume, and key fundamental/technical data
    to give the LLM context on momentum, valuation, and trends.
    """
    print(f"      -> Fetching market data for {ticker_symbol}...")
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Fetch recent price action
        hist = stock.history(period=f"{days}d", interval="1d")
        price_records = []
        for index, row in hist.iterrows():
            price_records.append({
                "date": index.strftime('%Y-%m-%d'),
                "close_price": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })
            
        # 2. Fetch technicals and fundamentals
        info = stock.info
        
        # If the ticker is invalid or delisted, info might be empty
        if not info or "symbol" not in info:
            return None

        details = {
            "ticker": ticker_symbol.upper(),
            "company_name": info.get("shortName", "Unknown"),
            "sector": info.get("sector", "Unknown"),
            "market_cap": info.get("marketCap", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "fifty_day_avg": info.get("fiftyDayAverage", "N/A"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "recent_history": price_records
        }
        
        return details
        
    except Exception as e:
        print(f"      ⚠️  Could not fetch data for {ticker_symbol}: {e}")
        return None