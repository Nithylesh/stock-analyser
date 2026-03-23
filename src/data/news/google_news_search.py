import feedparser
from duckduckgo_search import DDGS
import time
import requests
from bs4 import BeautifulSoup

def fetch_article_content(url: str, timeout: int = 8) -> str:
    """Fetches and extracts the main body text from a news article URL."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise tags
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "iframe", "noscript"]):
            tag.decompose()

        # Try semantic article containers first, fall back to <p> tags
        container = (
            soup.find("article")
            or soup.find("main")
            or soup.find(class_=lambda c: c and any(
                kw in c.lower() for kw in ("article", "story", "content", "body")
            ))
        )

        if container:
            paragraphs = container.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        # Join paragraphs, skip very short ones (nav crumbs, captions, etc.)
        text = " ".join(
            p.get_text(separator=" ", strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 60
        )

        # Return up to ~1000 chars (roughly 1 solid paragraph)
        return text[:1000].rsplit(".", 1)[0] + "." if text else ""

    except Exception as e:
        return ""


def scrape_trending_news():
    """Uses Google News for headlines and DuckDuckGo + full article fetch for context."""
    print("[+] 🕵️‍♂️ SCOUTING: Fetching Google News trends and DDG context...")
    raw_news_text = ""

    # STEP 1: Trending headlines from Google News RSS
    google_news_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS"
    feed = feedparser.parse(google_news_url)

    if not feed.entries:
        return "No news found."

    print("    [>] Cross-referencing headlines with search index...")

    with DDGS() as ddgs:
        for i, entry in enumerate(feed.entries[:10]):
            title = entry.title

            context = ""

            # STEP 2: DDG news search → get article URL
            try:
                results = ddgs.news(title, max_results=3)
            except Exception:
                results = []

            # STEP 3: Try fetching full article text from each DDG result URL
            for result in results:
                url = result.get("url", "")
                if not url:
                    continue

                content = fetch_article_content(url)
                if len(content) > 200:        # Accept if we got a real paragraph
                    context = content
                    break                      # Stop after the first good result

            # Fallback: stitch together all DDG snippets
            if not context and results:
                context = " ".join(
                    r.get("body", "") for r in results if r.get("body")
                ).strip()

            if not context:
                context = "Full context unavailable for this story."

            raw_news_text += f"Article {i+1}:\n"
            raw_news_text += f"Headline: {title}\n"
            raw_news_text += f"Context: {context}\n"
            raw_news_text += "-" * 40 + "\n\n"

            time.sleep(1)   # Stay polite to DDG

    return raw_news_text





# import feedparser
# from ddgs import DDGS
# import time

# def scrape_trending_news():
#     """Uses Google News for the headlines, and DuckDuckGo for the context."""
#     print("[+] 🕵️‍♂️ SCOUTING: Fetching Google News trends and DDG context...")
#     raw_news_text = ""
    
#     # STEP 1: Get the unbiased trending headlines from Google
#     google_news_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS"
#     feed = feedparser.parse(google_news_url)
    
#     if not feed.entries:
#         return "No news found on the front page."
        
#     print("    [>] Cross-referencing headlines with search index...")
    
#     with DDGS() as ddgs:
#         for i, entry in enumerate(feed.entries[:10]):
#             title = entry.title
            
#             # STEP 2: Ask DuckDuckGo for the summary of this exact headline
#             try:
#                 # We search DDG for the exact Google News title
#                 results = ddgs.news(title, max_results=1)
                
#                 if results:
#                     # DDG provides the juicy paragraph snippet natively!
#                     context = results[0].get('body', 'Context not indexed.')
#                 else:
#                     context = "Search index has not processed this breaking story yet."
#             except Exception:
#                 context = "Rate limit hit. Context skipped."
                
#             raw_news_text += f"Article {i+1}:\n"
#             raw_news_text += f"Headline: {title}\n"
#             raw_news_text += f"Context: {context}\n"
#             raw_news_text += "-" * 40 + "\n\n"
            
#             # Pause for 1 second between searches so DuckDuckGo doesn't block us for spamming
#             time.sleep(1)
            
#     return raw_news_text