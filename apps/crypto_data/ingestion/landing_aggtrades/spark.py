import logging

from pyspark.sql import functions as F
from pyspark.sql import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_aggtrades_data(spark, date, data_lake_bucket):
    base_path = f"s3a://{data_lake_bucket}/raw_zone/aggtrades/"
    read_path = f"{base_path}/date={date}/"
    event_date = date
    schema = types.StructType(
        [
            types.StructField("agg_trade_id", types.LongType(), True),
            types.StructField("price", types.DoubleType(), True),
            types.StructField("quantity", types.DoubleType(), True),
            types.StructField("first_trade_id", types.LongType(), True),
            types.StructField("last_trade_id", types.LongType(), True),
            types.StructField("timestamp", types.LongType(), True),
            types.StructField("is_buyer_maker", types.BooleanType(), True),
            types.StructField("is_best_match", types.BooleanType(), True),
        ]
    )
    spark.read.option("header", "false").option("basePath", base_path).schema(
        schema
    ).csv(read_path).withColumn(
        "ingested_at", F.to_timestamp(F.col("ingestion_ts"), "yyyyMMdd_HHmmss'Z'")
    ).withColumn(
        "event_time", (F.col("timestamp") / 1_000_000).cast("timestamp")
    ).withColumn("event_date", F.col("event_time").cast("date")).withColumn(
        "created_at", F.current_timestamp()
    ).filter(F.col("event_date") == event_date).drop("ingestion_ts").drop(
        "date"
    ).createOrReplaceTempView("aggtrades_raw")

    spark.sql("""
    select agg_trade_id, symbol, max(ingested_at) as latest_ingested_at
    from aggtrades_raw
    group by agg_trade_id, symbol
    """).createOrReplaceTempView("aggtrades_deduped")

    df_deduped = spark.sql("""
    select r.*
    from aggtrades_raw r
    join aggtrades_deduped d on r.agg_trade_id = d.agg_trade_id and r.symbol = d.symbol and r.ingested_at = d.latest_ingested_at
    """)

    write_path = f"s3a://{data_lake_bucket}/landing_zone/aggtrades/"
    df_deduped.repartition("symbol").write.mode("overwrite").partitionBy(
        "event_date", "symbol"
    ).parquet(write_path)
    logger.info(f"Parquet written to: {write_path}")
