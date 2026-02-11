import logging

from common.macd import make_macd_in_chunks
from pyspark.sql import types
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_macd_data(
    spark, transform_db, symbol, landing_date, klines_table, macd_table
):
    sql_stmt = f"""
    select * from {transform_db}.{klines_table}
    where landing_date = DATE('{landing_date}') AND symbol = '{symbol}'
    """
    df_sorted = (
        spark.sql(sql_stmt)
        .coalesce(1)  # one partition, not shuffle
        .sortWithinPartitions("group_id")
    )

    if table_exists(spark, transform_db, macd_table):
        sql_stmt = f"""
        SELECT
            ema12      AS macd_ema12,
            ema26      AS macd_ema26,
            signal     AS macd_signal
        FROM {transform_db}.{macd_table}
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

    df = df_sorted.mapInPandas(macd_in_chunks_with_state, schema)

    if table_exists(spark, transform_db, macd_table):
        df.writeTo(f"{transform_db}.{macd_table}").overwritePartitions()
    else:
        (
            df.writeTo(f"{transform_db}.{macd_table}")
            .tableProperty("format-version", "2")
            .partitionedBy("symbol", "landing_date")
            .createOrReplace()
        )
