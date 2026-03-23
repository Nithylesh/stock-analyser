from duckduckgo_search import DDGS

def fetch_web_news(query_term, max_results=5):
    """Fetches live news headlines using DuckDuckGo."""
    news_records = []
    with DDGS() as ddgs:
        results = ddgs.news(f"{query_term} financial news", max_results=max_results)
        if results:
            for article in results:
                news_records.append({
                    "title": article.get('title', 'No Title'),
                    "snippet": article.get('body', 'No summary available.'),
                    "source": article.get('source', 'Unknown Web Source'),
                    "url": article.get('url', '')
                })
    return news_records