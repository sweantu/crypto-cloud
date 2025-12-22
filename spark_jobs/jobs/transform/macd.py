# import argparse
import logging
import sys

from awsglue.utils import getResolvedOptions
from common.table import table_exists
from pyspark.sql import SparkSession, types

from spark_jobs.common.macd import make_macd_in_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

args = getResolvedOptions(
    sys.argv,
    [
        "symbol",
        "landing_date",
        "project_prefix_underscore",
        "data_lake_bucket",
        "iceberg_lock_table",
    ],
)

# parser = argparse.ArgumentParser()
# parser.add_argument("--symbol", required=True)
# parser.add_argument("--landing_date", required=True)
# parser.add_argument("--project_prefix_underscore", required=True)
# parser.add_argument("--data_lake_bucket", required=True)
# parser.add_argument("--iceberg_lock_table", required=True)
# args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]
logger.info(f"Transforming symbol={symbol} for date={landing_date}")

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
PROJECT_PREFIX_UNDERSCORE = args["project_prefix_underscore"]


spark = (
    SparkSession.builder.appName("TransformZone MACD")  # type: ignore
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
    # .config("spark.sql.parquet.enableVectorizedReader", "false")
    # .config("spark.sql.columnVector.offheap.enabled", "false")
    # .config("spark.memory.offHeap.enabled", "false")
    # .config(
    #     "spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled", "false"
    # )
    # .config("spark.driver.memory", "2g")
    # .config("spark.driver.extraJavaOptions", "-XX:MaxDirectMemorySize=1g")
    # .config("spark.sql.codegen.wholeStage", "false")
    # .config(
    #     "spark.jars.packages",
    #     ",".join(
    #         [
    #             "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1",
    #             "org.apache.iceberg:iceberg-aws-bundle:1.7.1",
    #         ]
    #     ),
    # )
    .getOrCreate()
)


serving_db = f"glue_catalog.{PROJECT_PREFIX_UNDERSCORE}_serving_db"
klines_table = "klines"
sql_stmt = f"""
select * from {serving_db}.{klines_table}
where landing_date = DATE('{landing_date}') AND symbol = '{symbol}'
"""
df_sorted = (
    spark.sql(sql_stmt)
    .coalesce(1)  # one partition, not shuffle
    .sortWithinPartitions("group_id")
)
logger.info(f"Input rows: {df_sorted.count()}")


schema = types.StructType(
    [
        *df_sorted.schema.fields,  # keep all original fields
        types.StructField("ema12", types.DoubleType(), True),
        types.StructField("ema26", types.DoubleType(), True),
        types.StructField("macd", types.DoubleType(), True),
        types.StructField("signal", types.DoubleType(), True),
        types.StructField("histogram", types.DoubleType(), True),
    ]
)

macd_table = "macd"

if table_exists(spark, serving_db, macd_table):
    sql_stmt = f"""
    SELECT
        ema12      AS macd_ema12,
        ema26      AS macd_ema26,
        signal     AS macd_signal
    FROM {serving_db}.{macd_table}
    WHERE landing_date = date_sub(DATE('{landing_date}'), 1)
      AND symbol = '{symbol}'
    ORDER BY group_id DESC
    LIMIT 1
    """
    row = spark.sql(sql_stmt).first()

    if row:
        prev_ema12 = row["macd_ema12"]
        prev_ema26 = row["macd_ema26"]
        prev_signal = row["macd_signal"]
    else:
        prev_ema12 = prev_ema26 = prev_signal = None
else:
    prev_ema12 = prev_ema26 = prev_signal = None

macd_in_chunks_with_state = make_macd_in_chunks(
    prev_ema12=prev_ema12,
    prev_ema26=prev_ema26,
    prev_signal=prev_signal,
)


df = df_sorted.mapInPandas(macd_in_chunks_with_state, schema)

if table_exists(spark, serving_db, macd_table):
    df.writeTo(f"{serving_db}.{macd_table}").overwritePartitions()
else:
    (
        df.writeTo(f"{serving_db}.{macd_table}")
        .tableProperty("format-version", "2")
        .partitionedBy("symbol", "landing_date")
        .createOrReplace()
    )

logger.info("✅ MACD transform job completed successfully.")
