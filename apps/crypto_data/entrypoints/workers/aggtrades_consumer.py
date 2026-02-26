import os

from serving.aggtrades.main import run
from shared_lib.kafka import KafkaConsumer
from shared_lib.kinesis import KinesisClient
from shared_lib.sqs import SQSClient

REGION = os.getenv("AWS_REGION", "")
NUM_OF_RECORDS = 500
MODE = "TRIM_HORIZON"  # or "LATEST"
ENV = os.getenv("ENV", "local")

if __name__ == "__main__":
    if ENV == "local":
        topic = "aggtrades-topic"
        kafka_consumer = KafkaConsumer(
            {
                "bootstrap.servers": "localhost:29092",
                "group.id": "test-group",
                "auto.offset.reset": "earliest",
            }
        )
        run(kafka_consumer, topic)
    else:
        kinesis_consumer = KinesisClient(region=REGION)
        sqs_consumer = SQSClient(region=REGION)

