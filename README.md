# End-to-End Retail Data Engineering Pipeline

**Status: starter implementation — Snowflake/dbt integration has not yet been validated.**

A reproducible, synthetic retail data project demonstrating batch ingestion, PySpark data cleaning, Snowflake loading, and dbt analytics modeling. No employer data is used.

## Architecture

```text
Synthetic retail orders CSV
        |              \
        v               v
Python generator     PySpark transformation → local Parquet (Silver)
        |
        v
Snowflake RAW.RAW_ORDERS → dbt staging model → dbt daily_sales mart
```

The PySpark Silver path and Snowflake/dbt path are parallel demonstrations. The Snowflake loader currently loads the raw CSV, **not** the Parquet output. Integrating the paths and introducing incremental loading are planned enhancements.

## Quick start (Mac/Linux)

1. Install Python 3.11+ and Java 17 (required for local Spark); install Git.
2. Create an environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install: `pip install -r requirements.txt`
4. Generate data: `python -m src.generate_data --count 1000`
5. Run Spark: `python -m src.transform_orders`
6. Test: `python -m pytest -q`

## Snowflake / dbt (optional next stage)

1. Create a warehouse and run the statements in `sql/setup.sql` in your Snowflake account.
2. Copy `.env.example` to `.env` and fill in your own account details. **Never commit `.env`.** Export the variables into the shell before running the loader (for example, `set -a; source .env; set +a` only for trusted local files).
3. Load synthetic raw orders: `python -m src.load_snowflake`.
4. Configure `~/.dbt/profiles.yml` with a `retail_analytics` profile and connection to the same Snowflake warehouse. Use a suitable target schema for dbt output.
5. Run `cd dbt && dbt debug && dbt build`.

Note: `load_snowflake.py` truncates and reloads the demo RAW_ORDERS table. Do not point it at any shared or production table.

## Current scope vs. roadmap

**Implemented in source:** deterministic synthetic data generator, local PySpark cleaning, Snowflake CSV loader, dbt staging/mart models, and basic tests.

**Planned:** validate end-to-end in Snowflake, add dbt profile example, integrate PySpark output into the warehouse path, incremental ingestion with MERGE, orchestration, CI, monitoring and a documented results screenshot.

## Security

Use only synthetic data. Keep credentials in environment variables. Never commit keys, tokens, account passwords or employer records.
