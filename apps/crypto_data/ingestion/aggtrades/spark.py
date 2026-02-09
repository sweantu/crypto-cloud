import logging

from pyspark.sql import functions as F
from pyspark.sql import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_aggtrades_data(spark, read_url, write_url):
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
    df = spark.read.option("header", "false").schema(schema).csv(read_url)

    df = df.withColumn("ingest_date", F.current_date()).withColumn(
        "ingest_timestamp", F.current_timestamp()
    )

    df.write.mode("overwrite").parquet(write_url)
    logger.info(f"Parquet written to: {write_url}")
