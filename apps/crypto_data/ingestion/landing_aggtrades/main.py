import logging

from .spark import process_aggtrades_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(spark, date, data_lake_bucket):
    process_aggtrades_data(spark, date, data_lake_bucket)

    logger.info(
        f"✅ Successfully ingested aggtrades data for {date} into {data_lake_bucket}"
    )
