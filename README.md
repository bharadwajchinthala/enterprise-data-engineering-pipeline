# End-to-End Retail Data Engineering Pipeline

**Status: integrated pipeline built locally; dbt rebuild against PySpark Silver source pending verification.**

A portfolio project using **synthetic retail orders** to demonstrate Python ingestion, PySpark transformations, Parquet storage, Snowflake loading, and dbt models/tests. No employer code or customer data is used.

## Architecture

```text
Python generator
      |
      v
data/orders.csv (raw) ──────────────→ Snowflake RAW.RAW_ORDERS (optional raw archive)
      |
      v
PySpark validation + gross_amount calculation
      |
      v
data/silver_orders/*.parquet
      |
      v
Python Snowflake Silver loader (small demonstration dataset only)
      |
      v
Snowflake RAW.SILVER_ORDERS
      |
      v
dbt stg_orders view → daily_sales table + dbt tests
```

## Local setup (macOS / Linux)

Use **Python 3.11** and **Java 17** for the tested learner setup.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.generate_data --count 1000
python -m pytest -q tests/test_generate_data.py
python -m src.transform_orders
```

## Load Snowflake Silver data

1. Create `RETAIL_PORTFOLIO.RAW` using `sql/setup.sql` and select an appropriately sized, auto-suspending warehouse.
2. Create a local `.env` file (never commit it) with your Snowflake connection settings, including `SNOWFLAKE_AUTHENTICATOR=OAUTH_AUTHORIZATION_CODE` if your account supports browser-based Google sign-in.
3. Run:

```bash
set -a
source .env
set +a
python -m src.load_silver_snowflake
```

For demonstration purposes, the loader handles up to 10,000 rows by collecting them locally and loading `RETAIL_PORTFOLIO.RAW.SILVER_ORDERS`. This is **not** a production-scale bulk ingestion pattern.

The optional `python -m src.load_snowflake` command loads the original CSV separately into `RAW_ORDERS`. The dbt models now read **SILVER_ORDERS**, not RAW_ORDERS.

## Run dbt

Configure `~/.dbt/profiles.yml` with profile name `retail_analytics`, Snowflake credentials/authenticator, database `RETAIL_PORTFOLIO` and output schema `DBT_DEV`.

```bash
dbt debug --project-dir dbt
dbt build --project-dir dbt
```

On some dbt Core v1 installations the optional `dbt-state` plugin triggers a separate account login. The plugin is not needed for this project and can be uninstalled.

Verify model results in Snowflake:

```sql
SELECT COUNT(*) FROM RETAIL_PORTFOLIO.DBT_DEV.STG_ORDERS;
SELECT * FROM RETAIL_PORTFOLIO.DBT_DEV.DAILY_SALES ORDER BY ORDER_DATE LIMIT 10;
```

## Current implementation and limitations

- Deterministic synthetic orders, PySpark filtering and deduplication, calculated `gross_amount`
- Local Parquet Silver layer; Snowflake Silver loader; dbt staging/mart models and source tests
- Validation of the **updated** dbt model against SILVER_ORDERS is still pending
- Planned improvements: end-to-end automation, incremental MERGE, Snowflake stages/COPY INTO for large-scale loading, CI, monitoring and architecture screenshots
- The demo Silver loader replaces records in a dedicated table, not a production target

## Security

Use synthetic data only. Never commit `.env`, passwords, access tokens, or private datasets.
