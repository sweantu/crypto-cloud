import json
import logging
import time

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KinesisClient:
    def __init__(self, region):
        self.kinesis_client = boto3.client("kinesis", region_name=region)

    def delivery_report(self, err, res):
        if err is not None:
            logger.info(f"❌ Delivery failed: {err}")
        else:
            succeeded_count = len(res["Records"]) - res["FailedRecordCount"]
            failed_count = res["FailedRecordCount"]
            logger.info(
                f"✅ Delivered {succeeded_count} records, {failed_count} failed records"
            )

    def get_shard_iters(self, iterator_type, stream_name):
        shards_resp = self.kinesis_client.describe_stream(StreamName=stream_name)
        shards = shards_resp["StreamDescription"]["Shards"]
        if not shards:
            raise RuntimeError(f"No shards found in {stream_name}")
        print(f"📦 Found {len(shards)} shard(s) in {stream_name}")

        shard_iters = {}
        for shard in shards:
            shard_id = shard["ShardId"]
            iter_resp = self.kinesis_client.get_shard_iterator(
                StreamName=stream_name,
                ShardId=shard_id,
                ShardIteratorType=iterator_type,
            )
            shard_iters[shard_id] = iter_resp["ShardIterator"]
        return shard_iters

    def produce_messages(self, stream_name: str, messages: list[dict[str, str]]):
        """Send multiple records safely with error handling."""
        if not messages:
            logger.info("No records to send")
            return
        logger.info(f"Putting {len(messages)} records to Kinesis stream {stream_name}")
        try:
            response = self.kinesis_client.put_records(
                StreamName=stream_name,
                Records=[
                    {
                        "Data": msg["value"].encode("utf-8"),
                        "PartitionKey": msg["key"],
                    }
                    for msg in messages
                ],
            )
            self.delivery_report(None, response)
        except Exception as e:
            self.delivery_report(e, None)

    def consume_messages(self, iterator_type, records_per_shard, stream_name):
        print("👂 Listening for messages...\n")
        shard_iters = self.get_shard_iters(iterator_type, stream_name)
        try:
            total = 0
            while True:
                for shard_id, iterator in list(shard_iters.items()):
                    try:
                        resp = self.kinesis_client.get_records(
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
