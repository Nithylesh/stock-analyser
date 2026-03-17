import sys
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../.."))
sys.path.append(root_dir)
# Load your environment variables
load_dotenv(find_dotenv())

from src.data.market.yfinance_client import get_comprehensive_stock_data

def run_reprediction_test():
    print("🚀 INITIALIZING BACKTEST: Repredicting yesterday's news with today's math...")
    filepath = "outputs/temp_global_trends.txt"
    
    # 1. Read the existing dossier
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filepath}.")
        return

    # 2. Extract ONLY Phase 3 (The Macro Analysis)
    print("[+] Isolating Phase 3 Macro Analysis...")
    try:
        # We split the string to grab everything between Phase 3 and Phase 4
        phase_3_split = content.split("=== PHASE 3: LLM STOCK IMPACT ANALYSIS ===")
        phase_3_text = phase_3_split[1].split("=== PHASE 4: NEXT-DAY DIRECTIONAL PREDICTIONS ===")[0].strip()
    except IndexError:
        print("❌ Could not parse Phase 3 from the file. Ensure the headers haven't changed.")
        return

    # 3. Extract the exact tickers you predicted yesterday using Regex
    print("[+] Extracting target tickers...")
    pattern = r"####\s+([A-Z0-9.&]+)\n"
    tickers = list(set(re.findall(pattern, content)))
    
    if not tickers:
        print("❌ No tickers found in the file to repredict.")
        return
        
    print(f"    [>] Found {len(tickers)} tickers: {', '.join(tickers)}")

    # 4. Fetch the NEW comprehensive data (with RSI, MACD, SMA)
    print("\n[+] Fetching NEW mathematical data (RSI, MACD, SMA)...")
    financial_data = []
    for ticker in tickers:
        data = get_comprehensive_stock_data(ticker, days=5)
        if data:
            financial_data.append(data)

    # 5. Call the LLM with the upgraded payload
    print("\n[+] Asking Qwen to repredict based on the new quantitative math...")
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("LLM_API_KEY"),
    )
    
    system_prompt = """
    You are a high-frequency trading algorithm's final decision module. 
    You will be provided with:
    1. A broader macro-economic news analysis.
    2. Real technical and fundamental data (recent prices, volume, RSI, MACD, SMA) for specific stocks.

    Based on the convergence of the NEWS SENTIMENT and the TECHNICAL REALITY, predict if each stock 
    will increase or decrease TOMORROW. 

    For each stock, provide:
    - TICKER
    - DIRECTION: (UP, DOWN, or NEUTRAL)
    - CONFIDENCE: (0-100%)
    - RATIONALE: 2 sentences max explaining why (e.g., "News is bullish, but the RSI is 85 indicating it is severely overbought. Expecting a pullback.")
    """

    user_payload = f"MACRO NEWS ANALYSIS:\n{phase_3_text}\n\nTECHNICAL/FINANCIAL DATA:\n{json.dumps(financial_data, indent=2)}"

    response = client.chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    predictions = response.choices[0].message.content
    
    # 6. Save to a NEW test file so we don't ruin the old one
    out_path = "outputs/reprediction_test.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("=== RE-PREDICTION WITH NEW TECHNICALS ===\n")
        f.write("==================================================\n\n")
        f.write(predictions)
        
    print(f"\n✅ DONE! Open {out_path} to see the mathematically-backed predictions.")

if __name__ == "__main__":
    run_reprediction_test()