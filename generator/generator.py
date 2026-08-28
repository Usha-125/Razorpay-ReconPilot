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


def iso(dt):
    return dt.isoformat() + "Z"


def generate_orders(n_orders, seed, outdir):
    random.seed(seed)
    path = os.path.join(outdir, "orders.csv")
    orders = []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "merchant_id", "merchant_reference", "customer_id", "created_at", "currency", "gross_amount", "status"])
        for i in range(1, n_orders + 1):
            order_id = f"ORD_{seed}_{i}"
            merchant_id = "M_1001"
            merchant_reference = f"REF_{i}"
            customer_id = f"CUST_{random.randint(1, 50000)}"
            created_at = iso(datetime.utcnow() - timedelta(days=random.randint(0, 30)))
            currency = "INR"
            gross_amount = random.randint(100, 200000)
            status = random.choices(["created", "paid", "cancelled"], weights=[5, 90, 5])[0]
            writer.writerow([order_id, merchant_id, merchant_reference, customer_id, created_at, currency, gross_amount, status])
            orders.append({"order_id": order_id, "amount": gross_amount, "status": status})
    return orders, path


def generate_payments(orders, seed, outdir, capture_rate=0.9):
    random.seed(seed + 1)
    path = os.path.join(outdir, "payments.csv")
    payments = []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["payment_id", "order_id", "customer_id", "amount", "currency", "method", "status", "captured_at", "created_at"])
        i = 1
        for o in orders:
            if o["status"] != "paid":
                continue
            if random.random() > capture_rate:
                status = "failed"
            else:
                status = "captured"
            payment_id = f"PAY_{seed}_{i}"
            created_at = iso(datetime.utcnow() - timedelta(days=random.randint(0, 30)))
            captured_at = created_at if status == "captured" else ""
            amount = o["amount"]
            method = random.choice(["card", "netbanking", "upi", "wallet"])
            customer_id = f"CUST_{random.randint(1, 50000)}"
            writer.writerow([payment_id, o["order_id"], customer_id, amount, "INR", method, status, captured_at, created_at])
            payments.append({"payment_id": payment_id, "order_id": o["order_id"], "amount": amount, "status": status})
            i += 1
    return payments, path


def generate_refunds(payments, seed, outdir, refund_rate=0.05):
    random.seed(seed + 2)
    path = os.path.join(outdir, "refunds.csv")
    refunds = []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["refund_id", "payment_id", "order_id", "amount", "currency", "status", "created_at", "processed_at", "reason"])
        i = 1
        for p in payments:
            if p["status"] != "captured":
                continue
            if random.random() < refund_rate:
                refund_amount = int(p["amount"] * random.choice([0.5, 1.0]))
                refund_id = f"REFN_{seed}_{i}"
                created_at = iso(datetime.utcnow() - timedelta(days=random.randint(0, 30)))
                processed_at = iso(datetime.utcnow() - timedelta(days=random.randint(0, 30)))
                reason = random.choice(["requested_by_customer", "fraud", "other"])
                status = random.choice(["processed", "pending"])
                writer.writerow([refund_id, p["payment_id"], p["order_id"], refund_amount, "INR", status, created_at, processed_at, reason])
                refunds.append({"refund_id": refund_id, "payment_id": p["payment_id"], "amount": refund_amount})
                i += 1
    return refunds, path


def generate_settlements(payments, seed, outdir, payments_per_settlement=20):
    random.seed(seed + 3)
    path = os.path.join(outdir, "settlements.csv")
    settlements = []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["settlement_id", "payment_id", "order_id", "settlement_date", "gross_amount", "fee", "tax", "adjustment", "net_amount", "status"])
        s = 1
        idx = 0
        captured = [p for p in payments if p["status"] == "captured"]
        while idx < len(captured):
            batch = captured[idx: idx + payments_per_settlement]
            gross = sum(p["amount"] for p in batch)
            fee = int(gross * 0.02)  # 2% fee
            tax = int(fee * 0.18)
            adjustment = 0
            net = gross - fee - tax + adjustment
            settlement_date = iso(datetime.utcnow() - timedelta(days=random.randint(0, 5)))
            settlement_id = f"SET_{seed}_{s}"
            for p in batch:
                writer.writerow([settlement_id, p["payment_id"], p["order_id"], settlement_date, p["amount"], int(p["amount"] * 0.02), int(p["amount"] * 0.02 * 0.18), 0, int(p["amount"] - (p["amount"] * 0.02) - int(p["amount"] * 0.02 * 0.18)), "settled"])
            settlements.append({"settlement_id": settlement_id, "payment_ids": [p["payment_id"] for p in batch], "gross": gross, "net": net})
            s += 1
            idx += payments_per_settlement
    return settlements, path


