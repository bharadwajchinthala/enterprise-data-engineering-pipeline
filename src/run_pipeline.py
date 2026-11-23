"""Run the local synthetic-retail pipeline in dependency order.

Usage (from repository root, with the venv active):
    set -a; source .env; set +a
    python -m src.run_pipeline

This is a repeatable local demo, not a scheduler or production orchestrator.
The Silver demo loader replaces only RETAIL_PORTFOLIO.RAW.SILVER_ORDERS.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def run_step(label: str, command: list[str]) -> None:
    print(f"\n{'=' * 64}", flush=True)
    print(f"START: {label}", flush=True)
    print("Command:", " ".join(command), flush=True)
    started = time.monotonic()
    # check=True stops the pipeline immediately if any stage fails.
    subprocess.run(command, cwd=ROOT, env=os.environ.copy(), check=True)
    print(f"SUCCESS: {label} ({time.monotonic() - started:.1f}s)", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local retail data pipeline")
    parser.add_argument("--count", type=int, default=1000,
                        help="Number of synthetic orders (default 1000; max 10000)")
    args = parser.parse_args()
    if not 1 <= args.count <= 10000:
        parser.error("--count must be between 1 and 10000")

    required = (
        "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA",
    )
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print("ERROR: Missing Snowflake settings: " + ", ".join(missing), file=sys.stderr)
        print("From the project folder run: set -a; source .env; set +a", file=sys.stderr)
        return 2
    if not shutil.which("java"):
        print("ERROR: Java is missing from PATH (Spark requires Java 17).", file=sys.stderr)
        return 2
    dbt = shutil.which("dbt")
    if not dbt:
        print("ERROR: dbt command not found. Activate .venv first.", file=sys.stderr)
        return 2

    steps = [
        ("Generate synthetic retail orders",
         [sys.executable, "-m", "src.generate_data", "--count", str(args.count)]),
        ("Validate generator with pytest",
         [sys.executable, "-m", "pytest", "-q", "tests/test_generate_data.py"]),
        ("Transform CSV into Silver Parquet with PySpark",
         [sys.executable, "-m", "src.transform_orders"]),
        ("Load cleaned Silver orders to Snowflake",
         [sys.executable, "-m", "src.load_silver_snowflake"]),
        ("Build dbt models and run data-quality tests",
         [dbt, "build", "--project-dir", "dbt"]),
    ]
    started = time.monotonic()
    for label, command in steps:
        try:
            run_step(label, command)
        except subprocess.CalledProcessError as exc:
            print(f"\nPIPELINE FAILED during '{label}' (exit code {exc.returncode}).",
                  file=sys.stderr, flush=True)
            return exc.returncode or 1
        except KeyboardInterrupt:
            print("\nPIPELINE INTERRUPTED by user.", file=sys.stderr, flush=True)
            return 130

    print(f"\nPIPELINE SUCCESS: All {len(steps)} stages passed in "
          f"{time.monotonic() - started:.1f}s.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
