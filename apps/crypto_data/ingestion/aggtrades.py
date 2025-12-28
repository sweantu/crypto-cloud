import argparse
import logging
import os

# import sys
# from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, types
from pyspark.sql import functions as F
from shared_lib.file import download_file, extract_file, remove_file
from shared_lib.s3 import upload_to_s3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# args = getResolvedOptions(
#     sys.argv,
#     [
#         "symbol",
#         "landing_date",
#         "transform_db",
#         "data_lake_bucket",
#         "iceberg_lock_table",
#     ],
# )

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", required=True)
parser.add_argument("--landing_date", required=True)
parser.add_argument("--transform_db", required=True)
parser.add_argument("--data_lake_bucket", required=True)
parser.add_argument("--iceberg_lock_table", required=True)
args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]

TRANSFORM_DB = args["transform_db"]
DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]


script_dir = "/tmp/data/raw"
extract_dir = os.path.join(script_dir, "unzipped_data")
url = f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
zip_path = os.path.join(script_dir, url.split("/")[-1])

download_file(url, zip_path)
csv_path = extract_file(extract_dir, zip_path)


spark = (
    SparkSession.builder.appName("Landing Job")  # type: ignore
    .config("spark.sql.session.timeZone", "UTC")
    # local mode optimizations to reduce memory consumption
    .config("spark.sql.parquet.enableVectorizedReader", "false")
    .config("spark.sql.columnVector.offheap.enabled", "false")
    .config("spark.memory.offHeap.enabled", "false")
    .config(
        "spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled", "false"
    )
    .config("spark.driver.memory", "2g")
    .config("spark.driver.extraJavaOptions", "-XX:MaxDirectMemorySize=1g")
    .config("spark.sql.codegen.wholeStage", "false")
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4")
    .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .getOrCreate()
)

s3_url = upload_to_s3(DATA_LAKE_BUCKET, csv_path)

schema = types.StructType(
    [
        types.StructField("agg_trade_id", types.LongType(), True),
        types.StructField("price", types.DoubleType(), True),
        types.StructField("quantity", types.DoubleType(), True),
        types.StructField("first_trade_id", types.LongType(), True),
        types.StructField("last_trade_id", types.LongType(), True),
        types.StructField("timestamp", types.LongType(), True),
        types.StructField("is_buyer_maker", types.BooleanType(), True),
        types.StructField("is_best_match", types.BooleanType(), True),
    ]
)

df = spark.read.option("header", "false").schema(schema).csv(s3_url)


df = df.withColumn("ingest_date", F.current_date()).withColumn(
    "ingest_timestamp", F.current_timestamp()
)

output_path = (
    f"s3://{DATA_LAKE_BUCKET}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"
)
df.write.mode("overwrite").parquet(output_path)
logger.info(f"Parquet written to: {output_path}")

remove_file(csv_path)
remove_file(zip_path)
logger.info("✅ Landing job completed successfully.")
