import json
import logging
import time

from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delivery_report(err, record_info):
    if err is not None:
        logger.info(f"❌ Delivery failed: {err}")
    else:
        logger.info(
            f"✅ Delivered to shard {record_info['ShardId']} Seq {record_info['SequenceNumber']}"
        )


def delivery_records_report(err, res):
    if err is not None:
        logger.info(f"❌ Delivery failed: {err}")
    else:
        succeeded_count = len(res["Records"]) - res["FailedRecordCount"]
        failed_count = res["FailedRecordCount"]
        logger.info(
            f"✅ Delivered {succeeded_count} records, {failed_count} failed records"
        )


def put_record_safe(kinesis_client, stream_name, data, partition_key):
    """Send one record safely with error handling."""
    try:
        response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=data.encode("utf-8"),
            PartitionKey=partition_key,
        )
        delivery_report(None, response)
    except Exception as e:
        delivery_report(e, None)


def put_records_safe(kinesis_client, stream_name, records):
    """Send multiple records safely with error handling."""
    if not records:
        logger.info("No records to send")
    logger.info(f"Putting {len(records)} records to Kinesis stream {stream_name}")
    return
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
        delivery_records_report(None, response)
    except Exception as e:
        delivery_records_report(e, None)


def get_shard_iters(kinesis, stream_name, iterator_type):
    shards_resp = kinesis.describe_stream(StreamName=stream_name)
    # print("shards_resp:", json.dumps(shards_resp, indent=2, default=str))
    shards = shards_resp["StreamDescription"]["Shards"]
    if not shards:
        raise RuntimeError(f"No shards found in {stream_name}")
    print(f"📦 Found {len(shards)} shard(s) in {stream_name}")

    shard_iters = {}
    for shard in shards:
        shard_id = shard["ShardId"]
        iter_resp = kinesis.get_shard_iterator(
            StreamName=stream_name,
            ShardId=shard_id,
            ShardIteratorType=iterator_type,
        )
        shard_iters[shard_id] = iter_resp["ShardIterator"]
    return shard_iters


def consume_messages(kinesis, shard_iters, records_per_shard):
    print("👂 Listening for messages...\n")
    try:
        total = 0
        while True:
            for shard_id, iterator in list(shard_iters.items()):
                try:
                    resp = kinesis.get_records(
                        ShardIterator=iterator, Limit=records_per_shard
                    )
                except ClientError as e:
                    print(f"❌ Error fetching records from {shard_id}: {e}")
                    continue

                records = resp.get("Records", [])
                if records:
                    total += len(records)
                    print(f"🔢 Total records consumed so far: {total}")
                for record in records[-1:]:
                    data = json.loads(record["Data"].decode("utf-8"))
                    seq = record["SequenceNumber"]
                    print(
                        f"📩 Shard {shard_id} Seq {seq}:\n{json.dumps(data, indent=2)}\n"
                    )

                # Move iterator forward
                shard_iters[shard_id] = resp.get("NextShardIterator")
                time.sleep(0.2)  # Small sleep to avoid throttling

    except KeyboardInterrupt:
        print("🛑 Stopped by user.")
