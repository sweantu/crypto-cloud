import logging
import os
from concurrent.futures import ThreadPoolExecutor

from shared_lib.file import download_file, extract_file, make_dir, remove_file
from shared_lib.time import get_current_timestamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_raw_aggtrades(
    script_dir,
    extract_dir,
    symbol,
    date,
    data_lake_bucket,
    upload_file,
    ingestion_ts,
):
    url = f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{date}.zip"
    zip_path = os.path.join(script_dir, url.split("/")[-1])
    csv_path = os.path.join(extract_dir, f"{symbol}-aggTrades-{date}.csv")
    download_file(url, zip_path)
    extract_file(extract_dir, zip_path)
    s3_key = f"raw_zone/aggtrades/date={date}/symbol={symbol}/ingestion_ts={ingestion_ts}/data.csv"
    url = upload_file(data_lake_bucket, csv_path, s3_key)
    logger.info(f"✅ Uploaded {csv_path} to {url}")
    remove_file(csv_path)
    remove_file(zip_path)


def run(date, data_lake_bucket, upload_file):
    script_dir = "/tmp/data/raw"
    extract_dir = os.path.join(script_dir, "unzipped_data")
    make_dir(extract_dir)
    symbols = ["BTCUSDT", "ADAUSDT", "DOTUSDT"]
    ingestion_ts = get_current_timestamp()

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_raw_aggtrades,
                script_dir,
                extract_dir,
                symbol,
                date,
                data_lake_bucket,
                upload_file,
                ingestion_ts,
            )
            for symbol in symbols
        ]
        for future in futures:
            future.result()

    logger.info("✅ All files processed and uploaded successfully")
