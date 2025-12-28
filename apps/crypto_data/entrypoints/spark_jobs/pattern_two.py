import argparse
import logging

# import sys
# from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession

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
parser.add_argument("--transform_db", required=True)
parser.add_argument("--data_lake_bucket", required=True)
parser.add_argument("--iceberg_lock_table", required=True)
args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]
logger.info(f"Transforming symbol={symbol} for date={landing_date}")

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
TRANSFORM_DB = args["transform_db"]


spark = (
    SparkSession.builder.appName("TransformZone Pattern Two")  # type: ignore
    .master("local[*]")
    .config("spark.sql.session.timeZone", "UTC")
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config(
        "spark.sql.catalog.glue_catalog.catalog-impl",
        "org.apache.iceberg.aws.glue.GlueCatalog",
    )
    .config("spark.sql.catalog.glue_catalog.lock.table", f"{ICEBERG_LOCK_TABLE}")
    # Disable vectorized reader
    .config("spark.sql.parquet.enableVectorizedReader", "false")
    .config("spark.sql.columnVector.offheap.enabled", "false")
    .config("spark.memory.offHeap.enabled", "false")
    .config(
        "spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled", "false"
    )
    .config("spark.driver.memory", "2g")
    .config("spark.driver.extraJavaOptions", "-XX:MaxDirectMemorySize=1g")
    .config("spark.sql.codegen.wholeStage", "false")
    .config(
        "spark.jars.packages",
        ",".join(
            [
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1",
                "org.apache.iceberg:iceberg-aws-bundle:1.7.1",
            ]
        ),
    )
    .getOrCreate()
)


if __name__ == "__main__":
    from transformation.batch.pattern_two.main import transform_pattern_two

    transform_pattern_two(
        spark=spark,
        symbol=symbol,
        landing_date=landing_date,
        transform_db=TRANSFORM_DB,
    )
    logger.info("✅Transform pattern two completed successfully.")
