import logging
import time
import uuid

import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQSClient:
    def __init__(self, region: str):
        self.sqs_client = boto3.client("sqs", region_name=region)

    def produce_messages(self, queue_url, messages: list[dict[str, str]]):
        if not messages:
            logger.info("No records to send")
            return
        logger.info(
            f"Putting {len(messages)} records to SQS queue {queue_url.split('/')[-1]}"
        )
        try:
            response = self.sqs_client.send_message_batch(
                QueueUrl=queue_url,
                Entries=[
                    {"Id": str(uuid.uuid4()), "MessageBody": msg["value"]}
                    for msg in messages
                ],
            )
            self.delivery_report(None, response)
        except Exception as e:
            self.delivery_report(e, None)

    def consume_messages(self, queue_url, max_messages):
        logger.info("👂 Listening for messages...\n")
        try:
            total = 0
            while True:
                resp = self.sqs_client.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=20,
                    VisibilityTimeout=60,
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

                resp = self.sqs_client.delete_message_batch(
                    QueueUrl=queue_url, Entries=entries
                )
                logger.info(f"🗑️ Deleted {len(resp.get('Successful', []))} messages")
                if resp.get("Failed"):
                    logger.info(
                        f"❌ Failed to delete {len(resp.get('Failed', []))} messages"
                    )
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n👋 Stopped listening for messages.")

    def delivery_report(self, err, res):
        if err is not None:
            logger.info(f"❌ Delivery failed: {err}")
        else:
            succeeded_count = len(res.get("Successful", []))
            failed_count = len(res.get("Failed", []))
            logger.info(
                f"✅ Delivered {succeeded_count} records, {failed_count} failed records"
            )