import csv
import json
import logging
import os
import subprocess
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

import boto3
import requests
from shared_lib.file import make_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STREAM_NAME = os.getenv("AGGTRADES_STREAM_NAME", "")
REGION = os.getenv("REGION")
DURATION = 60 * 1  # seconds
RECORDS_PER_SHARD = 500


def delivery_report(err, record_info):
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        print(
            f"✅ Delivered to shard {record_info['ShardId']} Seq {record_info['SequenceNumber']}"
        )


def delivery_records_report(err, res):
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        succeeded_count = len(res["Records"]) - res["FailedRecordCount"]
        failed_count = res["FailedRecordCount"]
        print(f"✅ Delivered {succeeded_count} records, {failed_count} failed records")


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


def put_record_safe(kinesis_client, stream_name, data, partition_key, callback):
    """Send one record safely with error handling."""
    try:
        response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=data.encode("utf-8"),
            PartitionKey=partition_key,
        )
        callback(None, response)
    except Exception as e:
        callback(e, None)


def put_records_safe(kinesis_client, stream_name, records, callback):
    """Send multiple records safely with error handling."""
    try:
        response = kinesis_client.put_records(
            StreamName=stream_name,
            Records=[
                {
                    "Data": record["data"].encode("utf-8"),
                    "PartitionKey": record["partition_key"],
                }
                for record in records
            ],
        )
        callback(None, response)
    except Exception as e:
        callback(e, None)


def produce_messages(stream_name: str, symbol: str, file_path: str) -> None:
    kinesis_client = boto3.client("kinesis", region_name=REGION)
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
                    i % min(RECORDS_PER_SHARD, int(num_lines / DURATION)) == 0
                    or i == num_lines
                ):
                    put_records_safe(
                        kinesis_client,
                        stream_name,
                        records,
                        delivery_records_report,
                    )
                    print(f"Produced {i} messages for {symbol} so far...")
                    records = []
                    time.sleep(1)
            except Exception as e:
                print(f"❌ Exception while producing message: {i}, error: {e}")

    t_end = time.time()
    print(
        f"✅ Time taken to produce {num_lines} messages: {t_end - t_start:.2f} seconds"
    )
    print(f"✅ Finished producing messages for file path: {file_path}")


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
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
        logger.info(f"Extracted CSV: {zip_path}")


def lambda_handler(event, context):
    symbols = event.get("symbols", [])
    landing_dates = event.get("landing_dates", [])
    print(f"Producing crypto trades for {symbols} on dates {landing_dates}")

    script_dir = "/tmp/data/raw"
    extract_dir = os.path.join(script_dir, "unzipped_data")
    make_dir(extract_dir)
    urls = [
        f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
        for symbol in symbols
        for landing_date in landing_dates
    ]
    zip_paths = [os.path.join(script_dir, url.split("/")[-1]) for url in urls]

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
    csv_paths = [
        f"{extract_dir}/{symbol}-aggTrades-{landing_date}.csv"
        for symbol in symbols
        for landing_date in landing_dates
    ]
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
                executor.submit(produce_messages, STREAM_NAME, symbol, file_path)
                for symbol, file_path in zip(symbols, file_paths)
            ]
            for future in futures:
                future.result()
            t_end_round = time.time()
            print(
                f"✅ Completed round {landing_date} taken for : {t_end_round - t_start_round:.2f} seconds"
            )
    t_end_all = time.time()
    print(f"✅ Total time taken: {t_end_all - t_start_all:.2f} seconds")
    for csv_path, zip_path in zip(csv_paths, zip_paths):
        print(f"Cleaning up {csv_path} and {zip_path}")
        remove_file(csv_path)
        remove_file(zip_path)
    print("✅ All rounds completed.")
    return {
        "symbols": symbols,
        "landing_dates": landing_dates,
        "region": REGION,
        "stream_name": STREAM_NAME,
    }
