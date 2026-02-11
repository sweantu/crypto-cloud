import argparse
import logging

# import sys
# from awsglue.utils import getResolvedOptions
from common.spark import get_spark_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# args = getResolvedOptions(
#     sys.argv,
#     [
#         "symbol",
#         "landing_date",
#         "transform_db",
#         "data_lake_bucket",
#         "iceberg_lock_table",
#     ],
# )

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", required=True)
parser.add_argument("--landing_date", required=True)
parser.add_argument("--data_lake_bucket", required=True)
parser.add_argument("--transform_db", required=True)
parser.add_argument("--iceberg_lock_table", required=True)
args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]
logger.info(f"Transforming symbol={symbol} for date={landing_date}")

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
TRANSFORM_DB = args["transform_db"]


if __name__ == "__main__":
    from transformation.pattern_two.main import transform_pattern_two

    spark = get_spark_session(app_name="TransformPatternTwo", iceberg=True)
    transform_db = f"hive_catalog.{TRANSFORM_DB}"
    transform_pattern_two(
        spark=spark,
        symbol=symbol,
        landing_date=landing_date,
        transform_db=transform_db,
    )
    logger.info("✅Transform pattern two completed successfully.")
