import logging

from .spark import process_signals_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(spark, date, transform_db):
    kline_features_table = "kline_features"
    signals_table = "signals"

    process_signals_data(
        spark, date, transform_db, kline_features_table, signals_table
    )
    logger.info("✅ Transform signals completed successfully")
