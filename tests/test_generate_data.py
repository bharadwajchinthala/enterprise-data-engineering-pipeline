import csv
import pytest
from src.generate_data import generate_orders


def test_rows_are_reproducible(tmp_path):
    a = generate_orders(tmp_path / "a.csv", count=12)
    b = generate_orders(tmp_path / "b.csv", count=12)
    assert a.read_bytes() == b.read_bytes()
    with a.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 12
    assert len({row["order_id"] for row in rows}) == 12


def test_rejects_nonpositive_count(tmp_path):
    with pytest.raises(ValueError):
        generate_orders(tmp_path / "x.csv", count=0)
