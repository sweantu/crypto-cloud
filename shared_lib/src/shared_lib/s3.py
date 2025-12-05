import logging
import os

import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_to_s3(bucket_name, file_path):
    s3 = boto3.client("s3")
    s3_key = f"raw_zone/{os.path.basename(file_path)}"
    s3.upload_file(file_path, bucket_name, s3_key)
    logger.info(f"Uploaded to s3://{bucket_name}/{s3_key}")
    return f"s3://{bucket_name}/{s3_key}"
