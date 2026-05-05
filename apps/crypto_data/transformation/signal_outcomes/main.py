import logging

from .spark import process_signal_outcomes_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(spark, date, transform_db):
    klines_table = "klines"
    signals_table = "signals"
    signal_outcomes_table = "signal_outcomes"

    process_signal_outcomes_data(
        spark, date, transform_db, klines_table, signals_table, signal_outcomes_table
    )

    logger.info("✅ Transform signal outcomes completed successfully")
