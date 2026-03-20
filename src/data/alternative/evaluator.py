import yfinance as yf
import re
import os
import pandas as pd

def evaluate_predictions(filepath):
    """Parses predictions and grades them using explicit Yesterday vs Today data."""
    print(f"\n[+] 🕵️‍♂️ AUDITOR: Reading predictions from {filepath}...")

    # 1. Read the file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filepath}.")
        return

    # 2. Parse the new format: "**TICKER: AAPL**" followed by "- **DIRECTION:** UP"
    pattern = r"TICKER(?:[\*\s:]+)([A-Z0-9.&]+)[^\n]*\n[^\n]*DIRECTION(?:[\*\s:]+)(UP|DOWN|NEUTRAL)"
    matches = re.findall(pattern, text)

    predictions = {ticker: direction for ticker, direction in matches}

    if not predictions:
        print("❌ No formatted predictions found in the file. Check the format.")
        return

    print(f"    [>] Found {len(predictions)} valid predictions. Fetching live market data...\n")

    # 3. Fetch Data
    tickers = list(predictions.keys())
    data = yf.download(tickers, period="5d", group_by="ticker", threads=True, progress=False)

    results = []
    correct_count = 0
    total_scored = 0
    
    date_base_str = "Unknown"
    date_actual_str = "Unknown"

    # 4. Evaluate
    for ticker in tickers:
        try:
            hist = data[ticker] if len(tickers) > 1 else data
            hist = hist.dropna()

            if len(hist) < 2:
                results.append((ticker, predictions[ticker], "ERROR", 0.0, "⚠️ NO DATA"))
                continue

            # Identify exact dates being compared
            date_base = hist.index[-2]   # Yesterday
            date_actual = hist.index[-1] # Today
            
            date_base_str = date_base.strftime('%Y-%m-%d')
            date_actual_str = date_actual.strftime('%Y-%m-%d')

            yesterday_close = hist['Close'].iloc[-2]
            today_close = hist['Close'].iloc[-1]
            
            # Safely cast to float
            yesterday_close = float(yesterday_close.iloc[0]) if isinstance(yesterday_close, pd.Series) else float(yesterday_close)
            today_close = float(today_close.iloc[0]) if isinstance(today_close, pd.Series) else float(today_close)

            pct_change = ((today_close - yesterday_close) / yesterday_close) * 100

            predicted_dir = predictions[ticker]
            
            # Define UP/DOWN thresholds
            if pct_change > 0.25:
                actual_dir = "UP"
            elif pct_change < -0.25:
                actual_dir = "DOWN"
            else:
                actual_dir = "NEUTRAL"

            is_hit = (predicted_dir == actual_dir)

            if predicted_dir in ["UP", "DOWN"]:
                total_scored += 1
                if is_hit:
                    correct_count += 1

            status = "✅ HIT" if is_hit else "❌ MISS"
            results.append((ticker, predicted_dir, actual_dir, pct_change, status))

        except Exception as e:
            results.append((ticker, predictions[ticker], "ERROR", 0.0, "⚠️ FAIL"))

    # 5. Output Report
    print(f"📅 EVALUATION WINDOW: Prediction Base ({date_base_str}) vs Actual Outcome ({date_actual_str})")
    print("=====================================================================")
    print(f"{'TICKER':<15} | {'PREDICTED':<10} | {'ACTUAL':<10} | {'CHANGE %':<10} | {'RESULT'}")
    print("=====================================================================")
    
    for res in results:
        ticker, pred, act, change, status = res
        change_str = f"{change:+.2f}%" if act != "ERROR" else "N/A"
        print(f"{ticker:<15} | {pred:<10} | {act:<10} | {change_str:<10} | {status}")
        
    print("=====================================================================")
    
    if total_scored > 0:
        accuracy = (correct_count / total_scored) * 100
        print(f"🎯 ALGORITHM ACCURACY: {accuracy:.2f}% ({correct_count}/{total_scored} directional calls correct)")
    else:
        print("🎯 ALGORITHM ACCURACY: No UP/DOWN predictions to score.")
    print("=====================================================================\n")

if __name__ == "__main__":
    # Point this to your text file containing the predictions
    target_file = "outputs/temp_global_trends.txt" 
    evaluate_predictions(target_file)