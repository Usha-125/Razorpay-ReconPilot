"""Run the deterministic reconciliation engine and print a summary."""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.reconciliation.engine import run_reconciliation


def main():
    res = run_reconciliation()
    print("Reconciliation summary:")
    for k, v in res.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
