# src/data/news/deep_researcher.py

import os
import json
import time
from openai import OpenAI
from ddgs import DDGS                          # ← updated from duckduckgo_search
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
from src.data.news.google_news_search import fetch_article_content
from src.data.market.yfinance_client import get_comprehensive_stock_data


# ── CI-aware performance settings ─────────────────────────────────────
_IS_CI            = os.getenv("CI", "false").lower() == "true"
ARTICLES_PER_TREND = 3 if _IS_CI else 10      # 3 in CI, 10 locally
SKIP_FULL_SCRAPE   = _IS_CI                    # skip slow HTTP scrape in CI
DDG_SLEEP          = 0.2 if _IS_CI else 0.5   # shorter pause in CI


def _llm_client() -> OpenAI:
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("LLM_API_KEY"),
        timeout=180.0,    # ← hard timeout: fail fast instead of hanging
        max_retries=3,   # ← auto-retry on transient network errors
    )


# ══════════════════════════════════════════════════════════
# PHASE 1A — Global macro dossier queries (--trending mode)
# ══════════════════════════════════════════════════════════
def generate_search_queries(filepath: str) -> list[dict]:
    print("[2/6] 🧠 STRATEGIZING: Reading global dossier and generating queries...")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            news_context = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filepath}. Run the scout first!")
        return []

    system_prompt = """
    You are an elite quantitative researcher. Read the provided global macro news dossier.
    Identify the 3 most critical trends that will impact the stock market.
    For each trend, write a highly specific search engine query to find granular data
    on how it affects specific industries, sectors, or supply chains.

    You MUST output ONLY a valid JSON object in this exact format:
    {
      "queries": [
        {"trend": "Name of Trend", "query": "Specific search string"},
        {"trend": "Name of Trend", "query": "Specific search string"},
        {"trend": "Name of Trend", "query": "Specific search string"}
      ]
    }
    """
    response = _llm_client().chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Here is the Phase 1 Dossier:\n{news_context}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content).get("queries", [])


# ══════════════════════════════════════════════════════════
# PHASE 1B — Stock-specific dossier builder (--deep-research)
# ══════════════════════════════════════════════════════════
def build_stock_dossier(ticker: str, filepath: str) -> None:
    print(f"[1/6] 🕵️  SCOUTING: Fetching live news for {ticker}...")

    articles_text = f"=== STOCK DOSSIER: {ticker} ===\n\n"

    with DDGS() as ddgs:
        searches = [
            f"{ticker} stock news",
            f"{ticker} earnings analyst forecast",
            f"{ticker} sector market outlook",
        ]
        for query in searches:
            try:
                results = ddgs.news(query, max_results=ARTICLES_PER_TREND)
            except Exception as e:
                print(f"    ⚠️  DDG error on '{query}': {e}")
                continue

            articles_text += f"--- Search: {query} ---\n"
            for r in results:
                url     = r.get("url", "")
                snippet = r.get("body", "")
                if SKIP_FULL_SCRAPE:
                    content = snippet + "  [DDG snippet — CI mode]"
                else:
                    content = fetch_article_content(url) if url else ""
                    if len(content) < 150:
                        content = snippet + "  [DDG snippet]"
                articles_text += f"Headline: {r.get('title', '')}\n"
                articles_text += f"Context : {content[:800]}\n"
                articles_text += "-" * 30 + "\n"
            time.sleep(DDG_SLEEP)

    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(articles_text)
    print(f"    [💾] Stock dossier saved to {filepath}")


def generate_stock_queries(ticker: str, filepath: str) -> list[dict]:
    print(f"[2/6] 🧠 STRATEGIZING: Generating deep-dive queries for {ticker}...")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            dossier = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filepath}.")
        return []

    system_prompt = f"""
    You are an elite equity research analyst focused on {ticker}.
    Read the provided news dossier about {ticker} and its market environment.

    Identify the 3 most important research angles that will determine 
    whether {ticker}'s stock price goes UP or DOWN in the next 1-5 days.

    For each angle, write a specific search query that will surface 
    granular data (supply chain impact, competitor reactions, analyst upgrades,
    regulatory risk, macro tailwinds/headwinds, institutional flows).

    You MUST output ONLY a valid JSON object in this exact format:
    {{
      "queries": [
        {{"trend": "Research Angle Name", "query": "Specific search string for {ticker}"}},
        {{"trend": "Research Angle Name", "query": "Specific search string for {ticker}"}},
        {{"trend": "Research Angle Name", "query": "Specific search string for {ticker}"}}
      ]
    }}
    """
    response = _llm_client().chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Here is the {ticker} dossier:\n{dossier}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    queries = json.loads(response.choices[0].message.content).get("queries", [])
    print(f"    Research angles: {[q['trend'] for q in queries]}")
    return queries


