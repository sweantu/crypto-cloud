import csv
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from generation.aggtrades.message import AggTrade
from shared_lib.file import download_file, extract_file, make_dir, remove_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


QUEUE_URL = os.getenv("AGGTRADES_QUEUE_URL", "")
REGION = os.getenv("AWS_REGION")
DURATION = 60 * 1  # seconds
MAX_MESSAGES = 500


def produce_messages(
    symbol: str, landing_date: str, csv_path: str, producer, topic: str
) -> None:
    num_lines = int(subprocess.check_output(["wc", "-l", csv_path]).split()[0])
    logger.info(f"Processing file: {csv_path}, total lines: {num_lines}")
    number_of_records = min(MAX_MESSAGES, int(num_lines / DURATION))
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        messages = []
        for i, row in enumerate(reader, 1):
            try:
                msg = AggTrade.get_message(row, symbol)
                messages.append(msg)
                if i % number_of_records == 0 or i == num_lines:
                    producer.produce_messages(topic, messages)
                    logger.info(
                        f"Produced messages for {symbol} at landing_date: {landing_date}, lines: {i}/{num_lines}"
                    )
                    messages = []
                    time.sleep(1)
            except Exception as e:
                logger.info(f"❌ Exception while producing message: {i}, error: {e}")


def download_and_extract_file(
    symbol: str, landing_date: str, script_dir: str, extract_dir: str
):
    url = f"https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{landing_date}.zip"
    zip_path = os.path.join(script_dir, url.split("/")[-1])
    download_file(url, zip_path)
    extract_file(extract_dir, zip_path)


def produce_aggtrades_messages(symbols, landing_dates, producer, topic):
    logger.info(
        f"Starting message production for symbols: {symbols} and landing_dates: {landing_dates}"
    )

    # Download and extract files in parallel
    with ThreadPoolExecutor() as executor:
        start_t = time.time()
        script_dir = "/tmp/data/raw"
        extract_dir = os.path.join(script_dir, "unzipped_data")
        make_dir(extract_dir)
        futures = [
            executor.submit(
                download_and_extract_file, symbol, landing_date, script_dir, extract_dir
            )
            for symbol in symbols
            for landing_date in landing_dates
        ]
        for future in futures:
            future.result()
        end_t = time.time()
        logger.info(
            f"Downloaded and extracted files in {(end_t - start_t):.2f} seconds"
        )

    # Produce messages for each symbol and landing_date in parallel
    for landing_date in landing_dates:
        with ThreadPoolExecutor() as executor:
            start_t = time.time()
            csv_paths = [
                os.path.join(extract_dir, f"{symbol}-aggTrades-{landing_date}.csv")
                for symbol in symbols
            ]
            futures = [
                executor.submit(
                    produce_messages,
                    symbol,
                    landing_date,
                    csv_path,
                    producer,
                    topic,
                )
                for symbol, csv_path in zip(symbols, csv_paths)
            ]
            for future in futures:
                future.result()
            end_t = time.time()
            logger.info(
                f"Finished producing messages for landing_date: {landing_date} in {(end_t - start_t):.2f} seconds"
            )

    # Clean up extracted files
    zip_paths = [
        os.path.join(script_dir, f"{symbol}-aggTrades-{landing_date}.zip")
        for symbol in symbols
        for landing_date in landing_dates
    ]
    csv_paths = [
        os.path.join(extract_dir, f"{symbol}-aggTrades-{landing_date}.csv")
        for symbol in symbols
        for landing_date in landing_dates
    ]
    for path in zip_paths + csv_paths:
        remove_file(path)
    logger.info("✅ All rounds completed.")
