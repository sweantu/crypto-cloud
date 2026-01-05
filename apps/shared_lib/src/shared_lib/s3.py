import logging

import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_to_s3(bucket_name, read_path, key):
    s3 = boto3.client("s3")
    s3.upload_file(read_path, bucket_name, key)
    url = f"s3://{bucket_name}/{key}"
    logger.info(f"Uploaded to S3: {url}")
    return url
