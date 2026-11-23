# End-to-End Retail Data Engineering Pipeline

[![Python and PySpark CI](https://github.com/bharadwajchinthala/enterprise-data-engineering-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/bharadwajchinthala/enterprise-data-engineering-pipeline/actions/workflows/ci.yml)

**Status: validated local end-to-end execution and passing GitHub Actions Python/PySpark CI.**

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

## Run the full pipeline

Once Snowflake is configured and the virtual environment is active, run all five local stages together:

```bash
set -a
source .env
set +a
python -m src.run_pipeline
```

This runs synthetic data generation, Python unit tests, PySpark cleaning, the Snowflake Silver loader, and dbt models/tests in order. It fails fast on errors. **Observed local run:** 5/5 stages passed in **25.1 seconds** for 1,000 synthetic orders; timing depends on local hardware and Snowflake authentication.

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

## Verified sample results

Results from a completed local run and Snowflake verification query using **1,000 synthetic orders**:

| Metric | Value |
| --- | ---: |
| Silver orders | 1,000 |
| dbt staging orders | 1,000 |
| Completed orders | 566 |
| Completed gross revenue | $412,491.12 |
| dbt build operations | 8/8 passed (2 models + 6 tests) |

The [Python and PySpark CI workflow](.github/workflows/ci.yml) also passed on GitHub Actions (first run: 43 seconds). CI uses Python 3.11 and Java 17; it intentionally does **not** connect to a live Snowflake account.

## Current implementation and limitations

- Deterministic synthetic orders, PySpark filtering and deduplication, calculated `gross_amount`
- Local Parquet Silver layer; Snowflake Silver loader; dbt staging/mart models and source tests
- Updated dbt model against SILVER_ORDERS was built successfully and cross-checked in Snowflake
- A one-command **local** orchestrator exists; it is not a scheduler and does not imply unattended cloud deployment
- Planned improvements: incremental MERGE, Snowflake stages/COPY INTO for large-scale loading, monitoring, and architecture screenshots
- The demo Silver loader replaces records in a dedicated table, not a production target

## Security

Use synthetic data only. Never commit `.env`, passwords, access tokens, or private datasets.
