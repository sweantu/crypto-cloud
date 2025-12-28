import logging

from .spark import process_aggtrades_data, process_klines_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transform_klines(spark, symbol, landing_date, data_lake_bucket, transform_db):
    aggtrades_url = f"s3://{data_lake_bucket}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"
    transform_db = f"glue_catalog.{transform_db}"
    aggtrades_table = "aggtrades"
    klines_table = "klines"

    process_aggtrades_data(
        spark, symbol, landing_date, aggtrades_url, transform_db, aggtrades_table
    )
    logger.info("✅ Transform aggtrades completed successfully")

    process_klines_data(
        spark, symbol, landing_date, transform_db, aggtrades_table, klines_table
    )
    logger.info("✅ Transform klines completed successfully")
