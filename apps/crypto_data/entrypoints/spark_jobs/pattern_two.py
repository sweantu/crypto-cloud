import logging

from shared_lib.arg import get_args
from shared_lib.spark import get_spark_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    from transformation.pattern_two.main import run

    args = get_args(
        [
            "symbol",
            "landing_date",
            "data_lake_bucket",
            "transform_db",
            "iceberg_lock_table",
        ]
    )
    symbol = args["symbol"]
    landing_date = args["landing_date"]
    logger.info(f"Transforming symbol={symbol} for date={landing_date}")

    data_lake_bucket = args["data_lake_bucket"]
    iceberg_lock_table = args["iceberg_lock_table"]
    transform_db = args["transform_db"]

    spark = get_spark_session(
        app_name="pattern_two_transform_job", local=True, minio=True, hive=True
    )
    transform_db = f"hive_catalog.{transform_db}"
    run(
        spark=spark,
        symbol=symbol,
        landing_date=landing_date,
        transform_db=transform_db,
    )
    logger.info("✅Transform pattern two completed successfully.")
