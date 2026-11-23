"""Load synthetic retail CSV into the dedicated Snowflake portfolio RAW_ORDERS table.

Supports browser/Google SSO via SNOWFLAKE_AUTHENTICATOR=OAUTH_AUTHORIZATION_CODE.
For this learning demo, existing RAW_ORDERS rows are replaced on each run.
This script never accesses employer data. Do not commit .env or credentials.
"""
import csv
import os
from pathlib import Path


REQUIRED = (
    "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA",
)


def load_csv(path="data/orders.csv"):
    import snowflake.connector

    missing = [key for key in REQUIRED if not os.getenv(key)]
    if missing:
        raise RuntimeError("Missing Snowflake environment variables: " + ", ".join(missing))

    # The demo loader deliberately refuses to run outside its isolated project.
    if (os.environ["SNOWFLAKE_DATABASE"].upper(), os.environ["SNOWFLAKE_SCHEMA"].upper()) != ("RETAIL_PORTFOLIO", "RAW"):
        raise RuntimeError("Refusing to load outside RETAIL_PORTFOLIO.RAW")

    auth = os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake")
    options = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "authenticator": auth,
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ["SNOWFLAKE_SCHEMA"],
    }
    if auth == "snowflake":
        password = os.getenv("SNOWFLAKE_PASSWORD")
        if not password:
            raise RuntimeError("Password authentication requires SNOWFLAKE_PASSWORD; Google sign-in users should set SNOWFLAKE_AUTHENTICATOR=OAUTH_AUTHORIZATION_CODE")
        options["password"] = password

    with Path(path).open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise RuntimeError("CSV has no data rows; refusing to replace Snowflake table")

    records = [
        (r["order_id"], r["customer_id"], r["product_id"], r["order_date"],
         int(r["quantity"]), r["unit_price"], r["status"])
        for r in rows
    ]

    conn = snowflake.connector.connect(**options)
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS RAW_ORDERS (
                ORDER_ID VARCHAR, CUSTOMER_ID VARCHAR, PRODUCT_ID VARCHAR,
                ORDER_DATE DATE, QUANTITY INTEGER, UNIT_PRICE NUMBER(12,2),
                STATUS VARCHAR)""")
            # Transactional DELETE rather than TRUNCATE: inserts can roll back
            # if something fails, preserving the previously loaded dataset.
            cur.execute("DELETE FROM RAW_ORDERS")
            cur.executemany(
                """INSERT INTO RAW_ORDERS
                (ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE, QUANTITY, UNIT_PRICE, STATUS)
                VALUES (%s, %s, %s, TO_DATE(%s), %s, %s, %s)""",
                records,
            )
            cur.execute("SELECT COUNT(*) FROM RAW_ORDERS")
            actual = cur.fetchone()[0]
            if actual != len(records):
                raise RuntimeError(f"Row count mismatch: expected {len(records)}, got {actual}")
        conn.commit()
        print(f"SUCCESS: Loaded {actual} synthetic orders into RETAIL_PORTFOLIO.RAW.RAW_ORDERS")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    load_csv()
