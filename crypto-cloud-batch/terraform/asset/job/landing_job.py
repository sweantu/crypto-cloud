import logging
import os
import time
import zipfile

import requests
from pyspark.sql import SparkSession, types
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


landing_date = "2025-09-27"
symbol = "ADAUSDT"


def download_file(url, file_name):
    if os.path.exists(file_name):
        logger.info(f"{file_name} exists")
        return
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_name, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        logger.info(
            f"Downloaded {file_name} {(os.path.getsize(file_name) / (1024 * 1024)):.2f}MB completed"
        )


def remove_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        logger.info(f"{file_name} removed")


def extract_file(extract_dir, zip_path):
    if not os.path.exists(zip_path):
        logger.info(f"{zip_path} not found")
        return
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
        csv_file = os.path.join(extract_dir, os.listdir(extract_dir)[0])
        logger.info(f"Extracted CSV: {csv_file}")
        return csv_file


script_dir = "./"
extract_dir = os.path.join(script_dir, "unzipped_data")
url = f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
file_name = os.path.join(script_dir, url.split("/")[-1])
logger.info(f"Downloading {url} -> {file_name}")

start_t = time.time()
download_file(url, file_name)
csv_file = extract_file(extract_dir, file_name)
end_t = time.time()
logger.info(f"Download + Extract processed in {(end_t - start_t):.3f} seconds")


project_prefix = "crypto-cloud-dev-583323753643"
data_lake_bucket_name = "crypto-cloud-dev-583323753643-data-lake-bucket"
data_lake_iceberg_lock_table_name = "crypto_cloud_dev_583323753643_iceberg_lock_table"
data_prefix = project_prefix.replace("-", "_")

spark = spark = SparkSession.builder.appName("LandingZone").getOrCreate()  # type: ignore


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

df = spark.read.option("header", "false").schema(schema).csv(csv_file)


df = df.withColumn("ingest_date", F.current_date()).withColumn(
    "ingest_timestamp", F.current_timestamp()
)


output_path = f"s3a://{data_lake_bucket_name}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"
df.write.mode("overwrite").parquet(output_path)
logger.info(f"Parquet written to: {output_path}")


remove_file(csv_file)
remove_file(file_name)
