import yfinance as yf
import pandas as pd
import pandas_ta as ta

def get_comprehensive_stock_data(ticker_symbol, days=5):
    """
    Fetches stock data and mathematically calculates Technical Indicators (RSI, MACD, SMA)
    in Python before passing them to the LLM, eliminating AI hallucinations.
    """
    print(f"      -> Fetching data & calculating technicals for {ticker_symbol}...")
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Fetch 6 months of data so we have enough history to calculate a 50-Day SMA
        hist = stock.history(period="6mo", interval="1d")
        
        if len(hist) < 50:
            print(f"      ⚠️  Not enough trading history for {ticker_symbol} to calculate indicators.")
            return None

        # 2. CALCULATE TECHNICAL INDICATORS IN PYTHON
        # This appends new columns directly to our historical dataframe
        hist.ta.rsi(length=14, append=True)
        hist.ta.macd(fast=12, slow=26, signal=9, append=True)
        hist.ta.sma(length=50, append=True)
        
        # Drop any NaN values that occur during the warmup period of the moving averages
        hist = hist.dropna()
        
        # 3. Extract the exact numbers for TODAY (the last row in the dataframe)
        today = hist.iloc[-1]
        current_price = round(today['Close'], 2)
        
        rsi_14 = round(today['RSI_14'], 2)
        sma_50 = round(today['SMA_50'], 2)
        
        # MACD Logic: If the MACD line is above the Signal line, momentum is Bullish
        macd_line = today['MACD_12_26_9']
        macd_signal = today['MACDs_12_26_9']
        macd_trend = "BULLISH" if macd_line > macd_signal else "BEARISH"
        
        # Calculate exactly how far the stock is stretched from its 50-day average
        distance_from_50_sma = round(((current_price - sma_50) / sma_50) * 100, 2)

        # 4. Grab the last X days of basic price/volume action for the LLM
        recent_hist = hist.tail(days)
        price_records = []
        for index, row in recent_hist.iterrows():
            price_records.append({
                "date": index.strftime('%Y-%m-%d'),
                "close_price": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })
            
        # 5. Fetch basic fundamentals
        info = stock.info

        # 6. Package it all up in a foolproof JSON structure for the LLM
        details = {
            "ticker": ticker_symbol.upper(),
            "company_name": info.get("shortName", "Unknown"),
            "sector": info.get("sector", "Unknown"),
            "current_price": current_price,
            
            # THE HARD MATH (LLM cannot hallucinate this now)
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