import logging

from .spark import process_pattern_two_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transform_pattern_two(spark, symbol, landing_date, transform_db):
    klines_table = "klines"
    pattern_two_table = "pattern_two"

    process_pattern_two_data(
        spark,
        symbol,
        landing_date,
        transform_db,
        klines_table,
        pattern_two_table,
    )

    logger.info("✅Transform pattern_two completed successfully.")
