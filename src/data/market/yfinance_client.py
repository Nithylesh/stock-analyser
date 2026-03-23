import yfinance as yf
import pandas as pd
import numpy as np

def get_comprehensive_stock_data(ticker_symbol, days=5):
    """
    Fetches stock data and manually calculates Technical Indicators (RSI, MACD, SMA)
    using pure Pandas math to avoid extra dependency issues.
    """
    print(f"      -> Fetching data & calculating technicals for {ticker_symbol}...")
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Fetch 6 months of data
        hist = stock.history(period="6mo", interval="1d")
        
        if len(hist) < 50:
            print(f"      ⚠️  Not enough trading history for {ticker_symbol}.")
            return None

        # 2. MANUAL CALCULATIONS (Replacing pandas_ta)
        
        # A. SMA (Simple Moving Average)
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()

        # B. RSI (Relative Strength Index)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI_14'] = 100 - (100 / (1 + rs))

        # C. MACD (Moving Average Convergence Divergence)
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = exp1 - exp2
        hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        
        # Clean up NaNs from calculation warmup
        hist = hist.dropna()
        
        # 3. Extract Today's Stats
        today = hist.iloc[-1]
        current_price = round(today['Close'], 2)
        rsi_14 = round(today['RSI_14'], 2)
        sma_50 = round(today['SMA_50'], 2)
        
        macd_trend = "BULLISH" if today['MACD'] > today['Signal_Line'] else "BEARISH"
        distance_from_50_sma = round(((current_price - sma_50) / sma_50) * 100, 2)

        # 4. Grab last X days for LLM context
        recent_hist = hist.tail(days)
        price_records = []
        for index, row in recent_hist.iterrows():
            price_records.append({
                "date": index.strftime('%Y-%m-%d'),
                "close_price": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })
            
        info = stock.info

        # 5. Package for LLM
        details = {
            "ticker": ticker_symbol.upper(),
            "company_name": info.get("shortName", "Unknown"),
            "sector": info.get("sector", "Unknown"),
            "current_price": current_price,
            "technical_indicators": {
                "RSI_14": rsi_14,
                "RSI_Status": "OVERBOUGHT" if rsi_14 > 70 else "OVERSOLD" if rsi_14 < 30 else "NEUTRAL",
                "MACD_Trend": macd_trend,
                "SMA_50": sma_50,
                "Distance_from_50_SMA_Percent": distance_from_50_sma
            },
            "fundamentals": {
                "forward_pe": info.get("forwardPE", "N/A"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", "N/A")
            },
            "recent_history": price_records
        }
        
        return details
        
    except Exception as e:
        print(f"      ⚠️  Could not fetch data for {ticker_symbol}: {e}")
        return None