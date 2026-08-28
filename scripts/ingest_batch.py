"""Script to ingest CSVs from a data directory into the DuckDB database."""
import sys
import os
import argparse

# Ensure project root on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.services.ingest import ingest_csvs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default="data/generated")
    parser.add_argument("--db", type=str, default=None)
    args = parser.parse_args()

    report = ingest_csvs(args.data_dir, args.db)
    print("Ingestion report:")
    for k, v in report.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
