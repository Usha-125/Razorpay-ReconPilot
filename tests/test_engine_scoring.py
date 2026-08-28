from backend.reconciliation.engine import score_candidate


def test_score_payment_id_exact():
    p = {"payment_id": "P1", "order_id": "O1", "amount": 1000, "created_at": "2020-01-01T00:00:00Z", "currency": "INR"}
    c = {"payment_id": "P1", "order_id": "O1", "gross_amount": 1000, "settlement_date": "2020-01-01T00:00:00Z", "currency": "INR"}
    score, reasons = score_candidate(p, c)
    assert score >= 50
    assert "payment_id_exact" in reasons
    assert "amount_exact" in reasons


def test_score_amount_within_tolerance():
    p = {"payment_id": "P2", "order_id": "O2", "amount": 1000, "created_at": "2020-01-01T00:00:00Z", "currency": "INR"}
    c = {"payment_id": "X", "order_id": "O2", "gross_amount": 1001, "settlement_date": "2020-01-02T00:00:00Z", "currency": "INR"}
    score, reasons = score_candidate(p, c)
    assert ("amount_within_tolerance" in reasons) or ("amount_exact" in reasons)


def test_date_proximity_and_order():
    p = {"payment_id": "P3", "order_id": "O3", "amount": 500, "created_at": "2020-01-10T00:00:00Z", "currency": "INR"}
    c = {"payment_id": "Y", "order_id": "O3", "gross_amount": 500, "settlement_date": "2020-01-12T00:00:00Z", "currency": "INR"}
    score, reasons = score_candidate(p, c)
    assert "order_id_match" in reasons
    assert "date_proximity" in reasons
