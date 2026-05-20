import sqlite3
from pathlib import Path
import pandas as pd

import src.data_pipeline as dp


def test_clean_prices_drops_bad_rows_and_forward_fills():
    df = pd.DataFrame(
        {
            "open": [1, 2, 3],
            "high": [1, 2, 3],
            "low": [1, 2, 3],
            "close": [1, 2, 3],
            "adj_close": [1.0, 0.0, None],
            "volume": [100, 0, 50],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
    )
    df.index.name = "date"

    cleaned = dp.clean_prices(df, "TEST")

    assert "adj_close" in cleaned.columns
    assert cleaned["adj_close"].min() > 0
    assert cleaned.shape[0] == 1
    assert cleaned.index.name == "date"


def test_save_and_load_prices_roundtrip(tmp_path):
    prices_dir = tmp_path / "prices"
    prices_dir.mkdir()

    df = pd.DataFrame(
        {
            "open": [1.0],
            "high": [2.0],
            "low": [0.5],
            "close": [1.5],
            "adj_close": [1.5],
            "volume": [100],
        },
        index=pd.to_datetime(["2024-01-02"]),
    )
    df.index.name = "date"

    dp.save_prices(df, "TEST", prices_dir=prices_dir)
    loaded = dp.load_prices("TEST", prices_dir=prices_dir)

    pd.testing.assert_frame_equal(df, loaded)


def test_db_metadata_upsert_and_last_download_date(tmp_path):
    db_path = tmp_path / "metadata.db"
    conn = dp.init_db(db_path)

    dp.update_metadata(
        conn,
        "TEST",
        last_downloaded="2024-01-02",
        end_date="2024-01-02",
        status="ok",
        row_count=1,
        missing_days=0,
    )

    assert dp.get_last_download_date(conn, "TEST") == "2024-01-02"
    conn.close()


def test_run_pipeline_records_ok_and_failed(tmp_path, monkeypatch):
    db_path = tmp_path / "metadata.db"
    prices_dir = tmp_path / "prices"
    prices_dir.mkdir()

    original_init_db = dp.init_db
    original_save_prices = dp.save_prices
    original_load_prices = dp.load_prices

    def fake_init_db(db_path_arg=None):
        return original_init_db(db_path)

    def fake_save_prices(df, ticker, prices_dir_arg=prices_dir):
        return original_save_prices(df, ticker, prices_dir=prices_dir_arg)

    def fake_load_prices(ticker, prices_dir_arg=prices_dir):
        return original_load_prices(ticker, prices_dir=prices_dir_arg)

    def fake_download_ticker(ticker, start, end):
        if ticker == "GOOD":
            df = pd.DataFrame(
                {
                    "open": [1.0, 2.0],
                    "high": [1.5, 2.5],
                    "low": [0.9, 1.9],
                    "close": [1.4, 2.4],
                    "adj_close": [1.4, 2.4],
                    "volume": [100, 105],
                },
                index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
            )
            df.index.name = "date"
            return df
        return None

    monkeypatch.setattr(dp, "init_db", fake_init_db)
    monkeypatch.setattr(dp, "DB_PATH", db_path)
    monkeypatch.setattr(dp, "save_prices", fake_save_prices)
    monkeypatch.setattr(dp, "load_prices", fake_load_prices)
    monkeypatch.setattr(dp, "download_ticker", fake_download_ticker)

    results = dp.run_pipeline(
        ["GOOD", "BAD"],
        start="2024-01-02",
        end="2024-01-04",
        max_workers=1,
        incremental=False,
        min_rows=1,
    )

    assert results["GOOD"] == "ok"
    assert results["BAD"] == "failed"

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT ticker, status FROM ticker_metadata ORDER BY ticker")
    rows = cursor.fetchall()
    conn.close()

    assert ("GOOD", "ok") in rows
    assert ("BAD", "failed") in rows
