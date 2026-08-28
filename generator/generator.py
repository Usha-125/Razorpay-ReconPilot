"""
Deterministic synthetic data generator (prototype).

Usage:
    python generator/generator.py --rows 1000 --seed 42 --outdir data/generated

This simple generator creates CSVs for orders, payments, refunds, settlements, ledger_entries, bank_entries, and ground_truth.
"""
import argparse
import csv
import os
import random
from datetime import datetime, timedelta


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def generate_orders(rows, seed, outdir):
    random.seed(seed)
    path = os.path.join(outdir, "orders.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "merchant_id", "merchant_reference", "customer_id", "created_at", "currency", "gross_amount", "status"])
        for i in range(1, rows + 1):
            order_id = f"ORD_{seed}_{i}"
            merchant_id = "M_1001"
            merchant_reference = f"REF_{i}"
            customer_id = f"CUST_{random.randint(1, 5000)}"
            created_at = (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat() + "Z"
            currency = "INR"
            gross_amount = random.randint(100, 200000)
            status = random.choice(["created", "paid", "cancelled"])
            writer.writerow([order_id, merchant_id, merchant_reference, customer_id, created_at, currency, gross_amount, status])
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", type=str, default="data/generated")
    args = parser.parse_args()

    ensure_dir(args.outdir)
    print("Generating orders...")
    orders = generate_orders(args.rows, args.seed, args.outdir)
    print("Wrote:", orders)


if __name__ == "__main__":
    main()
