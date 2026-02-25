import json
import os

from shared_lib.arg import get_args
from shared_lib.kafka import KafkaProducer
from shared_lib.kinesis import KinesisClient

REGION = os.getenv("AWS_REGION")

if __name__ == "__main__":
    from generation.aggtrades.main import run

    args = get_args(["symbols", "landing_dates"])
    symbols = json.loads(args["symbols"])
    landing_dates = json.loads(args["landing_dates"])

    # kinesis producer
    stream_name = os.getenv("AGGTRADES_STREAM_NAME", "")
    kinesis_producer = KinesisClient(region=REGION)

    # kafka producer
    topic = "aggtrades-topic"
    kafka_producer = KafkaProducer({"bootstrap.servers": "localhost:29092"})
    run(symbols, landing_dates, kafka_producer, topic)