def generate_ledger_entries(payments, settlements, seed, outdir):
    random.seed(seed + 4)
    path = os.path.join(outdir, "merchant_ledger.csv")
    entries = []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["journal_entry_id", "merchant_id", "reference_id", "entry_date", "account", "debit", "credit", "description", "currency"])
        i = 1
        for p in payments:
            je = f"JE_PAY_{seed}_{i}"
            entry_date = iso(datetime.utcnow() - timedelta(days=random.randint(0, 30)))
            writer.writerow([je, "M_1001", p["payment_id"], entry_date, "cash", p["amount"], 0, "payment recorded", "INR"])
            entries.append({"journal_entry_id": je, "reference_id": p["payment_id"], "amount": p["amount"]})
            i += 1
        for s in settlements:
            je = f"JE_SET_{seed}_{i}"
            entry_date = iso(datetime.utcnow() - timedelta(days=random.randint(0, 5)))
            writer.writerow([je, "M_1001", s["settlement_id"], entry_date, "bank", 0, s["net"], "settlement credited", "INR"])
            entries.append({"journal_entry_id": je, "reference_id": s["settlement_id"], "amount": s["net"]})
            i += 1
    return entries, path


def generate_bank_entries(settlements, seed, outdir):
    random.seed(seed + 5)
    path = os.path.join(outdir, "bank_entries.csv")
    entries = []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bank_entry_id", "utr", "merchant_id", "value_date", "amount", "currency", "description", "reference"])
        i = 1
        for s in settlements:
            be = f"BANK_{seed}_{i}"
            utr = f"UTR{seed}{i:06d}"
            value_date = iso(datetime.utcnow() - timedelta(days=random.randint(0, 5)))
            writer.writerow([be, utr, "M_1001", value_date, s["net"], "INR", "settlement credit", s["settlement_id"]])
            entries.append({"bank_entry_id": be, "settlement_id": s["settlement_id"], "amount": s["net"]})
            i += 1
    return entries, path


def inject_exceptions(payments, refunds, settlements, ledger_entries, bank_entries, seed, outdir, anomaly_fraction=0.01):
    random.seed(seed + 6)
    path = os.path.join(outdir, "ground_truth.csv")
    anomalies = []
    types = [
        "exact_match",
        "fee_variance",
        "tax_variance",
        "refund_timing_difference",
        "partial_settlement",
        "duplicate_transaction",
        "missing_settlement",
        "missing_ledger_entry",
        "wrong_mapping",
        "unexpected_adjustment",
        "delayed_settlement",
        "unexplained_anomaly",
    ]
    total_candidates = max(1, int(len(payments) * anomaly_fraction))
    chosen = random.sample(payments, total_candidates) if payments else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "true_match_id", "exception_type", "root_cause", "expected_resolution", "true_cash_impact", "ground_truth_status"])
        for p in chosen:
            ex = random.choice(types[1:])
            record_id = p["payment_id"]
            true_match_id = ""  # vary by type
            cash_impact = p["amount"] if ex in ["missing_settlement", "unexplained_anomaly"] else int(p["amount"] * 0.5)
            expected_resolution = random.choice(["HUMAN_REVIEW", "AUTO_RESOLVE", "MONITOR"])
            writer.writerow([record_id, true_match_id, ex, ex, expected_resolution, cash_impact, "injected"])
            anomalies.append({"record_id": record_id, "type": ex, "cash_impact": cash_impact})
    return anomalies, path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", type=str, default="data/generated")
    parser.add_argument("--anomaly-fraction", type=float, default=0.01)
    args = parser.parse_args()

    ensure_dir(args.outdir)
    print("Generating orders...")
    orders, orders_path = generate_orders(args.orders, args.seed, args.outdir)
    print("Wrote:", orders_path)

    print("Generating payments...")
    payments, payments_path = generate_payments(orders, args.seed, args.outdir)
    print("Wrote:", payments_path)

    print("Generating refunds...")
    refunds, refunds_path = generate_refunds(payments, args.seed, args.outdir)
    print("Wrote:", refunds_path)

    print("Generating settlements...")
    settlements, settlements_path = generate_settlements(payments, args.seed, args.outdir)
    print("Wrote:", settlements_path)

    print("Generating ledger entries...")
    ledger_entries, ledger_path = generate_ledger_entries(payments, settlements, args.seed, args.outdir)
    print("Wrote:", ledger_path)

    print("Generating bank entries...")
    bank_entries, bank_path = generate_bank_entries(settlements, args.seed, args.outdir)
    print("Wrote:", bank_path)

    print("Injecting anomalies and ground truth...")
    anomalies, gt_path = inject_exceptions(payments, refunds, settlements, ledger_entries, bank_entries, args.seed, args.outdir, args.anomaly_fraction)
    print("Wrote:", gt_path)

    print("Generation complete. Summary:")
    print(f"orders: {len(orders)} payments: {len(payments)} refunds: {len(refunds)} settlements: {len(settlements)} anomalies: {len(anomalies)}")


if __name__ == "__main__":
    main()
