import argparse
import logging
import os

import boto3

from common.sqs import consume_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGION = os.getenv("REGION")
NUM_OF_RECORDS = 10
MODE = "TRIM_HORIZON"  # or "LATEST"


if __name__ == "__main__":
    kinesis_client = boto3.client("kinesis", region_name=REGION)
    sqs_client = boto3.client("sqs", region_name=REGION)
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--mode", default=MODE)
    args = parser.parse_args()

    name = args.name
    mode = args.mode
    logger.info(f"Using name: {name}")
    logger.info(f"Using mode: {mode}")
    # shard_iters = get_shard_iters(kinesis_client, name, iterator_type=mode)
    # consume_messages(kinesis_client, shard_iters, NUM_OF_RECORDS)
    consume_messages(sqs_client, name, NUM_OF_RECORDS)
