import os
try:
    import duckdb
except Exception as e:
    raise ImportError(
        "DuckDB is required for database operations. Please install requirements: `pip install -r backend/requirements.txt`.\n"
        f"Original error: {e}"
    )


def get_connection(db_path=None):
    if db_path is None:
        db_path = os.environ.get("DATABASE_PATH", "data/reconpilot.duckdb")
    conn = duckdb.connect(database=db_path, read_only=False)
    return conn


def init_schema(conn):
    # Create minimal tables for Phase 1 ingestion
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id VARCHAR,
            merchant_id VARCHAR,
            merchant_reference VARCHAR,
            customer_id VARCHAR,
            created_at VARCHAR,
            currency VARCHAR,
            gross_amount BIGINT,
            status VARCHAR
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id VARCHAR,
            order_id VARCHAR,
            customer_id VARCHAR,
            amount BIGINT,
            currency VARCHAR,
            method VARCHAR,
            status VARCHAR,
            captured_at VARCHAR,
            created_at VARCHAR
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS refunds (
            refund_id VARCHAR,
            payment_id VARCHAR,
            order_id VARCHAR,
            amount BIGINT,
            currency VARCHAR,
            status VARCHAR,
            created_at VARCHAR,
            processed_at VARCHAR,
            reason VARCHAR
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settlements (
            settlement_id VARCHAR,
            payment_id VARCHAR,
            order_id VARCHAR,
            settlement_date VARCHAR,
            gross_amount BIGINT,
            fee BIGINT,
            tax BIGINT,
            adjustment BIGINT,
            net_amount BIGINT,
            status VARCHAR
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS merchant_ledger (
            journal_entry_id VARCHAR,
            merchant_id VARCHAR,
            reference_id VARCHAR,
            entry_date VARCHAR,
            account VARCHAR,
            debit BIGINT,
            credit BIGINT,
            description VARCHAR,
            currency VARCHAR
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bank_entries (
            bank_entry_id VARCHAR,
            utr VARCHAR,
            merchant_id VARCHAR,
            value_date VARCHAR,
            amount BIGINT,
            currency VARCHAR,
            description VARCHAR,
            reference VARCHAR
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ground_truth (
            record_id VARCHAR,
            true_match_id VARCHAR,
            exception_type VARCHAR,
            root_cause VARCHAR,
            expected_resolution VARCHAR,
            true_cash_impact BIGINT,
            ground_truth_status VARCHAR
        );
        """
    )
