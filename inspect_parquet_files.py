"""
inspect_parquet_files.py
------------------------
Inspect Parquet files saved by the pipeline.

Usage:
    python inspect_parquet_files.py
    python inspect_parquet_files.py --summary
    python inspect_parquet_files.py --ticker AAPL
    python inspect_parquet_files.py --path data/prices --limit 20
"""

import argparse
from pathlib import Path
import pandas as pd


def inspect_file(path: Path, show_rows: int = 5) -> None:
    print(f"\nInspecting: {path.name}")
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        print(f"ERROR: failed to read {path}: {exc}")
        return

    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    if df.index.name is not None:
        print(f"Index name: {df.index.name}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print("\nHead:")
    print(df.head(show_rows).to_string())
    print("\nTail:")
    print(df.tail(show_rows).to_string())


def summarize_files(files: list[Path]) -> None:
    print(f"Found {len(files)} parquet files")
    if not files:
        return

    print("\nFirst 10 files:")
    for path in sorted(files)[:10]:
        size = path.stat().st_size
        print(f"- {path.name} ({size:,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Parquet price files saved by the pipeline")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("data") / "prices",
        help="Directory containing Parquet price files",
    )
    parser.add_argument(
        "--ticker",
        help="Inspect a specific ticker's Parquet file",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary of available Parquet files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of file summaries to show when not inspecting a specific ticker",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=5,
        help="Rows to show for head/tail when inspecting a file",
    )
    args = parser.parse_args()

    if not args.path.exists():
        raise SystemExit(f"Path not found: {args.path}")
    if not args.path.is_dir():
        raise SystemExit(f"Path is not a directory: {args.path}")

    files = sorted(args.path.glob("*.parquet"))
    if args.ticker:
        file_path = args.path / f"{args.ticker}.parquet"
        if not file_path.exists():
            raise SystemExit(f"Parquet file not found for ticker: {args.ticker}")
        inspect_file(file_path, show_rows=args.rows)
        return

    if args.summary:
        summarize_files(files)
        return

    summarize_files(files)
    print("\nInspecting first file:")
    if files:
        inspect_file(files[0], show_rows=args.rows)


if __name__ == "__main__":
    main()
