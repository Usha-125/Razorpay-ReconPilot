"""Lightweight mock ingestion that doesn't require DuckDB.

It reads CSV files from the data directory and returns a simple report similar
to the real ingestion service. Useful as a fallback when dependencies can't be installed.
"""
import os
import csv
from typing import Dict


def mock_ingest(data_dir: str) -> Dict:
    files = [
        "orders.csv",
        "payments.csv",
        "refunds.csv",
        "settlements.csv",
        "merchant_ledger.csv",
        "bank_entries.csv",
        "ground_truth.csv",
    ]
    report = {"loaded": {}, "missing": [], "errors": []}
    for fname in files:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            report["missing"].append(fname)
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                # Count rows excluding header
                cnt = sum(1 for _ in reader) - 1
                report["loaded"][os.path.splitext(fname)[0]] = max(0, cnt)
        except Exception as e:
            report["errors"].append({"file": fname, "error": str(e)})
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default="data/generated")
    args = parser.parse_args()
    r = mock_ingest(args.data_dir)
    print("Mock ingestion report:")
    for k, v in r.items():
        print(f"{k}: {v}")
