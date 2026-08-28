from typing import Dict, List
from math import fabs
import json

from ..db import get_connection
from ..config import classify_materiality, map_severity


DEFAULT_AMOUNT_TOLERANCE = 1  # absolute INR tolerance for level 3
DEFAULT_DAYS_TOLERANCE = 5


def score_candidate(payment: Dict, candidate: Dict) -> (int, List[str]):
    score = 0
    reasons = []
    # payment_id exact
    if payment.get("payment_id") and candidate.get("payment_id") and payment["payment_id"] == candidate["payment_id"]:
        score += 50
        reasons.append("payment_id_exact")

    # amount exact
    if payment.get("amount") == candidate.get("gross_amount"):
        score += 20
        reasons.append("amount_exact")
    else:
        # amount within tolerance
        if abs(payment.get("amount", 0) - candidate.get("gross_amount", 0)) <= DEFAULT_AMOUNT_TOLERANCE:
            score += 10
            reasons.append("amount_within_tolerance")

    # order_id match
    if payment.get("order_id") and candidate.get("order_id") and payment["order_id"] == candidate["order_id"]:
        score += 15
        reasons.append("order_id_match")

    # date proximity - candidate settlement_date proximity to payment created_at
    # Both fields are strings; attempt simple numeric day comparison if possible
    try:
        from datetime import datetime

        pdt = datetime.fromisoformat(payment.get("created_at").replace("Z", ""))
        sdt = datetime.fromisoformat(candidate.get("settlement_date").replace("Z", ""))
        delta = abs((pdt - sdt).days)
        if delta <= DEFAULT_DAYS_TOLERANCE:
            score += 10
            reasons.append("date_proximity")
    except Exception:
        pass

    # currency match (assumed INR in prototype)
    if payment.get("currency", "INR") == candidate.get("currency", "INR"):
        score += 5
        reasons.append("currency_match")

    return score, reasons


def run_reconciliation(db_path: str = None) -> Dict:
    conn = get_connection(db_path)

    # Ensure matches and exceptions tables exist
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            payment_id VARCHAR,
            settlement_id VARCHAR,
            match_confidence DOUBLE,
            match_method VARCHAR,
            match_reasons VARCHAR,
            candidate_count INTEGER,
            candidates_json VARCHAR
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS exceptions (
            exception_id VARCHAR,
            payment_id VARCHAR,
            severity VARCHAR,
            materiality VARCHAR,
            exception_type VARCHAR,
            financial_amount BIGINT,
            candidate_matches VARCHAR,
            candidate_details VARCHAR,
            evidence_ids VARCHAR,
            root_cause VARCHAR,
            confidence DOUBLE,
            recommended_action VARCHAR,
            status VARCHAR,
            created_at VARCHAR
        );
        """
    )

    # Clear previous run results to keep results idempotent per run
    conn.execute("DELETE FROM matches;")
    conn.execute("DELETE FROM exceptions;")

    # Load payments into Python for iteration
    payments = conn.execute("SELECT payment_id, order_id, amount, status, created_at FROM payments").fetchall()
    settlements = conn.execute(
        "SELECT settlement_id, payment_id, order_id, settlement_date, gross_amount, net_amount FROM settlements"
    ).fetchall()

    # Convert to list of dicts
    def rows_to_dicts(rows, cols):
        return [dict(zip(cols, r)) for r in rows]

    payments = rows_to_dicts(payments, ["payment_id", "order_id", "amount", "status", "created_at"]) if payments else []
    settlements = rows_to_dicts(settlements, ["settlement_id", "payment_id", "order_id", "settlement_date", "gross_amount", "net_amount"]) if settlements else []

    total = len(payments)
    matched = 0
    exceptions = []

    for p in payments:
        # Level 1 exact identifier match (payment_id in settlements)
        candidate = next((s for s in settlements if s.get("payment_id") == p.get("payment_id")), None)
        if candidate:
            confidence = 1.0
            reasons = ["payment_id_exact"]
            conn.execute(
                "INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?)",
                [p["payment_id"], candidate["settlement_id"], confidence, "level_1_exact", ",".join(reasons), 1],
            )
            matched += 1
            continue

        # Level 2+3: generate candidates from settlements with order_id or amount proximity
        candidates = []
        for s in settlements:
            score, reasons = score_candidate({
                "payment_id": p.get("payment_id"),
                "order_id": p.get("order_id"),
                "amount": p.get("amount"),
                "created_at": p.get("created_at"),
                "currency": "INR",
            }, {
                "payment_id": s.get("payment_id"),
                "order_id": s.get("order_id"),
                "gross_amount": s.get("gross_amount"),
                "settlement_date": s.get("settlement_date"),
                "currency": "INR",
            })
            if score > 0:
                candidates.append((s, score, reasons))

        if not candidates:
            # No candidates -> exception
            exc_id = f"EX_{p.get('payment_id')}"
            materiality = classify_materiality(p.get("amount"))
            severity = map_severity(materiality, 0.0)
            conn.execute(
                "INSERT INTO exceptions (exception_id, payment_id, severity, materiality, exception_type, financial_amount, candidate_matches, evidence_ids, root_cause, confidence, recommended_action, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                [
                    exc_id,
                    p.get("payment_id"),
                    severity,
                    materiality,
                    "no_candidate",
                    p.get("amount"),
                    "0",
                    "",
                    "unknown",
                    0.0,
                    "review",
                    "open",
                ],
            )
            exceptions.append(exc_id)
            continue

        # Rank candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        top = candidates[0]
        top_score = top[1]
        # Normalize: assume max possible score 100
        confidence = min(1.0, top_score / 100.0)
        reasons_text = ";".join(top[2])
        conn.execute(
            "INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?)",
            [p["payment_id"], top[0]["settlement_id"], confidence, "ranked_candidate", reasons_text, len(candidates)],
        )

        # Decide threshold actions and exceptions
        # Determine materiality and severity
        materiality = classify_materiality(p.get("amount"))
        severity = map_severity(materiality, float(confidence))
        if confidence >= 0.95:
            matched += 1
        elif confidence >= 0.80:
            # review required
            exc_id = f"EX_{p.get('payment_id')}"
            conn.execute(
                "INSERT INTO exceptions (exception_id, payment_id, severity, materiality, exception_type, financial_amount, candidate_matches, evidence_ids, root_cause, confidence, recommended_action, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                [
                    exc_id,
                    p.get("payment_id"),
                    severity,
                    materiality,
                    "ambiguous_candidates",
                    p.get("amount"),
                    str(len(candidates)),
                    top[0]["settlement_id"],
                    "ambiguous",
                    float(confidence),
                    "review",
                    "open",
                ],
            )
            exceptions.append(exc_id)
        else:
            exc_id = f"EX_{p.get('payment_id')}"
            conn.execute(
                "INSERT INTO exceptions (exception_id, payment_id, severity, materiality, exception_type, financial_amount, candidate_matches, evidence_ids, root_cause, confidence, recommended_action, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                [
                    exc_id,
                    p.get("payment_id"),
                    severity,
                    materiality,
                    "low_confidence_match",
                    p.get("amount"),
                    str(len(candidates)),
                    top[0]["settlement_id"],
                    "low_confidence",
                    float(confidence),
                    "escalate",
                    "open",
                ],
            )
            exceptions.append(exc_id)

    # commit and summary
    conn.commit()
    summary = {
        "total_payments": total,
        "matched": matched,
        "exceptions": len(exceptions),
    }
    conn.close()
    return summary


if __name__ == "__main__":
    import json
    res = run_reconciliation()
    print(json.dumps(res, indent=2))
