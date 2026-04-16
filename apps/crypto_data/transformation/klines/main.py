import logging

from .spark import process_klines_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(spark, date, transform_db):
    aggtrades_table = "aggtrades"
    klines_table = "klines"

    process_klines_data(spark, date, transform_db, aggtrades_table, klines_table)
    logger.info("✅ Transform klines completed successfully")
