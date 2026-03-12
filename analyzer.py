import argparse
import os
# Import your custom modules
from src.data.market.yfinance_client import fetch_price_data
from src.data.news.duckduckgo_news import fetch_web_news
from src.data.news.reddit_scraper import fetch_reddit_chatter
from src.data.news.google_news_search import scrape_trending_news

def run_agent(ticker, period="5d", start=None, end=None, indicator=None, charts=False, report=False, trending=False):
    """The core engine that runs the analysis and saves it to a temp file."""
    temp_filename = f"temp_{ticker}_dossier.txt"
    filepath = os.path.join("outputs", temp_filename)
    
    # Clear the old file if it exists so we get a fresh context window!
    if os.path.exists(filepath):
        os.remove(filepath)
        
    print(f"\n========== AGENT TARGET: {ticker} ==========")
    print(f"[+] Initializing fresh memory file: {temp_filename}")

    # 1. Market Data
    print(f"[+] Fetching Market Data... Saving to file.")
    prices = fetch_price_data(ticker, days=5) 
    price_text = ""
    for p in prices:
        price_text += f"{p['date']}: Closing Price -> ${p['close_price']}\n"
    append_to_file(temp_filename, "MARKET DATA", price_text)

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
        print("🚀 INITIALIZING AUTONOMOUS RESEARCH AGENT (GLOBAL SCOUT)")
        print("==================================================\n")
        
        print("[+] Scraping Global Trending News... Saving to file.")
        trending_news = scrape_trending_news()
        
        # Save it to a global temp file
        temp_filename = "temp_global_trends.txt"
        filepath = os.path.join("outputs", temp_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
        append_to_file(temp_filename, "GLOBAL MACRO TRENDS", trending_news)
        
        print(f"    [💾] Data successfully saved to outputs/{temp_filename}")
        exit(0)
        
    else:
        print("❌ Error: You must provide at least one ticker using --ticker or --tickers.")
        exit(1)

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