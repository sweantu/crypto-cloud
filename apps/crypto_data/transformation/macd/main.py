import logging

from .spark import process_macd_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(spark, transform_db, symbol, landing_date):
    klines_table = "klines"
    macd_table = "macd"
    process_macd_data(
        spark, transform_db, symbol, landing_date, klines_table, macd_table
    )
    logger.info("✅ Transform macd completed successfully")
