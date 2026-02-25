import logging

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_aggtrades_data(
    spark: SparkSession,
    symbol,
    landing_date,
    aggtrades_url,
    transform_db,
    aggtrades_table,
):
    df = spark.read.parquet(aggtrades_url)
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

    if table_exists(spark, transform_db, aggtrades_table):
        logger.info(
            f"Table {transform_db}.{aggtrades_table} exists. Overwriting data..."
        )
        df.writeTo(f"{transform_db}.{aggtrades_table}").overwritePartitions()
        logger.info(
            f"Table {transform_db}.{aggtrades_table} overwritten for {symbol} on {landing_date}"
        )
    else:
        df.writeTo(f"{transform_db}.{aggtrades_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy(F.col("symbol"), F.col("landing_date")).createOrReplace()
        logger.info(
            f"Table {transform_db}.{aggtrades_table} created for {symbol} on {landing_date}"
        )


def process_klines_data(
    spark: SparkSession,
    symbol,
    landing_date,
    transform_db,
    aggtrades_table,
    klines_table,
):
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
    from {transform_db}.{aggtrades_table}
    where landing_date = DATE('{landing_date}') AND symbol = '{symbol}'
    group by group_id, group_date, landing_date, symbol
    """
    logger.info(f"SQL Statement:\n{sql_stmt}")
    df_kline = spark.sql(sql_stmt)

    if table_exists(spark, transform_db, klines_table):
        df_kline.writeTo(f"{transform_db}.{klines_table}").overwritePartitions()
        logger.info(
            f"Table {transform_db}.{klines_table} overwritten for {symbol} on {landing_date}"
        )
    else:
        df_kline.writeTo(f"{transform_db}.{klines_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy(F.col("symbol"), F.col("landing_date")).createOrReplace()
        logger.info(
            f"Table {transform_db}.{klines_table} created for {symbol} on {landing_date}"
        )
