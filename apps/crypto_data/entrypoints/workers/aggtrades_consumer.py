import os

from serving.aggtrades.main import run
from shared_lib.kafka import KafkaConsumer
from shared_lib.kinesis import KinesisClient
from shared_lib.local import LOCAL_ENV
from shared_lib.name import get_stream_name

if __name__ == "__main__":
    topic = get_stream_name("aggtrades-stream")
    if LOCAL_ENV:
        consumer = KafkaConsumer(
            {
                "bootstrap.servers": "localhost:29092",
                "group.id": "test-group",
                "auto.offset.reset": "earliest",
            }
        )
    else:
        region = os.getenv("AWS_REGION", "")
        consumer = KinesisClient(region=region)
    run(consumer, topic=topic)

