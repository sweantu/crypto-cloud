# import argparse
import logging
import sys

from awsglue.utils import getResolvedOptions
from common.table import table_exists
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

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

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
TRANSFORM_DB = args["transform_db"]

spark = (
    SparkSession.builder.appName("TransformZone")  # type: ignore
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
    # Disable vectorized Parquet reader to avoid off-heap memory issues
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
    #             "org.apache.hadoop:hadoop-aws:3.3.4",
    #         ]
    #     ),
    # )
    # .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    # .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    # .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .getOrCreate()
)

output_path = (
    f"s3://{DATA_LAKE_BUCKET}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"
)
df = spark.read.parquet(output_path)
df = (
    df.withColumn("timestamp_date", F.from_unixtime(F.col("timestamp") / 1_000_000))
    .withColumn("timestamp_second", (F.col("timestamp") / 1_000_000).cast("long"))
    .withColumn("group_id", (F.col("timestamp_second") / 900).cast("long"))
    .withColumn("group_date", F.from_unixtime(F.col("group_id") * 900))
    .withColumn("transform_date", F.current_date())
    .withColumn("transform_timestamp", F.current_timestamp())
    .withColumn("landing_date", F.to_date(F.lit(landing_date), "yyyy-MM-dd"))
    .withColumn("symbol", F.lit(symbol))
)

transform_db = f"glue_catalog.{TRANSFORM_DB}"

aggtrade_table = "aggtrades"
if table_exists(spark, transform_db, aggtrade_table):
    df.writeTo(f"{transform_db}.{aggtrade_table}").overwritePartitions()
    logger.info(
        f"Table {transform_db}.{aggtrade_table} overwritten for {symbol} on {landing_date}"
    )
else:
    df.writeTo(f"{transform_db}.{aggtrade_table}").tableProperty(
        "format-version", "2"
    ).partitionedBy("symbol", "landing_date").createOrReplace()
    logger.info(
        f"Table {transform_db}.{aggtrade_table} created for {symbol} on {landing_date}"
    )

sql_stmt = f"""
select 
    group_id,
    group_date,
    first(timestamp, true) as open_time,
    round(first(price, true), 4) as open_price,
    round(max(price), 4) as high_price,
    round(min(price), 4) as low_price,
    round(last(price, true), 4) as close_price,
    round(sum(quantity), 1) as volume,
    last(timestamp, true) as close_time,
    landing_date,
    symbol
from {transform_db}.{aggtrade_table}
where landing_date = DATE('{landing_date}') AND symbol = '{symbol}'
group by group_id, group_date, landing_date, symbol
"""
logger.info(f"SQL Statement:\n{sql_stmt}")
df_kline = spark.sql(sql_stmt)

klines_table = "klines"
if table_exists(spark, transform_db, klines_table):
    df_kline.writeTo(f"{transform_db}.{klines_table}").overwritePartitions()
    logger.info(
        f"Table {transform_db}.{klines_table} overwritten for {symbol} on {landing_date}"
    )
else:
    df_kline.writeTo(f"{transform_db}.{klines_table}").tableProperty(
        "format-version", "2"
    ).partitionedBy("symbol", "landing_date").createOrReplace()
    logger.info(
        f"Table {transform_db}.{klines_table} created for {symbol} on {landing_date}"
    )

logger.info("✅ Transform job completed successfully")
