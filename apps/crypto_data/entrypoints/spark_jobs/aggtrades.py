import argparse

# import sys
# from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from shared_lib.minio import upload_to_minio

# args = getResolvedOptions(
#     sys.argv,
#     [
#         "symbol",
#         "landing_date",
#         "data_lake_bucket",
#         "iceberg_lock_table",
#     ],
# )

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", required=True)
parser.add_argument("--landing_date", required=True)
parser.add_argument("--data_lake_bucket", required=True)
parser.add_argument("--iceberg_lock_table", required=True)
args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]


spark = (
    SparkSession.builder.appName("Landing Job")  # type: ignore
    .master("local[*]")
    .config("spark.sql.session.timeZone", "UTC")
    # local mode optimizations to reduce memory consumption
    .config("spark.sql.parquet.enableVectorizedReader", "false")
    .config("spark.sql.columnVector.offheap.enabled", "false")
    .config("spark.memory.offHeap.enabled", "false")
    .config(
        "spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled", "false"
    )
    .config("spark.driver.memory", "2g")
    .config("spark.driver.extraJavaOptions", "-XX:MaxDirectMemorySize=1g")
    .config("spark.sql.codegen.wholeStage", "false")
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4")
    .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    # minio specific configs
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
    )
    .config("spark.hadoop.fs.s3a.access.key", "admin")
    .config("spark.hadoop.fs.s3a.secret.key", "admin123")
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
    .getOrCreate()
)

if __name__ == "__main__":
    from ingestion.batch.aggtrades.main import ingest_aggtrades

    ingest_aggtrades(
        spark,
        symbol,
        landing_date,
        data_lake_bucket=DATA_LAKE_BUCKET,
        upload_file=upload_to_minio,
    )
