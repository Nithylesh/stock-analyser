from ddgs import DDGS

def fetch_reddit_chatter(ticker_symbol, max_results=3):
    """Scrapes recent Reddit posts for the ticker symbol."""
    reddit_records = []
    with DDGS() as ddgs:
        query = f"site:reddit.com {ticker_symbol}"
        results = ddgs.text(query, max_results=max_results)
        
        if results:
            for post in results:
                title = post.get('title', 'No Title')
                clean_title = title.split('-')[0].strip()
                reddit_records.append({
                    "title": clean_title,
                    "url": post.get('href', '')
                })
    return reddit_records