# main.py

import argparse
import os

from src.data.news.duckduckgo_news import fetch_web_news
from src.data.news.reddit_scraper import fetch_reddit_chatter
from src.data.news.google_news_search import scrape_trending_news
from src.data.news.deep_researcher import (
    generate_search_queries,
    execute_deep_dive,
    analyse_stock_impact,
    extract_tickers_from_analysis,
    predict_tomorrows_movers,
    run_stock_pipeline,        # ← single-stock orchestrator
)


# ══════════════════════════════════════════════════════════
# Per-ticker light agent (standard mode, no --deep-research)
# ══════════════════════════════════════════════════════════
def run_agent(ticker, period="5d", start=None, end=None,
              indicator=None, charts=False, report=False, trending=False):
    """Compiles a quick dossier: news + reddit + optional trending macro."""
    temp_filename = f"temp_{ticker}_dossier.txt"
    filepath      = os.path.join("outputs", temp_filename)

    if os.path.exists(filepath):
        os.remove(filepath)

    print(f"\n========== AGENT TARGET: {ticker} ==========")
    print(f"[+] Initializing fresh memory file: {temp_filename}")

    # Company news
    print("[+] Browsing Live Web News...")
    news      = fetch_web_news(ticker)
    news_text = "No recent news found.\n" if not news else "".join(
        f"{i+1}. {a['title']} (Source: {a['source']})\n" for i, a in enumerate(news)
    )
    append_to_file(temp_filename, "COMPANY NEWS", news_text)

    # Reddit chatter
    print("[+] Scraping Reddit Chatter...")
    posts       = fetch_reddit_chatter(ticker)
    reddit_text = "No recent Reddit chatter found.\n" if not posts else "".join(
        f"{i+1}. {p['title']}\n" for i, p in enumerate(posts)
    )
    append_to_file(temp_filename, "REDDIT CHATTER", reddit_text)

    # Optional global macro layer
    if trending:
        print("[+] Scraping Global Trending News...")
        append_to_file(temp_filename, "GLOBAL MACRO TRENDS", scrape_trending_news())

    print(f"    [💾] Dossier compiled → outputs/{temp_filename}")
    print("==================================================\n")


def append_to_file(filename, section_title, content):
    os.makedirs("outputs", exist_ok=True)
    with open(os.path.join("outputs", filename), "a", encoding="utf-8") as f:
        f.write(f"\n=== {section_title} ===\n{content}\n")


# ══════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════
def setup_cli():
    parser = argparse.ArgumentParser(description="AI Agentic Stock Analyser CLI")

    # Targets
    parser.add_argument("--ticker",  type=str,           help="Single ticker (e.g. AAPL)")
    parser.add_argument("--tickers", type=str, nargs="+", help="Multiple tickers (e.g. AAPL MSFT)")

    # Timeframe
    parser.add_argument("--start",  type=str,             help="Start date YYYY-MM-DD")
    parser.add_argument("--end",    type=str,             help="End date YYYY-MM-DD")
    parser.add_argument("--period", type=str, default="5d", help="Period e.g. 1mo, 1y")

    # Feature flags
    parser.add_argument("--report",    action="store_true", help="Export full report")
    parser.add_argument("--charts",    action="store_true", help="Generate charts")
    parser.add_argument("--indicator", type=str,            help="Technical indicator (RSI, MACD …)")
    parser.add_argument("--trending",  action="store_true", help="Run global macro pipeline")

    # ── NEW ──────────────────────────────────────────────────
    parser.add_argument(
        "--deep-research",
        action="store_true",
        dest="deep_research",
        help="Run full 6-phase deep research pipeline for the specified ticker(s)",
    )

    return parser.parse_args()


# ══════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    args = setup_cli()

    target_tickers = args.tickers or ([args.ticker] if args.ticker else [])

    # ── --deep-research --ticker AAPL ────────────────────────
    if args.deep_research:
        if not target_tickers:
            print("❌  --deep-research requires --ticker or --tickers.")
            exit(1)

        for ticker in target_tickers:
            ticker = ticker.upper()
            print("\n" + "="*50)
            print(f"🔬 DEEP RESEARCH MODE — {ticker}")
            print("="*50 + "\n")

            filepath = os.path.join("outputs", f"temp_{ticker}_deep_research.txt")
            os.makedirs("outputs", exist_ok=True)
            if os.path.exists(filepath):
                os.remove(filepath)

            predictions = run_stock_pipeline(ticker, filepath)

            print("\n" + "="*50)
            print(f"🔮 TOMORROW'S PREDICTION — {ticker}")
            print("="*50)
            print(predictions)
            print("="*50 + "\n")
            print(f"[!] Full dossier → {filepath}")

        exit(0)

    # ── --trending only (global macro pipeline) ──────────────
    if args.trending and not target_tickers:
        print("\n" + "="*50)
        print("🚀 AUTONOMOUS MACRO RESEARCH AGENT")
        print("="*50 + "\n")

        memory_filepath = os.path.join("outputs", "temp_global_trends.txt")
        os.makedirs("outputs", exist_ok=True)
        if os.path.exists(memory_filepath):
            os.remove(memory_filepath)

        # Phase 1 — Scout
        print("[1/6] 🕵️  SCOUTING: Fetching Google News trends...")
        trending_news = scrape_trending_news()
        with open(memory_filepath, "w", encoding="utf-8") as f:
            f.write("=== GLOBAL MACRO TRENDS ===\n" + trending_news)
        print(f"    [💾] Phase 1 data saved to {memory_filepath}")

        # Phases 2-6
        llm_queries = generate_search_queries(memory_filepath)
        if not llm_queries:
            print("❌ LLM failed to generate queries.")
            exit(1)

        all_trends     = execute_deep_dive(llm_queries, memory_filepath)
        final_analysis = analyse_stock_impact(all_trends, memory_filepath)

        print("\n" + "="*50)
        print("📊 FINAL PORTFOLIO SIGNAL & VERDICT")
        print("="*50)
        print(final_analysis)
        print("="*50 + "\n")

        tickers     = extract_tickers_from_analysis(final_analysis)
        predictions = predict_tomorrows_movers(final_analysis, tickers, memory_filepath)

        print("\n" + "="*50)
        print("🔮 NEXT-DAY DIRECTIONAL PREDICTIONS")
        print("="*50)
        print(predictions)
        print("="*50 + "\n")

        print("[!] AGENT RESEARCH COMPLETE.")
        print(f"    Full dossier → {memory_filepath}")
        exit(0)

    # ── Standard per-ticker mode ──────────────────────────────
    if not target_tickers:
        print("❌ Please provide --ticker, --tickers, --trending, or --deep-research.")
        exit(1)

    for ticker in target_tickers:
        run_agent(
            ticker=ticker,
            period=args.period,
            start=args.start,
            end=args.end,
            indicator=args.indicator,
            charts=args.charts,
            report=args.report,
            trending=args.trending,
        )