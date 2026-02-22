python main.py \
 --symbols '["ADAUSDT","SUIUSDT"]' \
 --landing_dates '["2025-09-27","2025-09-28"]'

docker run --rm \
 -e AGGTRADES_STREAM_NAME="$AGGTRADES_STREAM_NAME" \
  -e REGION="$REGION" \
 aggtrades-producer \
 --symbols '["ADAUSDT","SUIUSDT"]' \
 --landing_dates '["2025-09-27","2025-09-28"]'

# Create a topic

docker exec crypto-cloud-kafka kafka-topics --create \
 --topic test-topic \
 --bootstrap-server localhost:29092 \
 --partitions 1 --replication-factor 1

docker exec crypto-cloud-kafka kafka-topics --create \
 --topic aggtrades-topic --partitions 4 --replication-factor 1 \
 --bootstrap-server localhost:29092

# Produce a message

docker exec -it crypto-cloud-kafka kafka-console-producer \
 --topic test-topic --bootstrap-server localhost:29092

# Consume messages

docker exec -it crypto-cloud-kafka kafka-console-consumer \
 --topic test-topic --from-beginning --bootstrap-server localhost:29092

# check partitions

kafka-topics --bootstrap-server localhost:29092 --list
kafka-topics --bootstrap-server localhost:29092 --topic aggtrades-topic --describe

# Consume from partition 0

kafka-console-consumer --bootstrap-server localhost:29092 \
--topic aggtrades-topic --partition 0 --from-beginning --max-messages 5

# Consume from partition 1

kafka-console-consumer --bootstrap-server localhost:29092 \
--topic aggtrades-topic --partition 1 --from-beginning --max-messages 5
