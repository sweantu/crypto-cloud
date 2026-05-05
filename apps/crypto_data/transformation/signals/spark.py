import logging

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_signals_data(
    spark: SparkSession,
    date,
    transform_db,
    kline_features_table,
    signals_table,
):
    ema_signals_df = get_ema_signals(spark, transform_db, kline_features_table, date)
    rsi_signals_df = get_rsi_signals(spark, transform_db, kline_features_table, date)
    macd_signals_df = get_macd_signals(spark, transform_db, kline_features_table, date)
    patterns_df = get_patterns_signals(spark, transform_db, kline_features_table, date)

    signals_df = (
        ema_signals_df.unionByName(rsi_signals_df)
        .unionByName(macd_signals_df)
        .unionByName(patterns_df)
        .withColumnRenamed("open_time", "signal_time")
        .withColumnRenamed("close_price", "entry_price")
        .withColumn(
            "signal_id",
            F.md5(
                F.concat_ws(
                    "_",
                    F.col("symbol"),
                    F.col("interval"),
                    F.col("signal_time"),
                    F.col("date"),
                    F.col("signal_type"),
                )
            ),
        )
        .withColumn(
            "signal_direction",
            F.when(
                F.col("signal_type").isin(
                    "ema_cross_up",
                    "rsi_oversold",
                    "macd_cross_up",
                    "bullish_engulfing",
                    "hammer",
                ),
                "bullish",
            ).otherwise("bearish"),
        )
    )

    signals_df.createOrReplaceTempView("signals_view")
    final_signals_df = spark.sql(f"""
    select 
        *,
        CASE
            WHEN hour(signal_time) BETWEEN 0 AND 7 THEN 'asia'
            WHEN hour(signal_time) BETWEEN 8 AND 15 THEN 'europe'
            ELSE 'us'
        END AS session_name,
        dayofweek(signal_time) IN (1,7) AS is_weekend
    from signals_view
    """)

    final_signals_df = final_signals_df.repartition("symbol", "interval").sortWithinPartitions("signal_time")

    if table_exists(spark, transform_db, signals_table):
        final_signals_df.writeTo(f"{transform_db}.{signals_table}").overwritePartitions()
        logger.info(f"Table {transform_db}.{signals_table} overwritten for {date}")
    else:
        final_signals_df.writeTo(f"{transform_db}.{signals_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy(F.col("date")).createOrReplace()
        logger.info(f"Table {transform_db}.{signals_table} created for {date}")


def get_ema_signals(spark, transform_db, kline_features_table, date):
    return spark.sql(f"""
    with cte as (
        select 
            *,
            lag(ema7) over(partition by symbol, interval order by open_time) as ema7_prev,
            lag(ema20) over(partition by symbol, interval order by open_time) as ema20_prev
        from {transform_db}.{kline_features_table}
        where date = '{date}'
    ), ema_cross_signals as (
        select
            symbol,
            interval,
            open_time,
            date,
            close_price,
            case
                when ema7_prev is null or ema20_prev is null then 'none'
                when ema7_prev <= ema20_prev and ema7 > ema20 then 'ema_cross_up'
                when ema7_prev >= ema20_prev and ema7 < ema20 then 'ema_cross_down'
                else 'none'
            end as signal_type
        from cte
    )
    select * from ema_cross_signals where signal_type != 'none'
    """)


def get_rsi_signals(spark, transform_db, kline_features_table, date):
    return spark.sql(f"""
    with cte as (
        select 
            symbol,
            interval,
            open_time,
            date,
            close_price,
            case
                when rsi6 < 30 then 'rsi_oversold'
                when rsi6 > 70 then 'rsi_overbought'
                else 'none'
            end as signal_type
        from {transform_db}.{kline_features_table}
        where date = '{date}'
    )
    select * from cte where signal_type != 'none'
    """)


def get_macd_signals(spark, transform_db, kline_features_table, date):
    return spark.sql(f"""
    with cte as (
        select 
            *,
            lag(macd) over(partition by symbol, interval order by open_time) as macd_prev,
            lag(signal) over(partition by symbol, interval order by open_time) as signal_prev
        from {transform_db}.{kline_features_table}
        where date = '{date}'
    )
    , macd_cross_signals as (
        select 
            symbol,
            interval,
            open_time,
            date,
            close_price,
            case
                when macd_prev is null or signal_prev is null then 'none'
                when macd_prev <= signal_prev and macd > signal then 'macd_cross_up'
                when macd_prev >= signal_prev and macd < signal then 'macd_cross_down'
                else 'none'
            end as signal_type
        from cte
    )
    select * from macd_cross_signals where signal_type != 'none'
    """)


def get_patterns_signals(spark, transform_db, kline_features_table, date):
    return spark.sql(f"""
    with hammer as (
        select
            symbol,
            interval,
            open_time,
            date,
            close_price,
            'hammer' as signal_type
        from {transform_db}.{kline_features_table}
        where date = '{date}' and pattern_hammer is true
    )
    , bullish_engulfing as (
        select 
            symbol,
            interval,
            open_time,
            date,
            close_price,
            'bullish_engulfing' as signal_type
        from {transform_db}.{kline_features_table}
        where date = '{date}' and pattern_bullish_engulfing is true
    )
    , bearish_engulfing as (
        select 
            symbol,
            interval,
            open_time,
            date,
            close_price,
            'bearish_engulfing' as signal_type
        from {transform_db}.{kline_features_table}
        where date = '{date}' and pattern_bearish_engulfing is true
    )
    select * from hammer
    union all
    select * from bullish_engulfing
    union all
    select * from bearish_engulfing
    """)
