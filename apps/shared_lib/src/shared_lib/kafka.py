import logging

from confluent_kafka import Consumer, Producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self, conf: dict) -> None:
        self.producer = Producer(conf)

    def produce_messages(self, topic: str, messages: list[dict[str, str]]) -> None:
        # batch produce messages
        for msg in messages:
            self.producer.produce(
                topic,
                key=msg["key"].encode("utf-8"),
                value=msg["value"].encode("utf-8"),
                callback=self.delivery_report,
            )
        self.producer.flush()
        logger.info(f"✅ Produced {len(messages)} messages to topic: {topic}")

    def delivery_report(self, err, msg):
        if err is not None:
            logger.info(f"❌ Delivery failed: {err}")
        else:
            return
            logger.info(
                f"✅ Delivered to {msg.topic()} [{msg.partition()}] offset {msg.offset()}"
            )


class KafkaConsumer:
    def __init__(self, conf: dict) -> None:
        self.consumer = Consumer(conf)

    def consume_messages(self, topic: str) -> None:
        self.consumer.subscribe([topic])
        logger.info(f"👂 Listening for messages on topic: {topic}...\n")
        num_messages = 0
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.info(f"❌ Consumer error: {msg.error()}")
                    continue
                data = msg.value().decode("utf-8")
                num_messages += 1
                logger.info(
                    f"📩 Received from topic '{msg.topic()}' "
                    f"partition {msg.partition()} "
                    f"offset {msg.offset()}:\n{data}\n"
                )
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()
            logger.info(f"✅ Consumed {num_messages} messages from topic: {topic}")
