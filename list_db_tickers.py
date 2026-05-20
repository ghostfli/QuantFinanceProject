"""
list_db_tickers.py
-----------------
Read the ticker metadata database and print each row.

Usage:
    python list_db_tickers.py
    python list_db_tickers.py --db src/data/db/metadata.db
    python list_db_tickers.py --format table
"""

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.data_pipeline import DB_PATH


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def format_table(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("No rows found.")
        return

    headers = rows[0].keys()
    widths = [max(len(str(row[h])) for row in rows + [dict(zip(headers, headers))]) for h in headers]
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in widths)

    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(str(row[h]).ljust(widths[i]) for i, h in enumerate(headers)))


def format_csv(rows: list[sqlite3.Row]) -> None:
    import csv

    writer = csv.writer(sys.stdout)
    if not rows:
        return
    writer.writerow(rows[0].keys())
    for row in rows:
        writer.writerow([row[h] for h in row.keys()])


def main() -> None:
    parser = argparse.ArgumentParser(description="List ticker metadata rows from SQLite database")
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Path to SQLite metadata database",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv"],
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug diagnostics about the database and query",
    )
    args = parser.parse_args()

    db_path = args.db
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    if args.debug:
        print("DEBUG: reading database")
        print(f"DEBUG: db_path={db_path}")

    conn = get_connection(db_path)
    try:
        if args.debug:
            print("DEBUG: executing query: SELECT * FROM ticker_metadata ORDER BY ticker")
        cursor = conn.execute("SELECT * FROM ticker_metadata ORDER BY ticker")
        rows = cursor.fetchall()
        if args.debug:
            print(f"DEBUG: fetched {len(rows)} rows")
            print(f"DEBUG: columns={[col[0] for col in cursor.description]}")
    finally:
        conn.close()

    if args.format == "csv":
        format_csv(rows)
    else:
        format_table(rows)


if __name__ == "__main__":
    main()
