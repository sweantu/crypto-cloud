# import argparse
import logging
import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, types
from spark_jobs.common.rsi import make_rsi_in_chunks
from spark_jobs.common.table import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

args = getResolvedOptions(
    sys.argv,
    [
        "symbol",
        "landing_date",
        "transform_db",
        "data_lake_bucket",
        "iceberg_lock_table",
    ],
)

# parser = argparse.ArgumentParser()
# parser.add_argument("--symbol", required=True)
# parser.add_argument("--landing_date", required=True)
# parser.add_argument("--transform_db", required=True)
# parser.add_argument("--data_lake_bucket", required=True)
# parser.add_argument("--iceberg_lock_table", required=True)
# args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]
logger.info(f"Transforming symbol={symbol} for date={landing_date}")

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
TRANSFORM_DB = args["transform_db"]


spark = (
    SparkSession.builder.appName("TransformZone RSI")  # type: ignore
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


transform_db = f"glue_catalog.{TRANSFORM_DB}"
klines_table = "klines"
sql_stmt = f"""
select * from {transform_db}.{klines_table}
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
        types.StructField("rsi6", types.DoubleType(), True),
        types.StructField("rsi_ag", types.DoubleType(), True),
        types.StructField("rsi_al", types.DoubleType(), True),
    ]
)


rsi_table = "rsi6"

if table_exists(spark, transform_db, rsi_table):
    sql_stmt = f"""
    SELECT
        close_price AS prev_price,
        rsi_ag      AS prev_ag,
        rsi_al      AS prev_al
    FROM {transform_db}.{rsi_table}
    WHERE landing_date = date_sub(DATE('{landing_date}'), 1)
      AND symbol = '{symbol}'
    ORDER BY group_id DESC
    LIMIT 1
    """
    row = spark.sql(sql_stmt).first()

    if row:
        prev_price = row["prev_price"]
        prev_ag = row["prev_ag"]
        prev_al = row["prev_al"]
    else:
        prev_price = prev_ag = prev_al = None
else:
    prev_price = prev_ag = prev_al = None


rsi_in_chunks_with_state = make_rsi_in_chunks(
    prev_price=prev_price,
    prev_ag=prev_ag,
    prev_al=prev_al,
)

df = df_sorted.mapInPandas(rsi_in_chunks_with_state, schema)

if table_exists(spark, transform_db, rsi_table):
    df.writeTo(f"{transform_db}.{rsi_table}").overwritePartitions()
else:
    (
        df.writeTo(f"{transform_db}.{rsi_table}")
        .tableProperty("format-version", "2")
        .partitionedBy("symbol", "landing_date")
        .createOrReplace()
    )

logger.info("✅ Transform job completed successfully.")
