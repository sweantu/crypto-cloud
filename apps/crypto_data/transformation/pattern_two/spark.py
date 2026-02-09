import logging

from common.ema import make_ema_in_chunks
from common.spark import table_exists
from pyspark.sql import SparkSession, types
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_pattern_two_data(
    spark: SparkSession,
    symbol,
    landing_date,
    transform_db,
    klines_table,
    pattern_two_table,
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

    schema = types.StructType(
        [
            *df_sorted.schema.fields,  # keep all original fields
            types.StructField("ema7", types.DoubleType(), True),
            types.StructField("ema20", types.DoubleType(), True),
        ]
    )

    if table_exists(spark, transform_db, pattern_two_table):
        sql_stmt = f"""
        select ema7, ema20 from {transform_db}.{pattern_two_table}
        where landing_date = date_sub(DATE('{landing_date}'), 1) AND symbol = '{symbol}'
        order by group_id desc
        limit 1
        """
        row = spark.sql(sql_stmt).first()
        prev_ema7, prev_ema20 = (row["ema7"], row["ema20"]) if row else (None, None)
    else:
        prev_ema7, prev_ema20 = None, None

    ema_in_chunks_with_state = make_ema_in_chunks(prev_ema7, prev_ema20)

    df = df_sorted.mapInPandas(ema_in_chunks_with_state, schema)

    df.createOrReplaceTempView("temp")
    df = spark.sql("""
    with cte as (
        select
            *,
            case 
                when ema7 > ema20 then 'uptrend' 
                when ema7 < ema20 then 'downtrend' 
                else NULL 
            end as trend,
            LAG(open_price, 1) over(order by group_id) as open_price_prev,
            LAG(close_price, 1) over(order by group_id) as close_price_prev
        from temp
    )
    select
        group_id,
        group_date,
        open_time,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        close_time,
        landing_date,
        symbol,
        ema7,
        ema20,
        trend,
        case 
            when close_price_prev < open_price_prev
                and close_price > open_price
                and open_price < close_price_prev
                and close_price > open_price_prev
                and trend = 'downtrend'
            then 'bullish engulfing'
            when close_price_prev > open_price_prev
                and close_price < open_price
                and open_price > close_price_prev
                and close_price < open_price_prev
                and trend = 'uptrend'
            then 'bearish engulfing'
            else NULL
        end as pattern
    from cte
    """)

    if table_exists(spark, transform_db, pattern_two_table):
        df.writeTo(f"{transform_db}.{pattern_two_table}").overwritePartitions()
    else:
        df.writeTo(f"{transform_db}.{pattern_two_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy(F.col("symbol"), F.col("landing_date")).createOrReplace()
