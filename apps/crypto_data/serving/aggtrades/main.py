def consume_aggtrades_messages(consumer, topic):
    consumer.consume_messages(topic=topic)
