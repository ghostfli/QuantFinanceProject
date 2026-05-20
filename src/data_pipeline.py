"""
Phase 1: Data Pipeline
Downloads, cleans, and stores historical price data for S&P 500 stocks.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date

import yfinance as yf
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent
PRICES_DIR = ROOT / "data" / "prices"
DB_PATH    = ROOT / "data" / "db" / "metadata.db"

PRICES_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Metadata database ──────────────────────────────────────────────────────────

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    Create (or open) the SQLite metadata database.
    Tracks download status, date ranges, and data quality per ticker.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ticker_metadata (
            ticker          TEXT PRIMARY KEY,
            last_downloaded TEXT,          -- ISO date string
            start_date      TEXT,
            end_date        TEXT,
            row_count       INTEGER,
            missing_days    INTEGER,       -- trading days with no data
            status          TEXT           -- 'ok', 'failed', 'insufficient'
        )
    """)
    conn.commit()
    return conn


def update_metadata(conn: sqlite3.Connection, ticker: str, **kwargs) -> None:
    """Upsert a ticker's metadata record."""
    fields = ["ticker"] + list(kwargs.keys())
    values = [ticker] + list(kwargs.values())
    placeholders = ", ".join(["?"] * len(values))
    updates = ", ".join(f"{k} = excluded.{k}" for k in kwargs)
    conn.execute(
        f"""
        INSERT INTO ticker_metadata ({', '.join(fields)})
        VALUES ({placeholders})
        ON CONFLICT(ticker) DO UPDATE SET {updates}
        """,
        values,
    )
    conn.commit()


# ── Downloading ────────────────────────────────────────────────────────────────

def download_ticker(
    ticker: str,
    start: str = "2014-01-01",
    end: str | None = None,
) -> pd.DataFrame | None:
    """
    Download adjusted OHLCV data for a single ticker via yfinance.

    Returns a cleaned DataFrame with columns:
        open, high, low, close, adj_close, volume
    indexed by date (DatetimeIndex, daily frequency).

    Returns None if the download fails or data is insufficient.
    """
    end = end or date.today().isoformat()

    try:
        raw = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=False,   # keep both close and adj_close explicitly
            progress=False,
            multi_level_index=False,
        )
    except Exception as e:
        log.warning(f"{ticker}: download error — {e}")
        return None

    if raw.empty:
        log.warning(f"{ticker}: no data returned")
        return None

    # yfinance returns MultiIndex columns when auto_adjust=False
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    raw.columns = [c.lower().replace(" ", "_") for c in raw.columns]

    # Rename adj close column if needed
    if "adj_close" not in raw.columns and "adj close" in raw.columns:
        raw = raw.rename(columns={"adj close": "adj_close"})

    required = {"open", "high", "low", "close", "adj_close", "volume"}
    missing = required - set(raw.columns)
    if missing:
        log.warning(f"{ticker}: missing columns {missing}")
        return None

    df = raw[list(required)].copy()
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"

    return df


# ── Cleaning ───────────────────────────────────────────────────────────────────

def clean_prices(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Apply data quality rules to a raw price DataFrame.

    Rules:
    - Drop rows where adj_close is NaN or zero (bad data, not a real halt)
    - Drop rows where volume is zero (no trading activity — skip for now,
      but flag if > 5% of rows so you know to investigate)
    - Forward-fill remaining NaNs for at most 1 day (weekend/holiday boundary)
    - Clip extreme single-day returns (> ±50%) — likely split not adjusted
    """
    original_len = len(df)

    # Drop clearly bad rows
    df = df[df["adj_close"] > 0].copy()
    df = df.dropna(subset=["adj_close"])

    # Warn on zero-volume rows (don't drop — may be valid for illiquid days)
    zero_vol_pct = (df["volume"] == 0).mean() * 100
    if zero_vol_pct > 5:
        log.warning(f"{ticker}: {zero_vol_pct:.1f}% of rows have zero volume")

    # Forward-fill gaps of exactly 1 day (handles holidays at month boundaries)
    df = df.asfreq("B").ffill(limit=1)  # 'B' = business day frequency

    # Detect likely unadjusted splits: single-day return > ±50%
    returns = df["adj_close"].pct_change().abs()
    extreme = returns[returns > 0.50]
    if not extreme.empty:
        log.warning(
            f"{ticker}: {len(extreme)} day(s) with >50% return — possible "
            f"unadjusted split. Dates: {extreme.index.tolist()}"
        )

    dropped = original_len - len(df)
    if dropped > 0:
        log.info(f"{ticker}: dropped {dropped} bad rows during cleaning")

    return df


# ── Saving / loading ───────────────────────────────────────────────────────────

def save_prices(df: pd.DataFrame, ticker: str, prices_dir: Path = PRICES_DIR) -> Path:
    """Save a cleaned price DataFrame to a Parquet file."""
    path = prices_dir / f"{ticker}.parquet"
    df.to_parquet(path, engine="pyarrow", compression="snappy")
    return path


def load_prices(ticker: str, prices_dir: Path = PRICES_DIR) -> pd.DataFrame | None:
    """Load a ticker's price data from Parquet. Returns None if not found."""
    path = prices_dir / f"{ticker}.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path, engine="pyarrow")


# ── Orchestration ──────────────────────────────────────────────────────────────

def run_pipeline(
    tickers: list[str],
    start: str = "2014-01-01",
    end: str | None = None,
    min_rows: int = 1000,           # ~4 years of trading days
) -> dict[str, str]:
    """
    Run the full Phase 1 pipeline for a list of tickers.

    Downloads, cleans, saves to Parquet, and records metadata in SQLite.

    Returns a dict mapping ticker -> status ('ok' | 'failed' | 'insufficient').
    """
    conn = init_db()
    results = {}

    for i, ticker in enumerate(tickers, 1):
        log.info(f"[{i}/{len(tickers)}] Processing {ticker}...")

        raw = download_ticker(ticker, start=start, end=end)

        if raw is None:
            update_metadata(conn, ticker,
                last_downloaded=date.today().isoformat(),
                status="failed",
                row_count=0,
                missing_days=0,
            )
            results[ticker] = "failed"
            continue

        df = clean_prices(raw, ticker)

        if len(df) < min_rows:
            log.warning(f"{ticker}: only {len(df)} rows — skipping (need {min_rows})")
            update_metadata(conn, ticker,
                last_downloaded=date.today().isoformat(),
                status="insufficient",
                row_count=len(df),
                missing_days=0,
            )
            results[ticker] = "insufficient"
            continue

        save_prices(df, ticker)

        # Count trading days with any NaN remaining after cleaning
        missing_days = int(df["adj_close"].isna().sum())

        update_metadata(conn, ticker,
            last_downloaded=date.today().isoformat(),
            start_date=df.index.min().date().isoformat(),
            end_date=df.index.max().date().isoformat(),
            row_count=len(df),
            missing_days=missing_days,
            status="ok",
        )

        results[ticker] = "ok"
        log.info(f"{ticker}: saved {len(df)} rows ✓")

    conn.close()

    ok    = sum(1 for v in results.values() if v == "ok")
    fails = sum(1 for v in results.values() if v != "ok")
    log.info(f"\nPipeline complete: {ok} succeeded, {fails} failed/skipped")

    return results
