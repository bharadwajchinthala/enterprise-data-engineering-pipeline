"""Generate deterministic synthetic retail orders without sensitive records."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

FIELDS = ["order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price", "status"]
STATUSES = ["completed", "completed", "completed", "cancelled", "returned"]


def generate_orders(output_path: str | Path, count: int = 1000, seed: int = 42) -> Path:
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for i in range(1, count + 1):
            writer.writerow({
                "order_id": f"ORD{i:06d}",
                "customer_id": f"CUST{rng.randint(1, 200):04d}",
                "product_id": f"SKU{rng.randint(1, 50):03d}",
                "order_date": (date(2026, 1, 1) + timedelta(days=rng.randint(0, 89))).isoformat(),
                "quantity": rng.randint(1, 5),
                "unit_price": f"{rng.uniform(5, 500):.2f}",
                "status": rng.choice(STATUSES),
            })
    return path


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", default="data/orders.csv")
    p.add_argument("--count", type=int, default=1000)
    args = p.parse_args()
    print(generate_orders(args.output, args.count))
