import logging
import os
import time
import zipfile

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_file(url, file_path) -> str:
    if os.path.exists(file_path):
        logger.info(f"{file_path} exists")
        return file_path
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        logger.info(f"Downloading {url} -> {file_path}")
        start_t = time.time()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        end_t = time.time()
        logger.info(
            f"Downloaded {file_path} {(os.path.getsize(file_path) / (1024 * 1024)):.2f}MB completed in {(end_t - start_t):.3f} seconds"
        )
        return file_path


def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"{file_path} removed")


def extract_file(extract_dir, zip_path) -> str:
    if not os.path.exists(zip_path):
        logger.info(f"{zip_path} not found")
        raise FileNotFoundError(f"{zip_path} not found")
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        logger.info(f"Extracting {zip_path} -> {extract_dir}")
        start_t = time.time()
        zip_ref.extractall(extract_dir)
        end_t = time.time()
        file_path = os.path.join(extract_dir, os.listdir(extract_dir)[0])
        logger.info(f"Extracted CSV: {file_path} in {(end_t - start_t):.3f} seconds")
        return file_path