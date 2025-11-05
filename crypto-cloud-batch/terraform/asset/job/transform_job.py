import logging

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


project_prefix = "crypto-cloud-dev-583323753643"
data_lake_bucket_name = "crypto-cloud-dev-583323753643-data-lake-bucket"
data_lake_iceberg_lock_table_name = "crypto_cloud_dev_583323753643_iceberg_lock_table"
data_prefix = project_prefix.replace("-", "_")

landing_date = "2025-09-27"
symbol = "ADAUSDT"

spark = SparkSession.builder.appName("TransformZone").getOrCreate()  # type: ignore


output_path = f"s3a://{data_lake_bucket_name}/landing_zone/spot/daily/aggTrades/{symbol}/{landing_date}"
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


transform_db = f"{data_prefix}_transform_db"
spark.sql(f"""
CREATE DATABASE IF NOT EXISTS {transform_db}
LOCATION 's3a://{data_lake_bucket_name}/transform_zone/'
""")


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


serving_db = f"{data_prefix}_serving_db"
spark.sql(f"""
CREATE DATABASE IF NOT EXISTS {serving_db}
LOCATION 's3a://{data_lake_bucket_name}/serving_zone/'
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


klines_table = "klines"
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
