import logging
import time
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delivery_records_report(err, res):
    if err is not None:
        logger.info(f"❌ Delivery failed: {err}")
    else:
        succeeded_count = len(res.get("Successful", []))
        failed_count = len(res.get("Failed", []))
        logger.info(
            f"✅ Delivered {succeeded_count} records, {failed_count} failed records"
        )


def put_records_safe(sqs_client, queue_url, records):
    """Send multiple records safely with error handling."""
    if not records:
        logger.info("No records to send")
        return
    logger.info(
        f"Putting {len(records)} records to SQS queue {queue_url.split('/')[-1]}"
    )
    try:
        response = sqs_client.send_message_batch(
            QueueUrl=queue_url,
            Entries=[
                {"Id": str(uuid.uuid4()), "MessageBody": record["data"]}
                for record in records
            ],
        )
        delivery_records_report(None, response)
    except Exception as e:
        delivery_records_report(e, None)


def consume_messages(sqs_client, queue_url, max_messages):
    logger.info("👂 Listening for messages...\n")
    try:
        total = 0
        while True:
            resp = sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=20,
                VisibilityTimeout=60,  # 60 seconds
            )

            messages = resp.get("Messages", [])
            if not messages:
                logger.info("⚠️ No messages received")
                continue
            logger.info(f"✅ Received {len(messages)} messages")
            # 1. Process all messages
            for m in messages:
                total += 1
                logger.info(f"📩 Message {total}: {m['Body']}")

            # 2. Delete in batch
            entries = [
                {"Id": m["MessageId"], "ReceiptHandle": m["ReceiptHandle"]}
                for m in messages
                # if json.loads(m["Body"])["agg_trade_id"] % 10 != 0  # Example filter
            ]
            if not entries:
                logger.info("⚠️ No messages to delete")
                continue

            resp = sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=entries)
            logger.info(f"🗑️ Deleted {len(resp.get('Successful', []))} messages")
            if resp.get("Failed"):
                logger.info(
                    f"❌ Failed to delete {len(resp.get('Failed', []))} messages"
                )
            time.sleep(1)  # Throttle for a while
    except KeyboardInterrupt:
        logger.info("\n👋 Stopped listening for messages.")
