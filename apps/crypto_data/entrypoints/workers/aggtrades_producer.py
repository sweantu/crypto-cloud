import json
import os

from shared_lib.arg import get_args
from shared_lib.kafka import KafkaProducer
from shared_lib.kinesis import KinesisClient
from shared_lib.local import LOCAL_ENV
from shared_lib.name import get_stream_name

if __name__ == "__main__":
    from generation.aggtrades.main import run

    args = get_args(["symbols", "landing_dates"])
    symbols = json.loads(args["symbols"])
    landing_dates = json.loads(args["landing_dates"])

    topic = get_stream_name("aggtrades-stream")

    if LOCAL_ENV:
        producer = KafkaProducer({"bootstrap.servers": "localhost:29092"})
    else:
        REGION = os.getenv("AWS_REGION")
        producer = KinesisClient(region=REGION)
    run(symbols, landing_dates, producer, topic=topic)
