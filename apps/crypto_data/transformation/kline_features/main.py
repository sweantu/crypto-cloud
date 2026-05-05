import logging

from .spark import process_kline_features_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(spark, date, transform_db):
    klines_table = "klines"
    kline_features_table = "kline_features"

    process_kline_features_data(
        spark, date, transform_db, klines_table, kline_features_table
    )
    logger.info("✅ Transform kline features completed successfully")
