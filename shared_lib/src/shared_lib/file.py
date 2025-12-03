import logging
import os
import zipfile

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
