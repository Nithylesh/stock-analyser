import os
import json
import time
from openai import OpenAI
from ddgs import DDGS
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
from src.data.news.google_news_search import fetch_article_content


# ─────────────────────────────────────────────
# STEP 1 — Ask LLM to pick the top trends
# ─────────────────────────────────────────────
def generate_search_queries(filepath: str) -> list[dict]:
    """Reads the dossier and asks the LLM to generate deep-dive search queries."""
    print("[2/4] 🧠 STRATEGIZING: Reading dossier and generating research queries...")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            news_context = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {filepath}. Run the scout first!")
        return []

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("LLM_API_KEY"),
    )

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

    response = client.chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the Phase 1 Dossier:\n{news_context}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    json_response = json.loads(response.choices[0].message.content)
    return json_response.get("queries", [])


# ─────────────────────────────────────────────
# STEP 2 — Scrape 10 articles per trend
# ─────────────────────────────────────────────
def scrape_trend(ddgs, trend: str, query: str, max_results: int = 10) -> dict:
    """
    Searches DDG for `query`, scrapes up to `max_results` articles,
    and returns a structured dict ready for LLM analysis.
    """
    print(f"      -> Scraping 10 articles for: '{query}'")

    trend_data = {
        "trend": trend,
        "query": query,
        "articles": [],
    }

    try:
        results = ddgs.news(query, max_results=max_results)
    except Exception as e:
        print(f"         ⚠️  DDG error: {e}")
        return trend_data

    for i, result in enumerate(results):
        title   = result.get("title", "No Title")
        url     = result.get("url", "")
        snippet = result.get("body", "")
        source  = result.get("source", "Unknown")
        date    = result.get("date", "Unknown date")

        print(f"         [{i+1}/{len(results)}] {title[:60]}...")

        # Try full scrape; fall back to DDG snippet
        content = fetch_article_content(url) if url else ""
        if len(content) < 150:
            content = snippet + "  [DDG snippet — full article blocked]"

        trend_data["articles"].append({
            "index":   i + 1,
            "title":   title,
            "source":  source,
            "date":    date,
            "url":     url,
            "content": content,
        })

        time.sleep(0.5)   # be polite to DDG

    return trend_data


# ─────────────────────────────────────────────
# STEP 3 — Execute all deep dives & save
# ─────────────────────────────────────────────
def execute_deep_dive(queries: list[dict], filepath: str) -> list[dict]:
    """
    Runs scrape_trend() for every LLM query, writes a human-readable
    report to `filepath`, and returns the structured data for the LLM.
    """
    print("[3/4] 🔍 RESEARCHING: Executing deep-dive scrapes (10 articles × trend)...")

    all_trends: list[dict] = []

    with DDGS() as ddgs:
        for q in queries:
            trend_data = scrape_trend(ddgs, q["trend"], q["query"], max_results=10)
            all_trends.append(trend_data)

    # ── Write human-readable report ──────────────────────────────────────
    report_lines = [
        "\n\n" + "=" * 50,
        "=== PHASE 2: DEEP DIVE RESEARCH DATA ===",
        "=" * 50 + "\n",
    ]

    for td in all_trends:
        report_lines.append(f"\n{'#' * 40}")
        report_lines.append(f"TREND: {td['trend']}")
        report_lines.append(f"LLM Search Query: {td['query']}")
        report_lines.append(f"Articles scraped: {len(td['articles'])}")
        report_lines.append(f"{'#' * 40}\n")

        for article in td["articles"]:
            report_lines.append(f"[{article['index']}] {article['title']}")
            report_lines.append(f"    Source : {article['source']}  |  Date: {article['date']}")
            report_lines.append(f"    URL    : {article['url']}")
            report_lines.append(f"    Content: {article['content']}")
            report_lines.append("-" * 40 + "\n")

    print(f"    [💾] Appending Deep Dive report to {filepath}...")
    with open(filepath, "a", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    return all_trends


# ─────────────────────────────────────────────
# STEP 4 — LLM stock impact analysis
# ─────────────────────────────────────────────
def analyse_stock_impact(all_trends: list[dict], filepath: str) -> str:
    """
    Feeds all scraped trend data to the LLM and asks for a structured
    stock market impact report. Appends the report to `filepath`.
    """
    print("[4/4] 📈 ANALYSING: Asking LLM how each trend affects stock prices...")

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("LLM_API_KEY"),
    )

    # Build a compact but complete context block for the LLM
    context_parts = []
    for td in all_trends:
        block = [f"TREND: {td['trend']}", f"Research Query: {td['query']}", ""]
        for a in td["articles"]:
            block.append(f"  Article {a['index']}: {a['title']} ({a['source']}, {a['date']})")
            block.append(f"  {a['content'][:600]}")   # cap each article at 600 chars
            block.append("")
        context_parts.append("\n".join(block))

    full_context = "\n\n---\n\n".join(context_parts)

    system_prompt = """
    You are a senior equity strategist at a top hedge fund.
    You will receive research data on several macro trends, each backed by 10 news articles.

    For EACH trend produce:
    1. SUMMARY        — 2-sentence synthesis of the trend.
    2. BULLISH SECTORS — Industries/stocks likely to benefit. Give specific ticker examples.
    3. BEARISH SECTORS — Industries/stocks likely to suffer.  Give specific ticker examples.
    4. MAGNITUDE       — Rate the expected price impact: Low / Medium / High, with 1-line reason.
    5. TIME HORIZON    — Short (< 1 month) / Medium (1-6 months) / Long (6 months+).

    End with a PORTFOLIO SIGNAL section that ranks the trends by urgency and suggests
    a concrete allocation bias (e.g. "overweight energy, underweight consumer discretionary").

    Be direct. No filler. Back every claim with the research data provided.
    """

    response = client.chat.completions.create(
        model="qwen/qwen2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Here is the deep-dive research:\n\n{full_context}"},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    analysis = response.choices[0].message.content

    # Append to the same output file
    report_section = (
        "\n\n" + "=" * 50 + "\n"
        "=== PHASE 3: LLM STOCK IMPACT ANALYSIS ===\n"
        + "=" * 50 + "\n\n"
        + analysis
        + "\n"
    )

    print(f"    [💾] Appending Stock Impact Analysis to {filepath}...")
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(report_section)

    print("\n✅ DONE. Full report saved to:", filepath)
    return analysis


# ─────────────────────────────────────────────
# Orchestrator — wire everything together
# ─────────────────────────────────────────────
def run_pipeline(filepath: str = "stock-analyser/outputs/temp_global_trends.txt"):
    queries    = generate_search_queries(filepath)
    all_trends = execute_deep_dive(queries, filepath)
    analysis   = analyse_stock_impact(all_trends, filepath)
    return analysis


if __name__ == "__main__":
    run_pipeline()