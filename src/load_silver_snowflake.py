"""Load locally cleaned PySpark Parquet orders into a separate Snowflake Silver table.

Learning-scale loader: collects at most 10,000 rows locally and inserts using the
Snowflake Python connector. For large datasets, use stages/COPY INTO instead.
Requires the same environment variables as src.load_snowflake. No credentials
are stored in the repository. Does not touch RAW_ORDERS.
"""
import os
from pathlib import Path


def load_silver(path="data/silver_orders"):
    import snowflake.connector
    from pyspark.sql import SparkSession

    required = (
        "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA",
    )
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    if (os.environ["SNOWFLAKE_DATABASE"].upper(),
        os.environ["SNOWFLAKE_SCHEMA"].upper()) != ("RETAIL_PORTFOLIO", "RAW"):
        raise RuntimeError("This demo loads only into RETAIL_PORTFOLIO.RAW")
    if not Path(path).exists():
        raise FileNotFoundError(f"Parquet directory not found: {path}; run PySpark transformation first")

    spark = SparkSession.builder.appName("retail-parquet-to-snowflake").getOrCreate()
    try:
        df = spark.read.parquet(path).select(
            "order_id", "customer_id", "product_id", "order_date",
            "quantity", "unit_price", "status", "gross_amount"
        )
        # Small learning dataset only: prevent accidental large driver collections.
        sample = df.limit(10001).collect()
        if not sample:
            raise RuntimeError("Silver dataset is empty; refusing to replace table")
        if len(sample) > 10000:
            raise RuntimeError("Demo safety limit: more than 10,000 rows")
        records = [
            (r["order_id"], r["customer_id"], r["product_id"], r["order_date"],
             int(r["quantity"]), r["unit_price"], r["status"], r["gross_amount"])
            for r in sample
        ]
    finally:
        spark.stop()

    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake")
    settings = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "authenticator": authenticator,
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": "RETAIL_PORTFOLIO",
        "schema": "RAW",
        "autocommit": False,
    }
    if authenticator == "snowflake":
        if not os.getenv("SNOWFLAKE_PASSWORD"):
            raise RuntimeError("Set SNOWFLAKE_AUTHENTICATOR for browser sign-in")
        settings["password"] = os.environ["SNOWFLAKE_PASSWORD"]

    conn = snowflake.connector.connect(**settings)
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS SILVER_ORDERS (
                ORDER_ID VARCHAR(50), CUSTOMER_ID VARCHAR(50), PRODUCT_ID VARCHAR(50),
                ORDER_DATE DATE, QUANTITY INTEGER, UNIT_PRICE NUMBER(12,2),
                STATUS VARCHAR(20), GROSS_AMOUNT NUMBER(14,2))""")
            cur.execute("DELETE FROM SILVER_ORDERS")
            cur.executemany(
                """INSERT INTO SILVER_ORDERS (
                   ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE, QUANTITY,
                   UNIT_PRICE, STATUS, GROSS_AMOUNT
                   ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                records,
            )
            cur.execute("SELECT COUNT(*) FROM SILVER_ORDERS")
            loaded = cur.fetchone()[0]
            if loaded != len(records):
                raise RuntimeError(f"Row count mismatch: expected {len(records)}, got {loaded}")
        conn.commit()
        print(f"SUCCESS: Loaded {loaded} PySpark-cleaned orders into RETAIL_PORTFOLIO.RAW.SILVER_ORDERS")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    load_silver()
