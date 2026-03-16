import argparse
import os
# Import your custom modules
from src.data.news.duckduckgo_news import fetch_web_news
from src.data.news.reddit_scraper import fetch_reddit_chatter
from src.data.news.google_news_search import scrape_trending_news
from src.data.news.deep_researcher import generate_search_queries, execute_deep_dive, analyse_stock_impact, extract_tickers_from_analysis, predict_tomorrows_movers

def run_agent(ticker, period="5d", start=None, end=None, indicator=None, charts=False, report=False, trending=False):
    """The core engine that runs the analysis and saves it to a temp file."""
    temp_filename = f"temp_{ticker}_dossier.txt"
    filepath = os.path.join("outputs", temp_filename)
    
    # Clear the old file if it exists so we get a fresh context window!
    if os.path.exists(filepath):
        os.remove(filepath)
        
    print(f"\n========== AGENT TARGET: {ticker} ==========")
    print(f"[+] Initializing fresh memory file: {temp_filename}")

    # 2. News Data
    print("[+] Browsing Live Web News... Saving to file.")
    news = fetch_web_news(ticker)
    news_text = ""
    if not news:
        news_text = "No recent news found.\n"
    else:
        for i, article in enumerate(news):
            news_text += f"{i+1}. {article['title']} (Source: {article['source']})\n"
    append_to_file(temp_filename, "COMPANY NEWS", news_text)

    # 3. Alternative Data (Reddit)
    print("[+] Scraping Reddit Chatter... Saving to file.")
    reddit_posts = fetch_reddit_chatter(ticker)
    reddit_text = ""
    if not reddit_posts:
        reddit_text = "No recent Reddit chatter found.\n"
    else:
        for i, post in enumerate(reddit_posts):
            reddit_text += f"{i+1}. {post['title']}\n"
    append_to_file(temp_filename, "REDDIT CHATTER", reddit_text)

    # 4. Global Trending News
    if trending:
        print("[+] Scraping Global Trending News... Saving to file.")
        trending_news = scrape_trending_news()
        append_to_file(temp_filename, "GLOBAL MACRO TRENDS", trending_news)

    print(f"    [💾] Dossier successfully compiled in: outputs/{temp_filename}")
    print("==================================================\n")

def append_to_file(filename, section_title, content):
    """Silently appends data to a text file in the outputs folder."""
    # Ensure the outputs folder actually exists
    os.makedirs("outputs", exist_ok=True) 
    filepath = os.path.join("outputs", filename)
    
    # Open in 'a' (append) mode
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"\n=== {section_title} ===\n")
        f.write(content + "\n")

def setup_cli():
    """Sets up the command line arguments and flags."""
    parser = argparse.ArgumentParser(description="AI Agentic Stock Analyser CLI")

    # Target Selection Arguments
    parser.add_argument("--ticker", type=str, help="Single stock ticker symbol (e.g., AAPL)")
    parser.add_argument("--tickers", type=str, nargs="+", help="Multiple ticker symbols (e.g., AAPL MSFT NVDA)")

    # Timeframe Arguments
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--period", type=str, default="5d", help="Predefined period (e.g., 1mo, 1y)")

    # Feature Flags (Store True means if you include the flag, it equals True)
    parser.add_argument("--report", action="store_true", help="Export full analysis report")
    parser.add_argument("--charts", action="store_true", help="Generate visual charts")
    parser.add_argument("--indicator", type=str, help="Specific technical indicator (e.g., RSI, MACD)")

    # just to scrape news from trending google news 
    parser.add_argument("--trending", action="store_true", help="Scrape trending news from Google News")
    return parser.parse_args()


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    args = setup_cli()

    # Determine which tickers to process
    target_tickers = []
    if args.tickers:
        target_tickers = args.tickers
    elif args.ticker:
        target_tickers = [args.ticker]
    if args.trending and not target_tickers:
        print("\n==================================================")
        print("🚀 INITIALIZING AUTONOMOUS RESEARCH AGENT")
        print("==================================================\n")
        
        # Define where the memory file lives
        memory_filepath = os.path.join("outputs", "temp_global_trends.txt")
        
        # Ensure outputs folder exists
        os.makedirs("outputs", exist_ok=True)
        if os.path.exists(memory_filepath):
            os.remove(memory_filepath)
        
        # --- PHASE 1: SCOUTING ---
        trending_news = scrape_trending_news()
        with open(memory_filepath, 'w', encoding='utf-8') as f:
            f.write("=== GLOBAL MACRO TRENDS ===\n")
            f.write(trending_news)
        print(f"    [💾] Phase 1 Data saved to {memory_filepath}")
        
        # --- PHASE 2 & 3: STRATEGIZE AND DEEP DIVE ---
        llm_queries = generate_search_queries(memory_filepath)
        
        if llm_queries:
            # Note: We now capture the 'all_trends' returned by execute_deep_dive
            all_trends = execute_deep_dive(llm_queries, memory_filepath)
            
            # --- PHASE 4: LLM STOCK IMPACT ANALYSIS ---
            if all_trends:
                final_analysis = analyse_stock_impact(all_trends, memory_filepath)
                
                print("\n==================================================")
                print("📊 FINAL PORTFOLIO SIGNAL & VERDICT")
                print("==================================================")
                print(final_analysis)
                print("==================================================\n")

                print("==================================================")
                print("🔮 PHASE 4: PREDICTING TOMORROW'S MOVERS (WITH YFINANCE)")
                print("==================================================")
                
                # 1. Extract the tickers from the analysis text
                tickers = extract_tickers_from_analysis(final_analysis)
                
                # 2. Feed them into the predictor to get the UP/DOWN JSON
                predictions = predict_tomorrows_movers(final_analysis, tickers, memory_filepath)
                
                print(predictions)
                print("==================================================\n")
                
            print("\n[!] AGENT RESEARCH COMPLETE.")
            print(f"Open {memory_filepath} to view the full Intelligence Dossier.")
        else:
            print("❌ Error: LLM failed to generate queries.")
            
        exit(0)

    # Run the agent for every ticker provided
    for ticker in target_tickers:
        run_agent(
            ticker=ticker,
            period=args.period,
            start=args.start,
            end=args.end,
            indicator=args.indicator,
            charts=args.charts,
            report=args.report,
            trending=args.trending
        )