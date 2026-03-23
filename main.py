import yfinance as yf
from duckduckgo_search import DDGS

def get_price_data(ticker_symbol):
    print(f"\n========== AGENT TARGET: {ticker_symbol} ==========")
    print("[+] FETCHING LIVE PRICE DATA...")
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="5d", interval="1d") 
    
    for index, row in hist.iterrows():
        date = index.strftime('%Y-%m-%d')
        close_price = round(row['Close'], 2)
        print(f"    {date}: Closing Price -> ${close_price}")

def get_web_news(query_term):
    print("\n[+] BROWSING LIVE WEB NEWS...")
    with DDGS() as ddgs:
        # Searches the DuckDuckGo News tab
        news_results = ddgs.news(f"{query_term} financial news", max_results=5)
        
        if not news_results:
            print("    No recent news found.")
        else:
            for i, article in enumerate(news_results):
                title = article.get('title', 'No Title')
                source = article.get('source', 'Unknown Web Source')
                print(f"    {i+1}. {title} (Source: {source})")

def get_reddit_chatter(ticker_symbol):
    print("\n[+] SCRAPING REDDIT CHATTER (WallStreetBets & Stocks)...")
    with DDGS() as ddgs:
        # Uses a "Google Dork" style search specifically targeting Reddit
        reddit_query = f"site:reddit.com/r/wallstreetbets OR site:reddit.com/r/stocks {ticker_symbol}"
        reddit_results = ddgs.text(reddit_query, max_results=3)
        
        if not reddit_results:
            print("    No recent Reddit chatter found.")
        else:
            for i, post in enumerate(reddit_results):
                title = post.get('title', 'No Title')
                # Cleaning up the title to make it readable
                clean_title = title.split('-')[0].strip() 
                print(f"    {i+1}. {clean_title}")

# --- RUN THE AGENT ---
target_ticker = "NVDA"
company_name = "NVIDIA" # Used for better news searching

get_price_data(target_ticker)
get_web_news(company_name)
get_reddit_chatter(target_ticker)

print("\n==================================================\n")