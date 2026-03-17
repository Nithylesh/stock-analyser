import yfinance as yf
import re
import os

def evaluate_predictions(filepath):
    """Parses yesterday's predictions and grades them against today's actual market data."""
    print(f"\n[+] 🕵️‍♂️ AUDITOR: Reading predictions from {filepath}...")

    # 1. Parse the text file to extract predictions
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filepath}.")
        return

    # Regex magic to find: "#### TICKER" and "- **DIRECTION**: UP/DOWN/NEUTRAL"
    pattern = r"####\s+([A-Z0-9.&]+)\n-\s+\*\*DIRECTION\*\*:\s+(UP|DOWN|NEUTRAL)"
    matches = re.findall(pattern, text)

    predictions = {ticker: direction for ticker, direction in matches}

    if not predictions:
        print("❌ No formatted predictions found in the file.")
        return

    print(f"    [>] Found {len(predictions)} predictions. Fetching live market data...\n")

    # 2. Fetch market data for the last 5 days (to ensure we safely get yesterday & today)
    tickers = list(predictions.keys())
    
    # yfinance suppresses its massive print logs if you use threads=False
    data = yf.download(tickers, period="5d", group_by="ticker", threads=True, progress=False)

    results = []
    correct_count = 0
    total_scored = 0

    # 3. Evaluate each prediction
    for ticker in tickers:
        try:
            # Handle yfinance multi-index structure
            hist = data[ticker] if len(tickers) > 1 else data
            hist = hist.dropna()

            if len(hist) < 2:
                results.append((ticker, predictions[ticker], "ERROR", 0.0, "⚠️ NO DATA"))
                continue

            # Calculate actual percentage change between yesterday's close and today's close
            yesterday_close = hist['Close'].iloc[-2]
            today_close = hist['Close'].iloc[-1]
            pct_change = ((today_close - yesterday_close) / yesterday_close) * 100

            predicted_dir = predictions[ticker]
            
            # Define what actual UP/DOWN/NEUTRAL means in reality
            # (e.g., anything between -0.25% and +0.25% is effectively a flat/neutral day)
            if pct_change > 0.25:
                actual_dir = "UP"
            elif pct_change < -0.25:
                actual_dir = "DOWN"
            else:
                actual_dir = "NEUTRAL"

            # Grade it
            is_hit = (predicted_dir == actual_dir)

            # Strict scoring: We only grade UP or DOWN calls. Neutrals are hard to trade.
            if predicted_dir in ["UP", "DOWN"]:
                total_scored += 1
                if is_hit:
                    correct_count += 1

            status = "✅ HIT" if is_hit else "❌ MISS"
            results.append((ticker, predicted_dir, actual_dir, pct_change, status))

        except Exception as e:
            results.append((ticker, predictions[ticker], "ERROR", 0.0, "⚠️ FAIL"))

    # 4. Print the final audit report
    print("=====================================================================")
    print(f"{'TICKER':<15} | {'PREDICTED':<10} | {'ACTUAL':<10} | {'CHANGE %':<10} | {'RESULT'}")
    print("=====================================================================")
    
    for res in results:
        ticker, pred, act, change, status = res
        # Formatting the percentage to strictly 2 decimal places with a sign
        change_str = f"{change:+.2f}%" if act != "ERROR" else "N/A"
        print(f"{ticker:<15} | {pred:<10} | {act:<10} | {change_str:<10} | {status}")
        
    print("=====================================================================")
    
    if total_scored > 0:
        accuracy = (correct_count / total_scored) * 100
        print(f"🎯 AGENT ACCURACY: {accuracy:.2f}% ({correct_count}/{total_scored} directional calls correct)")
    else:
        print("🎯 AGENT ACCURACY: No UP/DOWN predictions to score.")
    print("=====================================================================\n")

if __name__ == "__main__":
    # Point this to whatever file holds your Phase 4 output
    target_file = "outputs/temp_global_trends.txt" 
    evaluate_predictions(target_file)


