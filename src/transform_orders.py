"""PySpark Silver transformation of raw retail orders."""
import argparse
from pyspark.sql import SparkSession, functions as F, types as T

SCHEMA = T.StructType([
    T.StructField("order_id", T.StringType(), True),
    T.StructField("customer_id", T.StringType(), True),
    T.StructField("product_id", T.StringType(), True),
    T.StructField("order_date", T.StringType(), True),
    T.StructField("quantity", T.IntegerType(), True),
    T.StructField("unit_price", T.DecimalType(12, 2), True),
    T.StructField("status", T.StringType(), True),
])


def clean_orders(df):
    return (df.dropDuplicates(["order_id"])
        .withColumn("order_date", F.to_date("order_date"))
        .filter(F.col("order_id").isNotNull()
                & F.col("customer_id").isNotNull()
                & F.col("order_date").isNotNull()
                & (F.col("quantity") > 0)
                & (F.col("unit_price") >= 0)
                & F.col("status").isin("completed", "cancelled", "returned"))
        .withColumn("gross_amount", F.round(F.col("quantity") * F.col("unit_price"), 2)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/orders.csv")
    parser.add_argument("--output", default="data/silver_orders")
    args = parser.parse_args()
    spark = SparkSession.builder.appName("retail-silver-orders").getOrCreate()
    try:
        raw = spark.read.option("header", True).schema(SCHEMA).csv(args.input)
        silver = clean_orders(raw)
        silver.write.mode("overwrite").parquet(args.output)
        print(f"Silver records: {silver.count()}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