# ══════════════════════════════════════════════════════════
# PHASE 3 — Scrape articles per trend/angle
# ══════════════════════════════════════════════════════════
def scrape_trend(ddgs, trend: str, query: str, max_results: int = ARTICLES_PER_TREND) -> dict:
    print(f"      -> Scraping {max_results} articles for: '{query}'")
    trend_data = {"trend": trend, "query": query, "articles": []}

    try:
        results = ddgs.news(query, max_results=max_results)
    except Exception as e:
        print(f"         ⚠️  DDG error: {e}")
        return trend_data

    for i, result in enumerate(results):
        title   = result.get("title", "No Title")
        url     = result.get("url", "")
        snippet = result.get("body", "")
        print(f"         [{i+1}/{len(results)}] {title[:60]}...")

        if SKIP_FULL_SCRAPE:
            content = snippet + "  [DDG snippet — CI mode]"
        else:
            content = fetch_article_content(url) if url else ""
            if len(content) < 150:
                content = snippet + "  [DDG snippet — full article blocked]"

        trend_data["articles"].append({
            "index":   i + 1,
            "title":   title,
            "source":  result.get("source", "Unknown"),
            "date":    result.get("date", "Unknown date"),
            "url":     url,
            "content": content,
        })
        time.sleep(DDG_SLEEP)
    return trend_data


def execute_deep_dive(queries: list[dict], filepath: str) -> list[dict]:
    print(f"[3/6] 🔍 RESEARCHING: Deep-dive scraping ({ARTICLES_PER_TREND} articles × angle)...")
    all_trends: list[dict] = []

    with DDGS() as ddgs:
        for q in queries:
            all_trends.append(scrape_trend(ddgs, q["trend"], q["query"]))

    lines = ["\n\n" + "="*50, "=== PHASE 2: DEEP DIVE RESEARCH DATA ===", "="*50 + "\n"]
    for td in all_trends:
        lines += [f"\n{'#'*40}", f"TREND: {td['trend']}", f"LLM Search Query: {td['query']}",
                  f"Articles scraped: {len(td['articles'])}", f"{'#'*40}\n"]
        for a in td["articles"]:
            lines += [f"[{a['index']}] {a['title']}",
                      f"    Source : {a['source']}  |  Date: {a['date']}",
                      f"    URL    : {a['url']}",
                      f"    Content: {a['content']}",
                      "-"*40 + "\n"]

    with open(filepath, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return all_trends


# ══════════════════════════════════════════════════════════
# PHASE 4 — Sector-level stock impact analysis
# ══════════════════════════════════════════════════════════
def analyse_stock_impact(all_trends: list[dict], filepath: str) -> str:
    print("[4/6] 📊 ANALYSING: Asking LLM how each trend affects stock sectors...")

    context_parts = []
    for td in all_trends:
        block = [f"TREND: {td['trend']}", f"Research Query: {td['query']}", ""]
        for a in td["articles"]:
            block.append(f"  Article {a['index']}: {a['title']} ({a['source']}, {a['date']})")
            block.append(f"  {a['content'][:400]}")   # tighter cap in CI
            block.append("")
        context_parts.append("\n".join(block))

    system_prompt = """
    You are a senior equity strategist at a top hedge fund.
    You will receive research data on several macro trends.

    For EACH trend produce:
    1. SUMMARY         — 2-sentence synthesis of the trend.
    2. BULLISH SECTORS — Industries/stocks likely to benefit. Give specific ticker examples.
    3. BEARISH SECTORS — Industries/stocks likely to suffer.  Give specific ticker examples.
    4. MAGNITUDE       — Rate expected price impact: Low / Medium / High, with 1-line reason.
    5. TIME HORIZON    — Short (< 1 month) / Medium (1-6 months) / Long (6 months+).

    End with a PORTFOLIO SIGNAL section with a concrete allocation bias.
    Be direct. No filler. Back every claim with the research data provided.
    """

    response = _llm_client().chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": "Here is the deep-dive research:\n\n" + "\n\n---\n\n".join(context_parts)},
        ],
        temperature=0.3,
        max_tokens=1500,    # ← reduced from 2000 to cut response time
    )
    analysis = response.choices[0].message.content

    if analysis is None:
        print("         ⚠️  LLM returned an empty response! (Likely tripped a safety filter).")
        analysis = "ERROR: No analysis generated by LLM due to API filter or timeout."

    with open(filepath, "a", encoding="utf-8") as f:
        f.write("\n\n" + "="*50 + "\n=== PHASE 3: LLM STOCK IMPACT ANALYSIS ===\n" + "="*50 + "\n\n" + analysis + "\n")
    print("\n✅ Phase 3 analysis saved to:", filepath)
    return analysis


