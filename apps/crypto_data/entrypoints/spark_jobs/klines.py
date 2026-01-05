import argparse
import logging

from common.spark import database_exists

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

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
TRANSFORM_DB = args["transform_db"]

spark = (
    SparkSession.builder.appName("TransformKlines")  # type: ignore
    .master("local[*]")
    .config("spark.sql.session.timeZone", "UTC")
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    # Glue Catalog
    # .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    # .config(
    #     "spark.sql.catalog.glue_catalog.catalog-impl",
    #     "org.apache.iceberg.aws.glue.GlueCatalog",
    # )
    # .config("spark.sql.catalog.glue_catalog.lock.table", f"{ICEBERG_LOCK_TABLE}")
    # Hive Catalog
    .config("spark.sql.catalog.hive_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config(
        "spark.sql.catalog.hive_catalog.catalog-impl",
        "org.apache.iceberg.hive.HiveCatalog",
    )
    .config(
        "spark.sql.catalog.hive_catalog.uri",
        "thrift://localhost:9083",
    )
    # minio specific configs
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
    )
    .config("spark.hadoop.fs.s3a.access.key", "admin")
    .config("spark.hadoop.fs.s3a.secret.key", "admin123")
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
    # Disable vectorized Parquet reader to avoid off-heap memory issues
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
                "org.apache.hadoop:hadoop-aws:3.3.4",
            ]
        ),
    )
    .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .getOrCreate()
)

if __name__ == "__main__":
    from transformation.batch.klines.main import transform_klines

    transform_db = f"hive_catalog.{TRANSFORM_DB}"
    if not database_exists(spark, transform_db):
        spark.sql(f"""
        CREATE DATABASE IF NOT EXISTS {transform_db}
        LOCATION 's3a://{DATA_LAKE_BUCKET}/transform_zone/'
        """)
    transform_klines(
        spark,
        symbol,
        landing_date,
        data_lake_bucket=DATA_LAKE_BUCKET,
        transform_db=transform_db,
    )
