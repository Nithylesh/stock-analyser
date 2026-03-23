from dotenv import find_dotenv, load_dotenv
import yfinance as yf
import re
import os
import pandas as pd
import requests
load_dotenv(find_dotenv())

def send_telegram_message(message):
    """Sends a text message to your Telegram Bot."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Telegram credentials not found in environment variables. Skipping message.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # We wrap the message in ``` so Telegram formats it like a clean monospaced table
    payload = {
        "chat_id": chat_id,
        "text": f"```text\n{message}\n```",
        "parse_mode": "MarkdownV2"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("\n✅ Report successfully sent to Telegram!")
    except Exception as e:
        print(f"\n❌ Failed to send Telegram message: {e}")

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
    patterns = [
        # Pattern 1: The original format -> "**TICKER: AAPL**" followed by "DIRECTION: UP"
        r"TICKER[\*\s:]+([A-Z0-9.&]+)[^\n]*\n(?:[^\n]*\n){0,4}[^\n]*DIRECTION[\*\s:]+(UP|DOWN|NEUTRAL)",
        
        # Pattern 2: The current Markdown header format -> "#### AAPL (Company Name)"
        r"####\s+([A-Z0-9.&]+)[^\n]*\n(?:[^\n]*\n){0,4}[^\n]*DIRECTION[\*\s:]+(UP|DOWN|NEUTRAL)",
        
        # Pattern 3: Bullet points or numbered lists -> "1. **AAPL**" or "- **AAPL**"
        r"^(?:\d+\.|-)\s*\*\*([A-Z0-9.&]+)\*\*[^\n]*\n(?:[^\n]*\n){0,4}[^\n]*DIRECTION[\*\s:]+(UP|DOWN|NEUTRAL)",
        
        # Pattern 4: Bare ticker fallback -> "AAPL:" or "**AAPL**:"
        r"^\s*\*\*?([A-Z0-9.&]+)\*\*?[\s:]*\n(?:[^\n]*\n){0,4}[^\n]*DIRECTION[\*\s:]+(UP|DOWN|NEUTRAL)"
    ]

    predictions = {}
    
    # Run through all patterns to extract predictions
    for pattern in patterns:
        # re.IGNORECASE catches lowercase variations like "Direction:" or "Neutral"
        # re.MULTILINE allows ^ to match the start of every line
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for ticker, direction in matches:
            ticker_clean = ticker.upper().strip()
            # Prevent overwriting if multiple patterns catch the same ticker
            if ticker_clean not in predictions:
                predictions[ticker_clean] = direction.upper().strip()

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
    report_lines = []
    report_lines.append(f"📅 EVALUATION WINDOW: {date_base_str} vs {date_actual_str}")
    report_lines.append("="*65)
    report_lines.append(f"{'TICKER':<15} | {'PRED':<10} | {'ACTUAL':<10} | {'CHANGE %':<10} | {'RESULT'}")
    report_lines.append("="*65)
    
    for res in results:
        ticker, pred, act, change, status = res
        change_str = f"{change:+.2f}%" if act != "ERROR" else "N/A"
        report_lines.append(f"{ticker:<15} | {pred:<10} | {act:<10} | {change_str:<10} | {status}")
        
    report_lines.append("="*65)
    
    if total_scored > 0:
        accuracy = (correct_count / total_scored) * 100
        report_lines.append(f"🎯 ACCURACY: {accuracy:.2f}% ({correct_count}/{total_scored} correct)")
    else:
        report_lines.append("🎯 ACCURACY: No UP/DOWN predictions to score.")
    
    report_lines.append("="*65)

    # Combine all lines into one big text block
    final_report = "\n".join(report_lines)

    # Send the report via Telegram
    send_telegram_message(final_report)

if __name__ == "__main__":
    # Point this to your text file containing the predictions
    target_file = "outputs/temp_global_trends.txt" 
    evaluate_predictions(target_file)