# ══════════════════════════════════════════════════════════
# PHASE 5 — Extract tickers from analysis text
# ══════════════════════════════════════════════════════════
def extract_tickers_from_analysis(analysis_text: str, seed_ticker: str | None = None) -> list[str]:
    print("[5/6] 🔎 EXTRACTING: Parsing tickers from macro analysis...")

    system_prompt = """
    You are a data extraction bot. Read the provided stock market analysis and extract 
    ALL valid US stock ticker symbols mentioned (including sector ETFs).
    Output ONLY: {"tickers": ["AAPL", "NVDA", "XOM"]}
    If no tickers found: {"tickers": []}
    """
    response = _llm_client().chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": analysis_text},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    tickers = json.loads(response.choices[0].message.content).get("tickers", [])

    if seed_ticker and seed_ticker.upper() not in [t.upper() for t in tickers]:
        tickers.insert(0, seed_ticker.upper())

    tickers = tickers[:15]
    print(f"    Tickers to analyse: {tickers}")
    return tickers


# ══════════════════════════════════════════════════════════
# PHASE 6 — Fetch yfinance data + predict tomorrow
# ══════════════════════════════════════════════════════════
def predict_tomorrows_movers(
    analysis_text: str,
    tickers: list[str],
    filepath: str,
    focus_ticker: str | None = None,
) -> str:
    if not tickers:
        print("[6/6] ⏭️  SKIPPING: No tickers found.")
        return ""

    print(f"[6/6] 🔮 PREDICTING: Fetching financials for {len(tickers)} tickers...")

    financial_data = []
    for ticker in tickers:
        data = get_comprehensive_stock_data(ticker, days=5)
        if data:
            financial_data.append(data)

    focus_line = (
        f"Your PRIMARY focus is {focus_ticker.upper()}. "
        f"Analyse competitors only as context for the {focus_ticker.upper()} prediction."
        if focus_ticker else "Analyse all tickers equally."
    )

    system_prompt = f"""
    You are a trading algorithm's final decision module.
    You have: (1) a research analysis and (2) technical/fundamental stock data.

    {focus_line}

    Predict if each stock will increase or decrease TOMORROW.
    For each stock provide:
    - TICKER
    - DIRECTION: UP, DOWN, or NEUTRAL
    - CONFIDENCE: 0-100%
    - RATIONALE: 2 sentences max. Cite a specific technical reading + news catalyst.

    Rules: RSI>70+bearish=DOWN | RSI<30+bullish=UP | contradictory signals=NEUTRAL
    """

    response = _llm_client().chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": (
                f"RESEARCH ANALYSIS:\n{analysis_text}\n\n"
                f"TECHNICAL/FINANCIAL DATA:\n{json.dumps(financial_data, indent=2)}"
            )},
        ],
        temperature=0.3,
        max_tokens=1500,    # ← reduced from 2000
    )
    predictions = response.choices[0].message.content

    phase_label = (
        f"PHASE 4: NEXT-DAY PREDICTION — {focus_ticker.upper()}"
        if focus_ticker else "PHASE 4: NEXT-DAY DIRECTIONAL PREDICTIONS"
    )
    with open(filepath, "a", encoding="utf-8") as f:
        f.write("\n\n" + "="*50 + f"\n=== {phase_label} ===\n" + "="*50 + "\n\n" + predictions + "\n")

    return predictions


# ══════════════════════════════════════════════════════════
# Orchestrators
# ══════════════════════════════════════════════════════════
def run_pipeline(filepath: str = "outputs/temp_global_trends.txt") -> str:
    queries     = generate_search_queries(filepath)
    all_trends  = execute_deep_dive(queries, filepath)
    analysis    = analyse_stock_impact(all_trends, filepath)
    tickers     = extract_tickers_from_analysis(analysis)
    predictions = predict_tomorrows_movers(analysis, tickers, filepath)
    print("\n✅ DONE. Full predictive report saved to:", filepath)
    return predictions


def run_stock_pipeline(ticker: str, filepath: str) -> str:
    build_stock_dossier(ticker, filepath)
    queries     = generate_stock_queries(ticker, filepath)
    all_trends  = execute_deep_dive(queries, filepath)
    analysis    = analyse_stock_impact(all_trends, filepath)
    tickers     = extract_tickers_from_analysis(analysis, seed_ticker=ticker)
    predictions = predict_tomorrows_movers(analysis, tickers, filepath, focus_ticker=ticker)
    print(f"\n✅ DONE. Full {ticker} research report saved to: {filepath}")
    return predictions


if __name__ == "__main__":
    run_pipeline()