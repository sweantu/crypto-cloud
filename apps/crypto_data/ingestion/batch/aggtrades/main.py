import logging
import os

# import sys
# from awsglue.utils import getResolvedOptions
from shared_lib.file import download_file, extract_file, remove_file
from shared_lib.s3 import upload_to_s3

from .spark import process_aggtrades_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_aggtrades(spark, symbol, landing_date, data_lake_bucket):
    script_dir = "/tmp/data/raw"
    extract_dir = os.path.join(script_dir, "unzipped_data")
    url = f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
    zip_path = os.path.join(script_dir, url.split("/")[-1])

    download_file(url, zip_path)
    csv_path = extract_file(extract_dir, zip_path)

    s3_key = f"raw_zone/{os.path.basename(csv_path)}"
    read_url = upload_to_s3(data_lake_bucket, csv_path, s3_key)
    write_url = f"s3://{data_lake_bucket}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"

    process_aggtrades_data(spark, read_url, write_url)

    remove_file(csv_path)
    remove_file(zip_path)
    logger.info(f"✅ Successfully ingested aggtrades data in {write_url} ")
