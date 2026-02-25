import logging
import os
import time
import zipfile

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def download_file(url, file_path) -> str:
    if os.path.exists(file_path):
        logger.info(f"{file_path} exists")
        return file_path
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

def extract_file(extract_dir, zip_path) -> None:
    if not os.path.exists(zip_path):
        logger.info(f"{zip_path} not found")
        raise FileNotFoundError(f"{zip_path} not found")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        logger.info(f"Extracting {zip_path} -> {extract_dir}")
        start_t = time.time()
        zip_ref.extractall(extract_dir)
        end_t = time.time()
        logger.info(f"Extracted {zip_path} in {(end_t - start_t):.3f} seconds")


def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"{file_path} removed")
