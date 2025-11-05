import logging
import os
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


# script_dir = "./"
# extract_dir = os.path.join(script_dir, "unzipped_data")
# url = f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
# file_name = os.path.join(script_dir, url.split("/")[-1])
# logger.info(f"Downloading {url} -> {file_name}")

# start_t = time.time()
# download_file(url, file_name)
# csv_file = extract_file(extract_dir, file_name)
# end_t = time.time()
# logger.info(f"Download + Extract processed in {(end_t - start_t):.3f} seconds")


project_prefix = "crypto-cloud-dev-650251698703"
data_lake_bucket_name = "crypto-cloud-dev-650251698703-data-lake-bucket"
data_lake_iceberg_lock_table_name = "crypto_cloud_dev_650251698703_iceberg_lock_table"
data_prefix = project_prefix.replace("-", "_")

spark = (
    SparkSession.builder.appName("LandingZone")  # type: ignore
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
        "org.apache.iceberg:iceberg-aws-bundle:1.6.1,"
        "org.apache.hadoop:hadoop-aws:3.3.4",
    )
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config(
        "spark.sql.catalog.glue_catalog.catalog-impl",
        "org.apache.iceberg.aws.glue.GlueCatalog",
    )
    .config(
        "spark.sql.catalog.glue_catalog.warehouse", f"s3a://{data_lake_bucket_name}/"
    )
    .config(
        "spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO"
    )
    .config(
        "spark.sql.catalog.glue_catalog.lock.table",
        f"{data_lake_iceberg_lock_table_name}",
    )
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    .config("spark.sql.defaultCatalog", "glue_catalog")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)


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

csv_file = "s3a://crypto-cloud-dev-650251698703-glue-scripts-bucket/ADAUSDT-aggTrades-2025-09-27.csv"
df = spark.read.option("header", "false").schema(schema).csv(csv_file)


df = df.withColumn("ingest_date", F.current_date()).withColumn(
    "ingest_timestamp", F.current_timestamp()
)


output_path = f"s3a://{data_lake_bucket_name}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"
df.write.mode("overwrite").parquet(output_path)
logger.info(f"✅ Parquet written to: {output_path}")


# remove_file(csv_file)
# remove_file(file_name)
