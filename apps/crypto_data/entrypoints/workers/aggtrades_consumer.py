import os

from serving.aggtrades.main import run
from shared_lib.kafka import KafkaConsumer
from shared_lib.kinesis import KinesisClient
from shared_lib.sqs import SQSClient

REGION = os.getenv("AWS_REGION", "")
NUM_OF_RECORDS = 500
MODE = "TRIM_HORIZON"  # or "LATEST"

if __name__ == "__main__":
    topic = "aggtrades-topic"
    kafka_consumer = KafkaConsumer(
        {
            "bootstrap.servers": "localhost:29092",
            "group.id": "test-group",
            "auto.offset.reset": "earliest",
        }
    )

    kinesis_consumer = KinesisClient(region=REGION)
    sqs_consumer = SQSClient(region=REGION)

    run(kafka_consumer, topic)
