import argparse
import csv
import json
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import boto3
from shared_lib.file import download_file, extract_file, remove_file
from shared_lib.kinesis import put_records_safe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STREAM_NAME = os.getenv("AGGTRADES_STREAM_NAME", "")
QUEUE_URL = os.getenv("AGGTRADES_QUEUE_URL", "")
REGION = os.getenv("AWS_REGION")
DURATION = 60 * 1  # seconds
NUM_OF_RECORDS = 500


class AggTrade:
    def __init__(self, row: list[str], symbol: str) -> None:
        self.agg_trade_id = int(row[0])
        self.price = float(row[1])
        self.quantity = float(row[2])
        self.first_trade_id = int(row[3])
        self.last_trade_id = int(row[4])
        self.ts_int = int(row[5])
        self.is_buyer_maker = row[6].strip().lower() == "true"
        self.is_best_match = row[7].strip().lower() == "true"
        self.symbol = symbol


def produce_messages(client, name: str, symbol: str, file_path: str) -> None:
    num_lines = int(subprocess.check_output(["wc", "-l", file_path]).split()[0])
    t_start = time.time()
    with open(
        file_path,
        newline="",
        encoding="utf-8",
    ) as f:
        reader = csv.reader(f)
        records = []
        for i, row in enumerate(reader, 1):
            try:
                msg = json.dumps(AggTrade(row, symbol).__dict__)
                records.append({"data": msg, "partition_key": symbol})
                if (
                    i % min(NUM_OF_RECORDS, int(num_lines / DURATION)) == 0
                    or i == num_lines
                ):
                    put_records_safe(client, name, records)
                    logger.info(f"Produced {i} messages for {symbol} so far...")
                    records = []
                    time.sleep(1)
            except Exception as e:
                logger.info(f"❌ Exception while producing message: {i}, error: {e}")

    t_end = time.time()
    logger.info(
        f"✅ Time taken to produce {num_lines} messages: {t_end - t_start:.2f} seconds"
    )
    logger.info(f"✅ Finished producing messages for file path: {file_path}")


if __name__ == "__main__":
    kinesis_client = boto3.client("kinesis", region_name=REGION)
    sqs_client = boto3.client("sqs", region_name=REGION)
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", required=True)
    parser.add_argument("--landing_dates", required=True)
    args = parser.parse_args().__dict__

    symbols = json.loads(args["symbols"])
    landing_dates = json.loads(args["landing_dates"])
    logger.info(f"Symbols: {symbols}")
    logger.info(f"Landing Dates: {landing_dates}")
    logger.info(f"Stream Name: {STREAM_NAME}")
    logger.info(f"Region: {REGION}")

    script_dir = "/tmp/data/raw"
    extract_dir = os.path.join(script_dir, "unzipped_data")
    urls = [
        f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
        for symbol in symbols
        for landing_date in landing_dates
    ]
    zip_paths = [os.path.join(script_dir, url.split("/")[-1]) for url in urls]
    csv_paths = [
        f"{extract_dir}/{symbol}-aggTrades-{landing_date}.csv"
        for symbol in symbols
        for landing_date in landing_dates
    ]

    start_t = time.time()
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(download_file, url, zip_path)
            for url, zip_path in zip(urls, zip_paths)
        ]
        for future in futures:
            future.result()
        futures = [
            executor.submit(extract_file, extract_dir, zip_path)
            for zip_path in zip_paths
        ]
        for future in futures:
            future.result()
    end_t = time.time()
    logger.info(f"Download + Extract processed in {(end_t - start_t):.3f} seconds")

    t_start_all = time.time()
    with ThreadPoolExecutor() as executor:
        for i, landing_date in enumerate(landing_dates):
            t_start_round = time.time()
            file_paths = [
                f"{extract_dir}/{symbol}-aggTrades-{landing_date}.csv"
                for symbol in symbols
            ]
            futures = [
                executor.submit(
                    produce_messages, kinesis_client, STREAM_NAME, symbol, file_path
                )
                for symbol, file_path in zip(symbols, file_paths)
            ]
            for future in futures:
                future.result()
            t_end_round = time.time()
            logger.info(
                f"✅ Completed round {landing_date} taken for : {t_end_round - t_start_round:.2f} seconds"
            )
    t_end_all = time.time()
    logger.info(f"✅ Total time taken: {t_end_all - t_start_all:.2f} seconds")
    for csv_path, zip_path in zip(csv_paths, zip_paths):
        logger.info(f"Cleaning up {csv_path} and {zip_path}")
        remove_file(csv_path)
        remove_file(zip_path)
    logger.info("✅ All rounds completed.")
