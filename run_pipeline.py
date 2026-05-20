"""
run_pipeline.py
---------------
Entry point for Phase 1. Fetches the current S&P 500 constituents from
Wikipedia and runs the data pipeline.

Usage:
    python run_pipeline.py                  # full S&P 500
    python run_pipeline.py --test           # 10 tickers only (fast sanity check)
    python run_pipeline.py --tickers AAPL MSFT GOOG
"""

import argparse
import sys
from pathlib import Path
import io

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from src.data_pipeline import run_pipeline, load_prices


def get_sp500_tickers() -> list[str]:
    """
    Scrape the current S&P 500 constituent list from Wikipedia.
    Returns a sorted list of ticker strings.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text))
    df = tables[0]
    tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
    return sorted(tickers)


def print_summary(tickers: list[str]) -> None:
    """Print a quick summary of what was downloaded."""
    from src.data_pipeline import DB_PATH
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM ticker_metadata ORDER BY ticker", conn)
    conn.close()

    print("\n── Download summary ──────────────────────────────")
    print(df.groupby("status")["ticker"].count().to_string())
    print(f"\nTotal rows stored: {df['row_count'].sum():,}")
    print(f"Avg rows per ticker: {df[df['status']=='ok']['row_count'].mean():.0f}")

    # Quick sanity check: load one ticker and show its tail
    sample = "AAPL"
    prices = load_prices(sample)
    if prices is not None:
        print(f"\nSample — {sample} (last 5 rows):")
        print(prices.tail())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 1: Data Pipeline")
    parser.add_argument("--test", action="store_true",
                        help="Run on 10 tickers only")
    parser.add_argument("--tickers", nargs="+",
                        help="Specify exact tickers to download")
    parser.add_argument("--start", default="2014-01-01",
                        help="Start date (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.tickers:
        tickers = args.tickers
    elif args.test:
        tickers = ["AAPL", "MSFT", "GOOG", "JPM", "GS",
                   "XOM", "CVX", "KO", "PEP", "WMT"]
    else:
        print("Fetching S&P 500 ticker list from Wikipedia...")
        tickers = get_sp500_tickers()
        print(f"Found {len(tickers)} tickers\n")

    run_pipeline(tickers, start=args.start)
    print_summary(tickers)
