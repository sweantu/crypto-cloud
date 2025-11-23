import json
import os
import time

import boto3
from botocore.exceptions import ClientError

STREAM_NAME = os.getenv("ENGULFINGS_STREAM_NAME")
REGION = os.getenv("REGION")


def get_shard_iters(kinesis, stream_name, iterator_type="TRIM_HORIZON"):
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


def consume_messages(kinesis, shard_iters):
    print("👂 Listening for messages...\n")
    try:
        total = 0
        while True:
            for shard_id, iterator in list(shard_iters.items()):
                try:
                    resp = kinesis.get_records(ShardIterator=iterator, Limit=500)
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


if __name__ == "__main__":
    kinesis = boto3.client("kinesis", region_name=REGION)
    shard_iters = get_shard_iters(kinesis, STREAM_NAME)
    consume_messages(kinesis, shard_iters)
