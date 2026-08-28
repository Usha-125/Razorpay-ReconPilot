import os
from typing import Dict

from ..db import get_connection, init_schema


def ingest_csvs(data_dir: str, db_path: str = None) -> Dict:
    """Ingest expected CSV files into DuckDB and return an ingestion report.

    This function is conservative: missing files are reported but do not abort ingestion.
    """
    conn = get_connection(db_path)
    init_schema(conn)

    files = {
        "orders": "orders.csv",
        "payments": "payments.csv",
        "refunds": "refunds.csv",
        "settlements": "settlements.csv",
        "merchant_ledger": "merchant_ledger.csv",
        "bank_entries": "bank_entries.csv",
        "ground_truth": "ground_truth.csv",
    }

    report = {"loaded": {}, "missing": [], "errors": []}

    for table, fname in files.items():
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            report["missing"].append(fname)
            continue
        try:
            # Use DuckDB's read_csv_auto to import with basic type inference
            conn.execute(f"COPY {table} FROM '{path}' (AUTO_DETECT TRUE, HEADER TRUE);")
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            report["loaded"][table] = int(count)
        except Exception as e:
            report["errors"].append({"file": fname, "error": str(e)})

    conn.close()
    return report
