import yfinance as yf
import re
import os
import pandas as pd

def evaluate_predictions(filepath):
    """Parses predictions and grades them using exact date comparisons."""
    print(f"\n[+] 🕵️‍♂️ AUDITOR: Reading QUANTITATIVE predictions from {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filepath}.")
        return

    predictions = {}
    current_ticker = None

    # --- THE INDESTRUCTIBLE PARSER ---
    for line in text.split('\n'):
        clean_line = line.strip().upper()
        
        # Step 1: Hunt for the Ticker (Must have at least 2 letters, ignores numbers)
        if "TICKER" in clean_line or clean_line.startswith("####") or (clean_line.startswith("- **") and "DIRECTION" not in clean_line and "CONFIDENCE" not in clean_line):
            # Erase common list numbers (like "10. ") and the word TICKER
            clean_str = re.sub(r'^\d+\.\s*', '', clean_line.replace('TICKER', '').replace(':', '').strip())
            
            # Extract the pure symbol (Requires at least 2 uppercase letters)
            match = re.search(r'\b([A-Z]{2,}[A-Z0-9.&]+)\b', clean_str)
            if match:
                current_ticker = match.group(1).replace('*', '')

        # Step 2: Hunt for the Direction
        if current_ticker and "DIRECTION" in clean_line:
            if "UP" in clean_line:
                predictions[current_ticker] = "UP"
            elif "DOWN" in clean_line:
                predictions[current_ticker] = "DOWN"
            elif "NEUTRAL" in clean_line:
                predictions[current_ticker] = "NEUTRAL"
            
            current_ticker = None 
    # ---------------------------------

    # Failsafe: Nuke any dictionary keys that don't have letters in them
    banned_words = {"RATIONALE", "DIRECTION", "CONFIDENCE", "TICKER", "UP", "DOWN", "NEUTRAL"}
    predictions = {k: v for k, v in predictions.items() if re.search(r'[A-Z]', k) and k not in banned_words}

    if not predictions:
        print("❌ No valid predictions found.")
        return

    print(f"    [>] Parsed {len(predictions)} valid predictions. Fetching live market data...\n")

    tickers = list(predictions.keys())
    data = yf.download(tickers, period="5d", group_by="ticker", threads=True, progress=False)

    results = []
    correct_count = 0
    total_scored = 0
    
    date_base_str = "Unknown"
    date_actual_str = "Unknown"

    for ticker in tickers:
        try:
            hist = data[ticker] if len(tickers) > 1 else data
            hist = hist.dropna()

            if len(hist) < 2:
                results.append((ticker, predictions[ticker], "ERROR", 0.0, "⚠️ NO DATA"))
                continue

            # GRAB EXACT DATES FOR TRANSPARENCY
            date_base = hist.index[-2]   # The day the prediction was made (Yesterday)
            date_actual = hist.index[-1] # The day being predicted (Today)
            
            date_base_str = date_base.strftime('%Y-%m-%d')
            date_actual_str = date_actual.strftime('%Y-%m-%d')

            yesterday_close = hist['Close'].iloc[-2]
            today_close = hist['Close'].iloc[-1]
            
            # Safely cast to float
            yesterday_close = float(yesterday_close.iloc[0]) if isinstance(yesterday_close, pd.Series) else float(yesterday_close)
            today_close = float(today_close.iloc[0]) if isinstance(today_close, pd.Series) else float(today_close)

            pct_change = ((today_close - yesterday_close) / yesterday_close) * 100

            predicted_dir = predictions[ticker]
            
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

    # PRINT THE FINAL REPORT
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
    target_file = "outputs/reprediction_test.txt" 
    evaluate_predictions(target_file)