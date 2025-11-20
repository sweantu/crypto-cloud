import logging
import sys

from awsglue.utils import getResolvedOptions
from pyspark.errors.exceptions.base import AnalysisException
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def table_exists(spark: SparkSession, database: str, table: str) -> bool:
    try:
        spark.catalog.getTable(f"{database}.{table}")
        return True
    except AnalysisException:
        return False


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
symbol = args["symbol"]
landing_date = args["landing_date"]

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
PROJECT_PREFIX_UNDERSCORE = args["project_prefix_underscore"]

output_path = (
    f"s3://{DATA_LAKE_BUCKET}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"
)
transform_db = f"{PROJECT_PREFIX_UNDERSCORE}_transform_db"
klines_table = "klines"
serving_db = f"{PROJECT_PREFIX_UNDERSCORE}_serving_db"
aggtrade_table = "aggtrades"

spark = (
    SparkSession.builder.appName("TransformZone")  # type: ignore
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config(
        "spark.sql.catalog.glue_catalog.catalog-impl",
        "org.apache.iceberg.aws.glue.GlueCatalog",
    )
    .config("spark.sql.catalog.glue_catalog.warehouse", f"s3://{DATA_LAKE_BUCKET}/")
    .config(
        "spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO"
    )
    .config("spark.sql.catalog.glue_catalog.lock.table", f"{ICEBERG_LOCK_TABLE}")
    .config("spark.sql.defaultCatalog", "glue_catalog")
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
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


spark.sql(f"""
CREATE DATABASE IF NOT EXISTS {transform_db}
LOCATION 's3://{DATA_LAKE_BUCKET}/transform_zone/'
""")
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


spark.sql(f"""
CREATE DATABASE IF NOT EXISTS {serving_db}
LOCATION 's3://{DATA_LAKE_BUCKET}/serving_zone/'
""")
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


if table_exists(spark, serving_db, klines_table):
    df_kline.writeTo(f"{serving_db}.{klines_table}").overwritePartitions()
    logger.info(
        f"Table {serving_db}.{klines_table} overwritten for {symbol} on {landing_date}"
    )
else:
    df_kline.writeTo(f"{serving_db}.{klines_table}").tableProperty(
        "format-version", "2"
    ).partitionedBy("symbol", "landing_date").createOrReplace()
    logger.info(
        f"Table {serving_db}.{klines_table} created for {symbol} on {landing_date}"
    )

logger.info("✅ Transform job completed successfully")
