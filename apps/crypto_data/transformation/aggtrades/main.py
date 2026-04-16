import logging

from .spark import process_aggtrades_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(spark, date, data_lake_bucket, transform_db):
    aggtrades_url = f"s3a://{data_lake_bucket}/landing_zone/aggtrades/"
    aggtrades_table = "aggtrades"

    process_aggtrades_data(spark, date, aggtrades_url, transform_db, aggtrades_table)
    logger.info(f"✅ Transform aggtrades completed successfully for {date}")
