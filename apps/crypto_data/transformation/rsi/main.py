import logging

from transformation.rsi.spark import process_rsi_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transform_rsi(spark, transform_db, symbol, landing_date):
    klines_table = "klines"
    rsi_table = "rsi6"
    process_rsi_data(spark, transform_db, symbol, landing_date, klines_table, rsi_table)
    logger.info("✅ Transform rsi completed successfully")
