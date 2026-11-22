import pytest

@pytest.fixture(scope="module")
def spark():
    pyspark = pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession
    try:
        session = SparkSession.builder.master("local[1]").appName("orders-test").getOrCreate()
    except Exception as exc:
        pytest.skip(f"Local Spark runtime unavailable: {exc}")
    yield session
    session.stop()


def test_clean_orders_filters_invalid_rows(spark):
    from src.transform_orders import clean_orders, SCHEMA
    rows = [
        ("A", "C1", "P1", "2026-01-01", 2, __import__("decimal").Decimal("10.00"), "completed"),
        ("B", "C2", "P2", "2026-01-01", 0, __import__("decimal").Decimal("15.00"), "completed"),
    ]
    result = clean_orders(spark.createDataFrame(rows, SCHEMA)).collect()
    assert len(result) == 1
    assert str(result[0].gross_amount) == "20.00"
