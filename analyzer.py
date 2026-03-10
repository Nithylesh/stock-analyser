import argparse

# Import your custom modules
from src.data.market.yfinance_client import fetch_price_data
from src.data.news.duckduckgo_news import fetch_web_news
from src.data.news.reddit_scraper import fetch_reddit_chatter

def run_agent(ticker, period="5d", start=None, end=None, indicator=None, charts=False, report=False):
    """The core engine that runs the analysis based on CLI flags."""
    print(f"\n========== AGENT TARGET: {ticker} ==========")
    
    # 1. Market Data (Handling periods or specific dates)
    print(f"[+] FETCHING MARKET DATA (Period: {period if not start else start + ' to ' + end})...")
    # Note: We will need to update fetch_price_data later to handle start/end dates!
    prices = fetch_price_data(ticker, days=5) 
    for p in prices:
        print(f"    {p['date']}: Closing Price -> ${p['close_price']}")

    # 2. News Data
    print("\n[+] BROWSING LIVE WEB NEWS...")
    news = fetch_web_news(ticker) # Using ticker as search term
    if not news:
        print("    No recent news found.")
    else:
        for i, article in enumerate(news):
            print(f"    {i+1}. {article['title']} (Source: {article['source']})")

    # 3. Alternative Data
    print("\n[+] SCRAPING REDDIT CHATTER (WallStreetBets & Stocks)...")
    reddit_posts = fetch_reddit_chatter(ticker)
    if not reddit_posts:
        print("    No recent Reddit chatter found.")
    else:
        for i, post in enumerate(reddit_posts):
            print(f"    {i+1}. {post['title']}")

    # --- PLACEHOLDERS FOR NEW FLAGS ---
    if indicator:
        print(f"\n[+] CALCULATING TECHNICAL INDICATOR: {indicator.upper()}...")
        print("    (Indicator logic goes here in the future)")

    if charts:
        print("\n[+] GENERATING VISUAL CHARTS...")
        print("    (Chart generation logic goes here in the future)")

    if report:
        print("\n[+] EXPORTING FULL ANALYSIS REPORT...")
        print(f"    (Report saved to outputs/{ticker}_report.pdf)")

    print("\n==================================================\n")


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
            report=args.report
        )