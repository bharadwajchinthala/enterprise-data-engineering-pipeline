"""Load generated CSV into Snowflake RAW_ORDERS using environment variables.

Note: this is a simple demo loader; production loads should use staged COPY INTO
and idempotent merges. Do not upload .env files or credentials.
"""
import csv
import os
from pathlib import Path


def load_csv(path="data/orders.csv"):
    import snowflake.connector
    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
                "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError("Missing Snowflake environment variables: " + ", ".join(missing))
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS RAW_ORDERS (
                ORDER_ID VARCHAR, CUSTOMER_ID VARCHAR, PRODUCT_ID VARCHAR,
                ORDER_DATE DATE, QUANTITY INTEGER, UNIT_PRICE NUMBER(12,2), STATUS VARCHAR)""")
            with Path(path).open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            # Demo idempotency: replace the entire synthetic dataset on each run.
            cur.execute("TRUNCATE TABLE RAW_ORDERS")
            cur.executemany(
                "INSERT INTO RAW_ORDERS (ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE, QUANTITY, UNIT_PRICE, STATUS) VALUES (%s, %s, %s, TO_DATE(%s), %s, %s, %s)",
                [(r["order_id"], r["customer_id"], r["product_id"], r["order_date"], int(r["quantity"]), r["unit_price"], r["status"]) for r in rows],
            )
        conn.commit()
        print(f"Loaded {len(rows)} synthetic orders into RAW_ORDERS")
    finally:
        conn.close()


if __name__ == "__main__":
    load_csv()
