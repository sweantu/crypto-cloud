import logging

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_aggtrades_data(
    spark: SparkSession,
    date,
    aggtrades_url,
    transform_db,
    aggtrades_table,
):
    df = spark.read.parquet(aggtrades_url)
    df = (
        df.where(f"event_date = '{date}'")
        .drop("created_at")
        .withColumn("notional", df["price"] * df["quantity"])
        .withColumn("created_at", F.current_timestamp())
    )

    if not table_exists(spark, transform_db, aggtrades_table):
        df.writeTo(f"{transform_db}.{aggtrades_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy(F.col("event_date"), F.col("symbol")).createOrReplace()
        logger.info(
            "Table created with format version 2 and partitioned by event_date and symbol."
        )
    else:
        df.writeTo(f"{transform_db}.{aggtrades_table}").overwritePartitions()
        logger.info("Table already exists. Partitions overwritten.")
