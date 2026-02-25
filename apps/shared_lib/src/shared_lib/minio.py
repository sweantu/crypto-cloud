import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _minio_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.getenv("MINIO_USER", "minio"),
        aws_secret_access_key=os.getenv("MINIO_PASSWORD", "minio123"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def upload_to_minio(bucket: str, local_path: str | Path, key: str) -> str:
    local_path = Path(local_path)

    if not local_path.exists():
        raise FileNotFoundError(f"File not found: {local_path}")

    s3 = _minio_client()

    try:
        s3.upload_file(
            Filename=str(local_path),
            Bucket=bucket,
            Key=key,
        )
    except (BotoCoreError, ClientError):
        logger.exception("Failed to upload file to MinIO")
        raise

    url = f"s3://{bucket}/{key}"
    logger.info("Uploaded to MinIO: %s", url)
    return url
