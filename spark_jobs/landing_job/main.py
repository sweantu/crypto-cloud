import logging
import os
import sys
import time
import zipfile

import boto3
import requests
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, types
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


args = getResolvedOptions(
    sys.argv,
    [
        "symbol",
        "landing_date",
        "project_prefix_underscore",
        "data_lake_bucket",
        "iceberg_lock_table",
    ],
)
symbol = args["symbol"]
landing_date = args["landing_date"]

PROJECT_PREFIX_UNDERSCORE = args["project_prefix_underscore"]
DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]


def download_file(url, file_path):
    if os.path.exists(file_path):
        logger.info(f"{file_path} exists")
        return
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        logger.info(
            f"Downloaded {file_path} {(os.path.getsize(file_path) / (1024 * 1024)):.2f}MB completed"
        )


def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"{file_path} removed")


def extract_file(extract_dir, zip_path):
    if not os.path.exists(zip_path):
        logger.info(f"{zip_path} not found")
        return
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
        file_path = os.path.join(extract_dir, os.listdir(extract_dir)[0])
        logger.info(f"Extracted CSV: {file_path}")
        return file_path


def upload_to_s3(bucket_name, file_path):
    s3 = boto3.client("s3")
    s3_key = f"raw_zone/{os.path.basename(file_path)}"
    s3.upload_file(file_path, bucket_name, s3_key)
    logger.info(f"Uploaded to s3://{bucket_name}/{s3_key}")
    return f"s3://{bucket_name}/{s3_key}"


script_dir = "/tmp"
extract_dir = os.path.join(script_dir, "unzipped_data")
url = f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
zip_path = os.path.join(script_dir, url.split("/")[-1])
logger.info(f"Downloading {url} -> {zip_path}")

start_t = time.time()
download_file(url, zip_path)
csv_path = extract_file(extract_dir, zip_path)
end_t = time.time()
logger.info(f"Download + Extract processed in {(end_t - start_t):.3f} seconds")


spark = SparkSession.builder.appName("LandingZone").getOrCreate()


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

s3_url = upload_to_s3(DATA_LAKE_BUCKET, csv_path)
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
